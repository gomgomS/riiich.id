import sys
import traceback
from flask import Blueprint, request, jsonify

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from view.reservation import view_reservation
from reservation import reservation_proc

reservation_blueprint = Blueprint("reservation_blueprint", __name__)

@reservation_blueprint.route("/reservation", methods=["GET"])
def index():
    try:
        return view_reservation.html_reservation()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500

@reservation_blueprint.route("/api/reservation/submit", methods=["POST"])
def api_submit_reservation():
    try:
        payload = request.get_json()
        result = reservation_proc.submit_reservation(payload)
        return jsonify(result)
    except Exception:
        print(traceback.format_exc())
        return jsonify({"ok": False, "msg": "Server error"}), 500
