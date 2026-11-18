# Setup — going from mock to real

Everything below is optional. The app runs fully in mock mode with no keys.

## 0. Environment file

```bash
cp .env.example .env
```

Set `STUDENT_OS_MOCK=false` once you want servers to use real APIs. You can mix:
with mock off, any server that still lacks credentials just returns its sample
data, so you can turn on one platform at a time.

## 1. GitHub (real, easiest — start here)

1. GitHub → Settings → Developer settings → **Personal access tokens** →
   *Tokens (classic)* → Generate new token.
2. Scopes: `repo:status`, `read:user`, `notifications` (read-only is enough).
3. Put it in `.env`:
   ```
   STUDENT_OS_MOCK=false
   GITHUB_TOKEN=ghp_xxx
   ```
4. `cd backend && python demo.py` — you should now see your real PRs/issues.

## 2. LLM writer (optional)

```
ANTHROPIC_API_KEY=sk-ant-xxx
LLM_MODEL=claude-sonnet-5
```
Without this, briefings/chat use the built-in rule-based writer (no key needed).

## 3. Google — Gmail + Calendar (real, one-time consent)

Gmail and Calendar are fully implemented against the real Google APIs and share
one OAuth token. Setup:

1. [Google Cloud Console](https://console.cloud.google.com/) → new project.
2. Enable the **Gmail API**, **Google Calendar API**, and **Google Classroom API**.
3. Configure the OAuth consent screen (External; add your Google account as a
   **test user**). Add the read-only Gmail, Calendar, and Classroom scopes.
4. Create **OAuth client credentials** → *Desktop app* → copy the client id/secret.
5. Put them in `.env` and turn real mode on:
   ```
   STUDENT_OS_MOCK=false
   GOOGLE_CLIENT_ID=...apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=...
   ```
6. Run the one-time login (opens your browser, asks for read-only consent):
   ```bash
   cd backend
   python -m mcp_servers.common.google_auth login
   ```
   This saves a refresh token to `backend/.google_token.json` (git-ignored).
   From then on the Gmail/Calendar/Classroom servers read your real data and
   refresh the token automatically. All scopes are read-only.

If credentials or the token are missing, both servers quietly fall back to mock
data (and print a hint to stderr), so the app never breaks.

## 3b. Codeforces (real, no auth for contests)

Upcoming contests come from the public Codeforces API with no credentials.
The optional practice reminder uses your handle:

```
CODEFORCES_HANDLE=your_cf_handle
```

## 4. Running both halves

```bash
# terminal 1
cd backend && uvicorn app.main:app --reload

# terminal 2
cd frontend && npm install && npm run dev
```

Open http://localhost:3000.

## 5. Tests & evaluations

```bash
cd backend && python -m pytest                 # 37 tests
python -m eval.run_eval                         # ranking benchmark + significance
python -m eval.extraction_eval                  # deadline-extraction precision/recall
```

## 6. Caching (optional Redis)

The briefing fan-out is cached so repeated calls don't re-hit every API.
By default this uses an in-memory cache — nothing to install. To use Redis:

```
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=90
```

## 7. Learned ranker (optional)

The rule-based ranker is the default. To use the trained learning-to-rank model:

```bash
cd backend
python -m app.intelligence.train    # writes app/intelligence/ranker_weights.json
```
Then set `RANKER=learned` in `.env`. If the weights file is missing, the app
falls back to the rule-based ranker automatically (cold start).

## 8. Notifications (optional)

The notifier pushes the daily brief + pre-deadline alerts. With nothing set it
runs in **dry-run** (prints the message). To send for real, set one channel:

```
# Telegram
TELEGRAM_BOT_TOKEN=123456:abc
TELEGRAM_CHAT_ID=123456789
# or email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASSWORD=app-password
NOTIFY_EMAIL_TO=you@gmail.com
```
Run once (wire to cron / Windows Task Scheduler for a daily brief):
```bash
cd backend && python -m app.notifier
```

## 9. Persistence (SQLite default, Postgres optional)

History and feedback are stored in SQLite (`backend/student_os.db`) with zero
setup. To use PostgreSQL instead:

```
DATABASE_URL=postgresql+psycopg://user:pass@localhost/student_os
```
(Install a driver too, e.g. `pip install "psycopg[binary]"`.) The feedback loop
powers the learned ranker.
