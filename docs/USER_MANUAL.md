# InternMatch User Manual

Student Skills and Internship Matching System · Version 1.0

## 1. What is InternMatch?

InternMatch is a website that matches students with internships. Students describe their education and skills and prove them with short tests. Employers post internships and the skills they need. The system gives every student–internship pair a **match score from 0% to 100%**, so students see the best internships first and employers see the best candidates first.

You need only a web browser (desktop or phone) and an internet connection. There is nothing to install.

There are three kinds of users:

| Role | What you can do |
|---|---|
| **Student** | Build a profile, take skill tests, see ranked internships, apply, track applications |
| **Employer** | Post internships, see ranked applicants, shortlist, accept or reject |
| **Administrator** | Manage users and listings, view platform reports |

## 2. Getting started

### 2.1 Create an account
1. Open the site and click **Sign up**.
2. Choose **Student** or **Employer**.
3. Enter your name, email and a password (at least 8 characters, with a letter and a number). Employers also enter the company name.
4. Click **Create account**. You are signed in and taken to your profile.

### 2.2 Log in and out
Click **Log in**, enter your email and password. After 5 wrong attempts in a row you must wait about 5 minutes. Click **Log out** (top right) when you finish, especially on a shared computer.

### 2.3 Change your password
Click your name in the top bar, enter your current password and a new one.

## 3. Student guide

### 3.1 Complete your profile (My profile)
A fuller profile gives better matches. The bar at the top shows how complete it is.
- **Education and interests:** university, degree level, major, GPA, graduation year, preferred location, interests (comma separated, e.g. *web development, data science*) and a short bio.
- **Skills:** type a skill, rate yourself 1–5, choose *Tech* or *Soft*, click **Add**. Adding the same skill again updates it.
- **Projects:** title, technologies used, and what you built.
- **Certifications:** name, issuer, year. (Certificates are not verified with the issuer.)

### 3.2 Verify skills with tests (Skill tests)
1. Open **Skill tests** and click **Start test** on a skill.
2. Answer all 8 multiple-choice questions and click **Submit answers**.
3. You see your score and the correct answers. You can retake the test; your **best** score is used.

Why take tests? A skill you only rate yourself counts for **70%** of its value in matching. A skill with a test result counts mainly by the test score, so a good result lifts your matches. Verified skills show a **verified** tag.

### 3.3 Find internships (Internships)
The list is sorted by your match score. Each card shows the score ring, your **matched skills** (green) and **missing skills** (red). Use the search box, location and minimum-match filters to narrow the list.

Score labels: **Excellent** 75%+, **Good** 55–74%, **Fair** 35–54%, **Low** below 35%.

### 3.4 Read a match
Open an internship to see the full details and a breakdown: required skills, preferred skills, education, interests, and projects and certificates. Missing skills tell you what to learn or test next.

### 3.5 Apply and track
1. On the internship page, add an optional cover note and click **Apply now**. You can apply once per internship, before its deadline.
2. Open **Applications** to follow the status: **Applied → Shortlisted → Accepted** or **Rejected**.
3. While an application is still **Applied** you can **Withdraw** it.

### 3.6 Dashboard
Shows profile completeness, open internships, your top 5 matches, applications by status and your test results.

## 4. Employer guide

### 4.1 Company profile
Open **Company** and fill in name, industry, location, website and description. Students see this on your listings.

### 4.2 Post an internship
Click **Post internship** and fill in:
- **Title** and **description**.
- **Required skills** (at least one) and **preferred skills**, comma separated. Use common names (*Python, SQL, React*).
- **Minimum degree**, **field of study**, **category**, **location**, **duration** and **deadline**.

Clear, complete requirements give accurate rankings. You can **Edit**, **Close/Reopen** or **Delete** a listing from the dashboard. Closed listings are hidden from students.

### 4.3 Review candidates
Click **Candidates** on a listing. Applicants are ranked by match score, with a green/red view of which required skills each one has. A ✓ next to a skill means it was test-verified.
- Click a name to read the full profile, cover note and score breakdown.
- Use the dropdown to set **Applied, Shortlisted, Accepted** or **Rejected**. Students see the change in their Applications page.
- Filter by status, and use **Export CSV** to download the ranked list.

You can only see students who applied to your own listings.

### 4.4 Dashboard
Open listings, total applicants, shortlisted and accepted counts, a pipeline chart and your top unreviewed candidates.

## 5. Administrator guide

- **Overview:** platform totals, applications by status, most common student skills, an **Institution report** by university (downloadable as CSV), and **Objective tracking** (time to first application, time to employer decision, placement rate). Enter the manual-process baselines from your own timed trial to see the percentage improvement.
- **Users:** search, filter by role, **Deactivate/Activate** (blocks login without deleting data) or **Delete** (permanent, removes the user's data). You cannot deactivate or delete yourself.
- **Listings:** **Remove** an inappropriate listing (hidden from students, restorable with **Restore**).

## 6. How privacy works
- Passwords are stored encrypted (hashed); nobody, including administrators, can read them.
- A student's profile is visible only to the student, the employers they applied to, and administrators.
- Matching uses only information entered inside InternMatch.

## 7. Troubleshooting

| Problem | What to do |
|---|---|
| "Invalid or missing CSRF token" | The page was open too long. Go back, reload it and try again. |
| "Too many failed attempts" | Wait about 5 minutes, then log in again. |
| I see no recommendations | Add skills to your profile; make sure at least one internship is open. |
| My score is low | Open the internship and look at **Missing**. Add skills you have, or take the test. |
| I can't apply | The listing may be closed, past its deadline, or you already applied. |
| Account deactivated | Contact the administrator. |
| Forgot password | Ask the administrator to delete and re-create the account (self-service reset is not part of this release). |

## 8. Limits of this release
Native mobile apps, in-app chat or interviews, payments, CV upload and parsing, university system integration, and certificate verification are outside the project scope. The system's role ends when the employer records a decision.
