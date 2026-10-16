"""End-to-end smoke test: python test_smoke.py  (uses a throwaway database)."""
import os
import re
import tempfile
import time

tmp = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["INTERNMATCH_DB"] = tmp

import seed  # noqa: E402
seed.seed()
from app import app  # noqa: E402


def token(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="csrf" value="([^"]+)"', html).group(1)


def login(email, pw="Demo@1234"):
    c = app.test_client()
    r = c.post("/login", data={"email": email, "password": pw, "csrf": token(c)})
    assert r.status_code == 302, (email, r.status_code)
    return c


def post(c, path, page, **data):
    return c.post(path, data={**data, "csrf": token(c, page)}, follow_redirects=True)


def ok(r, text=None):
    assert r.status_code == 200, (r.status_code, r.request.path)
    if text:
        assert text in r.get_data(as_text=True), f"{text!r} not in {r.request.path}"


# --- public + csrf + auth
c = app.test_client()
ok(c.get("/"), "InternMatch")
assert c.post("/login", data={"email": "x", "password": "y"}).status_code == 400  # no CSRF
assert c.get("/student").status_code == 302
r = c.post("/login", data={"email": "ayesha@student.test", "password": "bad", "csrf": token(c)})
assert r.status_code == 401

# --- registration validation + new accounts
r = c.post("/register", data={"name": "A", "email": "bad", "password": "short", "confirm": "x", "role": "student", "csrf": token(c, "/register")})
assert r.status_code == 400
r = post(c, "/register", "/register", name="New Student", email="new@student.test", password="Passw0rd!", confirm="Passw0rd!", role="student")
ok(r, "Education")
r = post(app.test_client(), "/register", "/register", name="E", email="e@co.test", password="Passw0rd!", confirm="Passw0rd!", role="employer", company="Co")
ok(r, "Company profile")

# --- student flow
s = login("ayesha@student.test")
ok(s.get("/student"), "Top matches")
r = s.get("/student/recommendations")
ok(r, "Backend Developer Intern")
html = r.get_data(as_text=True)
# ranking: the first listed title must be the best fit for Ayesha
assert html.index("Backend Developer Intern") < html.index("UI/UX Design Intern")
ok(s.get("/student/profile"), "Skills")
ok(post(s, "/student/skills", "/student/profile", skill="Kubernetes", level="2"), "Kubernetes")
ok(post(s, "/student/projects", "/student/profile", title="P1", tech="Python", description="d"), "P1")
ok(post(s, "/student/certs", "/student/profile", name="AWS CP", issuer="AWS", year="2025"), "AWS CP")
ok(s.get("/student/tests"), "Python")
tp = s.get("/student/tests/Python")
ok(tp)
qids = re.findall(r'name="qid" value="(\d+)"', tp.get_data(as_text=True))
assert len(qids) == 8
form = {"qid": qids, "csrf": token(s, "/student/tests/Python")}
con = seed.db.connect()
for qid in qids:
    form[f"q{qid}"] = con.execute("SELECT answer FROM questions WHERE id=?", (qid,)).fetchone()[0]
r = s.post("/student/tests/Python", data=form, follow_redirects=True)
ok(r, "8 / 8")
iid = con.execute("SELECT id FROM internships WHERE title='Backend Developer Intern'").fetchone()[0]
ok(s.get(f"/internships/{iid}"), "Apply now")
ok(post(s, f"/internships/{iid}/apply", f"/internships/{iid}", cover_note="Hello"), "match score")
ok(s.get("/student/applications"), "Backend Developer Intern")
assert s.get("/employer").status_code == 403 and s.get("/admin").status_code == 403

# --- employer flow
e = login("hr@techcorp.test")
ok(e.get("/employer"), "Your listings")
r = e.get(f"/employer/internships/{iid}/candidates")
ok(r, "Ayesha Rehman")
aid = con.execute("SELECT id FROM applications").fetchone()[0]
ok(post(e, f"/employer/applications/{aid}/status", f"/employer/internships/{iid}/candidates", status="shortlisted"), "Shortlisted")
ok(e.get(f"/employer/applications/{aid}"), "Ayesha Rehman")
ok(post(e, "/employer/internships/new", "/employer/internships/new", title="Cloud Intern", required_skills="AWS, Docker", location="Lahore"), "Cloud Intern")
# another employer cannot see these candidates
other = login("hr@datalab.test")
assert other.get(f"/employer/internships/{iid}/candidates").status_code == 404
assert other.get(f"/employer/applications/{aid}").status_code == 404
# student status reflects employer decision
ok(s.get("/student/applications"), "Shortlisted")

# --- admin flow
a = login("admin@internmatch.test", "Admin@123")
ok(a.get("/admin"), "Platform overview")
ok(a.get("/admin"), "Institution report")
ok(a.get("/admin"), "Objective tracking")
ok(post(a, "/admin/baselines", "/admin", base_tta="90", base_review="48"), "faster than baseline")
assert post(a, "/admin/baselines", "/admin", base_tta="abc", base_review="").status_code == 200
ok(e.get(f"/employer/internships/{iid}/candidates?page=999"), "Ayesha Rehman")
ok(a.get("/admin/users?page=2&role=student"), "users")
ok(a.get("/admin/institutions.csv"), "FAST NUCES")
ok(e.get(f"/employer/internships/{iid}/candidates.csv"), "Ayesha Rehman")
assert other.get(f"/employer/internships/{iid}/candidates.csv").status_code == 404
ok(a.get("/admin/users"), "ayesha@student.test")
ok(a.get("/admin/internships"), "Cloud Intern")
uid = con.execute("SELECT id FROM users WHERE email='usman@student.test'").fetchone()[0]
post(a, f"/admin/users/{uid}/toggle", "/admin/users")
assert app.test_client().post("/login", data={"email": "usman@student.test", "password": "Demo@1234", "csrf": token(app.test_client())}).status_code in (302, 400, 403)
c2 = app.test_client()
assert c2.post("/login", data={"email": "usman@student.test", "password": "Demo@1234", "csrf": token(c2)}).status_code == 403

# --- passwords stored hashed
pw = con.execute("SELECT password_hash FROM users WHERE email='ayesha@student.test'").fetchone()[0]
assert "Demo@1234" not in pw and pw.startswith(("scrypt:", "pbkdf2:"))

# --- response time
t = time.perf_counter()
for _ in range(10):
    s.get("/student/recommendations")
avg = (time.perf_counter() - t) / 10
print(f"avg recommendations page: {avg*1000:.0f} ms")
assert avg < 2.0
print("ALL SMOKE TESTS PASSED")
