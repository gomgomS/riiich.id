# CLAUDE.md — Perumahan Web Timika

Flask legacy app dengan custom MVC pattern (LL frameworks). **Jangan ubah pattern yang sudah ada.**

---

## Git Workflow (WAJIB)

- **JANGAN** commit langsung ke `master` atau `staging` — keduanya **PROTECTED**
- Semua perubahan via branch baru → PR ke master
- Format branch: `feat/[task-name]` | `fix/[task-name]` | `hotfix/[task-name]`

```bash
git checkout master && git pull origin master
git checkout -b feat/nama-fitur
# ... kerjakan ...
git push origin feat/nama-fitur
# Buat PR via GitHub — jangan merge dari CLI
```

**DON'T:** `git push` ke master/staging, force push, merge tanpa PR, commit file sensitif.

---

## Sensitive Files — JANGAN COMMIT/EXPOSE

```
pytavia_settings/config.py   # DB credentials, secret keys
.env / *.env                 # Environment variables
*.pem / *.key / *.p12        # Certificates & private keys
credentials*.json            # Service account credentials
logs/ / *.log                # Application logs (mengandung PII)
venv/                        # Virtual environment
__pycache__/ / *.pyc
```

Jika tidak sengaja commit: `git reset HEAD~1` → tambah ke `.gitignore` → rotate credentials.

---

## Environment & Runtime

| | |
|-|-|
| **Python** | 3.8.10 x86_64 (bukan ARM64 — lihat `validasi_python_x86.md` untuk M1/M2) |
| **Virtual env** | `venv3810` |
| **Framework** | Flask |
| **DB Driver** | PyMongo 4.10.1 |
| **MongoDB** | `mongodb://127.0.0.1:27017/` → db: `perumahan` |
| **Port** | 5004 (dev), host: 0.0.0.0 |
| **Start (dev)** | `start.sh` → `FLASK_ENV=development` |
| **Start (prod)** | `start-pytavia.sh` → `FLASK_ENV=production` |

---

## Legacy Code Rules (WAJIB)

1. **Jangan refactor** tanpa instruksi eksplisit — jangan rename class/method/variable yang sudah ada
2. **Ikuti pattern existing** — copy dari file mirip, bukan buat pattern baru
3. **Backward compatible** — jangan ubah nama field response; buat endpoint baru jika perlu breaking change
4. **Database aman** — jangan drop/rename collection; tambah field baru, jangan ubah yang lama
5. **Jangan hardcode** URL, credential, atau secret key — baca dari `config` via `from pytavia_core import config`

---

## Project Structure

```
perumahan-web-timika-1/
├── server.py                   # Entrypoint — route & blueprint registration (no business logic di sini)
├── pytavia_core/               # Framework core — JANGAN MODIFIKASI
│   ├── database.py             # MongoDB connection
│   └── middleware.py           # @middleware_privilege
├── pytavia_modules/            # Semua business logic (satu folder per domain)
│   ├── [feature]/
│   │   ├── [feature]_proc.py   # Business logic
│   │   └── [feature]_blueprint.py  # (opsional) Routes
│   └── view/[feature]/
│       └── view_[feature].py   # View/render logic
├── pytavia_settings/           # Config files — SENSITIVE
├── pytavia_stdlib/             # Utilities: idgen, sanitize, utils
├── pytavia_storage/            # S3/Wasabi helpers
├── templates/                  # Jinja2 HTML templates
├── static/v2/                  # Tailwind CSS (perumahan.output.css)
└── static/css/atomic.css       # Legacy Atomic CSS
```

---

## Registered Blueprints

| Blueprint | Prefix |
|-----------|--------|
| `gsheet_blueprint` | `/api/gsheet` |
| `published_blueprint` | `/api/products/published` |
| `webhook_blueprint` | `/api/webhook` |
| `event_checkin_blueprint` | `/` (root) |

---

## Conventions (Quick Reference)

### File Naming
- Process: `[feature]_proc.py`
- View: `view_[feature].py`
- Blueprint: `[feature]_blueprint.py`

### Import (WAJIB di setiap file)
```python
import sys
sys.path.append("pytavia_core"    )
sys.path.append("pytavia_modules" )
sys.path.append("pytavia_settings")
sys.path.append("pytavia_stdlib"  )
sys.path.append("pytavia_storage" )
```

### Wajib di setiap route
```python
params = sanitize.clean_html_dic(request.form.to_dict())  # sanitize input
```

### Closing comments (WAJIB)
```python
if x:
    pass
# end if

for i in items:
    pass
# end for

def method():
    pass
# end def

class MyClass:
    pass
# end class
```

### CSS — Brand Colors
| Kebutuhan | Class |
|-----------|-------|
| Primary action | `bg-green text-white` |
| Selected state | `bg-cgreen-200 border-green` |
| Unselected state | `bg-white border-cgray-200` |
| Error | `border-red text-red` |
| **JANGAN pakai** | `emerald-*`, `bg-green-500`, `text-green-600` |

---

## DO / DON'T

**DO:**
- `sys.path.append()` di setiap file baru
- `sanitize.clean_html_dic()` untuk semua input user
- `self.mgdDB` untuk database access
- `idgen._get_api_call_id()` untuk ID generation
- `try/except` + `self.webapp.logger.debug(traceback.format_exc())`
- `@middleware_privilege` untuk route yang butuh auth

**DON'T:**
- Relative imports (`from ..module import`)
- Ubah response format (`message_id`, `message_action`, dll)
- Bypass `@middleware_privilege`
- Buat helper baru jika sudah ada di `pytavia_stdlib/`
- Pakai `emerald-*` atau default Tailwind colors yang tidak ada di config

---

## Detail Lengkap → `docs/`

| Topik | File |
|-------|------|
| Class patterns, DB, routes, testing | [`docs/CODE_PATTERNS.md`](docs/CODE_PATTERNS.md) |
| Color palette lengkap, Atomic CSS | [`docs/COLORS.md`](docs/COLORS.md) |
| UI components, buttons, forms | [`docs/UI_PATTERNS.md`](docs/UI_PATTERNS.md) |
