# User Acceptance Test Script (WBS 8.3)

Site URL: ______________________  Date: ____________  Build/version: ____________

## Testers (at least one per role)
| Role | Name | Device / browser |
|---|---|---|
| Student | | |
| Employer | | |
| Administrator (supervisor or PM) | | |

Each tester creates their **own new account**; no one should use the demo accounts. Follow the steps in order. Mark Pass or Fail and describe anything unexpected.

## Scenario 1 — Student (about 15 min)
| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| S1 | Open the site, click Sign up, create a student account | Taken to profile page | | |
| S2 | Try a weak password (`abc`) first | Rejected with a clear message | | |
| S3 | Fill education and interests; add 4+ skills, 1 project, 1 certification | Saved; completeness bar rises | | |
| S4 | Take the Python (or another) skill test | Score and correct answers shown; skill tagged "verified" | | |
| S5 | Open Internships | List ranked best-first, each with a score, matched and missing skills | | |
| S6 | Open the top internship, then apply with a cover note | Confirmation; appears in Applications as "Applied" | | |
| S7 | Log out and log in again | Works; profile data still there | | |
| S8 | Repeat S1, S5 on a phone | Readable, no sideways scrolling | | |

## Scenario 2 — Employer (about 15 min)
| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| E1 | Sign up as an employer with a company name | Taken to company profile | | |
| E2 | Complete the company profile | Saved | | |
| E3 | Post an internship with required and preferred skills, degree, deadline | Appears in dashboard as open | | |
| E4 | After a student has applied, open Candidates | Applicants ranked by match score with skills shown | | |
| E5 | Open a candidate; set status to Shortlisted | Status saved; student sees it | | |
| E6 | Export the candidate list to CSV | File downloads and opens | | |
| E7 | Close the listing | Hidden from students | | |
| E8 | Change the URL to another employer's candidate page | Blocked ("not found") | | |

## Scenario 3 — Administrator (about 10 min)
| # | Step | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| A1 | Log in as admin | Overview with totals and charts | | |
| A2 | Open Users, search for the test student, deactivate them | They can no longer log in; Activate restores them | | |
| A3 | Open Listings and Remove the test listing | Hidden from students; Restore works | | |
| A4 | Download the institution report CSV | File downloads | | |
| A5 | Enter baselines in Objective tracking | Percentages appear | | |

## Non-functional checks
| # | Check | Expected | Pass/Fail | Notes |
|---|---|---|---|---|
| N1 | Pages load quickly on normal Wi-Fi (Internships, Candidates) | About 2 s or less | | |
| N2 | Works in Chrome, Edge, Firefox, and a phone browser | Same behaviour | | |
| N3 | Student cannot open `/employer` or `/admin` | "No access" page | | |
| N4 | Page is usable with keyboard only (Tab, Enter) | All controls reachable | | |

## Defect log
| ID | Where | What happened | Severity (Critical / Major / Minor) | Status |
|---|---|---|---|---|
| | | | | |

**Exit rule:** every Critical defect is fixed and re-tested before final submission.

## Sign-off
| Name | Role | Result (Accepted / Accepted with changes / Rejected) | Signature | Date |
|---|---|---|---|---|
| | Supervisor | | | |
| | Project manager | | | |
