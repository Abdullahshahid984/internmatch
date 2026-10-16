"""Load test: python perf_test.py [students] [internships]
Builds a large throwaway database and times the heaviest pages (target: < 2 s)."""
import os
import random
import re
import sys
import tempfile
import time

os.environ["INTERNMATCH_DB"] = os.path.join(tempfile.mkdtemp(), "perf.db")
import seed  # noqa: E402

seed.seed()
from werkzeug.security import generate_password_hash  # noqa: E402

N_STU = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
N_INT = int(sys.argv[2]) if len(sys.argv) > 2 else 300
SK = ["Python", "SQL", "Git", "JavaScript", "React", "HTML", "CSS", "Docker", "Flask", "Node.js", "Java",
      "Machine Learning", "Statistics", "Excel", "Figma", "AWS", "Communication", "C++", "Django", "MongoDB"]
random.seed(1)
con = seed.db.connect()
pw = generate_password_hash("Demo@1234")
emp = con.execute("SELECT id FROM users WHERE email='hr@techcorp.test'").fetchone()[0]
for n in range(N_INT):
    con.execute("INSERT INTO internships(employer_id,title,required_skills,preferred_skills,min_degree,field,category,location) VALUES(?,?,?,?,?,?,?,?)",
                (emp, f"Intern {n}", ", ".join(random.sample(SK, 4)), ", ".join(random.sample(SK, 2)), "Bachelor",
                 "Computer Science", "web development", "Lahore"))
for n in range(N_STU):
    uid = con.execute("INSERT INTO users(email,password_hash,role,name) VALUES(?,?,?,?)", (f"s{n}@load.test", pw, "student", f"Student {n}")).lastrowid
    con.execute("INSERT INTO student_profiles(user_id,university,degree,major,interests) VALUES(?,?,?,?,?)",
                (uid, f"Uni {n % 20}", "Bachelor", "Computer Science", "web development"))
    for s in random.sample(SK, 6):
        con.execute("INSERT INTO student_skills(user_id,skill,level) VALUES(?,?,?)", (uid, s, random.randint(1, 5)))
        if random.random() < .4:
            con.execute("INSERT INTO test_results(user_id,skill,correct,total,pct) VALUES(?,?,?,8,?)", (uid, s, 5, random.choice([50, 62.5, 75, 87.5])))
first = con.execute("SELECT MIN(id) FROM internships WHERE title LIKE 'Intern %'").fetchone()[0]
for n in range(N_STU):  # every student applies to the first listing -> big candidate list
    sid = con.execute("SELECT id FROM users WHERE email=?", (f"s{n}@load.test",)).fetchone()[0]
    con.execute("INSERT INTO applications(internship_id,student_id,score) VALUES(?,?,50)", (first, sid))
con.commit()

from app import app  # noqa: E402


def login(email, pw_):
    c = app.test_client()
    t = re.search(r'name="csrf" value="([^"]+)"', c.get("/login").get_data(as_text=True)).group(1)
    assert c.post("/login", data={"email": email, "password": pw_, "csrf": t}).status_code == 302
    return c


def timed(label, c, path):
    t = time.perf_counter()
    r = c.get(path)
    dt = time.perf_counter() - t
    assert r.status_code == 200, (path, r.status_code)
    print(f"{label:<28}{dt * 1000:8.0f} ms  {'OK' if dt < 2 else 'SLOW'}")
    return dt


s, e, a = login("s5@load.test", "Demo@1234"), login("hr@techcorp.test", "Demo@1234"), login("admin@internmatch.test", "Admin@123")
print(f"{N_STU} students, {N_INT + 7} internships, {N_STU} applicants on one listing")
worst = max(timed("student dashboard", s, "/student"), timed("recommendations", s, "/student/recommendations"),
            timed("employer dashboard", e, "/employer"), timed("candidates (all applicants)", e, f"/employer/internships/{first}/candidates"),
            timed("admin dashboard", a, "/admin"), timed("admin users", a, "/admin/users"))
print("PASS" if worst < 2 else "FAIL", f"(slowest {worst * 1000:.0f} ms)")
