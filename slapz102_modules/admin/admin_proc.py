import sys
import hashlib
import traceback
import time

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

import database
import config

def _get_db():
    client = database.get_database(config.mainDB)
    return client[config.mainDB]
# end def

def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
# end def

def login(username, password, user_agent="", ip_address=""):
    try:
        db = _get_db()
        hashed_pw = _hash_password(password)

        user = db["db_user"].find_one({
            "username"  : username,
            "password"  : hashed_pw,
            "role"      : "ADMIN",
            "is_active" : "TRUE"
        })

        if user is None:
            return { "ok": False, "msg": "Username atau password salah." }
        # end if

        # Log session to DB
        session_rec              = database.get_record("db_admin_session")
        session_rec["fk_user_id"] = str(user["_id"])
        session_rec["username"]   = username
        session_rec["role"]       = user["role"]
        session_rec["login_time"] = int(time.time() * 1000)
        session_rec["user_agent"] = user_agent
        session_rec["ip_address"] = ip_address
        session_rec["state"]      = "LOGIN_SUCCESS"
        db["db_admin_session"].insert_one(session_rec)

        return {
            "ok"        : True,
            "user_id"   : str(user["_id"]),
            "username"  : user["username"],
            "name"      : user.get("name", "Admin"),
            "role"      : user["role"],
        }
    except Exception:
        print(traceback.format_exc())
        return { "ok": False, "msg": "Terjadi kesalahan server." }
    # end try
# end def

def get_dashboard_stats():
    try:
        db = _get_db()

        total_users  = db["db_user"].count_documents({ "is_deleted": { "$ne": True } })
        total_hymns  = db["db_hymn"].count_documents({ "is_deleted": { "$ne": True } })
        total_active = db["db_hymn"].count_documents({ "status": "ACTIVE", "is_deleted": { "$ne": True } })

        recent_logins = list(
            db["db_admin_session"]
            .find({ "state": "LOGIN_SUCCESS" })
            .sort("login_time", -1)
            .limit(5)
        )

        for row in recent_logins:
            row["_id"] = str(row["_id"])
            ts = row.get("login_time", 0)
            if ts:
                row["login_time_str"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(ts / 1000)
                )
            else:
                row["login_time_str"] = "-"
            # end if
        # end for

        return {
            "ok"            : True,
            "total_users"   : total_users,
            "total_hymns"   : total_hymns,
            "total_active"  : total_active,
            "recent_logins" : recent_logins,
        }
    except Exception:
        print(traceback.format_exc())
        return {
            "ok"            : False,
            "total_users"   : 0,
            "total_hymns"   : 0,
            "total_active"  : 0,
            "recent_logins" : [],
        }
    # end try
def get_floor_plan():
    try:
        db = _get_db()
        plan = db["db_floor_plan"].find_one({"plan_name": "main_floor"})
        if not plan:
            return {"ok": True, "data": {"lines": [], "tables": []}}
        
        return {"ok": True, "data": plan.get("elements", {"lines": [], "tables": []})}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def save_floor_plan(payload):
    try:
        db = _get_db()
        db["db_floor_plan"].update_one(
            {"plan_name": "main_floor"},
            {"$set": {"elements": payload, "updated_at": int(time.time() * 1000)}},
            upsert=True
        )
        
        # Also sync tables to db_table for validation
        if "tables" in payload:
            for tbl in payload["tables"]:
                table_id = str(tbl.get("id", "")).strip()
                if not table_id:
                    continue

                table_name = str(tbl.get("table_name", "")).strip()
                display_label = table_name if table_name else str(tbl.get("label", "")).strip() or table_id
                db["db_table"].update_one(
                    {"table_id": table_id},
                    {
                        "$set": {
                            "seats": tbl.get("seats", 0),
                            "label": display_label,
                            "table_name": table_name
                        },
                        "$setOnInsert": {
                            "status": "Available",
                            "order_pkey": "",
                            "reserved_at": 0
                        }
                    },
                    upsert=True
                )
                
        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}
