# Paste this whole file into the WSGI configuration file on the PythonAnywhere Web tab,
# then replace every <...> value. Keep this file private once filled in; do not commit real values.
import os
import sys

PROJECT = "/home/<your-pythonanywhere-username>/internmatch"
sys.path.insert(0, PROJECT)

os.environ["SECRET_KEY"] = "<paste the key printed by the setup script>"
os.environ["HTTPS"] = "1"
os.environ["ADMIN_EMAIL"] = "<your admin email>"
os.environ["ADMIN_PASSWORD"] = "<a strong password, 8+ characters>"
os.environ["INTERNMATCH_DB"] = PROJECT + "/internmatch.db"
# os.environ["LOAD_DEMO"] = "1"   # uncomment ONCE for demo data, then remove it again

import bootstrap  # noqa: E402

bootstrap.main()

from app import app as application  # noqa: E402,F401
