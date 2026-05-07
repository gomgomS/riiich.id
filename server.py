import sys
sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

import config
import database
from flask import Flask

app = Flask(__name__)
app.secret_key = config.G_FLASK_SECRET

# Init DB connection
database.connect_db()

# Serve company profile landing page at root
@app.route("/")
def root():
    from view.company_profile import view_company_profile
    return view_company_profile.html_company_profile()
# end def

# Register Blueprints
from admin.admin_blueprint import admin_blueprint
app.register_blueprint(admin_blueprint)

from scrapper.scrapper_blueprint import scrapper_blueprint
app.register_blueprint(scrapper_blueprint)

from ss_bank.ss_bank_blueprint import ss_bank_blueprint
app.register_blueprint(ss_bank_blueprint)

from company_profile.company_profile_blueprint import company_profile_blueprint
app.register_blueprint(company_profile_blueprint)

from reservation.reservation_blueprint import reservation_blueprint
app.register_blueprint(reservation_blueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)
# end if
