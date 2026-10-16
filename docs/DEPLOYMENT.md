# Deployment Guide (WBS 8.4)

The app is deployment-ready. Production start-up (`bootstrap.py`) creates the tables, loads the 56 test questions and creates **one admin from environment variables**. It never loads the demo accounts, whose passwords are public in the README.

## What you need
- A free GitHub account, and the project pushed to a repository (the `.gitignore` already keeps the database and secrets out).
- An account on one hosting service. Create it yourself; do not share its password with anyone.

## Environment variables
| Variable | Value | Why |
|---|---|---|
| `SECRET_KEY` | a long random string | signs login sessions; if missing, a key file is generated and is lost on rebuilds |
| `HTTPS` | `1` | marks cookies secure |
| `ADMIN_EMAIL` | your admin email | first admin account |
| `ADMIN_PASSWORD` | 8+ characters | first admin password; change it after the first login |
| `INTERNMATCH_DB` | path on a persistent disk | where the SQLite file lives |
| `LOAD_DEMO` | `1` (optional) | loads demo students/employers; use only for a demo |

Generate a key: `python -c "import secrets; print(secrets.token_hex(32))"`

## Option A — PythonAnywhere (free, permanent storage)
Best fit for the "free or low-cost tools" constraint because files persist.
1. Create a free account at pythonanywhere.com and open a **Bash console**.
2. `git clone https://github.com/Abdullahshahid984/internmatch.git && cd internmatch`, then run `bash deploy/pythonanywhere_setup.sh` (steps 3 is done for you and it prints a secret key). In step 6 use `deploy/pythonanywhere_wsgi.py` as the template.
3. `python3 -m venv ~/.venv-im && source ~/.venv-im/bin/activate && pip install -r requirements.txt`
4. Open the **Web** tab → **Add a new web app** → **Manual configuration** → pick the Python version you used for the venv.
5. In the Web tab set **Virtualenv** to `/home/<you>/.venv-im` and **Source code** to `/home/<you>/internmatch`.
6. Edit the WSGI file shown on that tab: replace its contents with
   ```python
   import os, sys
   sys.path.insert(0, "/home/<you>/internmatch")
   os.environ["SECRET_KEY"] = "<paste the generated key>"
   os.environ["HTTPS"] = "1"
   os.environ["ADMIN_EMAIL"] = "<your admin email>"
   os.environ["ADMIN_PASSWORD"] = "<a strong password>"
   os.environ["INTERNMATCH_DB"] = "/home/<you>/internmatch/internmatch.db"
   import bootstrap; bootstrap.main()
   from app import app as application
   ```
7. Click **Reload**. Your site is at `https://<you>.pythonanywhere.com`. Free accounts must click a renewal button every few months or the site is disabled; check the current rules on their site.

## Option B — Render (paid disk needed for real data)
1. Push the repo to GitHub.
2. Render dashboard → **New → Blueprint** → select the repo. It reads `render.yaml`.
3. Enter `ADMIN_EMAIL` and `ADMIN_PASSWORD` when asked, then deploy.
4. Open `https://<service>.onrender.com/healthz` — it should say `ok`.

`render.yaml` uses a paid instance with a 1 GB disk so registrations survive restarts. On Render's free plan the filesystem is wiped on each restart or redeploy, so every user and application would be lost; use it only for a throw-away demo (remove the `disk` block and set `plan: free`). Check Render's current pricing before choosing.

## After deploying
1. Open `/healthz` (expect `ok`) and `/login`.
2. Log in as the admin and change the password (click your name in the top bar).
3. Register one student and one employer yourself and run the acceptance script in `docs/UAT_SCRIPT.md`.
4. For a presentation with sample data, set `LOAD_DEMO=1` once, redeploy, and **remove it afterwards and change the demo passwords** (or delete the demo users in Admin → Users).
5. Back up `internmatch.db` regularly (download it from the host).

## Production notes
- Run behind HTTPS only (both hosts provide it). `HTTPS=1` then enforces secure cookies.
- SQLite suits a class-project load (the load test used 2,000 students). For heavy production use, move to PostgreSQL.
- Login throttling and CSRF protection are built in; keep dependencies updated (`pip install -U flask`).
