"""Author the evaluation dataset and serialize it to dataset.json.

Every scenario and every relevance grade here is a HAND-SET human judgment
("how important is this to do today?", 0-3) — nothing is computed from the
prioritizer's rules, so the benchmark is not circular. This file is just a
convenient, auditable way to write ~40 scenarios without hand-editing JSON.

The set is deliberately balanced: some scenarios (pure deadline clusters) are
cases where naive "sort by due date" is already near-optimal, so the benchmark
does not secretly favor our ranker. Run:

    cd backend && python -m eval.build_dataset      # writes eval/dataset.json
"""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "dataset.json"


def it(source, kind, title, rel, due=None, category=None):
    d = {"source": source, "kind": kind, "title": title, "relevance": rel}
    if due is not None:
        d["due_offset_days"] = due
    if category is not None:
        d["category"] = category
    return d


# ---- common noise items (obvious human judgment: noise = grade 0) ----------
def otp():
    return it("gmail", "email", "Your one-time password (OTP)", 0, category="otp")


def promo(title="50% off online courses this week"):
    return it("gmail", "email", title, 0, category="other")


def newsletter(title="Weekly community digest"):
    return it("gmail", "email", title, 0, category="other")


def star():
    return it("github", "notification", "Someone starred your repo", 0)


def scen(sid, context, items):
    return {"id": sid, "context": context, "items": items}


