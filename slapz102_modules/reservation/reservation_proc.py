import sys
import traceback
import time

sys.path.append("slapz102_core")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")

import database
import config

def _get_db():
    return database.get_database(config.mainDB)[config.mainDB]

def get_reservation_data():
    try:
        db = _get_db()
        plan = db["db_floor_plan"].find_one({"plan_name": "main_floor"})
        elements = plan.get("elements", {"lines": [], "tables": []}) if plan else {"lines": [], "tables": []}
        
        # Merge real-time status
        table_statuses = {t["table_id"]: t["status"] for t in db["db_table"].find({})}
        for t in elements["tables"]:
            t["status"] = table_statuses.get(t["id"], "Available")
            
        return {"ok": True, "floor_plan": elements}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}

def submit_reservation(payload):
    try:
        db = _get_db()
        
        # Support both single table_id (legacy) and multi table_ids
        selected_ids = payload.get("table_ids", [])
        if not selected_ids and payload.get("table_id"):
            selected_ids = [payload.get("table_id")]

        # Create order record
        order_rec = database.get_record("db_order")
        order_rec["flow_type"]          = payload.get("flow_type", "Dine-In")
        order_rec["contact"]            = payload.get("contact", {})
        order_rec["arrival_time"]       = payload.get("arrival_time", "")
        order_rec["seat_mode"]          = payload.get("seat_mode", "choose")
        order_rec["seating_notes"]      = payload.get("seating_notes", "")
        order_rec["table_ids"]          = selected_ids
        order_rec["table_id"]           = selected_ids[0] if selected_ids else ""  # legacy compat
        order_rec["party_size"]         = payload.get("party_size", 1)
        order_rec["items"]              = payload.get("items", [])
        order_rec["service_timing"]     = payload.get("service_timing", "Serve on Arrival")
        order_rec["payment_status"]     = "Unpaid"
        order_rec["fulfillment_status"] = "Pending"
        order_rec["total_amount"]       = payload.get("total_amount", 0)

        db["db_order"].insert_one(order_rec)

        return {"ok": True, "order_id": order_rec["pkey"]}
    except Exception:
        print(traceback.format_exc())
        return {"ok": False, "msg": "Database error"}
