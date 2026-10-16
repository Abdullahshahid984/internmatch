"""Matching accuracy evaluation (WBS 8.0 / objective: >= 70% accuracy).

Compares the algorithm's suitable / not-suitable prediction (score >= THRESHOLD) with hand-labelled
ground truth for every student x internship pair in the seeded demo data.

    python evaluate_matching.py [threshold]

NOTE: the labels below are the team's judgement on the demo data. For the final report, replace them
with labels from real supervisors / employers on real profiles.
"""
import os
import sys
import tempfile

os.environ["INTERNMATCH_DB"] = os.path.join(tempfile.mkdtemp(), "eval.db")
import seed  # noqa: E402

seed.seed()
import app as A  # noqa: E402

THRESHOLD = float(sys.argv[1]) if len(sys.argv) > 1 else 55.0

GOLD = {  # student email -> internships that are a genuine fit
    "ayesha@student.test": {"Backend Developer Intern", "QA Automation Intern"},
    "bilal@student.test": {"Front-End Developer Intern", "Full-Stack Web Intern"},
    "sara@student.test": {"Data Analyst Intern", "Machine Learning Intern"},
    "usman@student.test": {"QA Automation Intern"},
    "hina@student.test": {"UI/UX Design Intern"},
}

tp = fp = tn = fn = 0
with A.app.app_context():
    con = seed.db.connect()
    for email, fits in GOLD.items():
        uid = con.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()[0]
        bundle = A.student_bundle(uid)
        for i in A.open_internships():
            predicted = A.match_for(bundle, i)["score"] >= THRESHOLD
            actual = i["title"] in fits
            tp += predicted and actual
            fp += predicted and not actual
            fn += (not predicted) and actual
            tn += (not predicted) and not actual

total = tp + fp + tn + fn
print(f"threshold {THRESHOLD:.0f}%  pairs {total}")
print(f"TP {tp}  FP {fp}  TN {tn}  FN {fn}")
print(f"accuracy  {100 * (tp + tn) / total:.1f}%")
print(f"precision {100 * tp / max(1, tp + fp):.1f}%   recall {100 * tp / max(1, tp + fn):.1f}%")
