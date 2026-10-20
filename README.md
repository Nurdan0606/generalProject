# FinalReady - Django, PostgreSQL, and OpenAI

FinalReady turns lecture PDFs and DOCX files into short daily quizzes, adaptive review,
and progress tracking. The application uses **PostgreSQL** and the **OpenAI API**.

## This workspace

- `.env` contains generated local database credentials and a Django secret.
- Add your own `OPENAI_API_KEY` to that file; its value is currently blank.
- PostgreSQL's project-local files live under `.local/` (excluded from version control).
- Your original `db.sqlite3` is preserved. The application no longer uses it.
- Your existing account, course, and lecture have already been transferred to PostgreSQL.
- `scripts/postgres.ps1` starts, stops, or checks the project-local PostgreSQL server.
- This local database does not start automatically when Windows restarts.

## Start the project (PowerShell)

From the project directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 status
# If PostgreSQL is stopped:
powershell -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 start
.\venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000. Sign in with your existing account, or create an account.
**Try demo course** provides 12 authored database questions without calling OpenAI.

Stop the database when you finish:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\postgres.ps1 stop
```

## Connect the OpenAI API

### 1. Get an API key

1. Sign in to the [OpenAI developer platform](https://platform.openai.com/).
2. Add prepaid credit or a payment method under **Billing** and set a conservative usage limit.
3. Open [API keys](https://platform.openai.com/api-keys), create a secret key, and copy it once.

ChatGPT Plus/Pro and API billing are separate. Paying for ChatGPT does not provide API credit.
The app defaults to `gpt-6-luna`, OpenAI's efficient model for focused, high-volume work.
The [official model page](https://developers.openai.com/api/docs/models/gpt-6-luna) lists
text pricing of $0.10 per million input tokens and $0.50 per million output tokens.

### 2. Put the key in .env

Open the `.env` file in the project root (beside `manage.py`) and edit these lines:

```dotenv
OPENAI_API_KEY=paste_your_actual_key_here
OPENAI_MODEL=gpt-6-luna
OPENAI_TIMEOUT_SECONDS=180
```

Keep the existing PostgreSQL credentials and Django secret. Do not replace the whole file.
For a fresh checkout only, create `.env` from `.env.example` first.

The key stays on the Django server. Never paste it into HTML, commit it, or send it in chat.
`.env` is already excluded by `.gitignore`.
Project-local OpenAI values in `.env` take precedence over user-level environment variables.
This prevents an older global API key from silently overriding the key for this project.

The default model is configurable. Use a model with Responses API and Structured Outputs support;
see the official [OpenAI model catalog](https://developers.openai.com/api/docs/models).

### 3. Check the connection

```powershell
.\venv\Scripts\python.exe manage.py check_openai
```

Expected output begins with `OpenAI connected. Model: ...`.
This performs a model lookup without sending lecture data or generating content.
It verifies authentication/model access; it does not prove you have generation quota.

### 4. Generate your questions

Restart Django after editing `.env`:

```powershell
.\venv\Scripts\python.exe manage.py runserver
```

Create or open a course, upload a PDF/DOCX lecture, and click **Generate questions**.
The server sends extracted lecture text to OpenAI and validates the returned JSON before
saving topics, questions, answer choices, and explanations. Then start the daily quiz.

Generation uses OpenAI's Python SDK, Responses API, and
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).
Original uploads are saved in `media/` and served only through owner-checked Django views.
Back up this directory together with PostgreSQL; do not expose it as public static media.
Click a lecture filename to download the original file directly.
Older uploads download saved text as a plain text file because their originals were not retained;
upload them again to retain the original file.
Use **Delete lecture** beside a lecture to remove it, its summary, related questions,
and the stored original file. Only the course owner can download or delete lectures.

Uploading automatically generates an English study guide through OpenAI using the configured
model: a short overview, explanations of the main concepts, and key takeaways. Click
**AI summary** beside the lecture to read it. Generation runs during the upload request;
the button shows progress while waiting. If the API fails, the lecture and original file
remain saved; open **AI summary** and click **Create summary** to retry. The same button
creates English summaries for older lectures, replacing previously saved Russian summaries
only after successful generation. Saved English summaries are reused without another API call.
Check generated summaries and answers against your lecture notes.

### Troubleshooting OpenAI

| Message | What to check |
| --- | --- |
| Set OPENAI_API_KEY | Save a real key in the root `.env`, then restart Django. |
| HTTP 400/401/403 | Verify the key, API billing, project permissions, and model access. |
| HTTP 404 / model access | Check `OPENAI_MODEL` against the models available to your project. |
| Quota or rate limit / HTTP 429 | Add API credit or check usage limits, then retry after the limit resets. |
| Temporarily unavailable / HTTP 5xx | The SDK retries automatically. Wait briefly if all attempts fail. |
| OpenAI took too long | Retry, or increase `OPENAI_TIMEOUT_SECONDS`; 180 seconds is the default. |
| Could not reach OpenAI | Check internet access, firewall/proxy settings, and retry. |
| No questions / invalid content | Try another lecture or retry. No partial question bank is saved. |

## PostgreSQL configuration

The normal Django settings always use PostgreSQL; there is no automatic SQLite fallback:

```dotenv
POSTGRES_DB=finalready
POSTGRES_USER=finalready
POSTGRES_PASSWORD=your_database_password
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

