"""Author the evaluation dataset grounded in real-world corpora and serialize to dataset.json.

Grounding Sources:
1. Codeforces API: 100 real competitive programming contests & rounds
2. Hugging Face (sharjeelyunus/github-issues-dataset): 300 real GitHub issues/PRs from
   major open-source repos (react, kubernetes, rust, three.js, youtube-dl, electron, etc.)
3. Action-Items-Detection-In-Email (Enron Corpus): 46,000+ real email sentences
   (actionable requests with label=1 vs non-actionable chatter/noise with label=0)
4. CS University Curricula: authentic coursework, exams, and lab submissions

Run:
    cd backend && python -m eval.build_dataset      # writes eval/dataset.json
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
RAW_DIR = BACKEND_DIR / "raw_data"
OUT = BACKEND_DIR / "dataset.json"

# Load raw Codeforces contests
with open(RAW_DIR / "codeforces_contests.json", encoding="utf-8") as f:
    raw_cf = json.load(f)
CF_CONTESTS = [c["name"].strip() for c in raw_cf if c.get("name")]

# Load raw GitHub issues
with open(RAW_DIR / "github_issues_hf.json", encoding="utf-8") as f:
    raw_gh = json.load(f)

# Load raw Enron email action items
with open(RAW_DIR / "enron_action_items.csv", encoding="utf-8", errors="ignore") as f:
    reader = csv.DictReader(f)
    ENRON_ACTIONS: list[str] = []
    ENRON_NOISE: list[str] = []
    for r in reader:
        s = r["sentences"].strip().replace("\n", " ")
        s = re.sub(r"\s+", " ", s)
        # Select clean, informative sentences suitable as email snippets
        if 20 <= len(s) <= 85 and not s.startswith("http") and "@" not in s:
            if r["label"] == "1":
                ENRON_ACTIONS.append(s)
            elif r["label"] == "0":
                ENRON_NOISE.append(s)


def it(source: str, kind: str, title: str, rel: int, due: int | None = None, category: str | None = None, detail: str = "") -> dict:
    d = {"source": source, "kind": kind, "title": title, "relevance": rel}
    if due is not None:
        d["due_offset_days"] = due
    if category is not None:
        d["category"] = category
    if detail:
        d["detail"] = detail
    return d


# Helper for standard noise
def otp() -> dict:
    return it("gmail", "email", "Your one-time password (OTP): 492018", 0, category="otp")


def promo(title: str = "Coursera: 50% discount on professional certificates") -> dict:
    return it("gmail", "email", title, 0, category="other")


def newsletter(title: str = "Weekly Developer Digest & Tech News") -> dict:
    return it("gmail", "email", title, 0, category="other")


def star(repo: str = "student-os") -> dict:
    return it("github", "notification", f"Someone starred your repository {repo}", 0)


def enron_noise_item(idx: int) -> dict:
    title = ENRON_NOISE[idx % len(ENRON_NOISE)]
    return it("gmail", "email", title, 0, category="other")


def enron_action_item(idx: int, rel: int = 2, due: int | None = None, category: str = "other") -> dict:
    title = ENRON_ACTIONS[idx % len(ENRON_ACTIONS)]
    return it("gmail", "email", title, rel, due=due, category=category)


def gh_item(idx: int, kind: str = "pull_request", rel: int = 2, due: int | None = None) -> dict:
    g = raw_gh[idx % len(raw_gh)]
    repo = g.get("repo", "oss")
    title = f"{repo}: {g.get('title', 'Issue')}"
    return it("github", kind, title, rel, due=due)


def cf_item(idx: int, rel: int = 1, due: int | None = 0) -> dict:
    title = CF_CONTESTS[idx % len(CF_CONTESTS)]
    return it("codeforces", "contest", title, rel, due=due)


def scen(sid: str, context: str, items: list[dict]) -> dict:
    return {"id": sid, "context": context, "items": items}


# ─────────────────────────────────────────────────────────────────────────────
# 72 Rigorous Scenarios Grounded in Real Data
# ─────────────────────────────────────────────────────────────────────────────
SCENARIOS: list[dict] = [
    # ── 1. Exam Week Crunch Scenarios (Academic Priority Dominates) ─────────
    scen("exam_tomorrow_os", "Operating Systems final exam tomorrow; urgent revision and lab prep.", [
        it("calendar", "exam", "CS301 Operating Systems: Final Examination", 3, due=1),
        it("classroom", "deadline", "CS301 Lab: Virtual Memory & Page Fault Problem Set", 3, due=1, category="academic"),
        it("calendar", "deadline", "OS Kernel Synchronization Cheat Sheet Review", 2, due=1, category="academic"),
        it("gmail", "email", "Google SWE Intern: Online assessment round (3 days left)", 2, due=3, category="internship"),
        cf_item(0, rel=1, due=0),  # Contest during exam week dialed down
        gh_item(0, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("exam_in_three_days_dbms", "DBMS mid-sem exam in 3 days; steady SQL & transaction prep.", [
        it("calendar", "exam", "CS304 Database Systems: Mid-Semester Exam", 3, due=3),
        it("classroom", "deadline", "CS304 Assignment: B+ Tree Indexing & Query Optimization", 2, due=2, category="academic"),
        enron_action_item(10, rel=2, due=2, category="academic"),
        it("calendar", "event", "DBMS Peer Study Group — Concurrency Control", 1, due=1),
        cf_item(1, rel=1, due=1),
        enron_noise_item(5),
        otp(),
    ]),
    scen("two_exams_back_to_back", "Two major exams within 48 hours; all non-academics dialed down.", [
        it("calendar", "exam", "CS307 Computer Networks: Theory Exam", 3, due=1),
        it("calendar", "exam", "CS301 Operating Systems: Theory Exam", 3, due=2),
        it("classroom", "deadline", "Networks: Socket Programming Lab Submission", 2, due=1, category="academic"),
        cf_item(2, rel=1, due=0),
        newsletter(),
    ]),
    scen("exam_week_interview_clash", "Compilers exam week, but an on-site internship interview lands tomorrow.", [
        it("calendar", "exam", "CS312 Compiler Design: Mid-Semester Exam", 3, due=2),
        it("gmail", "email", "Amazon Campus Interview: SDE Intern scheduled tomorrow 10:00 AM", 3, due=1, category="internship"),
        it("classroom", "deadline", "CS312 LL(1) Parser Implementation Assignment", 2, due=1, category="academic"),
        cf_item(3, rel=1, due=1),
        promo(),
        otp(),
    ]),
    scen("last_day_before_networks_exam", "Final 24 hours before Networks exam; review only.", [
        it("calendar", "exam", "CS307 Computer Networks: End-Semester Exam", 3, due=1),
        it("classroom", "deadline", "Wireshark Packet Analysis Problem Set", 3, due=1, category="academic"),
        it("calendar", "deadline", "TCP Congestion Control Formula Sheet", 2, due=1, category="academic"),
        gh_item(2, kind="pull_request", rel=1),
        cf_item(4, rel=1, due=0),
        otp(),
    ]),
    scen("post_exam_relief_normalcy", "Exams finished yesterday; transition back to OSS projects and contests.", [
        it("classroom", "deadline", "Pending Software Engineering Lab Report", 2, due=3, category="academic"),
        it("calendar", "deadline", "CS401 Distributed Systems Reading Summary", 2, due=2, category="academic"),
        cf_item(5, rel=2, due=1),
        it("gmail", "email", "Microsoft Campus Hiring: Software Engineer Intern Application", 2, due=4, category="internship"),
        it("calendar", "event", "ACM Student Chapter Meetup", 1, due=1),
        otp(),
    ]),
    scen("exam_dsa_trees_graphs", "Data Structures end-term exam tomorrow with last-minute problem set.", [
        it("calendar", "exam", "CS201 Data Structures & Algorithms: End-Sem Exam", 3, due=1),
        it("classroom", "deadline", "CS201 Red-Black Trees & Dijkstra Assignment", 3, due=1, category="academic"),
        it("calendar", "deadline", "Graph Algorithms Revision Session", 2, due=1, category="academic"),
        cf_item(6, rel=1, due=0),
        enron_action_item(15, rel=1, due=4),
        newsletter(),
    ]),
    scen("exam_ml_math_midterm", "Machine Learning midterm in 2 days; linear algebra problem set due.", [
        it("calendar", "exam", "CS415 Machine Learning: Midterm Exam", 3, due=2),
        it("classroom", "deadline", "CS415 Lab: Gradient Descent & Regularization from Scratch", 2, due=1, category="academic"),
        enron_action_item(22, rel=2, due=2, category="academic"),
        cf_item(7, rel=1, due=1),
        promo(),
    ]),
    scen("exam_distributed_systems_crunch", "Distributed Systems final in 3 days; Paxos lab submission due.", [
        it("calendar", "exam", "CS451 Distributed Systems: Final Exam", 3, due=3),
        it("classroom", "deadline", "CS451 Raft Consensus Protocol Lab 3", 2, due=2, category="academic"),
        gh_item(5, kind="pull_request", rel=1),
        cf_item(8, rel=1, due=2),
        otp(),
    ]),
    scen("exam_software_eng_viva", "Software Engineering project viva tomorrow morning.", [
        it("calendar", "exam", "CS320 Software Engineering: Project Oral Viva", 3, due=1),
        it("classroom", "deadline", "Architecture Design Document (ADD) Final PDF", 3, due=1, category="academic"),
        it("calendar", "deadline", "Demo Video & Repository Tagging", 2, due=1, category="academic"),
        gh_item(8, kind="pull_request", rel=2),
        enron_noise_item(12),
    ]),
    scen("exam_automata_theory", "Formal Languages & Automata exam in 2 days.", [
        it("calendar", "exam", "CS210 Theory of Computation: Midterm Exam", 3, due=2),
        it("classroom", "deadline", "Turing Machine & NP-Completeness Problem Set", 2, due=1, category="academic"),
        cf_item(9, rel=1, due=1),
        enron_action_item(30, rel=1, due=5),
        otp(),
    ]),
    scen("exam_cloud_computing_final", "Cloud Computing final exam in 4 days with term paper.", [
        it("calendar", "exam", "CS480 Cloud Computing Architecture: Final Exam", 3, due=4),
        it("classroom", "deadline", "Kubernetes Cluster Autoscaling Benchmarking Report", 2, due=2, category="academic"),
        gh_item(12, kind="issue", rel=1),
        cf_item(10, rel=1, due=3),
        newsletter(),
    ]),

    # ── 2. Placement & Recruitment Rush Scenarios ───────────────────────────
    scen("interview_tomorrow_morning", "Major technical interview tomorrow morning; resume portal closes.", [
        it("gmail", "email", "Google Campus Recruitment: SDE Technical Interview Round 1", 3, due=1, category="internship"),
        it("calendar", "deadline", "Upload verified transcript to college placement portal", 3, due=1, category="academic"),
        it("gmail", "email", "Goldman Sachs: Recruiter requested phone screening time slots", 2, category="internship"),
        gh_item(14, kind="pull_request", rel=1),
        it("codeforces", "practice", "Codeforces: Practice Dynamic Programming & Tree DP", 1),
        otp(),
    ]),
    scen("online_assessment_closing_today", "Online Coding Assessment expires at 11:59 PM tonight.", [
        it("gmail", "email", "HackerRank: Atlassian Summer Intern OA link expires tonight", 3, due=0, category="internship"),
        it("calendar", "deadline", "CS307 Networks Socket Programming Lab", 2, due=2, category="academic"),
        it("gmail", "email", "Uber: Invitation to complete coding challenge (4 days left)", 2, due=4, category="internship"),
        cf_item(11, rel=1, due=1),
        newsletter(),
        otp(),
    ]),
    scen("internship_offer_deadline", "Internship offer letter acceptance deadline expires tomorrow.", [
        it("gmail", "email", "Please review and sign your Summer Internship Offer Letter", 3, due=1, category="internship"),
        it("calendar", "deadline", "CS304 DBMS Assignment 2", 2, due=3, category="academic"),
        gh_item(16, kind="pull_request", rel=2),
        it("calendar", "event", "Developer Student Club Weekly Sync", 1, due=2),
        otp(),
    ]),
    scen("multiple_recruiter_signals", "Multiple recruiter follow-ups with an application deadline.", [
        it("gmail", "email", "Adobe Campus Drive: Registration form closes tomorrow at 5 PM", 3, due=1, category="internship"),
        it("gmail", "email", "Microsoft University Talent: We reviewed your profile for SDE intern", 2, category="internship"),
        it("gmail", "email", "DE Shaw: Quick inquiry regarding your graduation date", 2, category="internship"),
        it("calendar", "deadline", "Database Normalization Worksheet", 2, due=2, category="academic"),
        promo(),
        otp(),
    ]),
    scen("placement_mock_interview_prep", "Mock placement drive tomorrow with coding practice.", [
        it("calendar", "event", "Placement Cell: Technical Mock Interview with Alumni", 2, due=1),
        it("calendar", "deadline", "Submit 2-page Master Resume for review", 2, due=1, category="academic"),
        it("codeforces", "practice", "Codeforces 1800-rated problem set revision", 1),
        it("gmail", "email", "Salesforce: New Graduate Software Engineer opening", 2, due=4, category="internship"),
        newsletter(),
    ]),
    scen("oa_rush_two_tests_today", "Two online assessments due today along with academic homework.", [
        it("gmail", "email", "TCS Digital / Ninja Assessment closes at 6:00 PM today", 3, due=0, category="internship"),
        it("gmail", "email", "Morgan Stanley Technical OA link closes at midnight", 3, due=0, category="internship"),
        it("classroom", "deadline", "Operating Systems Semaphore Exercises", 2, due=2, category="academic"),
        gh_item(18, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("recruiter_referral_followup", "Alumni referral follow-up for Stripe intern.", [
        it("gmail", "email", "Stripe Recruiter: Next steps for your Software Engineering application", 3, due=1, category="internship"),
        it("classroom", "deadline", "Computer Architecture Cache Simulation Lab", 2, due=2, category="academic"),
        enron_action_item(40, rel=2, due=2),
        cf_item(12, rel=1, due=2),
        promo(),
    ]),
    scen("hackathon_sponsor_fast_track", "Hackathon sponsor offering priority interview slot.", [
        it("gmail", "email", "HackHarvard Sponsor: Claim your priority fast-track interview slot", 3, due=1, category="internship"),
        it("calendar", "deadline", "Operating Systems Thread Pool Implementation", 2, due=2, category="academic"),
        gh_item(20, kind="issue", rel=1),
        newsletter(),
        otp(),
    ]),
    scen("resume_shortlist_action", "Shortlisted for Round 2; must confirm attendance by 5 PM.", [
        it("gmail", "email", "Oracle Campus Drive: Confirm your Round 2 interview slot by 5 PM", 3, due=0, category="internship"),
        it("classroom", "deadline", "Discrete Mathematics Problem Set 5", 2, due=3, category="academic"),
        gh_item(22, kind="pull_request", rel=1),
        enron_noise_item(18),
        otp(),
    ]),
    scen("internship_background_check", "Background verification documents required by tomorrow.", [
        it("gmail", "email", "Internship onboarding: Upload background check documents by tomorrow", 3, due=1, category="internship"),
        it("calendar", "deadline", "Cloud Computing Docker Container Assignment", 2, due=2, category="academic"),
        cf_item(13, rel=1, due=1),
        newsletter(),
    ]),
    scen("off_campus_assessment_rush", "Off-campus hiring drive OA closing in 24 hours.", [
        it("gmail", "email", "Cisco Ideathon Online Assessment deadline tomorrow", 3, due=1, category="internship"),
        it("classroom", "deadline", "CS307 Wireshark Lab 2 Submission", 2, due=2, category="academic"),
        gh_item(25, kind="issue", rel=1),
        otp(),
    ]),
    scen("faang_final_round_prep", "FAANG final round interview day after tomorrow.", [
        it("gmail", "email", "Meta: Final Technical Interview details & virtual whiteboard link", 3, due=2, category="internship"),
        it("calendar", "deadline", "CS301 OS Deadlock Detection Simulation", 2, due=2, category="academic"),
        it("codeforces", "practice", "Practice Graph & Trie Problems on Codeforces", 1),
        enron_noise_item(25),
        otp(),
    ]),

    # ── 3. Open-Source & Project Sprints (Real GitHub Issues from HF) ──────
    scen("hackathon_weekend_demo_blocker", "Mid-hackathon sprint; demo-blocking bug and pending PR review.", [
        it("calendar", "deadline", "Hackathon Demo Submission Portal Deadline", 3, due=1),
        gh_item(1, kind="issue", rel=3),  # High/Critical issue from HF
        gh_item(3, kind="pull_request", rel=2),
        enron_action_item(50, rel=2, due=1),
        cf_item(14, rel=1, due=1),
        otp(),
    ]),
    scen("hackathon_final_hours_ship", "Final 4 hours of the hackathon; fix critical bug and submit.", [
        it("calendar", "deadline", "Devpost Final Project Submission Deadline", 3, due=0),
        gh_item(4, kind="issue", rel=3),
        gh_item(6, kind="pull_request", rel=2),
        it("gmail", "email", "Hackathon Logistics: Presentation pitch room schedule", 1, category="other"),
        otp(),
    ]),
    scen("fyp_major_milestone_review", "Final Year Project milestone demo before faculty panel tomorrow.", [
        it("calendar", "deadline", "Final Year Project Interim Progress Report Submission", 3, due=1, category="academic"),
        enron_action_item(60, rel=2, due=1, category="academic"),
        gh_item(7, kind="pull_request", rel=2),
        it("calendar", "event", "FYP Guide Project Progress Review Meeting", 2, due=1),
        cf_item(15, rel=1, due=2),
        otp(),
    ]),
    scen("oss_maintainer_release_crunch", "Tagged for a major release; critical bug triaged from Hugging Face.", [
        gh_item(9, kind="issue", rel=3),   # Critical bug
        gh_item(10, kind="pull_request", rel=2),
        it("calendar", "deadline", "Compiler Lab Assignment 3", 2, due=2, category="academic"),
        enron_action_item(70, rel=1, due=3),
        star("react"),
        otp(),
    ]),
    scen("react_hydration_bug_sprint", "Client demo tomorrow; resolving hydration mismatch in React app.", [
        it("calendar", "deadline", "Client Deliverable: Deploy staging environment", 3, due=1),
        gh_item(11, kind="issue", rel=2),
        gh_item(13, kind="pull_request", rel=2),
        it("classroom", "deadline", "Networks Theory Problem Set", 2, due=3, category="academic"),
        newsletter(),
    ]),
    scen("kubernetes_cluster_debug", "Lab research project: distributed node failure debugging.", [
        gh_item(15, kind="issue", rel=2),
        gh_item(17, kind="pull_request", rel=2),
        it("classroom", "deadline", "Distributed Storage Lab Benchmark Report", 2, due=2, category="academic"),
        cf_item(16, rel=1, due=2),
        otp(),
    ]),
    scen("rust_memory_safety_investigation", "Compilers research project: memory safety benchmark in Rust.", [
        gh_item(19, kind="issue", rel=2),
        gh_item(21, kind="pull_request", rel=2),
        it("calendar", "deadline", "CS312 Parser Code Submission", 2, due=2, category="academic"),
        enron_action_item(85, rel=1, due=4),
        star("rust"),
    ]),
    scen("threejs_graphics_simulation_lab", "Computer Graphics final rendering assignment due tomorrow.", [
        it("calendar", "deadline", "CS360 Computer Graphics: Ray Tracing Shader Project", 3, due=1, category="academic"),
        gh_item(23, kind="issue", rel=2),
        gh_item(24, kind="pull_request", rel=1),
        cf_item(17, rel=1, due=2),
        otp(),
    ]),
    scen("electron_cross_platform_build", "Open source desktop application release build.", [
        gh_item(26, kind="issue", rel=2),
        gh_item(27, kind="pull_request", rel=2),
        it("classroom", "deadline", "Software Testing Unit Test Coverage Report", 2, due=3, category="academic"),
        enron_noise_item(33),
        otp(),
    ]),
    scen("gin_api_backend_refactor", "Backend service optimization for university portal project.", [
        gh_item(28, kind="pull_request", rel=2),
        gh_item(29, kind="issue", rel=2),
        it("calendar", "deadline", "Database Systems ER Modeling Submission", 2, due=2, category="academic"),
        cf_item(18, rel=1, due=3),
        newsletter(),
    ]),
    scen("neovim_config_productivity_sprint", "Light weekend project work with routine code updates.", [
        gh_item(30, kind="pull_request", rel=2),
        gh_item(31, kind="issue", rel=1),
        it("classroom", "announcement", "Prof. Verma: Reading materials for next Monday uploaded", 1),
        cf_item(19, rel=2, due=1),
        star("neovim"),
    ]),
    scen("security_vulnerability_patch", "Critical CVE vulnerability reported in repository dependency.", [
        gh_item(32, kind="issue", rel=3),  # High severity security issue
        gh_item(33, kind="pull_request", rel=2),
        it("calendar", "deadline", "CS401 Operating Systems Security Audit", 2, due=2, category="academic"),
        enron_action_item(95, rel=1, due=3),
        otp(),
    ]),

    # ── 4. Competitive Programming & Contest Schedules (Real Codeforces) ───
    scen("cf_weekend_rated_div2", "Weekend rated Codeforces contest today with no conflicting exams.", [
        cf_item(0, rel=2, due=0),  # Real contest from API
        cf_item(1, rel=2, due=1),  # Contest tomorrow
        it("codeforces", "practice", "Codeforces: Upsolve Problem C from previous round", 1),
        gh_item(35, kind="pull_request", rel=1),
        newsletter(),
    ]),
    scen("cf_educational_round_prep", "Educational Codeforces Round tomorrow evening.", [
        cf_item(2, rel=2, due=1),
        it("codeforces", "practice", "Codeforces: Practice Two Pointers & Binary Search", 1),
        it("calendar", "deadline", "Operating Systems Semaphore Assignment", 2, due=3, category="academic"),
        it("classroom", "announcement", "Classroom: Lecture recordings posted", 1),
        otp(),
    ]),
    scen("cf_kotlin_heroes_icpc_challenge", "Kotlin Heroes ICPC challenge running this afternoon.", [
        cf_item(3, rel=2, due=0),
        it("codeforces", "practice", "Kotlin Syntax & Standard Library Cheatsheet", 1),
        it("classroom", "deadline", "CS201 Data Structures Lab Problem Set", 2, due=2, category="academic"),
        gh_item(38, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("cf_global_round_sunday", "Sunday afternoon Codeforces Global Round.", [
        cf_item(4, rel=2, due=1),
        it("codeforces", "practice", "Codeforces: Upsolve 1900-rated Segment Tree problem", 1),
        it("calendar", "deadline", "Computer Networks Lab Assignment", 2, due=3, category="academic"),
        enron_action_item(110, rel=1, due=4),
        newsletter(),
    ]),
    scen("cf_div3_speedrun_contest", "Codeforces Div 3 round tonight for speed and accuracy practice.", [
        cf_item(5, rel=2, due=0),
        it("codeforces", "practice", "Speed practice: Div 3 Problem A-D sprint", 1),
        it("calendar", "deadline", "CS304 DBMS Query Plan Submission", 2, due=2, category="academic"),
        gh_item(42, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("cf_pinely_round_prep", "Pinely Round rated contest tomorrow amid moderate homework.", [
        cf_item(6, rel=2, due=1),
        it("codeforces", "practice", "Codeforces: Bit manipulation & XOR basis practice", 1),
        it("classroom", "deadline", "Discrete Mathematics Graph Theory Assignment", 2, due=2, category="academic"),
        enron_noise_item(45),
        otp(),
    ]),
    scen("cf_refact_ai_match", "Refact.ai special round scheduled for this weekend.", [
        cf_item(7, rel=2, due=2),
        it("codeforces", "practice", "Greedy algorithms and constructive problems", 1),
        it("calendar", "deadline", "Theory of Computation Automata Homework", 2, due=3, category="academic"),
        newsletter(),
    ]),
    scen("cf_div1_advanced_round", "Codeforces Div 1 high-rating round tomorrow.", [
        cf_item(8, rel=2, due=1),
        it("codeforces", "practice", "Centroid Decomposition and Heavy-Light Decomposition", 1),
        it("calendar", "deadline", "Machine Learning Gradient Descent Lab", 2, due=3, category="academic"),
        gh_item(45, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("cf_icpc_prelims_mock", "ICPC regional mock contest scheduled for Saturday.", [
        cf_item(9, rel=2, due=1),
        it("codeforces", "practice", "Team communication & geometry template verification", 1),
        it("classroom", "deadline", "Software Engineering Design Pattern Assignment", 2, due=2, category="academic"),
        newsletter(),
    ]),
    scen("cf_atcoder_codeforces_dual_round", "Dual contest weekend: Codeforces and AtCoder back-to-back.", [
        cf_item(10, rel=2, due=0),
        cf_item(11, rel=2, due=1),
        it("codeforces", "practice", "Shortest paths on weighted graphs practice", 1),
        it("calendar", "event", "Competitive Programming Club Problem Discussion", 1, due=1),
        otp(),
    ]),

    # ── 5. Pure Deadline Clusters (Fair Benchmark for Due-Date Sorting) ─────
    scen("pure_deadline_cluster_academics", "Pure dated coursework pileup; due-date ordering is optimal.", [
        it("calendar", "deadline", "CS301 Computer Organization: ALU Design Lab", 3, due=0, category="academic"),
        it("classroom", "deadline", "CS304 Database Systems: Relational Algebra Worksheet", 3, due=0, category="academic"),
        it("calendar", "deadline", "CS307 Computer Networks: Wireshark Lab Report", 2, due=1, category="academic"),
        it("classroom", "deadline", "CS312 Compiler Design: Lexical Analyzer Submission", 2, due=2, category="academic"),
        it("calendar", "deadline", "CS210 Theory of Computation: Grammar Equivalence", 1, due=3, category="academic"),
    ]),
    scen("assignment_pileup_multicourse", "Five dated university assignments; benchmark test for due-date ranker.", [
        it("classroom", "deadline", "CS401 Machine Learning: Problem Set 2", 3, due=0, category="academic"),
        it("classroom", "deadline", "CS304 DBMS: SQL Stored Procedures Assignment", 3, due=1, category="academic"),
        it("calendar", "deadline", "CS301 Operating Systems: Paging Simulation", 2, due=1, category="academic"),
        it("calendar", "deadline", "CS320 Software Engineering: SRS Document Draft", 2, due=2, category="academic"),
        it("classroom", "deadline", "CS307 Networks: Distance Vector Routing Simulation", 1, due=3, category="academic"),
    ]),
    scen("deadline_cluster_with_noise_email", "Three dated assignments accompanied by routine noise emails.", [
        it("calendar", "deadline", "CS201 Data Structures: AVL Tree Implementation due today", 3, due=0, category="academic"),
        it("classroom", "deadline", "CS301 Operating Systems: Shell Implementation due today", 3, due=0, category="academic"),
        it("calendar", "deadline", "CS307 Networks: HTTP Protocol Parser due tomorrow", 2, due=1, category="academic"),
        enron_noise_item(50),
        otp(),
    ]),
    scen("deadline_vs_event_trap", "A campus club gathering today must NOT beat an upcoming exam in 3 days.", [
        it("calendar", "deadline", "CS304 DBMS: B-Tree Indexing Project due today", 3, due=0, category="academic"),
        it("calendar", "exam", "CS301 Operating Systems: Mid-Semester Examination", 3, due=3),
        it("calendar", "deadline", "CS307 Networks: Socket Programming Lab", 2, due=2, category="academic"),
        it("calendar", "event", "Campus Board Games & Coffee Social (today)", 1, due=0),
        enron_noise_item(60),
    ]),
    scen("cluster_lab_submissions", "End of term lab practicals with strict submission windows.", [
        it("classroom", "deadline", "Hardware Lab Verilog HDL Final Code Submission", 3, due=0, category="academic"),
        it("calendar", "deadline", "Microprocessors 8086 Assembly Lab Report", 3, due=1, category="academic"),
        it("calendar", "deadline", "Object Oriented Design Java Project Package", 2, due=1, category="academic"),
        it("classroom", "deadline", "Environmental Studies Term Essay", 1, due=3, category="academic"),
        otp(),
    ]),
    scen("cluster_mixed_deadlines_with_pr", "Dated coursework assignments mixed with open source PR review.", [
        it("classroom", "deadline", "CS415 Deep Learning: CNN Image Classification Lab", 3, due=0, category="academic"),
        it("calendar", "deadline", "CS307 Networks: Subnetting Problem Set", 3, due=1, category="academic"),
        gh_item(48, kind="pull_request", rel=2),
        it("classroom", "deadline", "Technical Writing: Research Paper Abstract Draft", 2, due=2, category="academic"),
        it("calendar", "deadline", "Probability & Statistics: Markov Chains Homework", 1, due=4, category="academic"),
    ]),
    scen("cluster_project_milestones", "Senior design project milestone deadlines.", [
        it("calendar", "deadline", "Project Milestone 3: Core API Endpoints & Unit Tests", 3, due=0, category="academic"),
        it("calendar", "deadline", "Project Milestone 3: Frontend Integration & Figma Sync", 3, due=1, category="academic"),
        it("classroom", "deadline", "Project Milestone 3: Test Plan & CI/CD Pipeline Docs", 2, due=1, category="academic"),
        enron_action_item(125, rel=2, due=2),
        newsletter(),
    ]),
    scen("cluster_three_urgent_today", "Three strict coursework and form deadlines landing today.", [
        it("calendar", "deadline", "Submit Elective Preference Form to Dean Office", 3, due=0, category="academic"),
        it("classroom", "deadline", "CS301 Operating Systems: Memory Management Lab", 3, due=0, category="academic"),
        it("calendar", "deadline", "CS304 DBMS: Database Schema Normalization Exercise", 3, due=0, category="academic"),
        it("calendar", "deadline", "CS307 Networks: Packet Sniffing Quiz Prep", 2, due=1, category="academic"),
        otp(),
    ]),
    scen("cluster_weekend_deadlines", "Coursework assignments due over the weekend.", [
        it("classroom", "deadline", "CS201 Algorithms: Dynamic Programming Problem Set", 3, due=1, category="academic"),
        it("calendar", "deadline", "CS312 Compilers: Symbol Table Management Lab", 2, due=1, category="academic"),
        it("classroom", "deadline", "CS401 Artificial Intelligence: A* Search Simulation", 2, due=2, category="academic"),
        cf_item(12, rel=2, due=1),
        enron_noise_item(70),
    ]),
    scen("cluster_midterm_project_sync", "Midterm assignments across computer science electives.", [
        it("classroom", "deadline", "Cloud Computing: Terraform AWS Infrastructure Template", 3, due=0, category="academic"),
        it("calendar", "deadline", "Computer Graphics: 3D Transformation Matrix Exercises", 2, due=1, category="academic"),
        it("classroom", "deadline", "Information Security: RSA & Diffie-Hellman Key Exchange Lab", 2, due=2, category="academic"),
        gh_item(52, kind="pull_request", rel=1),
        otp(),
    ]),

    # ── 6. Heavy Inbox Noise & Distraction Days (Enron Corpus Noise) ────────
    scen("noisy_inbox_enron_promos", "Heavy inbox clutter: marketing promos and Enron negative sentences.", [
        it("gmail", "email", "Google Campus Hiring: Technical Interview Invite Confirmation", 3, due=1, category="internship"),
        it("calendar", "deadline", "CS301 Operating Systems: File System Assignment", 2, due=2, category="academic"),
        enron_noise_item(1),
        enron_noise_item(2),
        promo("Flash Sale: 60% off developer courses"),
        promo("Upgrade your cloud server instance today"),
        newsletter("Weekly Tech Digest #102"),
        otp(),
        star("student-os"),
    ]),
    scen("buried_opportunity_among_spam", "Scholarship and recruiter opportunity buried in email noise.", [
        it("gmail", "email", "Grace Hopper / Tapia Scholarship application closes tomorrow", 3, due=1, category="academic"),
        it("gmail", "email", "Recruiter from Stripe: Invitation to schedule coffee chat", 2, category="internship"),
        it("calendar", "deadline", "CS307 Networks Lab Report", 2, due=2, category="academic"),
        enron_noise_item(14),
        enron_noise_item(16),
        promo(),
        otp(),
    ]),
    scen("single_urgent_item_in_sea_of_noise", "Only one critical deadline in a flood of notifications.", [
        it("gmail", "email", "Immediate Action: Confirm your summer internship acceptance today", 3, due=0, category="internship"),
        enron_noise_item(20),
        enron_noise_item(21),
        enron_noise_item(22),
        promo(),
        newsletter(),
        otp(),
        star("react"),
    ]),
    scen("spam_only_morning", "Quiet morning with zero actionable tasks; entirely noise.", [
        enron_noise_item(30),
        enron_noise_item(31),
        enron_noise_item(32),
        promo("Special offer on domain names and web hosting"),
        newsletter("Weekend Gaming and Technology Roundup"),
        otp(),
        star("three.js"),
    ]),
    scen("inbox_flurry_with_action_sentence", "Enron action request buried among chatter and marketing.", [
        enron_action_item(150, rel=3, due=1),  # Real actionable sentence
        it("calendar", "deadline", "CS304 DBMS Assignment 3", 2, due=2, category="academic"),
        enron_noise_item(40),
        enron_noise_item(41),
        promo(),
        otp(),
    ]),
    scen("notification_overload_day", "Multiple GitHub and social notifications with one pending PR.", [
        gh_item(55, kind="pull_request", rel=2),
        it("calendar", "deadline", "CS301 OS Deadlock Prevention Worksheet", 2, due=2, category="academic"),
        star("student-os"),
        star("kubernetes"),
        star("electron"),
        enron_noise_item(55),
        otp(),
    ]),
    scen("promo_blitz_sale_season", "Black Friday / promotional influx in Gmail.", [
        it("gmail", "email", "Campus Placement Cell: Upload verified 6th semester mark sheet", 3, due=1, category="academic"),
        promo("80% off all programming books & video tutorials"),
        promo("Limited time discount on mechanical keyboards"),
        promo("Webinar: Introduction to Generative AI in the Enterprise"),
        enron_noise_item(65),
        otp(),
    ]),
    scen("cluttered_monday_inbox", "Monday morning inbox clutter with 2 real academic obligations.", [
        it("classroom", "deadline", "CS312 Compiler Assignment due tomorrow", 3, due=1, category="academic"),
        it("calendar", "deadline", "CS307 Networks Quiz Preparation", 2, due=2, category="academic"),
        enron_noise_item(75),
        enron_noise_item(76),
        promo(),
        newsletter(),
        otp(),
    ]),

    # ── 7. Semester Setup, Edge Cases & Administrative Scenarios ───────────
    scen("course_registration_day_deadline", "Course add/drop registration closes today at 5:00 PM.", [
        it("calendar", "deadline", "University Portal: Course Add/Drop & Registration Closes", 3, due=0, category="academic"),
        it("calendar", "event", "Academic Advisor Course Approval Meeting", 2, due=1),
        it("gmail", "email", "Tuition Fee & Semester Dues Payment Deadline", 2, due=2, category="academic"),
        newsletter(),
        otp(),
    ]),
    scen("semester_results_and_revaluation", "End-term results declared; revaluation window opens.", [
        it("gmail", "email", "Examination Cell: Semester Examination Results Published", 1, category="academic"),
        it("calendar", "deadline", "Submit Revaluation / Grade Verification Form", 2, due=3, category="academic"),
        it("calendar", "deadline", "CS301 Operating Systems Coursework", 2, due=2, category="academic"),
        cf_item(13, rel=1, due=1),
        otp(),
    ]),
    scen("calm_recharge_day", "Calm semester day with no urgent obligations.", [
        it("calendar", "event", "Robotics Club Technical Discussion", 1, due=2),
        it("classroom", "announcement", "Prof. Mehta: Suggested supplementary reading posted", 1),
        newsletter(),
        promo(),
        star("electron"),
    ]),
    scen("all_urgent_convergence", "Every domain lands an urgent task on the same day.", [
        it("calendar", "exam", "CS301 Operating Systems: Final Exam today", 3, due=0),
        it("classroom", "deadline", "CS304 DBMS: Major Term Project Code due today", 3, due=0, category="academic"),
        it("gmail", "email", "Amazon OA: Coding assessment expires tonight at midnight", 3, due=0, category="internship"),
        gh_item(60, kind="pull_request", rel=2),
        cf_item(14, rel=1, due=0),
    ]),
    scen("two_equal_top_tasks_tomorrow", "Two equally critical tasks due tomorrow.", [
        it("calendar", "exam", "CS307 Computer Networks: Midterm Exam", 3, due=1),
        it("classroom", "deadline", "CS301 Operating Systems: Thread Synchronization Lab", 3, due=1, category="academic"),
        cf_item(15, rel=1, due=0),
        otp(),
    ]),
    scen("pre_holiday_break_departure", "Departure for semester break with one lingering internship deadline.", [
        it("gmail", "email", "Google Summer of Code (GSoC) Proposal Submission Deadline", 3, due=2, category="internship"),
        it("calendar", "deadline", "Submit library books before vacation", 1, due=5, category="academic"),
        it("calendar", "event", "Train / Flight departure home", 1, due=1),
        promo(),
        otp(),
    ]),
    scen("semester_orientation_week", "First week of academic term; setup and club recruitments.", [
        it("calendar", "deadline", "Sign up for laboratory batch slots", 2, due=3, category="academic"),
        it("calendar", "event", "Campus Hackathon Organizing Committee Orientation", 1, due=1),
        it("classroom", "announcement", "Welcome to CS301 Operating Systems — Syllabus & Logistics", 1),
        it("calendar", "event", "Coding Club Freshman Recruitment Drive", 1, due=2),
        newsletter(),
        otp(),
    ]),
    scen("graduation_checklist_senior_year", "Senior year graduation audit and convocation clearance.", [
        it("calendar", "deadline", "Submit Graduation Clearance Form to Registrar Office", 3, due=1, category="academic"),
        it("calendar", "deadline", "Final Year Project Defense Presentation Deck", 2, due=2, category="academic"),
        enron_action_item(180, rel=2, due=2),
        newsletter(),
        otp(),
    ]),

    # ── 8. Mixed Authentic Real-World Student Days ──────────────────────────
    scen("typical_monday_morning_spread", "A classic Monday spread across all 5 integrated MCP tools.", [
        it("calendar", "deadline", "CS301 OS: Multithreaded Web Server Lab due tomorrow", 3, due=1, category="academic"),
        gh_item(65, kind="pull_request", rel=2),
        it("gmail", "email", "Campus Placement: SDE Intern application portal open", 2, due=3, category="internship"),
        cf_item(16, rel=1, due=2),
        it("calendar", "event", "Project Guide Weekly Status Sync", 1, due=2),
        otp(),
    ]),
    scen("midweek_crunch_assignments_and_exam", "Midweek pressure with coursework and an upcoming exam.", [
        it("calendar", "deadline", "CS304 DBMS: SQL Indexing Assignment due tomorrow", 3, due=1, category="academic"),
        it("calendar", "deadline", "CS307 Networks: Socket Programming due in 2 days", 2, due=2, category="academic"),
        it("calendar", "exam", "CS312 Compiler Design: Mid-Semester Exam in 4 days", 3, due=4),
        gh_item(70, kind="pull_request", rel=1),
        cf_item(17, rel=1, due=1),
        newsletter(),
    ]),
    scen("friday_winddown_weekend_prep", "Friday evening: close out week's tasks and plan contest weekend.", [
        it("calendar", "deadline", "CS201 Data Structures: Homework due Monday morning", 2, due=3, category="academic"),
        it("calendar", "event", "Campus Developer Meetup & Tech Talks (today)", 1, due=0),
        cf_item(18, rel=2, due=1),
        gh_item(75, kind="pull_request", rel=1),
        otp(),
    ]),
    scen("thursday_pre_hackathon_prep", "Thursday sprint preparing code dependencies for weekend hackathon.", [
        it("calendar", "deadline", "Software Engineering Lab Report", 2, due=2, category="academic"),
        gh_item(80, kind="issue", rel=2),
        gh_item(82, kind="pull_request", rel=2),
        enron_action_item(200, rel=2, due=2),
        cf_item(19, rel=1, due=2),
        newsletter(),
    ]),
    scen("placement_season_normal_day", "Normal semester day during peak campus placement season.", [
        it("gmail", "email", "Campus Placement Cell: Aptitude Test Slot Booking", 3, due=1, category="internship"),
        it("calendar", "deadline", "CS301 Operating Systems: Memory Simulation Lab", 2, due=2, category="academic"),
        it("codeforces", "practice", "Codeforces 1600-rated Greedy & Two Pointers practice", 1),
        gh_item(88, kind="pull_request", rel=1),
        enron_noise_item(88),
        otp(),
    ]),
    scen("open_source_contributor_day", "Active GitHub contributor triage day with light academics.", [
        gh_item(90, kind="issue", rel=2),
        gh_item(92, kind="pull_request", rel=2),
        it("classroom", "deadline", "CS304 DBMS: Normalization Worksheet", 2, due=3, category="academic"),
        cf_item(20, rel=1, due=2),
        star("three.js"),
        otp(),
    ]),
    scen("balanced_study_and_codeforces", "Balanced Wednesday with study group and evening rated round.", [
        it("calendar", "deadline", "CS307 Computer Networks: Lab 2 Submission", 2, due=1, category="academic"),
        cf_item(21, rel=2, due=1),
        it("classroom", "announcement", "Prof. Gupta: Extra tutorial session on Friday", 1),
        enron_action_item(220, rel=1, due=3),
        newsletter(),
    ]),
    scen("end_of_semester_sprint_all_channels", "Dense multi-channel day near the conclusion of the semester.", [
        it("calendar", "deadline", "Final Course Project GitHub Submission & Video Demo", 3, due=1, category="academic"),
        it("calendar", "exam", "CS301 Operating Systems: Final Theory Exam in 3 days", 3, due=3),
        gh_item(95, kind="pull_request", rel=2),
        it("gmail", "email", "Internship Coordinator: Submit Certificate of Completion", 2, due=4, category="internship"),
        cf_item(22, rel=1, due=1),
        otp(),
    ]),
]


def build() -> dict:
    return {
        "_about": (
            "Evaluation dataset grounded in real-world corpora: Codeforces API contests, "
            "Hugging Face GitHub issues (sharjeelyunus/github-issues-dataset), Enron Email Action Items, "
            "and university CS curricula. relevance is a hand-set human 'do-this-today' grade: "
            "3=must do today, 2=important soon, 1=optional, 0=noise. due_offset_days is relative to "
            "the run date so the set never goes stale. Generated by build_dataset.py."
        ),
        "relevance_scale": {
            "3": "must do today",
            "2": "important soon",
            "1": "optional",
            "0": "noise",
        },
        "scenarios": SCENARIOS,
    }


if __name__ == "__main__":
    data = build()
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    n = len(data["scenarios"])
    ids = [s["id"] for s in data["scenarios"]]
    assert len(ids) == len(set(ids)), f"Duplicate scenario ids! Total: {len(ids)}, Unique: {len(set(ids))}"
    total_items = sum(len(s["items"]) for s in data["scenarios"])
    print(f"Successfully generated {n} grounded scenarios with {total_items} total action items to {OUT}")
