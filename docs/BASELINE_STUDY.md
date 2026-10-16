# Baseline Study — measuring the 50% and 60% objectives

The objectives compare InternMatch with the **manual** process. Only a real trial can give the manual numbers, so run this small study (about 1 hour of work) and type the two averages into **Admin → Objective tracking → Baselines**. The system then computes the improvement from live usage data.

## Study A — time to application (objective: 50% faster)
**Question:** how long does a student take to go from "start looking" to "submitted one application" the manual way?

**Participants:** at least 5 students (more is better) who have not used InternMatch.

**Manual task (stopwatch):**
1. Give the student a profile card (degree, 5 skills, one interest) and a stack of 8–10 real internship advertisements (job sites, notice boards, printed adverts).
2. Say: "Find the internship that suits this profile and submit your application (prepare and send the application email or form)."
3. Start the timer when they begin reading; stop when they press send. Record minutes.

**With InternMatch:** the system already records this automatically (registration → first application) for every real user; no stopwatch needed. For the pilot, ask the same students to register and apply on the live site.

| Student | Manual time (min) | Notes |
|---|---|---|
| 1 | | |
| 2 | | |
| 3 | | |
| 4 | | |
| 5 | | |
| **Average** | | ← enter as *Baseline: manual time to first application* |

## Study B — employer screening time (objective: 60% faster)
**Question:** how long does it take an employer (or the team acting as one) to reach a decision on candidates from CVs?

**Participants:** at least 3 people acting as hiring managers (lecturers, senior students, or real employers).

**Manual task:**
1. Prepare 15 short CVs (printed or PDF) for one internship with clear requirements.
2. Ask the screener to read them and mark each Shortlist / Accept / Reject. Time the whole task.
3. Divide total time by 15 to get minutes per candidate, then convert the average to **hours per candidate**.

| Screener | Total time (min) | Per candidate (min) | Per candidate (hours) |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| **Average** | | | ← enter as *Baseline: manual time to screen/decide (hours)* |

**Important:** the system measures *time from application to the employer's decision*, which includes waiting time, not only reading time. For a fair comparison, in the pilot ask the employers to review the ranked list in one sitting right after the applications arrive, and note the limitation in your report.

## Reporting
- State the number of participants and the date of the study.
- Compare: improvement = (baseline − measured) / baseline × 100. The dashboard does this for you.
- Say honestly if the sample is small, or if the targets (50% and 60%) were met or missed.
- Matching accuracy (objective 1) is covered separately by `evaluate_matching.py`: replace the labels in that file with judgements from your supervisor or real employers for the final report.
