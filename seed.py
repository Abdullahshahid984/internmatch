"""Seed the database with the skill-test question bank and demo data.

    python seed.py            # question bank + demo users/internships (skips if already seeded)
    python seed.py --reset    # delete the database first

Demo logins (local demo only, change before any real deployment):
    admin     admin@internmatch.test       Admin@123
    employer  hr@techcorp.test             Demo@1234   (also hr@datalab.test, hr@designhub.test)
    student   ayesha@student.test          Demo@1234   (also bilal@, sara@, usman@, hina@student.test)
"""
import os
import sys

import db
from werkzeug.security import generate_password_hash

QUESTIONS = [
    # ---- Python
    ("Python", "Which keyword defines a function in Python?", "func", "def", "function", "lambda only", "b"),
    ("Python", "What is the output of len([1, 2, 3])?", "2", "3", "4", "Error", "b"),
    ("Python", "Which data type is immutable?", "list", "dict", "tuple", "set", "c"),
    ("Python", "How do you start a comprehension of squares for x in range(3)?", "[x*x for x in range(3)]", "(for x in range(3): x*x)", "{x*x in range(3)}", "map(x*x, 3)", "a"),
    ("Python", "What does `pip` do?", "Runs tests", "Installs packages", "Formats code", "Compiles Python", "b"),
    ("Python", "Which statement handles exceptions?", "try/except", "catch/throw", "error/handle", "if/error", "a"),
    ("Python", "What is `None` in Python?", "Zero", "An empty string", "The null object", "A syntax error", "c"),
    ("Python", "Which method adds an item to the end of a list?", "push()", "append()", "add()", "insert_end()", "b"),
    # ---- JavaScript
    ("JavaScript", "Which keyword declares a block-scoped variable?", "var", "let", "def", "dim", "b"),
    ("JavaScript", "What does `===` do?", "Assigns a value", "Compares value only", "Compares value and type", "Declares equality", "c"),
    ("JavaScript", "Which method converts JSON text to an object?", "JSON.stringify", "JSON.parse", "JSON.object", "JSON.decode", "b"),
    ("JavaScript", "What is the result of typeof []?", "array", "object", "list", "undefined", "b"),
    ("JavaScript", "Which array method returns a new array of transformed items?", "forEach", "map", "push", "splice", "b"),
    ("JavaScript", "What does `async` before a function do?", "Makes it run in a thread", "Makes it return a Promise", "Makes it private", "Blocks the event loop", "b"),
    ("JavaScript", "How do you write a single-line comment?", "# comment", "<!-- comment -->", "// comment", "/* comment", "c"),
    ("JavaScript", "What does `NaN` stand for?", "Not a Node", "No assigned name", "Not a Number", "Null and None", "c"),
    # ---- SQL
    ("SQL", "Which clause filters rows?", "ORDER BY", "WHERE", "GROUP BY", "LIMIT", "b"),
    ("SQL", "Which statement adds new rows?", "ADD ROW", "INSERT INTO", "UPDATE", "CREATE ROW", "b"),
    ("SQL", "Which join returns only rows with matches in both tables?", "LEFT JOIN", "INNER JOIN", "CROSS JOIN", "FULL JOIN only", "b"),
    ("SQL", "Which function counts rows?", "SUM()", "COUNT()", "TOTAL()", "ROWS()", "b"),
    ("SQL", "What does PRIMARY KEY guarantee?", "Fast deletes", "Unique, non-null identifier", "Encrypted column", "Sorted rows", "b"),
    ("SQL", "Which clause groups rows for aggregates?", "GROUP BY", "SORT BY", "COLLECT", "AGGREGATE", "a"),
    ("SQL", "How do you sort descending?", "ORDER BY col DESC", "SORT col DOWN", "ORDER col REVERSE", "GROUP col DESC", "a"),
    ("SQL", "Which removes a table entirely?", "DELETE TABLE", "REMOVE TABLE", "DROP TABLE", "TRUNCATE ROWS", "c"),
    # ---- HTML
    ("HTML", "Which tag creates a hyperlink?", "<link>", "<a>", "<href>", "<url>", "b"),
    ("HTML", "Which tag is the largest heading?", "<h6>", "<heading>", "<h1>", "<head>", "c"),
    ("HTML", "Which attribute gives an image alternative text?", "title", "alt", "src", "text", "b"),
    ("HTML", "Which element holds the visible page content?", "<body>", "<head>", "<main-content>", "<html-body>", "a"),
    ("HTML", "Which tag makes an unordered list?", "<ol>", "<ul>", "<li>", "<list>", "b"),
    ("HTML", "What does the viewport meta tag help with?", "SEO ranking", "Responsive layout on mobile", "Page caching", "Security", "b"),
    ("HTML", "Which input type shows a date picker?", "type=\"calendar\"", "type=\"date\"", "type=\"time-date\"", "type=\"day\"", "b"),
    ("HTML", "Which element should wrap navigation links semantically?", "<nav>", "<menu-bar>", "<links>", "<div-nav>", "a"),
    # ---- Git
    ("Git", "Which command creates a new commit from staged changes?", "git push", "git commit", "git stage", "git save", "b"),
    ("Git", "Which command stages all changes?", "git add .", "git stage --all", "git commit -a .", "git include", "a"),
    ("Git", "Which command copies a remote repository locally?", "git copy", "git pull", "git clone", "git fork", "c"),
    ("Git", "What does `git branch feature` do?", "Switches to feature", "Creates a branch called feature", "Deletes feature", "Merges feature", "b"),
    ("Git", "Which command shows uncommitted changes status?", "git status", "git log", "git show", "git info", "a"),
    ("Git", "What does `git pull` do?", "Uploads commits", "Fetches and merges remote changes", "Deletes a branch", "Creates a tag", "b"),
    ("Git", "Which file lists paths Git should not track?", ".gitconfig", ".gitignore", ".gitkeep", "ignore.txt", "b"),
    ("Git", "Which command uploads local commits to the remote?", "git send", "git upload", "git push", "git sync", "c"),
    # ---- React
    ("React", "What is JSX?", "A database", "A syntax extension that looks like HTML in JS", "A CSS preprocessor", "A bundler", "b"),
    ("React", "Which hook manages local component state?", "useEffect", "useState", "useRef only", "useData", "b"),
    ("React", "What do props do?", "Pass data to a child component", "Store global state", "Route pages", "Style components", "a"),
    ("React", "When does useEffect with an empty dependency array run?", "Every render", "Once after the first render", "Never", "Only on unmount", "b"),
    ("React", "Why give list items a `key`?", "For styling", "To help React identify changed items", "For accessibility", "To sort them", "b"),
    ("React", "How do you handle a click in JSX?", "onclick=\"fn()\"", "onClick={fn}", "on-click=fn", "@click=fn", "b"),
    ("React", "A React component name must start with…", "A lowercase letter", "A number", "An uppercase letter", "An underscore", "c"),
    ("React", "What is the virtual DOM?", "A browser plugin", "An in-memory representation React diffs to update the UI", "A server", "A CSS feature", "b"),
    # ---- Communication
    ("Communication", "A teammate misses a deadline. What is the best first step?", "Report them publicly", "Ask privately what blocked them and offer help", "Redo their work silently", "Ignore it", "b"),
    ("Communication", "In a meeting you don't understand a term. You should…", "Pretend to understand", "Ask for a short clarification", "Leave", "Google it silently and say nothing later", "b"),
    ("Communication", "Which email subject is clearest?", "Hi", "Question", "Request: Feedback on report draft by Friday", "URGENT!!!", "c"),
    ("Communication", "Active listening includes…", "Planning your reply while they talk", "Paraphrasing to confirm understanding", "Interrupting early", "Checking your phone", "b"),
    ("Communication", "When giving feedback, it is most effective to be…", "Vague and general", "Specific and focused on behaviour", "Public", "Sarcastic", "b"),
    ("Communication", "Your status update to a manager should lead with…", "A long backstory", "The key result and any blockers", "Apologies", "Technical detail only", "b"),
    ("Communication", "A client's request is ambiguous. You…", "Guess", "Ask clarifying questions before starting", "Wait silently", "Do the easiest interpretation", "b"),
    ("Communication", "Which is a good habit in remote teams?", "Writing decisions down", "Avoiding written updates", "Never turning on cameras", "Replying days later", "a"),
]