For this workspace, keep the generated password already in `.env`.
Changing it in `.env` alone does not change the PostgreSQL role's password.

The project-local server listens on loopback and requires password authentication.
Its `finalready` role is a local development administrator so Django can create test databases.
For production, use a separate database server and a restricted application role.

### Fresh installation on another Windows computer

Install Python 3.12+ and PostgreSQL 17+.
The [official Windows download page](https://www.postgresql.org/download/windows/)
links to the EDB installer, which includes PostgreSQL and pgAdmin.

Using pgAdmin's Query Tool, connected to the default `postgres` database as the installer
administrator, run these statements individually. Replace the example password:

```sql
CREATE ROLE finalready LOGIN PASSWORD 'replace_with_your_password';
CREATE DATABASE finalready OWNER finalready;
```

For a development database where you will run Django tests, also run:

```sql
ALTER ROLE finalready CREATEDB;
```

Then prepare the project:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env: database password, Django secret, and OpenAI API key.
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

The project-local control script applies only to the bundled `.local/` installation.
An installer-based PostgreSQL server is normally managed as a Windows service.

### Optional Docker setup

If you already use Docker Desktop, `compose.yaml` can run PostgreSQL 17 instead.
Set `POSTGRES_PASSWORD` in `.env`, stop any other server on the configured port, then:

```powershell
docker compose up -d db
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py runserver
```

Database files persist in a named volume. The container receives only database settings,
not the OpenAI key. Docker's POSTGRES variables initialize a new volume only; editing them
does not alter credentials in an existing volume.

## Transfer an earlier SQLite database

Use this only once when moving an earlier installation to an **empty** PostgreSQL database.
The transfer has already been completed in this workspace; do not run it again here.
Stop Django first so the source data cannot change during export. Keep `db.sqlite3` as a backup.

```powershell
.\venv\Scripts\python.exe -X utf8 manage.py dumpdata --settings=finalready.legacy_sqlite --natural-foreign --natural-primary --exclude=contenttypes --exclude=auth.permission --exclude=sessions --output=sqlite-export.json --verbosity=0
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe -X utf8 manage.py loaddata sqlite-export.json
```

This transfers accounts (including password hashes), courses, lectures, questions, and progress.
Active browser sessions are excluded, so sign in again. The export contains private study data
and is excluded from version control. Do not re-import it into a database where you have
already added new data.

## Features and scheduling

- Student accounts and ownership checks.
- Courses with exam dates and daily budgets of 1-10 minutes per course.
- PDF/DOCX text extraction, including DOCX tables.
- OpenAI-generated question banks and explanations.
- Daily quizzes prioritizing due questions and weaker topics.
- Weekly reviews covering topics before adding more weak questions.
- Server-side grading, duplicate-submission protection, streaks, and session history.

A question is estimated to take one minute including explanation review. The daily target
grows from five questions (or a smaller budget) toward
`ceil(question_count / remaining_days)`, capped at the course budget.
This is an estimate, not a timed lockout or a guarantee of coverage before the final.

There is one daily session per course/date and one weekly session per Monday-based calendar
week. Starting again resumes the session or displays its results. Weekly sessions select up
to twice the daily budget, capped at 20 questions.

Correct answers add 25 mastery points; incorrect answers subtract 35, bounded to 0-100.
Successful questions return 1-7 days later, sooner near the final; incorrect answers return
the next day. Readiness averages mastery across all questions, including unseen questions
at zero. It is a study heuristic, not an exam-score prediction.
Streaks count distinct completion dates across courses in Asia/Qyzylorda time.

## Architecture and checks

Django templates -> views/forms -> OpenAI and scheduling services -> Django ORM -> PostgreSQL.
Models: Course, Lecture, Topic, Question, StudySession, SessionItem, and Django User.

```powershell
.\venv\Scripts\python.exe manage.py check
.\venv\Scripts\python.exe manage.py test
.\venv\Scripts\python.exe manage.py makemigrations --check --dry-run
```

Normal tests use a temporary PostgreSQL database named `test_finalready`.
The database user needs CREATEDB. To run only application tests without a PostgreSQL server:

```powershell
.\venv\Scripts\python.exe manage.py test --settings=finalready.test_settings
```

That explicit test configuration uses in-memory SQLite and does not verify PostgreSQL behavior.
Tests mock OpenAI, so no key or paid generation is needed to run tests. Use `check_openai`
and the lecture flow for live verification.

## MVP limits

Generation is synchronous with a configurable 180-second HTTP timeout. Larger deployments should move
extraction/generation into a job queue, add quotas/rate limits and logging, and evaluate
question quality with real lecture material. Scanned PDFs need external OCR. Uploads are
limited to 10 MB, 150 PDF pages, and 60,000 text characters. Email/password recovery is not
configured. There are no teacher accounts, leaderboards, or XP.

For production, use HTTPS and an application server, set DJANGO_DEBUG=false, use a random
DJANGO_SECRET_KEY and explicit DJANGO_ALLOWED_HOSTS, serve static files, back up PostgreSQL,
and run `manage.py check --deploy`. The bundled server and Django runserver are for local development.