SCENARIOS = [
    # ---------------- Exam contexts ----------------
    scen("exam_tomorrow_single", "One exam tomorrow; coursework dominates.", [
        it("calendar", "exam", "Operating Systems exam", 3, due=1),
        it("classroom", "deadline", "Pre-exam problem set", 3, due=1, category="academic"),
        it("calendar", "deadline", "Quiz prep checklist", 2, due=1, category="academic"),
        it("gmail", "email", "Internship application (5 days left)", 2, due=5, category="internship"),
        it("codeforces", "contest", "Codeforces Round (today)", 1, due=0),
        it("github", "pull_request", "PR: small refactor", 1),
        otp(),
    ]),
    scen("exam_in_three_days", "Exam a few days out; steady prep.", [
        it("calendar", "exam", "DBMS mid-sem exam", 3, due=3),
        it("classroom", "deadline", "Lab 3 — scheduling sim", 2, due=2, category="academic"),
        it("gmail", "email", "Assignment rubric updated", 2, due=2, category="academic"),
        it("calendar", "event", "Revision group", 1, due=1),
        it("codeforces", "contest", "Educational Codeforces Round", 1, due=1),
        newsletter(),
        otp(),
    ]),
    scen("two_exams_back_to_back", "Two exams within days; nothing else matters much.", [
        it("calendar", "exam", "OS exam", 3, due=1),
        it("calendar", "exam", "DBMS exam", 3, due=2),
        it("classroom", "deadline", "Assignment due before exam", 2, due=1, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 1, due=0),
        newsletter(),
    ]),
    scen("exam_week_internship_clash", "Exam week, but an interview lands tomorrow.", [
        it("calendar", "exam", "Compiler design exam", 3, due=2),
        it("gmail", "email", "Interview scheduled tomorrow 10am", 3, due=1, category="internship"),
        it("classroom", "deadline", "Assignment", 2, due=1, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 1, due=1),
        promo(),
        otp(),
    ]),
    scen("last_day_before_exam", "Exam tomorrow; final revision only.", [
        it("calendar", "exam", "Networks exam", 3, due=1),
        it("classroom", "deadline", "Pre-exam problem set", 3, due=1, category="academic"),
        it("calendar", "deadline", "Quiz checklist", 2, due=1, category="academic"),
        it("github", "pull_request", "PR: review requested", 1),
        it("codeforces", "contest", "Codeforces Round (today)", 1, due=0),
        otp(),
    ]),
    scen("post_exam_relief", "Exams done; back to a normal, project-y week.", [
        it("classroom", "deadline", "Pending lab report", 2, due=3, category="academic"),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 2, due=1),
        it("gmail", "email", "Internship listing — apply", 2, due=3, category="internship"),
        it("calendar", "event", "Coding club", 1, due=1),
        otp(),
    ]),

    # ---------------- Normal week ----------------
    scen("normal_light", "Regular week, light load.", [
        it("github", "pull_request", "PR: review requested", 2),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 2, due=2),
        it("classroom", "announcement", "No lecture Friday", 1),
        it("calendar", "event", "FYP sync with guide", 1, due=2),
        otp(),
    ]),
    scen("normal_moderate", "Regular week, a closing internship.", [
        it("gmail", "email", "Internship application closes tomorrow", 3, due=1, category="internship"),
        it("calendar", "deadline", "Networks assignment", 2, due=2, category="academic"),
        it("github", "pull_request", "PR: review requested", 2),
        it("codeforces", "contest", "Educational Round", 2, due=1),
        it("classroom", "announcement", "Slides uploaded", 1),
        newsletter(),
    ]),
    scen("normal_project_heavy", "Project work is the theme this week.", [
        it("github", "pull_request", "PR: review requested", 2),
        it("github", "issue", "Bug in the demo", 2),
        it("calendar", "deadline", "Assignment", 2, due=3, category="academic"),
        it("calendar", "event", "FYP sync with guide", 2, due=1),
        it("codeforces", "contest", "Codeforces Round", 1, due=3),
        otp(),
    ]),
    scen("normal_quiet_ish", "Little urgent; mostly optional things.", [
        it("calendar", "deadline", "Assignment", 1, due=4, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 1, due=4),
        it("classroom", "announcement", "Reading uploaded", 1),
        it("calendar", "event", "Club meetup", 1, due=2),
        newsletter(),
        star(),
    ]),

    # ---------------- Placement / internship ----------------
    scen("interview_tomorrow", "Placements on; interview + resume due.", [
        it("gmail", "email", "Interview scheduled tomorrow", 3, due=1, category="internship"),
        it("calendar", "deadline", "Submit updated resume to portal", 3, due=1, category="academic"),
        it("gmail", "email", "Recruiter interested — SDE intern", 2, category="internship"),
        it("github", "pull_request", "PR: docs fix", 1),
        it("codeforces", "practice", "Practice reminder", 1),
        otp(),
    ]),
    scen("online_assessment_today", "An OA closes today; do not miss it.", [
        it("gmail", "email", "Online assessment closes today", 3, due=0, category="internship"),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        it("gmail", "email", "Recruiter message", 2, category="internship"),
        it("codeforces", "contest", "Codeforces Round", 1, due=1),
        newsletter(),
        otp(),
    ]),
    scen("offer_deadline", "An offer must be accepted by tomorrow.", [
        it("gmail", "email", "Accept internship offer by tomorrow", 3, due=1, category="internship"),
        it("calendar", "deadline", "Assignment", 2, due=3, category="academic"),
        it("github", "pull_request", "PR: review requested", 2),
        it("calendar", "event", "Club event", 1, due=2),
        otp(),
    ]),
    scen("recruiter_flurry", "Several recruiter signals plus a deadline.", [
        it("gmail", "email", "Recruiter A: interested", 2, category="internship"),
        it("gmail", "email", "Recruiter B: quick call?", 2, category="internship"),
        it("gmail", "email", "Internship application deadline", 3, due=2, category="internship"),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        promo(),
        otp(),
    ]),
    scen("placement_prep", "Prepping for placements; nothing due today.", [
        it("calendar", "event", "Mock interview tomorrow", 2, due=1),
        it("calendar", "deadline", "Resume review deadline", 2, due=1, category="academic"),
        it("codeforces", "practice", "DSA practice reminder", 1),
        it("gmail", "email", "New internship listing", 2, due=4, category="internship"),
        newsletter(),
    ]),

    # ---------------- Deadline clusters (fair to due_date) ----------------
    scen("pure_deadline_cluster", "Only dated coursework; due-date order is basically right.", [
        it("calendar", "deadline", "COA assignment", 3, due=0, category="academic"),
        it("classroom", "deadline", "ER worksheet", 3, due=0, category="academic"),
        it("calendar", "deadline", "Lab report", 2, due=1, category="academic"),
        it("classroom", "deadline", "Essay draft", 2, due=2, category="academic"),
        it("calendar", "deadline", "Reading response", 1, due=3, category="academic"),
    ]),
    scen("assignment_pileup", "Five assignments, all dated; a fair test for due-date sorting.", [
        it("classroom", "deadline", "Assignment A", 3, due=0, category="academic"),
        it("classroom", "deadline", "Assignment B", 3, due=1, category="academic"),
        it("calendar", "deadline", "Assignment C", 2, due=1, category="academic"),
        it("calendar", "deadline", "Assignment D", 2, due=2, category="academic"),
        it("classroom", "deadline", "Assignment E", 1, due=3, category="academic"),
    ]),
    scen("cluster_with_one_noise", "Dated work plus a single noise email.", [
        it("calendar", "deadline", "Assignment due today", 3, due=0, category="academic"),
        it("classroom", "deadline", "Lab due today", 3, due=0, category="academic"),
        it("calendar", "deadline", "Report due tomorrow", 2, due=1, category="academic"),
        otp(),
    ]),
    scen("deadline_vs_event_trap", "A club event today should NOT beat an exam in 4 days.", [
        it("calendar", "deadline", "Assignment due today", 3, due=0, category="academic"),
        it("calendar", "exam", "Exam", 3, due=4),
        it("calendar", "deadline", "Report", 2, due=2, category="academic"),
        it("calendar", "event", "Club event today", 1, due=0),
    ]),

    # ---------------- Hackathon / project ----------------
    scen("hackathon_weekend", "Mid-hackathon; submission and demo work first.", [
        it("calendar", "deadline", "Hackathon submission", 3, due=1),
        it("github", "pull_request", "PR: review for demo", 2),
        it("github", "issue", "Bug blocking the demo", 2),
        it("gmail", "email", "Teammate: push the API?", 1, category="other"),
        it("codeforces", "contest", "Codeforces Round", 1, due=1),
        otp(),
    ]),
    scen("hackathon_final_hours", "Final hours; ship it.", [
        it("calendar", "deadline", "Hackathon submission today", 3, due=0),
        it("github", "issue", "Demo-blocking bug", 3),
        it("github", "pull_request", "PR: review requested", 2),
        it("gmail", "email", "Sponsor logistics", 1, category="other"),
        otp(),
    ]),
    scen("fyp_report_due", "Final-year-project report is due.", [
        it("calendar", "deadline", "FYP report submission", 3, due=1, category="academic"),
        it("gmail", "email", "Guide feedback on draft", 2, category="academic"),
        it("github", "pull_request", "PR: code cleanup", 1),
        it("calendar", "event", "Plagiarism check slot", 1, due=1),
        it("codeforces", "contest", "Codeforces Round", 1, due=2),
        otp(),
    ]),

    # ---------------- Contest weekends ----------------
    scen("contest_saturday_normal", "Weekend, no exams; contests genuinely matter.", [
        it("codeforces", "contest", "Codeforces Round (today)", 2, due=0),
        it("codeforces", "contest", "AtCoder-style round tomorrow", 2, due=1),
        it("codeforces", "practice", "Upsolve reminder", 1),
        it("github", "pull_request", "PR: review requested", 1),
        newsletter(),
    ]),
    scen("rated_round_prep", "A rated round tomorrow amid light coursework.", [
        it("codeforces", "contest", "Codeforces Round", 2, due=1),
        it("codeforces", "practice", "Upsolve last round", 1),
        it("calendar", "deadline", "Assignment", 2, due=3, category="academic"),
        it("classroom", "announcement", "Notes uploaded", 1),
        otp(),
    ]),

    # ---------------- Semester start / low urgency ----------------
    scen("semester_start", "First days of term; set-up tasks.", [
        it("calendar", "deadline", "Add/drop closes", 2, due=4, category="academic"),
        it("calendar", "event", "Orientation", 1, due=1),
        it("classroom", "announcement", "Syllabus posted", 1),
        it("calendar", "event", "Club recruitment", 1, due=2),
        newsletter(),
        otp(),
    ]),
    scen("first_week_quiet", "Quiet first week; mostly optional.", [
        it("classroom", "deadline", "Intro reading", 1, due=5, category="academic"),
        it("calendar", "event", "Club event", 1, due=2),
        it("classroom", "announcement", "Welcome note", 1),
        newsletter(),
        star(),
    ]),

    # ---------------- Registration / results ----------------
    scen("course_registration_day", "Registration closes today.", [
        it("calendar", "deadline", "Course registration closes", 3, due=0, category="academic"),
        it("calendar", "event", "Advisor meeting", 2, due=1),
        it("gmail", "email", "Fee payment reminder", 2, due=2, category="academic"),
        newsletter(),
        otp(),
    ]),
    scen("results_day", "Results are out; a revaluation window opens.", [
        it("gmail", "email", "Semester results announced", 1, category="academic"),
        it("calendar", "deadline", "Revaluation request deadline", 2, due=3, category="academic"),
        it("calendar", "deadline", "Assignment", 2, due=1, category="academic"),
        it("codeforces", "contest", "Codeforces Round", 1, due=1),
        otp(),
    ]),

    # ---------------- Internship buried in noise ----------------
    scen("buried_internship", "A closing internship hidden among noise.", [
        it("gmail", "email", "Internship application deadline tomorrow", 3, due=1, category="internship"),
        it("gmail", "email", "Recruiter wants to connect", 2, category="internship"),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        promo(),
        promo("Flash sale: gadgets"),
        newsletter(),
        otp(),
        star(),
    ]),
    scen("noisy_inbox", "Mostly promos; two real things.", [
        it("gmail", "email", "Internship interview invite", 3, due=2, category="internship"),
        it("gmail", "email", "College notice: form submission", 2, due=2, category="academic"),
        promo(),
        promo("Webinar you might like"),
        promo("Upgrade your plan"),
        otp(),
    ]),
    scen("opportunity_hidden", "A scholarship and a hackathon invite among noise.", [
        it("gmail", "email", "Scholarship application deadline", 3, due=1, category="academic"),
        it("gmail", "email", "Hackathon invite — register", 2, due=4, category="internship"),
        it("calendar", "deadline", "Assignment", 2, due=2, category="academic"),
        newsletter(),
        otp(),
    ]),

    # ---------------- Edge cases ----------------
    scen("nothing_urgent", "A genuinely calm day.", [
        it("calendar", "event", "Club event", 1, due=3),
        it("classroom", "announcement", "FYI notice", 1),
        newsletter(),
        promo(),
        star(),
    ]),
    scen("everything_urgent_today", "Everything lands today at once.", [
        it("calendar", "exam", "Exam today", 3, due=0),
        it("classroom", "deadline", "Assignment due today", 3, due=0, category="academic"),
        it("gmail", "email", "OA closes today", 3, due=0, category="internship"),
        it("github", "pull_request", "PR: review requested", 2),
        it("codeforces", "contest", "Codeforces Round today", 1, due=0),
    ]),
    scen("only_noise", "A spam-only morning (nothing worth doing).", [
        otp(),
        promo(),
        newsletter(),
        promo("Limited-time offer"),
        star(),
    ]),
    scen("single_urgent_among_noise", "One critical item drowning in noise.", [
        it("gmail", "email", "Internship deadline today", 3, due=0, category="internship"),
        promo(),
        newsletter(),
        promo("Deals inside"),
        otp(),
        star(),
    ]),
    scen("two_equal_top", "Two equally critical items tomorrow.", [
        it("calendar", "exam", "Exam", 3, due=1),
        it("classroom", "deadline", "Assignment due", 3, due=1, category="academic"),
        it("codeforces", "contest", "Codeforces Round today", 1, due=0),
        otp(),
    ]),

    # ---------------- More realistic mornings ----------------
    scen("monday_morning_mix", "Typical Monday spread.", [
        it("calendar", "deadline", "Assignment due", 3, due=1, category="academic"),
        it("github", "pull_request", "PR: review requested", 2),
        it("gmail", "email", "Internship listing — apply", 2, due=3, category="internship"),
        it("codeforces", "contest", "Codeforces Round", 1, due=2),
        it("calendar", "event", "Guide meeting", 1, due=2),
        otp(),
    ]),
    scen("midweek_crunch", "Two assignments and an exam approaching.", [
        it("calendar", "deadline", "Assignment 1 due tomorrow", 3, due=1, category="academic"),
        it("calendar", "deadline", "Assignment 2", 2, due=2, category="academic"),
        it("calendar", "exam", "Exam in 4 days", 3, due=4),
        it("github", "pull_request", "PR: minor", 1),
        it("codeforces", "contest", "Codeforces Round", 1, due=1),
        newsletter(),
    ]),
    scen("friday_winddown", "Weekend ahead; plan Monday's work.", [
        it("calendar", "deadline", "Assignment due Monday", 2, due=3, category="academic"),
        it("calendar", "event", "Club event today", 1, due=0),
        it("codeforces", "contest", "Weekend round", 2, due=1),
        it("github", "pull_request", "PR: review requested", 1),
        otp(),
    ]),
    scen("pre_holiday", "Break starting; one deadline survives it.", [
        it("gmail", "email", "Internship application deadline", 3, due=2, category="internship"),
        it("calendar", "deadline", "Assignment due after break", 1, due=6, category="academic"),
        it("calendar", "event", "Travel home", 1, due=1),
        promo(),
        otp(),
    ]),
]


def build() -> dict:
    return {
        "_about": (
            "Labeled scenarios for evaluating the prioritizer. relevance is a "
            "hand-set human 'do-this-today' grade: 3=must do today, 2=important "
            "soon, 1=optional, 0=noise. due_offset_days is relative to the run "
            "date so the set never goes stale. Generated by build_dataset.py; "
            "see docs/EVALUATION.md."
        ),
        "relevance_scale": {"3": "must do today", "2": "important soon", "1": "optional", "0": "noise"},
        "scenarios": SCENARIOS,
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=2))
    n = len(data["scenarios"])
    ids = [s["id"] for s in data["scenarios"]]
    assert len(ids) == len(set(ids)), "duplicate scenario ids!"
    print(f"Wrote {n} scenarios to {OUT}")
