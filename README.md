# InternMatch Student Skills and Internship Matching System

Flask + SQLite web app. Students build skill profiles and take verified tests; employers post internships; a matching algorithm ranks internships for students and candidates for employers.

## Run

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt      # Windows (use .venv/bin/pip on Linux/macOS)
.venv/Scripts/python seed.py                       # question bank + demo data
.venv/Scripts/python app.py                        # http://localhost:5000
```

`python seed.py --reset` rebuilds the database. `python test_smoke.py` runs an end-to-end test on a throwaway DB.

## Demo accounts (local demo only)

| Role | Email | Password |
|---|---|---|
| Admin | admin@internmatch.test | Admin@123 |
| Employer | hr@techcorp.test (also hr@datalab.test, hr@designhub.test) | Demo@1234 |
| Student | ayesha@student.test (also bilal@, sara@, usman@, hina@student.test) | Demo@1234 |

## Matching algorithm (`matching.py`)

Score 0–100 = required skills 50% + preferred skills 15% + education (degree level + field) 15% + interests 10% + projects/certs mentioning the required skills 10%.
A skill's proficiency is `0.7 × level/5` when only self-rated, and `0.3 × level/5 + 0.7 × best test %` when test-verified, so verified skills count more. Each score shows matched/missing skills and a per-factor breakdown.

## Requirements coverage

| SOW item | Where |
|---|---|
| Registration, login, role-based access | `/register`, `/login`, `login_required(role)` in `app.py` |
| Student profile, skills, projects, certs | `/student/profile` |
| Skill tests + performance tracking | `/student/tests`, dashboard |
| Employer profile + internship management | `/employer/*` |
| Ranked recommendations / ranked candidates | `/student/recommendations`, `/employer/internships/<id>/candidates` |
| Apply + track status (applied → shortlisted/accepted/rejected) | `/student/applications`, candidate pages |
| Dashboards + analytics | student, employer, admin dashboards (Chart.js) |
| Admin panel | `/admin`, `/admin/users`, `/admin/internships` |
| Security | hashed passwords, CSRF tokens, parameterized SQL, login throttling, employers see only their own applicants |
| Responsive UI | Bootstrap 5 |

## Deploying

See `docs/DEPLOYMENT.md` (PythonAnywhere free with permanent storage, or Render via `render.yaml`). Production start-up runs `bootstrap.py`, which creates the first admin from `ADMIN_EMAIL` / `ADMIN_PASSWORD` and never loads the demo accounts. Health check: `/healthz`.
Out of scope per the SOW: native apps, chat/interviews, payments, CV parsing, SIS/LMS integration.

## Accuracy evaluation

`python evaluate_matching.py [threshold]` compares predictions (score >= threshold) with hand-labelled fit for all 35 student x internship pairs in the demo data. Current result at 55%: 97.1% accuracy, 88.9% precision, 100% recall. The labels are the team's judgement on 5 demo students, so re-run it with real labelled data for the final report.
Employers can export ranked candidates to CSV; admins can download an institution report (students, applications, placements per university).

## Performance, objective tracking and documents

- `python perf_test.py` loads 2,000 students, 307 internships and 2,000 applicants on one listing, then times every heavy page. Slowest page: about 0.5 s (target 2 s). Candidate lists and admin users are paginated and profiles are loaded in batches.
- Admin → Objective tracking measures time to first application, application-to-decision time and placement rate from real usage. Enter your manual-process baselines there to get the 50% and 60% improvement figures.
- `docs/USER_MANUAL.md`, `docs/PROJECT_CHARTER.md`, `docs/WBS_AND_PLAN.md` (WBS, schedule, test plan, traceability) and `docs/DESIGN.md` (ERD, UI/UX design).

- `docs/DEPLOYMENT.md` (hosting steps), `docs/UAT_SCRIPT.md` (acceptance test for real testers), `docs/BASELINE_STUDY.md` (how to measure the manual baselines for the 50% and 60% targets).
