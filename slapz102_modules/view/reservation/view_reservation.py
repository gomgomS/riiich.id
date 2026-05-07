import sys
sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")

from flask import render_template
from reservation import reservation_proc
from company_profile import company_profile_proc

def html_reservation():
    res_data = reservation_proc.get_reservation_data()
    company_data = company_profile_proc.get_company_profile()
    return render_template("reservation.html", data=company_data, floor_plan=res_data.get("floor_plan", {}))
