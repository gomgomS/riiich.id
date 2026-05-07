import time
import copy
import pymongo
import os
import sys

from bson.objectid import ObjectId

class mongo_model:

    def __init__(self, record, lookup, db_handle):
        self._mongo_record  = copy.deepcopy(record)
        self._lookup_record = copy.deepcopy(lookup)
        self._db_handle     = db_handle
    # end def

    def put(self, key, value):
        if not (key in self._lookup_record):
            raise ValueError('SETTING_NON_EXISTING_FIELD', key, value)
        # end if
        self._mongo_record[key] = value
    # end def

    def get(self):
        return self._mongo_record
    # end def   

    def delete(self , query):
        collection_name = self._lookup_record["__db__name__"]
        self._db_handle[collection_name].remove( query )
    # end def

    def insert(self, lock=None):
        collection_name = self._lookup_record["__db__name__"]
        del self._mongo_record["__db__name__"]
        # if 
        #if not(collection_name in self._db_handle.list_collection_names()):
        #    self._db_handle.create_collection( collection_name )
        # end if
        if lock == None:
            self._db_handle[collection_name].insert_one(  
                self._mongo_record
            )
        else:
            self._db_handle[collection_name].insert_one(  
                self._mongo_record,
                session=lock
            )
        # end if
    # end def

    def update(self, query):
        collection_name = self._lookup_record["__db__name__"]
        self._db_handle[collection_name].update(
            query, 
            { "$set" : self._mongo_record }
        )
    # end def
# end class
#
#
# Define the models/collections here for the mongo db
#
db = {

    # Admin user accounts
    "db_user" : {
        "fk_user_id"    : "",
        "user_uuid"     : "",
        "username"      : "",
        "password"      : "",   # sha256 hashed
        "role"          : "",   # ASSISTENT | ADMIN
        "name"          : "",
        "phone"         : "",
        "is_active"     : "TRUE",
    },

    # Admin login sessions (stored in Flask session, log here)
    "db_admin_session" : {
        "fk_user_id"    : "",
        "username"      : "",
        "role"          : "",
        "login_time"    : 0,
        "user_agent"    : "",
        "ip_address"    : "",
        "state"         : "LOGIN_SUCCESS",  # LOGIN_SUCCESS | LOGOUT
    },

    # Hymn songs (future - from Flutter app data)
    "db_hymn" : {
        "hymn_number"   : 0,
        "title"         : "",
        "lyrics"        : [],
        "language"      : "",
        "status"        : "ACTIVE",
    },

    # Sekolah Sabat Bank — one doc per week (metadata)
    "db_ss_pelajaran" : {
        "year"           : 0,     # e.g. 2026
        "triwulan"       : 0,     # 1 | 2 | 3 | 4
        "pelajaran_no"   : 0,     # 1 – 13
        "pelajaran_name" : "",    # user-provided, e.g. "PERAN ALKITAB"
        "ppt_url"        : "",
        "status"         : "ACTIVE",
    },

    # Sekolah Sabat Bank — one doc per day (7 per pelajaran)
    "db_ss_materi" : {
        "fk_pelajaran_id" : "",   # pkey of db_ss_pelajaran
        "year"            : 0,
        "triwulan"        : 0,
        "pelajaran_no"    : 0,
        "pelajaran_name"  : "",
        "day_of_week"     : "",   # Sabtu|Minggu|Senin|Selasa|Rabu|Kamis|Jumat
        "day_label"       : "",   # e.g. "18 April 2026"
        "source_url"      : "",
        "title"           : "",   # scraped section title (day topic)
        "content"         : [],   # list of {type, text}
        "ppt_url"         : "",
        "status"          : "ACTIVE",
    },

    # Cafe reservations & orders
    "db_order" : {
        "flow_type"          : "",   # Dine-In | Takeaway
        "contact"            : {},   # {name, whatsapp}
        "table_ids"          : [],   # list of reserved table IDs
        "table_id"           : "",   # kept for legacy single-table compat
        "party_size"         : 0,
        "items"              : [],   # [{item_id, name, quantity, price}]
        "service_timing"     : "",   # Serve on Arrival | Ready after Arrival
        "payment_status"     : "",   # Unpaid | Paid
        "fulfillment_status" : "",   # Pending | In Progress | Served | Done
        "total_amount"       : 0,
    },

    # Individual table status tracking
    "db_table" : {
        "table_id"     : "",
        "label"        : "",
        "status"       : "Available",  # Available | Reserved | Occupied
        "reserved_at"  : 0,
        "order_pkey"   : "",
    },

}
