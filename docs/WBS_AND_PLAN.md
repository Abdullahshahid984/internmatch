# Work Breakdown Structure, Schedule and Test Plan

## 1. WBS (hierarchy)

```
Student Skills and Internship Matching System                (16 weeks, Project Manager)
├─ 1.0 Project Planning and Design                           (3 wks)
│   ├─ 1.1 Project Charter                                   -> docs/PROJECT_CHARTER.md
│   ├─ 1.2 SOW and Scope Statement
│   ├─ 1.3 WBS and WBS Dictionary                            -> this file
│   ├─ 1.4 System Design (Database and UI)                   -> docs/DESIGN.md
│   └─ 1.5 Progress Tracking and Reporting                   -> section 6 below
├─ 2.0 User Management Module                                (2 wks)
│   ├─ 2.1 Registration and Login
│   ├─ 2.2 Role-Based Access
│   └─ 2.3 Admin User Management                             (/admin/users)
├─ 3.0 Student Profile Module                                (2 wks)
│   ├─ 3.1 Profile Creation
│   ├─ 3.2 Skill Verification Test
│   └─ 3.3 Profile Performance Tracking
├─ 4.0 Employer and Internship Module                        (2 wks)
│   ├─ 4.1 Employer Profile
│   ├─ 4.2 Internship Listing Management
│   └─ 4.3 Admin Listing Management                          (/admin/internships)
├─ 5.0 Matching Module                                       (3 wks)
│   ├─ 5.1 Matching Criteria and Scoring Rules               (matching.py)
│   ├─ 5.2 Matching Algorithm
│   └─ 5.3 Ranked Recommendations with Matching Score
├─ 6.0 Application Tracking Module                           (2 wks)
│   ├─ 6.1 Application Submission
│   ├─ 6.2 Application Status Tracking
│   └─ 6.3 Ranked Candidate Review
├─ 7.0 Dashboard and Analytics                               (1 wk)
│   ├─ 7.1 Student Dashboard
│   ├─ 7.2 Employer Dashboard
│   └─ 7.3 Reports and Analytics
└─ 8.0 Testing and Deployment                                (3 wks)
    ├─ 8.1 Functional and Integration Testing                (section 4 below)
    ├─ 8.2 Matching Accuracy Evaluation                      (evaluate_matching.py)
    ├─ 8.3 User Acceptance Testing                           (section 5 below)
    ├─ 8.4 Deployment and Hosting                            (Procfile, README)
    └─ 8.5 User Manual and Final Handover                    -> docs/USER_MANUAL.md
```

Module durations overlap (sprints run in parallel across the two team members), so they add up to more than 16 weeks of calendar time.

## 2. Work package dictionary

| ID | Task | Responsible | Duration | Resources | Output / done when |
|---|---|---|---|---|---|
| 1.0 | Planning and design | Project Manager, UI/UX Designer | 3 wks | MS Word, draw.io, Figma | Charter, SOW, WBS, ERD and wireframes approved |
| 2.0 | User management | Backend Developer | 2 wks | VS Code, GitHub, database | Register/login work; wrong-role access returns 403 |
| 3.0 | Student profile | Developer | 2 wks | VS Code, database, question bank | Profile saved; tests scored; best score stored |
| 4.0 | Employer and internships | Frontend + Backend Developer | 2 wks | VS Code, database | Listing created with required and preferred skills |
| 5.0 | Matching | Development Team Lead, Backend Developer | 3 wks | VS Code, database, sample data | Scores 0–100 with breakdown, ranked lists |
| 6.0 | Application tracking | Backend Developer | 2 wks | VS Code, database, sample data | Apply, withdraw, status change visible to student |
| 7.0 | Dashboards | UI/UX Designer, Frontend Developer | 1 wk | VS Code, Chart.js | Dashboards show correct counts and charts |
| 8.0 | Testing and deployment | QA Engineer, Deployment Engineer | 3 wks | Test cases, browsers, free hosting | All critical defects closed; live URL; manual delivered |

With two members, the roles above are shared: the project manager takes planning, design, QA and documentation; the team member takes most development and deployment, and both review each other's work.

## 3. Schedule (16 weeks)

| Week | Planned work | Deliverable |
|---|---|---|
| 1–2 | Requirements, charter | Requirements document, charter (wk 2) |
| 3 | Scope, SOW, WBS | Scope/SOW/WBS (wk 3) |
| 4–5 | Database and UI/UX design | Design documents (wk 5) |
| 6–7 | User management; student profile | Auth, profile working |
| 8–9 | Student profile tests; employer and listing module | Student and employer modules (wk 9) |
| 10–11 | Matching algorithm; application tracking | Matching algorithm (wk 11) |
| 12 | Dashboards and admin panel | Admin dashboard (wk 12) |
| 13–14 | Integration, system testing, accuracy evaluation | Test report (wk 14) |
| 15–16 | Deployment, user manual, handover | Final deployment, handover, manual (wk 16) |

