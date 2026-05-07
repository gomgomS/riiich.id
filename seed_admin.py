import sys
import hashlib

sys.path.append("slapz102_core")
sys.path.append("slapz102_modules")
sys.path.append("slapz102_settings")

import database
import config

def _hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def seed_admin():
    database.connect_db()
    db = database.get_database(config.mainDB)[config.mainDB]
    
    admin = db["db_user"].find_one({"username": "admin"})
    if not admin:
        print("Seeding admin user...")
        db["db_user"].insert_one({
            "username": "admin",
            "password": _hash_password("admin123"),
            "role": "ADMIN",
            "name": "Super Admin",
            "is_active": "TRUE"
        })
        print("Admin user 'admin' created with password 'admin123'.")
    else:
        print("Admin user already exists.")

if __name__ == "__main__":
    seed_admin()
