"""Matching algorithm: scores a student profile against an internship.

Score (0-100) = weighted sum of
  required skills   50%  (proficiency-weighted coverage)
  preferred skills  15%
  education         15%  (degree level + field of study)
  interests         10%  (internship category / title vs student interests)
  evidence          10%  (projects and certifications that mention the required skills)

Proficiency of a skill (0-1):
  self-rated level only      -> 0.7 * level/5   (unverified skills are discounted)
  with a skill-test result   -> 0.3 * level/5 + 0.7 * test%   (test result dominates)
"""
import re

ALIASES = {
    "js": "javascript", "node": "node.js", "nodejs": "node.js", "reactjs": "react",
    "react.js": "react", "py": "python", "ml": "machine learning", "postgres": "postgresql",
    "mongo": "mongodb", "html5": "html", "css3": "css", "ts": "typescript",
    "c plus plus": "c++", "cpp": "c++", "golang": "go", "ai": "machine learning",
}
DEGREE_RANK = {"": 0, "any": 0, "high school": 1, "diploma": 1, "associate": 1,
               "bachelor": 2, "bachelors": 2, "bs": 2, "master": 3, "masters": 3, "ms": 3, "phd": 4}

W_REQ, W_PREF, W_EDU, W_INT, W_EVID = 0.50, 0.15, 0.15, 0.10, 0.10


def norm(skill):
    s = re.sub(r"\s+", " ", (skill or "").strip().lower())
    return ALIASES.get(s, s)


def split_list(text):
    return [norm(x) for x in re.split(r"[,;\n]", text or "") if x.strip()]


def _tokens(text):
    return set(re.findall(r"[a-z0-9\+\#\.]{2,}", (text or "").lower()))


def proficiency(level, test_pct):
    base = max(1, min(5, level or 1)) / 5.0
    if test_pct is None:
        return 0.7 * base
    return 0.3 * base + 0.7 * (test_pct / 100.0)


def degree_rank(text):
    low = (text or "").strip().lower()
    for key in ("phd", "master", "bachelor", "diploma", "high school"):
        if key in low:
            return DEGREE_RANK[key]
    return DEGREE_RANK.get(low, 0)


def education_score(student, internship):
    need = degree_rank(internship["min_degree"])
    have = degree_rank(student["degree"])
    degree = 1.0 if have >= need else (0.5 if have == need - 1 and have > 0 else 0.0)
    if need == 0:
        degree = 1.0
    field = (internship["field"] or "").strip().lower()
    major = (student["major"] or "").strip().lower()
    if not field:
        fld = 1.0
    elif field in major or major in field and major:
        fld = 1.0
    else:
        overlap = _tokens(field) & _tokens(major)
        fld = 0.6 if overlap else 0.0
    return 0.5 * degree + 0.5 * fld


def interest_score(student, internship):
    interests = _tokens(student["interests"])
    target = _tokens(internship["category"]) | _tokens(internship["title"])
    if not interests:
        return 0.0
    if not target:
        return 0.5
    hits = len(interests & target)
    return min(1.0, hits / max(1, min(len(interests), 3)))


def evidence_score(required, projects, certs):
    if not required:
        return 0.0
    text = " ".join(f"{p['title']} {p['description']} {p['tech']}" for p in projects)
    text += " " + " ".join(f"{c['name']} {c['issuer']}" for c in certs)
    low = text.lower()
    hits = sum(1 for s in required if s in low)
    return hits / len(required)


def compute_match(student, skills, tests, projects, certs, internship):
    """student: profile row/dict; skills: [{skill, level}]; tests: {skill: best_pct};
    returns dict with score (0-100), breakdown, matched/missing skills."""
    have = {norm(s["skill"]): proficiency(s["level"], tests.get(norm(s["skill"]))) for s in skills}
    verified = {norm(s["skill"]) for s in skills if norm(s["skill"]) in tests}

    required = split_list(internship["required_skills"])
    preferred = split_list(internship["preferred_skills"])

    def coverage(wanted):
        if not wanted:
            return 1.0
        return sum(have.get(w, 0.0) for w in wanted) / len(wanted)

    req_cov, pref_cov = coverage(required), coverage(preferred)
    edu = education_score(student, internship)
    inter = interest_score(student, internship)
    evid = evidence_score(required, projects, certs)

    # Requirement coverage is scaled up so a fully-skilled, verified candidate can reach ~100%.
    score = 100 * (W_REQ * min(1.0, req_cov / 0.85) + W_PREF * min(1.0, pref_cov / 0.85)
                   + W_EDU * edu + W_INT * inter + W_EVID * evid)
    return {
        "score": round(min(100.0, score), 1),
        "breakdown": {
            "Required skills": round(100 * min(1.0, req_cov / 0.85)),
            "Preferred skills": round(100 * min(1.0, pref_cov / 0.85)),
            "Education": round(100 * edu),
            "Interests": round(100 * inter),
            "Projects & certs": round(100 * evid),
        },
        "matched": [s for s in required if s in have],
        "missing": [s for s in required if s not in have],
        "matched_pref": [s for s in preferred if s in have],
        "verified": sorted(verified & set(required + preferred)),
    }


def label(score):
    if score >= 75:
        return "Excellent"
    if score >= 55:
        return "Good"
    if score >= 35:
        return "Fair"
    return "Low"
