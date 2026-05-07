import sys
sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from flask import render_template, session, redirect, url_for
from admin import admin_proc

def html_login(error=None):
    return render_template("admin/login.html", error=error)
# end def

def html_dashboard():
    stats = admin_proc.get_dashboard_stats()
    admin_name = session.get("admin_name", "Admin")
    return render_template("admin/dashboard.html", stats=stats, admin_name=admin_name)

def html_floor_designer():
    return render_template("admin/floor_designer.html")

def html_operations():
    admin_name = session.get("admin_name", "Admin")
    return render_template("admin/operations.html", admin_name=admin_name)

def html_seat_map_control():
    admin_name = session.get("admin_name", "Admin")
    return render_template("admin/seat_map_control.html", admin_name=admin_name)

def html_operations_history(order_status="all", payment_status="all"):
    admin_name = session.get("admin_name", "Admin")
    result = admin_proc.get_order_history(order_status, payment_status)
    orders = result.get("data", []) if result.get("ok") else []
    return render_template(
        "admin/operations_history.html",
        admin_name=admin_name,
        orders=orders,
        selected_order_status=order_status,
        selected_payment_status=payment_status
    )
