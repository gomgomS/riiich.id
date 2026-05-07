import sys
sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")
sys.path.append("slapz102_stdlib")
sys.path.append("slapz102_storage")

from flask import render_template
from ss_bank import ss_bank_proc

def html_bank_list(flash=None):
    data = ss_bank_proc.get_bank_list()
    return render_template("admin/ss_bank/ss_bank_list.html",
                           active_menu="ss_bank", data=data, flash=flash)
# end def

def html_pelajaran_detail(pelajaran_id):
    data = ss_bank_proc.get_pelajaran_detail(pelajaran_id)
    return render_template("admin/ss_bank/ss_bank_detail.html",
                           active_menu="ss_bank", data=data)
# end def

def html_materi_edit(materi_id):
    data = ss_bank_proc.get_materi(materi_id)
    return render_template("admin/ss_bank/ss_bank_edit.html",
                           active_menu="ss_bank", data=data)
# end def

def html_materi_create(prefill=None):
    if prefill is None: prefill = {}
    return render_template("admin/ss_bank/ss_bank_create.html",
                           active_menu="ss_bank", prefill=prefill)
# end def

