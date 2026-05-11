import sys
import traceback

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from flask import Blueprint, request, session, redirect, url_for
from admin import admin_proc
from view.admin import view_admin

admin_blueprint = Blueprint("admin_blueprint", __name__)

def _is_logged_in():
    return session.get("admin_logged_in") == True
# end def

@admin_blueprint.route("/admin/login", methods=["GET"])
def login_page():
    try:
        if _is_logged_in():
            return redirect(url_for("admin_blueprint.dashboard"))
        # end if
        return view_admin.html_login()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500
    # end try
# end def

@admin_blueprint.route("/admin/login", methods=["POST"])
def login_submit():
    try:
        username   = request.form.get("username", "").strip()
        password   = request.form.get("password", "").strip()
        user_agent = request.headers.get("User-Agent", "")
        ip_address = request.remote_addr or ""

        result = admin_proc.login(username, password, user_agent, ip_address)

        if not result["ok"]:
            return view_admin.html_login(error=result["msg"])
        # end if

        session["admin_logged_in"] = True
        session["admin_user_id"]   = result["user_id"]
        session["admin_username"]  = result["username"]
        session["admin_name"]      = result["name"]
        session["admin_role"]      = result["role"]

        return redirect(url_for("admin_blueprint.dashboard"))
    except Exception:
        print(traceback.format_exc())
        return view_admin.html_login(error="Terjadi kesalahan. Coba lagi.")
    # end try
# end def

@admin_blueprint.route("/admin/logout", methods=["GET"])
def logout():
    try:
        session.clear()
        return redirect(url_for("admin_blueprint.login_page"))
    except Exception:
        print(traceback.format_exc())
        return redirect(url_for("admin_blueprint.login_page"))
    # end try
# end def

@admin_blueprint.route("/admin", methods=["GET"])
@admin_blueprint.route("/admin/dashboard", methods=["GET"])
def dashboard():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        return view_admin.html_dashboard()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@admin_blueprint.route("/admin/floor_designer", methods=["GET"])
def floor_designer():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        return view_admin.html_floor_designer()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@admin_blueprint.route("/admin/operations", methods=["GET"])
def operations():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        return view_admin.html_operations()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@admin_blueprint.route("/admin/seat-map-control", methods=["GET"])
def seat_map_control():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        return view_admin.html_seat_map_control()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@admin_blueprint.route("/admin/operations/history", methods=["GET"])
def operations_history():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))

        order_status = request.args.get("order_status", "all")
        payment_status = request.args.get("payment_status", "all")
        try:
            page = int(request.args.get("page", 1))
        except (TypeError, ValueError):
            page = 1
        try:
            per_page = int(request.args.get("per_page", 20))
        except (TypeError, ValueError):
            per_page = 20
        return view_admin.html_operations_history(order_status, payment_status, page, per_page)
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

from flask import jsonify

@admin_blueprint.route("/admin/api/floor_plan", methods=["GET"])
def api_get_floor_plan():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        
        result = admin_proc.get_floor_plan()
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/floor_plan/save", methods=["POST"])
def api_save_floor_plan():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
            
        payload = request.get_json()
        result = admin_proc.save_floor_plan(payload)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500
@admin_blueprint.route("/admin/api/orders", methods=["GET"])
def api_get_orders():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        
        result = admin_proc.get_active_orders()
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/menus/for-order", methods=["GET"])
def api_menus_for_order():
    """Same menu catalog as customer reservation (available items only)."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        result = admin_proc.get_available_menus()
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/order/status", methods=["POST"])
def api_update_order_status():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
            
        payload = request.get_json()
        order_id = payload.get("order_id")
        update_type = payload.get("update_type")
        new_status = payload.get("new_status")
        
        result = admin_proc.update_order_status(order_id, update_type, new_status)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/order/release", methods=["POST"])
def api_release_table():
    """Release all tables linked to an order back to Available status."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401

        payload  = request.get_json()
        order_id = payload.get("order_id")

        result = admin_proc.release_table(order_id)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/order/reassign_tables", methods=["POST"])
def api_reassign_order_tables():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401

        payload = request.get_json()
        order_id = payload.get("order_id")
        table_ids = payload.get("table_ids", [])
        result = admin_proc.reassign_order_tables(order_id, table_ids)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/order/update", methods=["POST"])
def api_update_order_transaction():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401

        payload = request.get_json() or {}
        order_id = payload.get("order_id", "")
        if not order_id:
            return jsonify({"ok": False, "msg": "order_id required"}), 400

        body = {k: v for k, v in payload.items() if k != "order_id"}
        result = admin_proc.update_order_transaction(order_id, body)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/tables/reset", methods=["POST"])
