"""Proactive notifications — push the brief instead of waiting to be asked.

Formats the daily briefing plus pre-deadline alerts and sends them to the
student where they already are: Telegram or email. With nothing configured it
runs in **dry-run** mode (returns the text), so it's fully testable offline and
demoable with zero setup.

Run once (for a cron job / Windows Task Scheduler):
    cd backend && python -m app.notifier
"""
from __future__ import annotations

import asyncio
from datetime import date

from app.config import get_settings

_PRIORITY_MARK = {"urgent": "‼", "high": "❗", "medium": "•", "low": "·"}


def _days_until(due: str | None, ref: date) -> int | None:
    if not due:
        return None
    try:
        return (date.fromisoformat(due[:10]) - ref).days
    except ValueError:
        return None


def _due_phrase(days: int | None) -> str:
    if days is None:
        return ""
    if days <= 0:
        return " (due today)"
    if days == 1:
        return " (due tomorrow)"
    return f" (in {days}d)"


def build_message(headline: str, summary: str, items: list, ref: date | None = None,
                  top: int = 5) -> str:
    """Format a plain-text notification. Pure + testable."""
    ref = ref or date.today()
    lines = [f"📌 Student OS — {ref.isoformat()}", "", headline, ""]

    # Pre-deadline alerts: anything due today/tomorrow, first.
    soon = [it for it in items if (_days_until(it.due, ref) or 99) <= 1]
    if soon:
        lines.append("⏰ Due now:")
        for it in soon[:top]:
            d = _days_until(it.due, ref)
            lines.append(f"  {_PRIORITY_MARK.get(_pri(it), '•')} {it.title}{_due_phrase(d)}")
        lines.append("")

    lines.append("Today's top items:")
    for it in items[:top]:
        d = _days_until(it.due, ref)
        lines.append(f"  {_PRIORITY_MARK.get(_pri(it), '•')} {it.title}{_due_phrase(d)}")
    if summary:
        lines += ["", summary]
    return "\n".join(lines)


def _pri(item) -> str:
    p = getattr(item, "priority", "medium")
    return p.value if hasattr(p, "value") else str(p)


def _send_telegram(text: str) -> bool:
    s = get_settings()
    if not (s.telegram_bot_token and s.telegram_chat_id):
        return False
    import httpx

    try:
        r = httpx.post(
            f"https://api.telegram.org/bot{s.telegram_bot_token}/sendMessage",
            json={"chat_id": s.telegram_chat_id, "text": text},
            timeout=25,
        )
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def _send_email(text: str) -> bool:
    s = get_settings()
    if not (s.smtp_host and s.smtp_user and s.notify_email_to):
        return False
    import smtplib
    from email.mime.text import MIMEText

    try:
        msg = MIMEText(text)
        msg["Subject"] = "Student OS — your daily brief"
        msg["From"] = s.smtp_user
        msg["To"] = s.notify_email_to
        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as server:
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)
            server.send_message(msg)
        return True
    except Exception:  # noqa: BLE001
        return False


def notify(text: str) -> dict:
    """Send via the first configured channel; otherwise dry-run."""
    if _send_telegram(text):
        return {"channel": "telegram", "sent": True, "preview": text}
    if _send_email(text):
        return {"channel": "email", "sent": True, "preview": text}
    return {"channel": "dry-run", "sent": False, "preview": text}


async def build_preview() -> str:
    """Build the notification text from today's briefing (no send)."""
    from app.orchestrator.agent import build_briefing

    b = await build_briefing()
    return build_message(b.headline, b.summary, b.items, date.today())


async def run_once() -> dict:
    """Build today's briefing and push it."""
    return notify(await build_preview())


if __name__ == "__main__":
    result = asyncio.run(run_once())
    print(f"[{result['channel']}] sent={result['sent']}\n")
    print(result["preview"])