EMPLOYERS = [
    ("hr@techcorp.test", "Maria Khan", "TechCorp Solutions", "Software", "Lahore", "We build web platforms and cloud tools for retail and fintech clients."),
    ("hr@datalab.test", "Omar Siddiqui", "DataLab Analytics", "Data & AI", "Islamabad", "Applied analytics and machine learning for logistics and health."),
    ("hr@designhub.test", "Zainab Ali", "DesignHub Studio", "Design & Marketing", "Remote", "A product design and front-end studio working with startups."),
]

INTERNSHIPS = [
    (0, "Backend Developer Intern", "Build REST APIs and database queries for our retail platform.", "Python, SQL, Git", "Docker, Flask", "Bachelor", "Computer Science", "backend development", "Lahore", "3 months"),
    (0, "Full-Stack Web Intern", "Work on React dashboards backed by Node services.", "JavaScript, React, HTML", "Node.js, SQL", "Bachelor", "Computer Science", "web development", "Lahore", "6 months"),
    (0, "QA Automation Intern", "Write automated tests and report defects.", "Python, Git", "JavaScript, SQL", "Diploma", "Software Engineering", "testing", "Lahore", "3 months"),
    (1, "Data Analyst Intern", "Clean datasets, write SQL reports and build charts.", "SQL, Python, Data Analysis", "Excel, Communication", "Bachelor", "Data Science", "data science", "Islamabad", "4 months"),
    (1, "Machine Learning Intern", "Prototype models for demand forecasting.", "Python, Machine Learning, Statistics", "SQL, Git", "Bachelor", "Computer Science", "machine learning", "Islamabad", "6 months"),
    (2, "Front-End Developer Intern", "Implement responsive UIs from Figma designs.", "HTML, CSS, JavaScript", "React, Git, Communication", "Diploma", "Computer Science", "web development", "Remote", "3 months"),
    (2, "UI/UX Design Intern", "Create wireframes and prototypes, run usability tests.", "Figma, UX Research, Communication", "HTML, CSS", "Bachelor", "Design", "design", "Remote", "3 months"),
]

