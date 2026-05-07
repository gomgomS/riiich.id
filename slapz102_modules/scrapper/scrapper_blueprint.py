import sys
import traceback

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from flask import Blueprint, request, session, redirect, url_for
from view.scrapper import view_scrapper

scrapper_blueprint = Blueprint("scrapper_blueprint", __name__)

def _is_logged_in():
    return session.get("admin_logged_in") == True
# end def

@scrapper_blueprint.route("/admin/scrapper", methods=["GET"])
def scrapper_menu():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        # end if
        return view_scrapper.html_scrapper_menu()
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500
    # end try
# end def

@scrapper_blueprint.route("/admin/scrapper/sekolah-sabat", methods=["GET"])
def sekolah_sabat_form():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        # end if
        prefill_url = request.args.get("url", "")
        return view_scrapper.html_sekolah_sabat_form(prefill_url=prefill_url)
    except Exception:
        print(traceback.format_exc())
        return "An error occurred", 500
    # end try
# end def

@scrapper_blueprint.route("/admin/scrapper/sekolah-sabat", methods=["POST"])
def sekolah_sabat_scrape():
    try:
        if not _is_logged_in():
            return redirect(url_for("admin_blueprint.login_page"))
        # end if

        url     = request.form.get("url", "").strip()
        tanggal = request.form.get("tanggal", "").strip()

        if not url:
            return view_scrapper.html_sekolah_sabat_form(error="URL tidak boleh kosong.")
        # end if

        if not url.startswith("http"):
            return view_scrapper.html_sekolah_sabat_form(error="URL tidak valid. Harus dimulai dengan http/https.")
        # end if

        return view_scrapper.html_sekolah_sabat_result(url, tanggal)
    except Exception:
        print(traceback.format_exc())
        return view_scrapper.html_sekolah_sabat_form(error="Terjadi kesalahan server.")
    # end try
# end def
