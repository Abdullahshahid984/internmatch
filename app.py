import os
import re
import secrets
import time
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import db as database
from matching import compute_match, label, norm

BASE = os.path.dirname(os.path.abspath(__file__))
STATUSES = ["applied", "shortlisted", "accepted", "rejected"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def load_secret():
    env = os.environ.get("SECRET_KEY")
    if env:
        return env
    path = os.path.join(BASE, ".secret_key")
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write(secrets.token_hex(32))
    with open(path) as f:
        return f.read().strip()


app = Flask(__name__)
app.config.update(
    SECRET_KEY=load_secret(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("HTTPS", "") == "1",
    MAX_CONTENT_LENGTH=1024 * 1024,
)
app.teardown_appcontext(database.close_db)
database.init_db()

FAILED = {}  # (ip/email) -> [count, first_time]  simple brute-force throttle


# ---------------------------------------------------------------- helpers
def q(sql, args=(), one=False):
    cur = database.get_db().execute(sql, args)
    rows = cur.fetchall()
    return (rows[0] if rows else None) if one else rows


def run(sql, args=()):
    db = database.get_db()
    cur = db.execute(sql, args)
    db.commit()
    return cur


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token
app.jinja_env.globals["label"] = label


@app.before_request
def load_user():
    g.user = None
    uid = session.get("uid")
    if uid:
        user = q("SELECT * FROM users WHERE id=?", (uid,), one=True)
        if user and user["active"]:
            g.user = user
        else:
            session.clear()
    if request.method == "POST":
        token = request.form.get("csrf", "")
        if not token or not secrets.compare_digest(token, session.get("csrf", "")):
            abort(400, "Invalid or missing CSRF token. Go back and reload the page.")


@app.after_request
def secure_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp


def login_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a, **kw):
            if not g.user:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("login", next=request.path))
            if roles and g.user["role"] not in roles:
                abort(403)
            return fn(*a, **kw)
        return wrapper
    return deco


def home_for(user):
    return url_for({"student": "student_dashboard", "employer": "employer_dashboard",
                    "admin": "admin_dashboard"}[user["role"]])


def clean(name, maxlen=200):
    return (request.form.get(name) or "").strip()[:maxlen]


def to_int(v, default=None):
    try:
        return int(v)
    except (TypeError, ValueError):
        return default


def csv_clean(text):
    seen, out = set(), []
    for part in re.split(r"[,;\n]", text or ""):
        part = re.sub(r"\s+", " ", part.strip())
        if part and part.lower() not in seen:
            seen.add(part.lower())
            out.append(part)
    return ", ".join(out)


# ---------------------------------------------------------------- matching data
def student_bundle(uid):
    profile = q("SELECT * FROM student_profiles WHERE user_id=?", (uid,), one=True)
    skills = q("SELECT * FROM student_skills WHERE user_id=? ORDER BY skill", (uid,))
    tests = {norm(r["skill"]): r["best"] for r in q(
        "SELECT skill, MAX(pct) AS best FROM test_results WHERE user_id=? GROUP BY skill", (uid,))}
    projects = q("SELECT * FROM projects WHERE user_id=?", (uid,))
    certs = q("SELECT * FROM certifications WHERE user_id=?", (uid,))
    return profile, skills, tests, projects, certs


def bulk_bundles(uids):
    """student_bundle for many students in 5 queries instead of 5 per student."""
    uids = list(uids)
    out = {u: [None, [], {}, [], []] for u in uids}
    if not uids:
        return {}
    marks = ",".join("?" * len(uids))
    for r in q(f"SELECT * FROM student_profiles WHERE user_id IN ({marks})", uids):
        out[r["user_id"]][0] = r
    for r in q(f"SELECT * FROM student_skills WHERE user_id IN ({marks})", uids):
        out[r["user_id"]][1].append(r)
    for r in q(f"SELECT user_id, skill, MAX(pct) AS best FROM test_results WHERE user_id IN ({marks}) GROUP BY user_id, skill", uids):
        out[r["user_id"]][2][norm(r["skill"])] = r["best"]
    for r in q(f"SELECT * FROM projects WHERE user_id IN ({marks})", uids):
        out[r["user_id"]][3].append(r)
    for r in q(f"SELECT * FROM certifications WHERE user_id IN ({marks})", uids):
        out[r["user_id"]][4].append(r)
    return {u: tuple(v) for u, v in out.items()}