def api_reset_all_tables():
    """Emergency reset — clear ALL tables back to Available at once."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401

        result = admin_proc.reset_all_tables()
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/tables/reserved", methods=["GET"])
def api_get_reserved_tables():
    """Return all tables currently marked as Reserved or Occupied."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        result = admin_proc.get_reserved_tables()
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/tables/release", methods=["POST"])
def api_release_single_table():
    """Release one table by table_id — all logic delegated to admin_proc."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        payload  = request.get_json()
        table_id = payload.get("table_id")
        if not table_id:
            return jsonify({"ok": False, "msg": "table_id required"}), 400
        result = admin_proc.release_table_by_id(table_id)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/table/status", methods=["POST"])
def api_set_table_status():
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        payload = request.get_json()
        table_id = payload.get("table_id", "")
        new_status = payload.get("status", "")
        result = admin_proc.set_table_status(table_id, new_status)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

@admin_blueprint.route("/admin/api/order/cancel", methods=["POST"])
def api_cancel_order():
    """Cancel an order — sets status to Cancelled and frees all reserved tables."""
    try:
        if not _is_logged_in():
            return jsonify({"ok": False, "msg": "Unauthorized"}), 401
        payload = request.get_json()
        order_id = payload.get("order_id", "")
        if not order_id:
            return jsonify({"ok": False, "msg": "order_id required"}), 400
        result = admin_proc.cancel_order(order_id)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500

# ─── Menu Management ──────────────────────────────────────────────────────────

@admin_blueprint.route("/admin/menu", methods=["GET"])
def menu_management():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        admin_name = session.get("admin_name", "Admin")
        menus_result = admin_proc.get_menus()
        types_result = admin_proc.get_menu_types()
        menus = menus_result.get("data", []) if menus_result.get("ok") else []
        menu_types = types_result.get("data", []) if types_result.get("ok") else []
        edit_menu_id = request.args.get("edit_menu_id", "").strip()
        edit_type_id = request.args.get("edit_type_id", "").strip()
        edit_menu = next((m for m in menus if m.get("menu_id") == edit_menu_id), None)
        edit_type = next((t for t in menu_types if t.get("type_id") == edit_type_id), None)
        from flask import render_template
        return render_template(
            "admin/menu_management.html",
            admin_name=admin_name,
            menus=menus,
            menu_types=menu_types,
            edit_menu=edit_menu,
            edit_type=edit_type
        )
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@admin_blueprint.route("/admin/menu/type/save", methods=["POST"])
def form_save_menu_type():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        type_id = request.form.get("type_id", "").strip()
        name = request.form.get("type_name", "").strip()
        result = admin_proc.save_menu_type(type_id=type_id, name=name)
        if not result.get("ok"):
            return redirect(url_for("admin_blueprint.menu_management", edit_type_id=type_id))
        return redirect(url_for("admin_blueprint.menu_management"))
    except Exception:
        print(traceback.format_exc())
        return redirect(url_for("admin_blueprint.menu_management"))

@admin_blueprint.route("/admin/menu/type/delete", methods=["POST"])
def form_delete_menu_type():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        type_id = request.form.get("type_id", "").strip()
        admin_proc.delete_menu_type(type_id)
        return redirect(url_for("admin_blueprint.menu_management"))
    except Exception:
        print(traceback.format_exc())
        return redirect(url_for("admin_blueprint.menu_management"))

@admin_blueprint.route("/admin/menu/save", methods=["POST"])
def form_save_menu():
    import os, uuid
    from werkzeug.utils import secure_filename
    from flask import current_app
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))

        menu_id = request.form.get("menu_id", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price = request.form.get("price", "0").strip()
        description = request.form.get("description", "").strip()
        image_url = request.form.get("image_url", "").strip()
        is_available = request.form.get("is_available", "") == "on"

        # Optional image upload from form POST
        if "image" in request.files and request.files["image"].filename:
            file = request.files["image"]
            safe_name = secure_filename(file.filename)
            root, ext_raw = os.path.splitext(safe_name)
            ext = ext_raw.replace(".", "").lower()
            allowed = {"png", "jpg", "jpeg", "webp", "gif"}
            if root and ext in allowed:
                unique_name = f"{uuid.uuid4().hex}.{ext}"
                upload_dir = os.path.join(current_app.root_path, "static", "uploads", "menu")
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, unique_name))
                image_url = f"/static/uploads/menu/{unique_name}"

        admin_proc.save_menu(
            menu_id=menu_id,
            name=name,
            category=category,
            price=price or 0,
            description=description,
            image_url=image_url,
            is_available=is_available
        )
        return redirect(url_for("admin_blueprint.menu_management"))
    except Exception:
        print(traceback.format_exc())
        return redirect(url_for("admin_blueprint.menu_management"))

@admin_blueprint.route("/admin/menu/delete", methods=["POST"])
def form_delete_menu():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        menu_id = request.form.get("menu_id", "").strip()
        admin_proc.delete_menu(menu_id)
        return redirect(url_for("admin_blueprint.menu_management"))
    except Exception:
        print(traceback.format_exc())
        return redirect(url_for("admin_blueprint.menu_management"))

