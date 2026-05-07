import sys
sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from flask import render_template, session
from scrapper import scrapper_proc

from datetime import datetime

# Indonesian weekday names (Python weekday: Mon=0 … Sun=6)
_HARI_MAP = {0:"Senin", 1:"Selasa", 2:"Rabu", 3:"Kamis", 4:"Jumat", 5:"Sabtu", 6:"Minggu"}

def _derive_hari(tanggal_str):
    """'2026-04-18' → 'Sabtu'"""
    try:
        dt = datetime.strptime(tanggal_str, "%Y-%m-%d")
        return _HARI_MAP[dt.weekday()]
    except Exception:
        return ""
    # end try
# end def

def html_scrapper_menu():
    return render_template("admin/scrapper/scrapper_menu.html", active_menu="scrapper")
# end def

def html_sekolah_sabat_form(error=None, prefill_url=""):
    return render_template(
        "admin/scrapper/sekolah_sabat_form.html",
        active_menu="scrapper",
        error=error,
        prefill_url=prefill_url
    )
# end def

def html_sekolah_sabat_result(url, tanggal):
    result = scrapper_proc.scrape_sekolah_sabat(url)
    hari   = _derive_hari(tanggal)
    return render_template(
        "admin/scrapper/sekolah_sabat_result.html",
        active_menu="scrapper",
        result=result,
        tanggal=tanggal,
        hari=hari,
        source_url=url
    )
# end def