def ranked_applicants(internship, apps):
    """[(application_row, match)] sorted best-first, using batched profile loading."""
    bundles = {}
    ids = [a["student_id"] for a in apps]
    for n in range(0, len(ids), 500):  # stay under SQLite's variable limit
        bundles.update(bulk_bundles(ids[n:n + 500]))
    rows = [(a, match_for(bundles[a["student_id"]], internship)) for a in apps]
    rows.sort(key=lambda t: -t[1]["score"])
    return rows


def match_for(bundle, internship):
    profile, skills, tests, projects, certs = bundle
    return compute_match(profile, skills, tests, projects, certs, internship)


def open_internships():
    return q("""SELECT i.*, e.company FROM internships i
                LEFT JOIN employer_profiles e ON e.user_id=i.employer_id
                JOIN users u ON u.id=i.employer_id AND u.active=1
                WHERE i.status='open' AND i.removed=0""")


def profile_completeness(uid):
    profile, skills, tests, projects, certs = student_bundle(uid)
    checks = [bool(profile["university"]), bool(profile["degree"]), bool(profile["major"]),
              profile["gpa"] is not None, bool(profile["interests"]), bool(profile["bio"]),
              len(skills) >= 3, len(projects) >= 1, len(certs) >= 1, len(tests) >= 1]
    return round(100 * sum(checks) / len(checks))


# ---------------------------------------------------------------- public / auth
@app.route("/")
def index():
    if g.user:
        return redirect(home_for(g.user))
    stats = {
        "students": q("SELECT COUNT(*) c FROM users WHERE role='student'", one=True)["c"],
        "employers": q("SELECT COUNT(*) c FROM users WHERE role='employer'", one=True)["c"],
        "internships": q("SELECT COUNT(*) c FROM internships WHERE status='open' AND removed=0", one=True)["c"],
    }
    return render_template("index.html", stats=stats)


@app.route("/healthz")
def healthz():
    q("SELECT 1")
    return "ok"


@app.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(home_for(g.user))
    if request.method == "POST":
        name, email = clean("name", 100), clean("email", 150).lower()
        password, role = request.form.get("password", ""), request.form.get("role")
        errors = []
        if not name:
            errors.append("Name is required.")
        if not EMAIL_RE.match(email):
            errors.append("Enter a valid email address.")
        if role not in ("student", "employer"):
            errors.append("Choose student or employer.")
        if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            errors.append("Password must be at least 8 characters and contain a letter and a number.")
        if password != request.form.get("confirm", ""):
            errors.append("Passwords do not match.")
        if not errors and q("SELECT 1 FROM users WHERE email=?", (email,), one=True):
            errors.append("An account with this email already exists.")
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form), 400
        uid = run("INSERT INTO users(email,password_hash,role,name) VALUES(?,?,?,?)",
                  (email, generate_password_hash(password), role, name)).lastrowid
        if role == "student":
            run("INSERT INTO student_profiles(user_id) VALUES(?)", (uid,))
        else:
            run("INSERT INTO employer_profiles(user_id, company) VALUES(?,?)", (uid, clean("company", 120) or name))
        session.clear()
        session["uid"] = uid
        flash("Welcome! Your account has been created.", "success")
        return redirect(url_for("student_profile" if role == "student" else "employer_profile"))
    return render_template("register.html", form={})


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(home_for(g.user))
    if request.method == "POST":
        email = clean("email", 150).lower()
        key = (request.remote_addr, email)
        rec = FAILED.get(key)
        if rec and rec[0] >= 5 and time.time() - rec[1] < 300:
            flash("Too many failed attempts. Try again in a few minutes.", "danger")
            return render_template("login.html"), 429
        user = q("SELECT * FROM users WHERE email=?", (email,), one=True)
        if user and check_password_hash(user["password_hash"], request.form.get("password", "")):
            if not user["active"]:
                flash("This account has been deactivated. Contact the administrator.", "danger")
                return render_template("login.html"), 403
            FAILED.pop(key, None)
            session.clear()
            session["uid"] = user["id"]
            nxt = request.args.get("next", "")
            if nxt.startswith("/") and not nxt.startswith("//"):
                return redirect(nxt)
            return redirect(home_for(user))
        rec = FAILED.get(key)
        if not rec or time.time() - rec[1] >= 300:
            rec = FAILED[key] = [0, time.time()]
        rec[0] += 1
        flash("Invalid email or password.", "danger")
        return render_template("login.html"), 401
    return render_template("login.html")


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/account/password", methods=["GET", "POST"])
@login_required()
def change_password():
    if request.method == "POST":
        new = request.form.get("new", "")
        if not check_password_hash(g.user["password_hash"], request.form.get("old", "")):
            flash("Current password is incorrect.", "danger")
        elif len(new) < 8 or not re.search(r"[A-Za-z]", new) or not re.search(r"\d", new):
            flash("New password must be at least 8 characters with a letter and a number.", "danger")
        else:
            run("UPDATE users SET password_hash=? WHERE id=?", (generate_password_hash(new), g.user["id"]))
            flash("Password updated.", "success")
            return redirect(home_for(g.user))
    return render_template("password.html")