def get_active_orders():
    try:
        db = _get_db()
        orders = list(db["db_order"].find({
            "$or": [
                {"payment_status": {"$ne": "Paid"}},
                {"fulfillment_status": {"$ne": "Done"}}
            ]
        }).sort("rec_timestamp", -1))
        
        for o in orders:
            o["_id"] = str(o["_id"])
        
        return {"ok": True, "data": orders}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def get_reserved_tables():
    """Return all tables that are currently not Available (Reserved or Occupied)."""
    try:
        db = _get_db()
        tables = list(db["db_table"].find({"status": {"$ne": "Available"}}))
        for t in tables:
            t["_id"] = str(t["_id"])
        return {"ok": True, "data": tables}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "data": []}

def release_table_by_id(table_id):
    """
    Release a single table by table_id.
    - Frees the db_table record back to Available.
    - Removes this table from the linked order's table_ids array.
    - If the order has no remaining reserved tables → auto-close (fulfillment_status=Done).
    All logic is server-side to prevent frontend inconsistency.
    """
    try:
        db = _get_db()

        # Fetch the table record to get its linked order
        table_rec = db["db_table"].find_one({"table_id": table_id})
        if not table_rec:
            return {"ok": False, "msg": f"Table '{table_id}' not found in db_table"}

        order_pkey = table_rec.get("order_pkey", "")

        # 1. Free the physical seat
        db["db_table"].update_one(
            {"table_id": table_id},
            {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
        )

        order_done = False
        remaining_tables = []

        if order_pkey:
            # 2. Remove this table from the order's table_ids array atomically
            db["db_order"].update_one(
                {"pkey": order_pkey},
                {"$pull": {"table_ids": table_id}}
            )

            # 3. Re-fetch the order to check remaining tables
            order = db["db_order"].find_one({"pkey": order_pkey})
            if order:
                remaining_ids = order.get("table_ids", [])

                # Cross-check: which of the remaining IDs are still Reserved in db_table?
                still_reserved = db["db_table"].count_documents({
                    "table_id": {"$in": remaining_ids},
                    "status":   {"$ne": "Available"}
                })

                remaining_tables = remaining_ids

                if still_reserved == 0:
                    # All seats freed — close the order
                    db["db_order"].update_one(
                        {"pkey": order_pkey},
                        {"$set": {
                            "fulfillment_status": "Done",
                            "seat_released_at":   int(time.time() * 1000)
                        }}
                    )
                    order_done = True

        return {
            "ok":               True,
            "order_done":       order_done,
            "remaining_tables": remaining_tables
        }
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def update_order_status(order_id, update_type, new_status):
    try:
        db = _get_db()
        field = "payment_status" if update_type == "payment" else "fulfillment_status"

        # Reserve selected seats only when payment is confirmed.
        if update_type == "payment" and new_status == "Paid":
            order = db["db_order"].find_one({"pkey": order_id})
            if not order:
                return {"ok": False, "msg": "Order not found"}

            table_ids = order.get("table_ids", [])
            if not table_ids and order.get("table_id"):
                table_ids = [order["table_id"]]

            locked_ids = []
            for tid in table_ids:
                locked = db["db_table"].find_one_and_update(
                    {"table_id": tid, "status": "Available"},
                    {"$set": {"status": "Reserved", "order_pkey": order_id, "reserved_at": int(time.time() * 1000)}}
                )
                if not locked:
                    if locked_ids:
                        db["db_table"].update_many(
                            {"table_id": {"$in": locked_ids}},
                            {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
                        )
                    return {"ok": False, "msg": f"Seat {tid} is no longer available. Please refresh and choose another seat."}
                locked_ids.append(tid)

        db["db_order"].update_one(
            {"pkey": order_id},
            {"$set": {field: new_status}}
        )

        # Auto-release tables whenever fulfillment reaches 'Done'
        if update_type == "fulfillment" and new_status == "Done":
            order = db["db_order"].find_one({"pkey": order_id})
            if order:
                table_ids = order.get("table_ids", [])
                if not table_ids and order.get("table_id"):
                    table_ids = [order["table_id"]]
                if table_ids:
                    db["db_table"].update_many(
                        {"table_id": {"$in": table_ids}},
                        {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
                    )

        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def release_table(order_id):
    """Mark order as Done and free all linked tables back to Available."""
    try:
        db = _get_db()

        order = db["db_order"].find_one({"pkey": order_id})
        if not order:
            return {"ok": False, "msg": "Order not found"}

        # Collect all table IDs linked to this order
        table_ids = order.get("table_ids", [])
        if not table_ids and order.get("table_id"):
            table_ids = [order["table_id"]]

        # Release tables back to Available
        if table_ids:
            db["db_table"].update_many(
                {"table_id": {"$in": table_ids}},
                {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
            )

        # Mark order as fully done
        db["db_order"].update_one(
            {"pkey": order_id},
            {"$set": {"fulfillment_status": "Done", "seat_released_at": int(time.time() * 1000)}}
        )

        return {"ok": True, "released_tables": table_ids}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def reassign_order_tables(order_id, new_table_ids):
    try:
        db = _get_db()
        order = db["db_order"].find_one({"pkey": order_id})
        if not order:
            return {"ok": False, "msg": "Order not found"}

        if new_table_ids is None:
            new_table_ids = []

        # Normalize and deduplicate while preserving order
        cleaned = []
        for tid in new_table_ids:
            t = str(tid).strip()
            if t and t not in cleaned:
                cleaned.append(t)

        old_ids = order.get("table_ids", [])
        if not old_ids and order.get("table_id"):
            old_ids = [order.get("table_id")]

        payment_paid = order.get("payment_status") == "Paid"

        if payment_paid:
            to_add = [tid for tid in cleaned if tid not in old_ids]
            to_remove = [tid for tid in old_ids if tid not in cleaned]

            locked_ids = []
            for tid in to_add:
                locked = db["db_table"].find_one_and_update(
                    {
                        "table_id": tid,
                        "$or": [
                            {"status": "Available"},
                            {"order_pkey": order_id}
                        ]
                    },
                    {"$set": {"status": "Reserved", "order_pkey": order_id, "reserved_at": int(time.time() * 1000)}}
                )
                if not locked:
                    if locked_ids:
                        db["db_table"].update_many(
                            {"table_id": {"$in": locked_ids}},
                            {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
                        )
                    return {"ok": False, "msg": f"Seat {tid} is not available."}
                locked_ids.append(tid)

            if to_remove:
                db["db_table"].update_many(
                    {"table_id": {"$in": to_remove}, "order_pkey": order_id},
                    {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
                )

        db["db_order"].update_one(
            {"pkey": order_id},
            {"$set": {"table_ids": cleaned, "table_id": cleaned[0] if cleaned else ""}}
        )
        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def reset_all_tables():
    """Emergency reset — set every table back to Available regardless of order state."""
    try:
        db = _get_db()
        result = db["db_table"].update_many(
            {},
            {"$set": {"status": "Available", "order_pkey": "", "reserved_at": 0}}
        )
        return {"ok": True, "modified": result.modified_count}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def get_order_history(order_status="", payment_status=""):
    try:
        db = _get_db()
        query_filter = {}

        if order_status and order_status != "all":
            query_filter["fulfillment_status"] = order_status

        if payment_status and payment_status != "all":
            query_filter["payment_status"] = payment_status

        orders = list(
            db["db_order"]
            .find(query_filter)
            .sort("rec_timestamp", -1)
        )

        for row in orders:
            row["_id"] = str(row["_id"])
            ts = row.get("rec_timestamp", 0)
            if ts:
                row["created_time_str"] = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(ts / 1000)
                )
            else:
                row["created_time_str"] = "-"

        return {"ok": True, "data": orders}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "data": [], "msg": "Database error"}

def set_table_status(table_id, new_status):
    try:
        db = _get_db()
        if not table_id:
            return {"ok": False, "msg": "table_id required"}

        valid_status = ["Available", "Reserved", "Occupied"]
        if new_status not in valid_status:
            return {"ok": False, "msg": "invalid status"}

        table = db["db_table"].find_one({"table_id": table_id})
        if not table:
            return {"ok": False, "msg": f"Table '{table_id}' not found"}

        update_data = {"status": new_status}
        if new_status == "Available":
            update_data["order_pkey"] = ""
            update_data["reserved_at"] = 0
        elif new_status == "Reserved":
            update_data["order_pkey"] = table.get("order_pkey") or "MANUAL_ADMIN"
            update_data["reserved_at"] = int(time.time() * 1000)
        elif new_status == "Occupied":
            update_data["order_pkey"] = table.get("order_pkey") or "MANUAL_ADMIN"
            update_data["reserved_at"] = table.get("reserved_at") or int(time.time() * 1000)

        db["db_table"].update_one({"table_id": table_id}, {"$set": update_data})
        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

# ─── Menu Management ──────────────────────────────────────────────────────────

def get_menus():
    """Return all active menu items sorted by category then name."""
    try:
        db = _get_db()
        menus = list(db["db_menu"].find({"is_deleted": {"$ne": True}}).sort("created_at", 1))
        for m in menus:
            m["_id"] = str(m["_id"])
        return {"ok": True, "data": menus}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "data": [], "msg": "Database error"}

def get_available_menus():
    """Return available menu items for customer reservation page."""
    try:
        db = _get_db()
        menus = list(
            db["db_menu"].find({
                "is_deleted": {"$ne": True},
                "is_available": {"$ne": False}
            }).sort([("category", 1), ("name", 1)])
        )
        for m in menus:
            m["_id"] = str(m["_id"])
        return {"ok": True, "data": menus}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "data": [], "msg": "Database error"}

def save_menu(menu_id, name, category, price, description, image_url, is_available):
    """Insert or update a menu item."""
    try:
        import uuid
        db = _get_db()
        now = int(time.time() * 1000)

        if menu_id:
            # Update existing
            db["db_menu"].update_one(
                {"menu_id": menu_id},
                {"$set": {
                    "name": name,
                    "category": category,
                    "price": int(price),
                    "description": description,
                    "image_url": image_url,
                    "is_available": bool(is_available),
                    "updated_at": now
                }}
            )
        else:
            new_id = "MENU-" + str(uuid.uuid4())[:8].upper()
            db["db_menu"].insert_one({
                "menu_id": new_id,
                "name": name,
                "category": category,
                "price": int(price),
                "description": description,
                "image_url": image_url,
                "is_available": bool(is_available),
                "is_deleted": False,
                "created_at": now,
                "updated_at": now
            })
            menu_id = new_id

        return {"ok": True, "menu_id": menu_id}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def delete_menu(menu_id):
    """Soft-delete a menu item."""
    try:
        db = _get_db()
        db["db_menu"].update_one(
            {"menu_id": menu_id},
            {"$set": {"is_deleted": True, "updated_at": int(time.time() * 1000)}}
        )
        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def get_menu_types():
    """Return menu types/categories that admin configured."""
    try:
        db = _get_db()
        rows = list(
            db["db_menu_type"]
            .find({"is_deleted": {"$ne": True}})
            .sort("name", 1)
        )
        for row in rows:
            row["_id"] = str(row["_id"])
        return {"ok": True, "data": rows}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "data": [], "msg": "Database error"}

def save_menu_type(type_id, name):
    """Insert or update menu type."""
    try:
        import uuid
        db = _get_db()
        now = int(time.time() * 1000)
        clean_name = str(name or "").strip()
        if not clean_name:
            return {"ok": False, "msg": "Type name is required"}

        existing = db["db_menu_type"].find_one({
            "name": {"$regex": f"^{clean_name}$", "$options": "i"},
            "is_deleted": {"$ne": True}
        })
        if existing and (not type_id or existing.get("type_id") != type_id):
            return {"ok": False, "msg": "Type already exists"}

        if type_id:
            db["db_menu_type"].update_one(
                {"type_id": type_id},
                {"$set": {"name": clean_name, "updated_at": now, "is_deleted": False}}
            )
            return {"ok": True, "type_id": type_id}

        new_id = "TYPE-" + str(uuid.uuid4())[:8].upper()
        db["db_menu_type"].insert_one({
            "type_id": new_id,
            "name": clean_name,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now
        })
        return {"ok": True, "type_id": new_id}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def delete_menu_type(type_id):
    """Soft delete menu type if not used by active menus."""
    try:
        db = _get_db()
        type_row = db["db_menu_type"].find_one({"type_id": type_id, "is_deleted": {"$ne": True}})
        if not type_row:
            return {"ok": False, "msg": "Type not found"}

        type_name = type_row.get("name", "")
        used_count = db["db_menu"].count_documents({
            "is_deleted": {"$ne": True},
            "category": type_name
        })
        if used_count > 0:
            return {"ok": False, "msg": "Type is used by menu items"}

        db["db_menu_type"].update_one(
            {"type_id": type_id},
            {"$set": {"is_deleted": True, "updated_at": int(time.time() * 1000)}}
        )
        return {"ok": True}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}
