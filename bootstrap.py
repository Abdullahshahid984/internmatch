"""Production start-up: creates tables, loads the skill-test question bank and the first admin.
Never loads demo users. Safe to run on every start.

Environment:
    ADMIN_EMAIL, ADMIN_PASSWORD   creates the first admin if no admin exists yet
    LOAD_DEMO=1                   (optional) also load the demo data from seed.py - for presentations only
"""
import os

import db
from werkzeug.security import generate_password_hash


def main():
    db.init_db()
    conn = db.connect()
    from seed import QUESTIONS
    if not conn.execute("SELECT 1 FROM questions LIMIT 1").fetchone():
        conn.executemany("INSERT INTO questions(skill,question,a,b,c,d,answer) VALUES(?,?,?,?,?,?,?)", QUESTIONS)
        print(f"Loaded {len(QUESTIONS)} test questions.")
    if not conn.execute("SELECT 1 FROM users WHERE role='admin'").fetchone():
        email, pw = os.environ.get("ADMIN_EMAIL", "").strip().lower(), os.environ.get("ADMIN_PASSWORD", "")
        if email and len(pw) >= 8:
            conn.execute("INSERT INTO users(email,password_hash,role,name) VALUES(?,?,?,?)",
                         (email, generate_password_hash(pw), "admin", "Administrator"))
            print(f"Created admin {email}.")
        else:
            print("WARNING: no admin exists. Set ADMIN_EMAIL and ADMIN_PASSWORD (8+ chars) and restart.")
    conn.commit()
    conn.close()
    if os.environ.get("LOAD_DEMO") == "1":
        import seed
        seed.seed()


if __name__ == "__main__":
    main()