# ---------------------------------------------------------------- student
@app.route("/student")
@login_required("student")
def student_dashboard():
    uid = g.user["id"]
    bundle = student_bundle(uid)
    scored = []
    for i in open_internships():
        m = match_for(bundle, i)
        scored.append((i, m))
    scored.sort(key=lambda t: -t[1]["score"])
    counts = {s: 0 for s in STATUSES}
    for r in q("SELECT status, COUNT(*) c FROM applications WHERE student_id=? GROUP BY status", (uid,)):
        counts[r["status"]] = r["c"]
    results = q("""SELECT skill, MAX(pct) AS best, COUNT(*) AS attempts, MAX(taken_at) AS last
                   FROM test_results WHERE user_id=? GROUP BY skill ORDER BY best DESC""", (uid,))
    recent = q("""SELECT a.*, i.title, e.company FROM applications a JOIN internships i ON i.id=a.internship_id
                  LEFT JOIN employer_profiles e ON e.user_id=i.employer_id
                  WHERE a.student_id=? ORDER BY a.updated_at DESC LIMIT 5""", (uid,))
    return render_template("student/dashboard.html", top=scored[:5], counts=counts, results=results,
                           recent=recent, completeness=profile_completeness(uid),
                           total_open=len(scored), skill_count=len(bundle[1]))


@app.route("/student/profile", methods=["GET", "POST"])
@login_required("student")
def student_profile():
    uid = g.user["id"]
    if request.method == "POST":
        gpa = request.form.get("gpa", "").strip()
        try:
            gpa_val = float(gpa) if gpa else None
            if gpa_val is not None and not (0 <= gpa_val <= 4.5):
                raise ValueError
        except ValueError:
            flash("GPA must be a number between 0 and 4.5.", "danger")
            return redirect(url_for("student_profile"))
        name = clean("name", 100)
        if name:
            run("UPDATE users SET name=? WHERE id=?", (name, uid))
        run("""UPDATE student_profiles SET university=?, degree=?, major=?, gpa=?, grad_year=?,
               interests=?, bio=?, location=?, phone=? WHERE user_id=?""",
            (clean("university"), clean("degree", 50), clean("major"), gpa_val,
             to_int(request.form.get("grad_year")), csv_clean(request.form.get("interests"))[:300],
             clean("bio", 1000), clean("location"), clean("phone", 30), uid))
        flash("Profile saved.", "success")
        return redirect(url_for("student_profile"))
    profile, skills, tests, projects, certs = student_bundle(uid)
    return render_template("student/profile.html", p=profile, skills=skills, tests=tests,
                           projects=projects, certs=certs, completeness=profile_completeness(uid))


@app.post("/student/skills")
@login_required("student")
def add_skill():
    skill = re.sub(r"\s+", " ", clean("skill", 50))
    level = min(5, max(1, to_int(request.form.get("level"), 3)))
    kind = "soft" if request.form.get("kind") == "soft" else "technical"
    if not skill:
        flash("Enter a skill name.", "danger")
    else:
        run("""INSERT INTO student_skills(user_id,skill,level,kind) VALUES(?,?,?,?)
               ON CONFLICT(user_id,skill) DO UPDATE SET level=excluded.level, kind=excluded.kind""",
            (g.user["id"], skill, level, kind))
        flash(f"Skill “{skill}” saved.", "success")
    return redirect(url_for("student_profile") + "#skills")


@app.post("/student/<kind>/<int:item_id>/delete")
@login_required("student")
def delete_item(kind, item_id):
    table = {"skills": "student_skills", "projects": "projects", "certs": "certifications"}.get(kind)
    if not table:
        abort(404)
    run(f"DELETE FROM {table} WHERE id=? AND user_id=?", (item_id, g.user["id"]))
    return redirect(url_for("student_profile") + "#" + kind)


@app.post("/student/projects")
@login_required("student")
def add_project():
    title = clean("title", 120)
    if not title:
        flash("Project title is required.", "danger")
    else:
        run("INSERT INTO projects(user_id,title,description,tech) VALUES(?,?,?,?)",
            (g.user["id"], title, clean("description", 600), csv_clean(request.form.get("tech"))[:200]))
        flash("Project added.", "success")
    return redirect(url_for("student_profile") + "#projects")


