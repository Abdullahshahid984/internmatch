# Project Charter — Student Skills and Internship Matching System

| | |
|---|---|
| **Project title** | Student Skills and Internship Matching System (InternMatch) |
| **Supervisor** | Prof. Amna Shoukat |
| **Project manager** | Aleena Shahid |
| **Team member** | Tehzeeb Moazzam |
| **Duration** | 16-week semester, Agile (iterative sprints) |

## 1. Purpose and justification
Students apply for internships without knowing whether they fit and spend long hours reading advertisements. Employers face the reverse problem of screening large numbers of resumes. A single platform that compares student profiles with internship requirements and returns ranked, scored matches saves time on both sides and improves placement quality.

## 2. Goal
Build a web-based platform that gives each student a ranked list of suitable internships based on their skills, education and interests, delivered with an Agile approach within the semester timeline.

## 3. Measurable objectives
| # | Objective | How it is measured in the system |
|---|---|---|
| O1 | Matching algorithm ranks candidates by required and preferred skills with **at least 70% accuracy** | `evaluate_matching.py` compares predictions with labelled fits (accuracy/precision/recall) |
| O2 | Reduce student **time-to-application by 50%** vs manual searching | Admin → Objective tracking: registration → first application time vs a manual baseline |
| O3 | Employers review qualified candidates **60% faster** than resume screening | Admin → Objective tracking: application → decision time vs a manual baseline |
| O4 | Improve placement success through quality matches | Admin → Objective tracking: placement rate (students with an accepted application) |

Baselines for O2 and O3 come from a timed manual trial or survey run by the team before the pilot.

## 4. High-level scope
**In scope:** registration/login with student, employer and admin roles; student profiles; skill tests and performance tracking; employer profiles and internship listings; matching algorithm with ranked recommendations and scores; application submission and tracking; student and employer dashboards; admin panel; responsive web interface.
**Out of scope:** native apps, payments or stipends, university SIS/LMS or LinkedIn integration, CV parsing, certificate verification, chat/video/interview scheduling, offer letters and onboarding, long-term maintenance.

## 5. Deliverables and milestones
| Deliverable | Week |
|---|---|
| Requirements document, project charter | 2 |
| Scope, SOW and WBS | 3 |
| UI/UX design, database design | 5 |
| Student and employer modules | 9 |
| Matching algorithm | 11 |
| Admin dashboard | 12 |
| Integration and system testing | 14 |
| Final deployment, handover, user manual | 16 |

## 6. Stakeholders
| Stakeholder | Interest |
|---|---|
| Project supervisor (Prof. Amna Shoukat) | Approves deliverables, receives progress reports |
| Students | Find suitable internships faster |
| Employers | Find qualified interns with less screening |
| Educational institutions | Monitor internship participation through admin reports |
| System administrator | Keeps users, listings and the platform healthy |

## 7. Roles and authority
**Project manager (Aleena Shahid)** plans tasks and deadlines, assigns work by skill set, manages risks, resolves project and team problems, and reports progress to the supervisor. **Team member (Tehzeeb Moazzam)** delivers assigned work packages. Both share development, design and testing duties because the team has two members.

## 8. Assumptions
Students give correct skill information; employers post complete requirements; users have internet access and basic computer skills; both team members are available all semester; free hosting and tools stay available.

## 9. Constraints
16-week deadline; free or low-cost tools only; two-person team; student data must stay private and protected; matching accuracy depends on test quality and data quality.

## 10. Key risks
| Risk | Likelihood | Impact | Response |
|---|---|---|---|
| Incomplete or inaccurate profile/listing data lowers match quality | High | High | Profile completeness bar, required-skill field mandatory, skill tests weight verified skills higher |
| Two-person team: illness or overload delays work | Medium | High | Weekly sprint plan, buffer in weeks 14–16, cut non-critical features first |
| Free hosting limits (sleep, no persistent disk) | Medium | Medium | Document hosting steps early, keep SQLite file backed up, PostgreSQL migration path |
| Security flaw exposes personal data | Low | High | Hashed passwords, CSRF protection, parameterised SQL, role checks, tests for access control |
| Scope creep (chat, payments) | Medium | Medium | Out-of-scope list is frozen; changes need supervisor approval |
| Too few test questions or real users to validate accuracy | Medium | Medium | Seed bank of 56 questions, labelled evaluation set, expand with real feedback |

## 11. Acceptance criteria
Students register and log in securely; employers register and post internships and define requirements; students create and update profiles; the algorithm generates ranked recommendations; dashboards work for each role; the site works on desktop and mobile browsers; passwords are stored encrypted and personal data is visible only to authorised users; pages respond in about two seconds or less under normal conditions; all critical defects are fixed before submission.

## 12. Approval
| Name | Role | Signature | Date |
|---|---|---|---|
| Prof. Amna Shoukat | Supervisor | | |
| Aleena Shahid | Project manager | | |
| Tehzeeb Moazzam | Team member | | |
