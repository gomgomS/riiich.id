import os
import  urllib.parse
G_FLASK_SECRET=b'_5#y2L"F4Q8z\n\xec]/'
G_WALLET_ID_SUFFIX = 6

# This is the
G_HOME_PATH=os.getcwd()

# This is where all the cookies are stored
G_STATIC_URL_PATH           = "/static"
G_UPLOAD_PATH               = G_HOME_PATH + G_STATIC_URL_PATH + "/upload"
G_UPLOAD_URL_PATH           = G_STATIC_URL_PATH + "/upload"



############################################################################################################################################################

# DEVELOPMENT
                        
# DATABASE
mainDB                      = "sch_id"
mainDB_string               = "mongodb://127.0.0.1:27017/"  + mainDB

G_BASE_URL_PROD          = "http://202.155.94.7:5003/"


# Local Storage
G_BASE_S3_URL               = "http://0.0.0.0:49003"

G_IMAGE_URL_DISPATCH        = G_BASE_S3_URL + "/v1/cfs/get-file?"


############################################################################################################################################################


# This is where we have all the databases we want to connect to
G_DATABASE_CONNECT=[
    {"dbname" : mainDB    , "dbstring"  : mainDB_string    }
]

JKTA_TZ = 7
MS_24_HOURS = 86399999