@app.post("/student/certs")
@login_required("student")
def add_cert():
    name = clean("name", 150)
    if not name:
        flash("Certification name is required.", "danger")
    else:
        run("INSERT INTO certifications(user_id,name,issuer,year) VALUES(?,?,?,?)",
            (g.user["id"], name, clean("issuer", 120), to_int(request.form.get("year"))))
        flash("Certification added.", "success")
    return redirect(url_for("student_profile") + "#certs")


# ---- skill tests
@app.route("/student/tests")
@login_required("student")
def tests_home():
    uid = g.user["id"]
    banks = q("SELECT skill, COUNT(*) n FROM questions GROUP BY skill ORDER BY skill")
    best = {r["skill"].lower(): r for r in q(
        """SELECT skill, MAX(pct) AS best, COUNT(*) AS attempts FROM test_results
           WHERE user_id=? GROUP BY skill""", (uid,))}
    history = q("SELECT * FROM test_results WHERE user_id=? ORDER BY taken_at DESC, id DESC LIMIT 15", (uid,))
    return render_template("student/tests.html", banks=banks, best=best, history=history)


@app.route("/student/tests/<skill>", methods=["GET", "POST"])
@login_required("student")
def take_test(skill):
    if not q("SELECT 1 FROM questions WHERE skill=? COLLATE NOCASE", (skill,), one=True):
        abort(404)
    if request.method == "POST":
        ids = [to_int(x) for x in request.form.getlist("qid") if to_int(x) is not None][:10]
        if not ids:
            abort(400)
        marks = ",".join("?" * len(ids))
        rows = q(f"SELECT * FROM questions WHERE id IN ({marks}) AND skill=? COLLATE NOCASE", (*ids, skill))
        correct = sum(1 for r in rows if request.form.get(f"q{r['id']}") == r["answer"])
        total = len(rows)
        pct = round(100 * correct / total, 1) if total else 0
        canonical = q("SELECT skill FROM questions WHERE skill=? COLLATE NOCASE LIMIT 1", (skill,), one=True)["skill"]
        run("INSERT INTO test_results(user_id,skill,correct,total,pct) VALUES(?,?,?,?,?)",
            (g.user["id"], canonical, correct, total, pct))
        if not q("SELECT 1 FROM student_skills WHERE user_id=? AND skill=? COLLATE NOCASE", (g.user["id"], canonical), one=True):
            run("INSERT INTO student_skills(user_id,skill,level) VALUES(?,?,3)", (g.user["id"], canonical))
        review = [{"q": r, "chosen": request.form.get(f"q{r['id']}")} for r in rows]
        return render_template("student/test_result.html", skill=canonical, correct=correct,
                               total=total, pct=pct, review=review)
    questions = q("SELECT * FROM questions WHERE skill=? COLLATE NOCASE ORDER BY RANDOM() LIMIT 8", (skill,))
    return render_template("student/test.html", skill=questions[0]["skill"], questions=questions)


# ---- recommendations / internships / applications
@app.route("/student/recommendations")
@login_required("student")
def recommendations():
    uid = g.user["id"]
    bundle = student_bundle(uid)
    search = (request.args.get("q") or "").strip().lower()
    min_score = to_int(request.args.get("min"), 0)
    loc = (request.args.get("loc") or "").strip().lower()
    applied = {r["internship_id"] for r in q("SELECT internship_id FROM applications WHERE student_id=?", (uid,))}
    rows = []
    for i in open_internships():
        hay = f"{i['title']} {i['company']} {i['required_skills']} {i['preferred_skills']} {i['category']}".lower()
        if search and search not in hay:
            continue
        if loc and loc not in (i["location"] or "").lower():
            continue
        m = match_for(bundle, i)
        if m["score"] < min_score:
            continue
        rows.append((i, m))
    rows.sort(key=lambda t: -t[1]["score"])
    return render_template("student/recommendations.html", rows=rows, applied=applied,
                           q=request.args.get("q", ""), min=min_score, loc=request.args.get("loc", ""))


@app.route("/internships/<int:iid>")
@login_required()
def internship_detail(iid):
    i = q("""SELECT i.*, e.company, e.description AS company_desc, e.website, e.industry FROM internships i
             LEFT JOIN employer_profiles e ON e.user_id=i.employer_id WHERE i.id=?""", (iid,), one=True)
    if not i:
        abort(404)
    role = g.user["role"]
    if role == "employer" and i["employer_id"] != g.user["id"]:
        abort(403)
    if role == "student" and (i["removed"] or q("SELECT active FROM users WHERE id=?", (i["employer_id"],), one=True)["active"] == 0):
        abort(404)
    match = application = None
    if role == "student":
        match = match_for(student_bundle(g.user["id"]), i)
        application = q("SELECT * FROM applications WHERE internship_id=? AND student_id=?", (iid, g.user["id"]), one=True)
    return render_template("internship.html", i=i, match=match, application=application)


