"""Produce one self-contained .zip per version into releases/.

Each archive is the project as it stood at that version — a manifest lists the
files that existed at each step (the project grew mostly by *adding* files), and
version-accurate `requirements.txt` and `servers.json` are generated so the
dependency list and connector registry match that version.

    cd student-os && python tools/make_release_zips.py

Note: archives are feature snapshots that show how the codebase grew. Shared
wiring files (main.py, agent.py, ...) carry their latest content, so the newest
archive (v0.10.0) is the canonical runnable one; earlier archives are for
demonstrating the incremental build. See releases/README.md.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RELEASES = REPO / "releases"

# Documentation is "living" — included in EVERY version snapshot so each archive
# is self-documenting (content reflects the latest, current docs).
BASE_FILES = [
    "README.md",
    "docs/OVERVIEW.html",
    "docs/ARCHITECTURE.md", "docs/SETUP.md", "docs/ROADMAP.md",
    "docs/EVALUATION.md", "docs/GUIDE.html", "docs/PRODUCT_PLAN.md",
]

# Files first introduced at each version (cumulative when we build a snapshot).
VERSIONS: list[tuple[str, str, list[str]]] = [
    ("0.1.0", "Initial platform: orchestrator, 3 MCP servers, prioritizer, API, mock mode", [
        ".gitignore", ".env.example",
        "backend/demo.py",
        "backend/app/__init__.py", "backend/app/config.py", "backend/app/schemas.py",
        "backend/app/main.py",
        "backend/app/orchestrator/__init__.py", "backend/app/orchestrator/agent.py",
        "backend/app/orchestrator/llm.py", "backend/app/orchestrator/mcp_manager.py",
        "backend/app/orchestrator/prioritizer.py",
        "backend/app/routers/__init__.py", "backend/app/routers/briefing.py",
        "backend/app/routers/chat.py",
        "backend/mcp_servers/__init__.py",
        "backend/mcp_servers/common/__init__.py", "backend/mcp_servers/common/util.py",
        "backend/mcp_servers/github_server/__init__.py", "backend/mcp_servers/github_server/server.py",
        "backend/mcp_servers/gmail_server/__init__.py", "backend/mcp_servers/gmail_server/server.py",
        "backend/mcp_servers/calendar_server/__init__.py", "backend/mcp_servers/calendar_server/server.py",
        "backend/tests/__init__.py", "backend/tests/test_prioritizer.py",
    ]),
    ("0.2.0", "Next.js + TypeScript web app (dashboard + chat)", [
        "frontend/package.json", "frontend/tsconfig.json", "frontend/next.config.js",
        "frontend/next-env.d.ts",
        "frontend/app/layout.tsx", "frontend/app/page.tsx", "frontend/app/globals.css",
        "frontend/components/BriefingPanel.tsx", "frontend/components/ChatPanel.tsx",
        "frontend/components/PriorityBadge.tsx",
        "frontend/lib/api.ts", "frontend/lib/types.ts",
    ]),
    ("0.3.0", "Codeforces MCP server (real public API)", [
        "backend/mcp_servers/codeforces_server/__init__.py",
        "backend/mcp_servers/codeforces_server/server.py",
    ]),
    ("0.4.0", "Shared Google OAuth; real Gmail + Calendar", [
        "backend/mcp_servers/common/google_auth.py",
    ]),
    ("0.5.0", "Caching layer (Redis + in-memory fallback)", [
        "backend/app/cache.py",
    ]),
    ("0.6.0", "Google Classroom MCP server", [
        "backend/mcp_servers/classroom_server/__init__.py",
        "backend/mcp_servers/classroom_server/server.py",
    ]),
    ("0.7.0", "Evaluation harness (metrics, baselines, runner)", [
        "backend/eval/__init__.py", "backend/eval/metrics.py",
        "backend/eval/rankers.py", "backend/eval/run_eval.py",
        "backend/tests/test_metrics.py",
    ]),
    ("0.8.0", "40-scenario dataset + statistical significance", [
        "backend/eval/build_dataset.py", "backend/eval/dataset.json",
        "backend/eval/stats.py", "backend/tests/test_stats.py",
    ]),
    ("0.9.0", "Documentation set formalized + changelog", [
        "CHANGELOG.md",
    ]),
    ("0.10.0", "Learned ranker + persistence + feedback loop", [
        "backend/app/store.py", "backend/app/routers/feedback.py",
        "backend/app/orchestrator/ranking.py",
        "backend/app/intelligence/__init__.py", "backend/app/intelligence/features.py",
        "backend/app/intelligence/train.py", "backend/app/intelligence/learned_ranker.py",
        "backend/app/intelligence/ranker_weights.json",
        "backend/tests/test_store.py", "backend/tests/test_features.py",
        "backend/tests/test_learned_ranker.py",
    ]),
    ("0.11.0", "NLP deadline extraction from email/announcement text", [
        "backend/mcp_servers/common/extraction.py",
        "backend/eval/extraction_dataset.json", "backend/eval/extraction_eval.py",
        "backend/tests/test_extraction.py",
    ]),
    ("0.12.0", "Intelligent day-scheduler + wellbeing-aware pacing", [
        "backend/app/intelligence/scheduler.py",
        "backend/app/routers/schedule.py",
        "backend/tests/test_scheduler.py",
    ]),
    ("0.13.0", "Proactive notifier (Telegram/email + dry-run)", [
        "backend/app/notifier.py", "backend/app/routers/notify.py",
        "backend/tests/test_notifier.py",
    ]),
    ("0.14.0", "Opportunity radar + application tracking", [
        "backend/app/intelligence/opportunities.py",
        "backend/app/routers/opportunities.py",
        "backend/tests/test_opportunities.py",
    ]),
    ("0.15.0", "Action layer with propose/confirm guardrails", [
        "backend/app/actions.py", "backend/app/routers/actions.py",
        "backend/tests/test_actions.py",
    ]),
    ("0.16.0", "Security hardening (prompt-injection defence, token vault, scope audit)", [
        "backend/app/security.py", "backend/eval/security_eval.py",
        "backend/tests/test_security.py",
    ]),
    ("0.17.0", "Progress & habit dashboard", [
        "frontend/app/progress/page.tsx", "backend/tests/test_progress.py",
    ]),
    ("0.18.0", "Study-material RAG assistant", [
        "backend/app/intelligence/rag.py", "backend/app/routers/study.py",
        "backend/eval/rag_corpus/os_notes.md", "backend/eval/rag_corpus/dbms_notes.md",
        "backend/tests/test_rag.py",
    ]),
]


# Short slugs for readable, correctly-ordered archive names.
SLUGS = {
    "0.1.0": "initial-platform",
    "0.2.0": "web-app",
    "0.3.0": "codeforces",
    "0.4.0": "google-oauth",
    "0.5.0": "caching",
    "0.6.0": "classroom",
    "0.7.0": "evaluation-harness",
    "0.8.0": "dataset-and-significance",
    "0.9.0": "documentation",
    "0.10.0": "learned-ranker",
    "0.11.0": "deadline-extraction",
    "0.12.0": "day-scheduler",
    "0.13.0": "notifier",
    "0.14.0": "opportunity-radar",
    "0.15.0": "action-layer",
    "0.16.0": "security",
    "0.17.0": "progress-dashboard",
    "0.18.0": "rag-assistant",
}


def _servers_json(v_index: int) -> str:
    servers = [
        {"name": "github", "description": "Open PRs, assigned issues, notifications.",
         "command": "python", "args": ["-m", "mcp_servers.github_server.server"], "enabled": True},
        {"name": "gmail", "description": "Unread priority mail.",
         "command": "python", "args": ["-m", "mcp_servers.gmail_server.server"], "enabled": True},
        {"name": "calendar", "description": "Events, deadlines, exams.",
         "command": "python", "args": ["-m", "mcp_servers.calendar_server.server"], "enabled": True},
    ]
    if v_index >= 2:  # v0.3.0+
        servers.append({"name": "codeforces", "description": "Upcoming contests + practice reminder.",
                        "command": "python", "args": ["-m", "mcp_servers.codeforces_server.server"], "enabled": True})
    if v_index >= 5:  # v0.6.0+
        servers.append({"name": "classroom", "description": "Pending assignments + announcements.",
                        "command": "python", "args": ["-m", "mcp_servers.classroom_server.server"], "enabled": True})
    return json.dumps({"servers": servers}, indent=2)


def _requirements(v_index: int) -> str:
    deps = [
        "fastapi==0.115.6", "uvicorn[standard]==0.34.0", "pydantic==2.10.4",
        "pydantic-settings==2.7.0", "python-dotenv==1.0.1", "mcp==1.2.0",
        "httpx==0.28.1", "anthropic==0.42.0", "pytest==8.3.4", "pytest-asyncio==0.25.0",
    ]
    if v_index >= 3:  # v0.4.0+
        deps += ["google-auth==2.37.0", "google-auth-oauthlib==1.2.1"]
    if v_index >= 4:  # v0.5.0+
        deps += ["redis==5.2.1"]
    if v_index >= 9:  # v0.10.0+
        deps += ["sqlalchemy==2.0.36", "numpy==2.2.6"]
    return "\n".join(deps) + "\n"


def build() -> None:
    RELEASES.mkdir(exist_ok=True)
    for old in RELEASES.glob("*.zip"):  # clear any previous archives
        try:
            old.unlink()
        except OSError:
            print(f"  ! could not remove {old.name}")
    cumulative: list[str] = list(BASE_FILES)  # docs present in every snapshot
    for idx, (ver, theme, new_files) in enumerate(VERSIONS):
        cumulative += new_files
        step = idx + 1
        slug = SLUGS[ver]
        top = f"student-os-v{ver}"
        with tempfile.TemporaryDirectory() as tmp:
            stage = Path(tmp) / top
            for rel in cumulative:
                src = REPO / rel
                if not src.exists():
                    print(f"  ! missing (skipped): {rel}")
                    continue
                dst = stage / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            # Version-accurate generated files.
            (stage / "backend").mkdir(parents=True, exist_ok=True)
            (stage / "backend" / "servers.json").write_text(_servers_json(idx))
            (stage / "backend" / "requirements.txt").write_text(_requirements(idx))
            (stage / "VERSION.txt").write_text(
                f"Student OS v{ver}\n{theme}\n\n"
                f"Feature snapshot: files present reflect the project's scope at "
                f"this version. The newest archive (v0.10.0) is the canonical "
                f"runnable project.\n"
            )
            out = RELEASES / f"{step:02d}-student-os-v{ver}-{slug}.zip"
            with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
                for path in sorted(stage.rglob("*")):
                    if path.is_file():
                        zf.write(path, path.relative_to(stage.parent))
            n = sum(1 for _ in stage.rglob("*") if _.is_file())
            print(f"v{ver:<7} {n:>3} files  ->  releases/{out.name}")


if __name__ == "__main__":
    build()