## 4. Test plan

| ID | Area | Test | Expected result | Automated in |
|---|---|---|---|---|
| T1 | Auth | Register with weak password / bad email | Rejected with message | test_smoke.py |
| T2 | Auth | Wrong password, repeated failures | 401, then throttled after 5 | test_smoke.py |
| T3 | Security | POST without CSRF token | 400 | test_smoke.py |
| T4 | Security | Password in database | Hash, never plain text | test_smoke.py |
| T5 | Access | Student opens /employer or /admin | 403 | test_smoke.py |
| T6 | Access | Employer opens another employer's candidates | 404 | test_smoke.py |
| T7 | Student | Add skill, project, certification | Shown on profile | test_smoke.py |
| T8 | Student | Take test with all correct answers | 8 / 8 stored, skill verified | test_smoke.py |
| T9 | Matching | Ranking for a backend student | Backend internship ranks above design internship | test_smoke.py |
| T10 | Applications | Apply, employer shortlists, student sees status | Status "Shortlisted" visible | test_smoke.py |
| T11 | Admin | Deactivate user | User cannot log in (403) | test_smoke.py |
| T12 | Reports | CSV exports, institution report, baselines | Download works, % shown | test_smoke.py |
| T13 | Accuracy | Labelled pairs vs predictions | Accuracy ≥ 70% | evaluate_matching.py |
| T14 | Performance | 2,000 students, 307 listings, 2,000 applicants | Every page < 2 s | perf_test.py |
| T15 | Responsive | All student, employer, admin and public pages at 375 px width | No horizontal scroll, menus collapse | checked in browser, all pages pass |
| T16 | Browsers | Chrome, Edge, Firefox, mobile Chrome | Same behaviour | Chrome 155 on Windows: full flow passed (login, ranked list, apply, employer review, CSV, admin, charts). Edge, Firefox and a physical phone: to be run by the team using docs/UAT_SCRIPT.md |

Run automated tests: `python test_smoke.py`, `python evaluate_matching.py`, `python perf_test.py`.
Exit criterion: all T1–T16 pass and no critical defect is open.

## 5. User acceptance testing (WBS 8.3)

The full printable script with roles, steps, defect log and sign-off is in `docs/UAT_SCRIPT.md`; the table below is the summary mapped to the SOW acceptance criteria.

Run with at least one student, one employer and the supervisor acting as administrator, on the deployed site. Each item maps to an acceptance criterion in the SOW. Tick Pass/Fail and note defects; all critical defects must be closed before submission.

| # | Acceptance criterion | Task for the tester | Pass | Fail | Notes |
|---|---|---|---|---|---|
| U1 | Students can register and securely log in | Register a new student, log out, log in again | | | |
| U2 | Employers can register and post internships | Register an employer, post an internship | | | |
| U3 | Students can create and update their profiles | Add skills, a project, a certification; edit the GPA | | | |
| U4 | Employers can define internship requirements | Set required and preferred skills, degree, deadline | | | |
| U5 | The algorithm generates ranked recommendations | Open Internships; best fit is first and score is shown | | | |
| U6 | Dashboards work for the relevant users | Open student, employer and admin dashboards; counts match the data | | | |
| U7 | Works on desktop and mobile browsers | Repeat U1, U5 on a phone | | | |
| U8 | Passwords encrypted; data visible only to authorised users | Try opening another user's candidate page by URL (expect blocked) | | | |
| U9 | Page response about 2 s or less | Open the recommendations and candidates pages on normal Wi-Fi | | | |
| U10 | Application tracking | Apply as a student; employer shortlists; student sees the status | | | |

## 6. Progress tracking and reporting (WBS 1.5)

The project manager sends the supervisor a weekly report using this template.

| Field | Content |
|---|---|
| Week / date | |
| Planned work this week | |
| Completed (WBS IDs) | |
| In progress, % complete | |
| Next week | |
| Issues and risks (new or changed) | |
| Help needed from supervisor | |
| Schedule status | On track / At risk / Late |

Progress is measured as completed WBS work packages divided by total (8 modules, 28 sub-tasks). Review the risk table in the charter every two weeks.

## 7. Requirements traceability

| Requirement | Module | Test |
|---|---|---|
| Registration, login, role-based access | 2.0 | T1–T3, T5, T11 |
| Student profile, verification tests, performance tracking | 3.0 | T7, T8 |
| Employer listings with detailed requirements | 4.0 | T10 |
| Matching with ranked recommendations and score | 5.0 | T9, T13 |
| Application submission and tracking | 6.0 | T10 |
| Dashboards and analytics | 7.0 | T12, U6 |
| Response time under 2 s | all | T14 |
| Data security | 2.0 | T3, T4, T6 |
| Responsive UI | all | T15, T16 |