@app.post("/internships/<int:iid>/apply")
@login_required("student")
def apply(iid):
    i = q("SELECT * FROM internships WHERE id=? AND status='open' AND removed=0", (iid,), one=True)
    if not i:
        flash("This internship is no longer open.", "danger")
        return redirect(url_for("recommendations"))
    if i["deadline"] and i["deadline"] < time.strftime("%Y-%m-%d"):
        flash("The application deadline has passed.", "danger")
        return redirect(url_for("internship_detail", iid=iid))
    if q("SELECT 1 FROM applications WHERE internship_id=? AND student_id=?", (iid, g.user["id"]), one=True):
        flash("You have already applied.", "info")
        return redirect(url_for("my_applications"))
    m = match_for(student_bundle(g.user["id"]), i)
    run("INSERT INTO applications(internship_id,student_id,score,cover_note) VALUES(?,?,?,?)",
        (iid, g.user["id"], m["score"], clean("cover_note", 1000)))
    flash(f"Application submitted — your match score was {m['score']}%.", "success")
    return redirect(url_for("my_applications"))


@app.route("/student/applications")
@login_required("student")
def my_applications():
    rows = q("""SELECT a.*, i.title, i.location, e.company FROM applications a
                JOIN internships i ON i.id=a.internship_id
                LEFT JOIN employer_profiles e ON e.user_id=i.employer_id
                WHERE a.student_id=? ORDER BY a.updated_at DESC""", (g.user["id"],))
    return render_template("student/applications.html", rows=rows)


@app.post("/student/applications/<int:aid>/withdraw")
@login_required("student")
def withdraw(aid):
    cur = run("DELETE FROM applications WHERE id=? AND student_id=? AND status='applied'", (aid, g.user["id"]))
    flash("Application withdrawn." if cur.rowcount else "Only pending applications can be withdrawn.", "info")
    return redirect(url_for("my_applications"))


# ---------------------------------------------------------------- employer
def own_internship(iid):
    i = q("SELECT * FROM internships WHERE id=? AND employer_id=?", (iid, g.user["id"]), one=True)
    if not i:
        abort(404)
    return i


@app.route("/employer")
@login_required("employer")
def employer_dashboard():
    uid = g.user["id"]
    listings = q("""SELECT i.*, (SELECT COUNT(*) FROM applications a WHERE a.internship_id=i.id) AS apps,
                    (SELECT ROUND(AVG(score),1) FROM applications a WHERE a.internship_id=i.id) AS avg_score
                    FROM internships i WHERE i.employer_id=? AND i.removed=0 ORDER BY i.created_at DESC""", (uid,))
    counts = {s: 0 for s in STATUSES}
    for r in q("""SELECT a.status, COUNT(*) c FROM applications a JOIN internships i ON i.id=a.internship_id
                  WHERE i.employer_id=? GROUP BY a.status""", (uid,)):
        counts[r["status"]] = r["c"]
    top = q("""SELECT a.*, u.name, i.title FROM applications a JOIN users u ON u.id=a.student_id
               JOIN internships i ON i.id=a.internship_id WHERE i.employer_id=? AND a.status='applied'
               ORDER BY a.score DESC LIMIT 5""", (uid,))
    return render_template("employer/dashboard.html", listings=listings, counts=counts, top=top,
                           open_count=sum(1 for l in listings if l["status"] == "open"),
                           total_apps=sum(counts.values()))


@app.route("/employer/profile", methods=["GET", "POST"])
@login_required("employer")
def employer_profile():
    uid = g.user["id"]
    if request.method == "POST":
        company = clean("company", 120)
        if not company:
            flash("Company name is required.", "danger")
            return redirect(url_for("employer_profile"))
        website = clean("website", 200)
        if website and not re.match(r"^https?://", website):
            website = "https://" + website
        run("UPDATE employer_profiles SET company=?, industry=?, website=?, description=?, location=? WHERE user_id=?",
            (company, clean("industry"), website, clean("description", 1000), clean("location"), uid))
        flash("Company profile saved.", "success")
        return redirect(url_for("employer_dashboard"))
    return render_template("employer/profile.html",
                           p=q("SELECT * FROM employer_profiles WHERE user_id=?", (uid,), one=True))