# (email, name, uni, degree, major, gpa, year, interests, location, bio, skills[(name, level)], projects, certs)
STUDENTS = [
    ("ayesha@student.test", "Ayesha Rehman", "FAST NUCES", "Bachelor", "Computer Science", 3.6, 2026,
     "backend development, data science", "Lahore", "Final-year CS student who loves building APIs.",
     [("Python", 4), ("SQL", 4), ("Git", 4), ("Flask", 3), ("Docker", 2), ("Communication", 4)],
     [("Library API", "REST API for a library system with auth.", "Python, Flask, SQLite")],
     [("Python Institute PCAP", "Python Institute", 2025)],
     {"Python": 87.5, "SQL": 75.0, "Git": 100.0}),
    ("bilal@student.test", "Bilal Ahmed", "NUST", "Bachelor", "Computer Science", 3.2, 2026,
     "web development", "Islamabad", "Front-end focused, enjoys clean UIs.",
     [("JavaScript", 4), ("React", 4), ("HTML", 5), ("CSS", 4), ("Git", 3)],
     [("Portfolio site", "Responsive portfolio with React.", "React, CSS"), ("Task board", "Kanban app.", "JavaScript, HTML")],
     [("Meta Front-End Certificate", "Coursera", 2025)],
     {"JavaScript": 75.0, "React": 62.5, "HTML": 87.5}),
    ("sara@student.test", "Sara Malik", "LUMS", "Bachelor", "Data Science", 3.8, 2027,
     "data science, machine learning", "Lahore", "Data enthusiast, Kaggle competitor.",
     [("Python", 5), ("Machine Learning", 4), ("Statistics", 4), ("SQL", 3), ("Data Analysis", 5), ("Excel", 4)],
     [("Churn predictor", "Logistic regression on telecom data.", "Python, Machine Learning"), ("Sales dashboard", "SQL + charts.", "SQL, Data Analysis")],
     [("Google Data Analytics", "Coursera", 2025)],
     {"Python": 100.0, "SQL": 62.5}),
    ("usman@student.test", "Usman Tariq", "COMSATS", "Diploma", "Software Engineering", 2.9, 2026,
     "testing", "Lahore", "Interested in quality assurance.",
     [("Python", 3), ("Git", 3), ("JavaScript", 2)],
     [("Selenium suite", "Automated tests for a shop site.", "Python")],
     [],
     {"Git": 62.5}),
    ("hina@student.test", "Hina Farooq", "NCA", "Bachelor", "Design", 3.5, 2026,
     "design", "Remote", "Product designer who also writes some HTML/CSS.",
     [("Figma", 5), ("UX Research", 4), ("Communication", 5), ("HTML", 3), ("CSS", 3)],
     [("Banking app redesign", "Case study with usability tests.", "Figma, UX Research")],
     [("Google UX Design", "Coursera", 2024)],
     {"Communication": 87.5, "HTML": 50.0}),
]


