import os
import sqlite3
from flask import g

DB_PATH = os.environ.get("INTERNMATCH_DB", os.path.join(os.path.dirname(__file__), "internmatch.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('student','employer','admin')),
    name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS student_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    university TEXT DEFAULT '', degree TEXT DEFAULT '', major TEXT DEFAULT '',
    gpa REAL, grad_year INTEGER, interests TEXT DEFAULT '', bio TEXT DEFAULT '',
    location TEXT DEFAULT '', phone TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS student_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL, level INTEGER NOT NULL DEFAULT 3, kind TEXT NOT NULL DEFAULT 'technical',
    UNIQUE(user_id, skill)
);
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL, description TEXT DEFAULT '', tech TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL, issuer TEXT DEFAULT '', year INTEGER
);
CREATE TABLE IF NOT EXISTS employer_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    company TEXT DEFAULT '', industry TEXT DEFAULT '', website TEXT DEFAULT '',
    description TEXT DEFAULT '', location TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS internships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employer_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL, description TEXT DEFAULT '',
    required_skills TEXT DEFAULT '', preferred_skills TEXT DEFAULT '',
    min_degree TEXT DEFAULT '', field TEXT DEFAULT '', category TEXT DEFAULT '',
    location TEXT DEFAULT '', duration TEXT DEFAULT '', deadline TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','closed')),
    removed INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    internship_id INTEGER NOT NULL REFERENCES internships(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT NOT NULL DEFAULT 'applied' CHECK (status IN ('applied','shortlisted','accepted','rejected')),
    score REAL NOT NULL DEFAULT 0, cover_note TEXT DEFAULT '',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(internship_id, student_id)
);
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    skill TEXT NOT NULL, question TEXT NOT NULL,
    a TEXT NOT NULL, b TEXT NOT NULL, c TEXT NOT NULL, d TEXT NOT NULL,
    answer TEXT NOT NULL CHECK (answer IN ('a','b','c','d'))
);
CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    skill TEXT NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL, pct REAL NOT NULL,
    taken_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_apps_student ON applications(student_id);
CREATE INDEX IF NOT EXISTS idx_apps_internship ON applications(internship_id);
CREATE INDEX IF NOT EXISTS idx_results_user ON test_results(user_id, skill);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def connect():
    """Standalone connection (seed scripts, tests)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = connect()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