def internship_form_values():
    title = clean("title", 150)
    required = csv_clean(request.form.get("required_skills"))
    errors = []
    if not title:
        errors.append("Title is required.")
    if not required:
        errors.append("List at least one required skill.")
    deadline = clean("deadline", 10)
    if deadline and not re.match(r"^\d{4}-\d{2}-\d{2}$", deadline):
        errors.append("Deadline must be a valid date.")
    vals = (title, clean("description", 3000), required, csv_clean(request.form.get("preferred_skills")),
            clean("min_degree", 50), clean("field", 100), clean("category", 100),
            clean("location", 100), clean("duration", 50), deadline)
    return vals, errors


@app.route("/employer/internships/new", methods=["GET", "POST"])
@login_required("employer")
def new_internship():
    if request.method == "POST":
        vals, errors = internship_form_values()
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("employer/internship_form.html", i=request.form, editing=False), 400
        iid = run("""INSERT INTO internships(employer_id,title,description,required_skills,preferred_skills,
                     min_degree,field,category,location,duration,deadline) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                  (g.user["id"], *vals)).lastrowid
        flash("Internship posted.", "success")
        return redirect(url_for("candidates", iid=iid))
    return render_template("employer/internship_form.html", i={}, editing=False)


@app.route("/employer/internships/<int:iid>/edit", methods=["GET", "POST"])
@login_required("employer")
def edit_internship(iid):
    i = own_internship(iid)
    if request.method == "POST":
        vals, errors = internship_form_values()
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("employer/internship_form.html", i=request.form, editing=True, iid=iid), 400
        run("""UPDATE internships SET title=?,description=?,required_skills=?,preferred_skills=?,min_degree=?,
               field=?,category=?,location=?,duration=?,deadline=? WHERE id=?""", (*vals, iid))
        flash("Internship updated.", "success")
        return redirect(url_for("employer_dashboard"))
    return render_template("employer/internship_form.html", i=i, editing=True, iid=iid)


@app.post("/employer/internships/<int:iid>/toggle")
@login_required("employer")
def toggle_internship(iid):
    i = own_internship(iid)
    if i["removed"]:
        abort(403)
    run("UPDATE internships SET status=? WHERE id=?", ("closed" if i["status"] == "open" else "open", iid))
    return redirect(url_for("employer_dashboard"))


@app.post("/employer/internships/<int:iid>/delete")
@login_required("employer")
def delete_internship(iid):
    own_internship(iid)
    run("DELETE FROM internships WHERE id=?", (iid,))
    flash("Internship deleted.", "info")
    return redirect(url_for("employer_dashboard"))


@app.route("/employer/internships/<int:iid>/candidates")
@login_required("employer")
def candidates(iid):
    i = own_internship(iid)
    status = request.args.get("status", "")
    apps = q("""SELECT a.*, u.name, u.email, sp.university, sp.degree, sp.major, sp.gpa
                FROM applications a JOIN users u ON u.id=a.student_id
                LEFT JOIN student_profiles sp ON sp.user_id=a.student_id
                WHERE a.internship_id=?""", (iid,))
    if status in STATUSES:
        apps = [a for a in apps if a["status"] == status]
    rows = ranked_applicants(i, apps)  # live scores (profiles may have improved)
    per_page = 50
    pages = max(1, -(-len(rows) // per_page))
    page = min(max(to_int(request.args.get("page"), 1), 1), pages)
    return render_template("employer/candidates.html", i=i, rows=rows[(page - 1) * per_page:page * per_page],
                           status=status, statuses=STATUSES, page=page, pages=pages, total=len(rows),
                           offset=(page - 1) * per_page)


def csv_response(filename, header, rows):
    import csv
    import io
    from flask import Response
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for row in rows:  # neutralise spreadsheet formula injection
        w.writerow([("'" + c if isinstance(c, str) and c[:1] in "=+-@" else c) for c in row])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


@app.route("/employer/internships/<int:iid>/candidates.csv")
@login_required("employer")
def candidates_csv(iid):
    i = own_internship(iid)
    apps = q("""SELECT a.*, u.name, u.email, sp.university, sp.degree, sp.major, sp.gpa
                FROM applications a JOIN users u ON u.id=a.student_id
                LEFT JOIN student_profiles sp ON sp.user_id=a.student_id WHERE a.internship_id=?""", (iid,))
    scored = ranked_applicants(i, apps)
    rows = [(n, a["name"], a["email"], a["university"], a["degree"], a["major"], a["gpa"], m["score"],
             a["status"], ", ".join(m["missing"])) for n, (a, m) in enumerate(scored, 1)]
    return csv_response(f"candidates_{iid}.csv", ["rank", "name", "email", "university", "degree", "major",
                        "gpa", "match_score", "status", "missing_required_skills"], rows)


@app.post("/employer/applications/<int:aid>/status")
@login_required("employer")
def set_status(aid):
    a = q("""SELECT a.*, i.employer_id FROM applications a JOIN internships i ON i.id=a.internship_id
             WHERE a.id=?""", (aid,), one=True)
    if not a or a["employer_id"] != g.user["id"]:
        abort(404)
    status = request.form.get("status")
    if status not in STATUSES:
        abort(400)
    run("UPDATE applications SET status=?, updated_at=datetime('now') WHERE id=?", (status, aid))
    flash(f"Candidate marked as {status}.", "success")
    return redirect(request.referrer or url_for("candidates", iid=a["internship_id"]))


@app.route("/employer/applications/<int:aid>")
@login_required("employer")
def view_candidate(aid):
    a = q("""SELECT a.*, i.employer_id FROM applications a JOIN internships i ON i.id=a.internship_id
             WHERE a.id=?""", (aid,), one=True)
    if not a or a["employer_id"] != g.user["id"]:
        abort(404)  # employers see only students who applied to their own listings
    i = q("SELECT * FROM internships WHERE id=?", (a["internship_id"],), one=True)
    student = q("SELECT id,name,email FROM users WHERE id=?", (a["student_id"],), one=True)
    bundle = student_bundle(a["student_id"])
    results = q("SELECT skill, MAX(pct) best FROM test_results WHERE user_id=? GROUP BY skill", (a["student_id"],))
    return render_template("employer/candidate.html", a=a, i=i, s=student, bundle=bundle,
                           match=match_for(bundle, i), results=results, statuses=STATUSES)


# ---------------------------------------------------------------- admin
@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    one = lambda sql: q(sql, one=True)["c"]
    stats = {
        "students": one("SELECT COUNT(*) c FROM users WHERE role='student'"),
        "employers": one("SELECT COUNT(*) c FROM users WHERE role='employer'"),
        "internships": one("SELECT COUNT(*) c FROM internships WHERE removed=0"),
        "open": one("SELECT COUNT(*) c FROM internships WHERE removed=0 AND status='open'"),
        "applications": one("SELECT COUNT(*) c FROM applications"),
        "placed": one("SELECT COUNT(*) c FROM applications WHERE status='accepted'"),
        "tests": one("SELECT COUNT(*) c FROM test_results"),
    }
    by_status = {s: 0 for s in STATUSES}
    for r in q("SELECT status, COUNT(*) c FROM applications GROUP BY status"):
        by_status[r["status"]] = r["c"]
    top_skills = q("""SELECT skill, COUNT(*) c FROM student_skills GROUP BY LOWER(skill)
                      ORDER BY c DESC LIMIT 8""")
    avg_score = q("SELECT ROUND(AVG(score),1) c FROM applications", one=True)["c"]
    institutions = q("""SELECT COALESCE(NULLIF(sp.university,''),'(not set)') AS university,
                        COUNT(DISTINCT sp.user_id) AS students,
                        COUNT(a.id) AS applications,
                        COALESCE(SUM(a.status='shortlisted'),0) AS shortlisted,
                        COALESCE(SUM(a.status='accepted'),0) AS placed
                        FROM student_profiles sp JOIN users u ON u.id=sp.user_id AND u.active=1
                        LEFT JOIN applications a ON a.student_id=sp.user_id
                        GROUP BY 1 ORDER BY placed DESC, students DESC""")
    return render_template("admin/dashboard.html", stats=stats, by_status=by_status,
                           top_skills=top_skills, avg_score=avg_score, institutions=institutions,
                           impact=impact_metrics())


def impact_metrics():
    """Measures the SOW objectives from real usage data.
    Baselines (manual process) are entered by the team from their own timed trial/survey."""
    tta = q("""SELECT ROUND(AVG((julianday(first_app) - julianday(u.created_at)) * 1440), 1) AS minutes, COUNT(*) AS n
               FROM (SELECT student_id, MIN(created_at) AS first_app FROM applications GROUP BY student_id) f
               JOIN users u ON u.id = f.student_id""", one=True)
    rev = q("""SELECT ROUND(AVG((julianday(updated_at) - julianday(created_at)) * 24), 2) AS hours, COUNT(*) AS n
               FROM applications WHERE status != 'applied'""", one=True)
    placed = q("SELECT COUNT(DISTINCT student_id) c FROM applications WHERE status='accepted'", one=True)["c"]
    students = q("SELECT COUNT(*) c FROM users WHERE role='student'", one=True)["c"]
    cfg = {r["key"]: float(r["value"]) for r in q("SELECT * FROM settings")}

    def gain(baseline, measured):
        if not baseline or measured is None:
            return None
        return round(100 * (baseline - measured) / baseline, 1)

    return {
        "tta_minutes": tta["minutes"], "tta_n": tta["n"],
        "review_hours": rev["hours"], "review_n": rev["n"],
        "placement_rate": round(100 * placed / students, 1) if students else 0, "placed": placed,
        "base_tta": cfg.get("base_tta"), "base_review": cfg.get("base_review"),
        "tta_gain": gain(cfg.get("base_tta"), tta["minutes"]),
        "review_gain": gain(cfg.get("base_review"), rev["hours"]),
    }


@app.post("/admin/baselines")
@login_required("admin")
def admin_baselines():
    for key in ("base_tta", "base_review"):
        raw = request.form.get(key, "").strip()
        if raw == "":
            run("DELETE FROM settings WHERE key=?", (key,))
            continue
        try:
            val = float(raw)
            if val <= 0:
                raise ValueError
        except ValueError:
            flash("Baselines must be positive numbers.", "danger")
            return redirect(url_for("admin_dashboard"))
        run("INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(val)))
    flash("Baselines saved.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/institutions.csv")
@login_required("admin")
def admin_institutions_csv():
    rows = q("""SELECT COALESCE(NULLIF(sp.university,''),'(not set)') AS university,
                COUNT(DISTINCT sp.user_id) AS students, COUNT(a.id) AS applications,
                COALESCE(SUM(a.status='accepted'),0) AS placed
                FROM student_profiles sp LEFT JOIN applications a ON a.student_id=sp.user_id
                GROUP BY 1 ORDER BY 1""")
    return csv_response("institution_report.csv", ["university", "students", "applications", "placed"],
                        [tuple(r) for r in rows])


@app.route("/admin/users")
@login_required("admin")
def admin_users():
    role = request.args.get("role", "")
    term = (request.args.get("q") or "").strip()
    sql, args = "SELECT * FROM users WHERE 1=1", []
    if role in ("student", "employer", "admin"):
        sql += " AND role=?"
        args.append(role)
    if term:
        sql += " AND (name LIKE ? OR email LIKE ?)"
        args += [f"%{term}%"] * 2
    page = max(to_int(request.args.get("page"), 1), 1)
    total = q(sql.replace("SELECT *", "SELECT COUNT(*) c", 1), args, one=True)["c"]
    users = q(sql + " ORDER BY created_at DESC, id DESC LIMIT 100 OFFSET ?", [*args, (page - 1) * 100])
    return render_template("admin/users.html", users=users, role=role, term=term, page=page,
                           pages=max(1, -(-total // 100)), total=total)


@app.post("/admin/users/<int:uid>/toggle")
@login_required("admin")
def admin_toggle_user(uid):
    if uid == g.user["id"]:
        flash("You cannot deactivate your own account.", "danger")
    else:
        run("UPDATE users SET active = 1 - active WHERE id=?", (uid,))
        flash("User status updated.", "success")
    return redirect(request.referrer or url_for("admin_users"))


@app.post("/admin/users/<int:uid>/delete")
@login_required("admin")
def admin_delete_user(uid):
    if uid == g.user["id"]:
        flash("You cannot delete your own account.", "danger")
    else:
        run("DELETE FROM users WHERE id=?", (uid,))
        flash("User and related data deleted.", "info")
    return redirect(url_for("admin_users"))


@app.route("/admin/internships")
@login_required("admin")
def admin_internships():
    rows = q("""SELECT i.*, e.company, (SELECT COUNT(*) FROM applications a WHERE a.internship_id=i.id) AS apps
                FROM internships i LEFT JOIN employer_profiles e ON e.user_id=i.employer_id
                ORDER BY i.created_at DESC""")
    return render_template("admin/internships.html", rows=rows)


@app.post("/admin/internships/<int:iid>/remove")
@login_required("admin")
def admin_remove_internship(iid):
    run("UPDATE internships SET removed = 1 - removed WHERE id=?", (iid,))
    flash("Listing visibility updated.", "success")
    return redirect(url_for("admin_internships"))


# ---------------------------------------------------------------- errors
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(400)
def error_page(e):
    return render_template("error.html", e=e), e.code


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 5000)))