def seed():
    db.init_db()
    conn = db.connect()
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
        print("Database already has users; skipping demo data (use --reset to start over).")
        conn.close()
        return
    conn.executemany("INSERT INTO questions(skill,question,a,b,c,d,answer) VALUES(?,?,?,?,?,?,?)", QUESTIONS)

    def add_user(email, name, role, pw):
        return conn.execute("INSERT INTO users(email,password_hash,role,name) VALUES(?,?,?,?)",
                            (email, generate_password_hash(pw), role, name)).lastrowid

    add_user("admin@internmatch.test", "System Admin", "admin", "Admin@123")

    emp_ids = []
    for email, name, company, industry, loc, desc in EMPLOYERS:
        uid = add_user(email, name, "employer", "Demo@1234")
        emp_ids.append(uid)
        conn.execute("INSERT INTO employer_profiles(user_id,company,industry,location,description,website) VALUES(?,?,?,?,?,?)",
                     (uid, company, industry, loc, desc, "https://example.com"))
    for e, title, desc, req, pref, deg, field, cat, loc, dur in INTERNSHIPS:
        conn.execute("""INSERT INTO internships(employer_id,title,description,required_skills,preferred_skills,
                        min_degree,field,category,location,duration) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                     (emp_ids[e], title, desc, req, pref, deg, field, cat, loc, dur))

    for email, name, uni, deg, major, gpa, year, interests, loc, bio, skills, projects, certs, tests in STUDENTS:
        uid = add_user(email, name, "student", "Demo@1234")
        conn.execute("""INSERT INTO student_profiles(user_id,university,degree,major,gpa,grad_year,interests,bio,location)
                        VALUES(?,?,?,?,?,?,?,?,?)""", (uid, uni, deg, major, gpa, year, interests, bio, loc))
        conn.executemany("INSERT INTO student_skills(user_id,skill,level,kind) VALUES(?,?,?,?)",
                         [(uid, s, lv, "soft" if s == "Communication" else "technical") for s, lv in skills])
        conn.executemany("INSERT INTO projects(user_id,title,description,tech) VALUES(?,?,?,?)",
                         [(uid, *p) for p in projects])
        conn.executemany("INSERT INTO certifications(user_id,name,issuer,year) VALUES(?,?,?,?)",
                         [(uid, *c) for c in certs])
        for skill, pct in tests.items():
            conn.execute("INSERT INTO test_results(user_id,skill,correct,total,pct) VALUES(?,?,?,8,?)",
                         (uid, skill, round(pct * 8 / 100), pct))
    conn.commit()
    conn.close()
    print("Seeded question bank, 1 admin, 3 employers, 7 internships, 5 students.")


if __name__ == "__main__":
    if "--reset" in sys.argv and os.path.exists(db.DB_PATH):
        os.remove(db.DB_PATH)
    seed()
