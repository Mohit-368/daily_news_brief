# SSB Daily Brief

An automated current-affairs briefing service for SSB aspirants.

Every morning, GitHub Actions:

1. Collects current news from RSS feeds and optionally News API.
2. Removes duplicate stories.
3. Sends the candidate articles to an LLM.
4. Selects the most SSB-relevant stories.
5. Generates concise summaries and SSB-oriented questions.
6. Creates GD and lecturette topics.
7. Archives the briefing in `daily/`.
8. Emails the briefing.

## Architecture

```text
GitHub Actions
      |
      v
Python
      |
      +--> RSS / News API
      |
      v
Article collection
      |
      v
LLM classification + summarization
      |
      +--> SSB questions
      +--> GD topics
      +--> Lecturette topics
      |
      v
Daily JSON archive
      |
      v
Email
```

## Setup

### 1. Create a repository

Create a GitHub repository and copy this project into it.

### 2. Configure secrets

Go to:

`Repository -> Settings -> Secrets and variables -> Actions`

Add:

- `GEMINI_API_KEY`
- `GEMINI_MODEL` (optional)
- `NEWS_API_KEY` (optional)
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `EMAIL_FROM`
- `EMAIL_TO`

### Gmail

For Gmail SMTP, use an **App Password**, not your normal Gmail password.

Typical configuration:

```text
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@gmail.com
SMTP_PASSWORD=your_16_character_app_password
EMAIL_FROM=your@gmail.com
EMAIL_TO=recipient@gmail.com
```

### 3. Test locally

```bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

export GEMINI_API_KEY="..."
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USERNAME="..."
export SMTP_PASSWORD="..."
export EMAIL_FROM="..."
export EMAIL_TO="..."

python -m src.main
```

### 4. Run through GitHub Actions

Push the repository.

Then:

`Actions -> SSB Daily Brief -> Run workflow`

The scheduled workflow runs every day at **07:00 IST**.

The cron expression is:

```yaml
- cron: "30 1 * * *"
```

GitHub Actions schedules are UTC.

## Important production notes

### News quality

RSS feeds are only the ingestion layer. The LLM should not be treated as a source of truth.

For a stronger production version, add more primary sources such as:

- Press Information Bureau
- Ministry of Defence
- Ministry of External Affairs
- DRDO
- ISRO
- Indian Army
- Indian Navy
- Indian Air Force

and preserve the original source URL for every generated claim.

### Cost control

Keep the article batch small and send only relevant fields to the LLM.

You can also cache previously processed URLs to avoid repeated processing.

### Security

Never put API keys directly in the repository.

Use GitHub Actions Secrets.

### Scaling

This project intentionally does not use FastAPI, Redis, Celery or PostgreSQL in v1.

Add those only if you later need:

- user accounts
- personalized briefings
- a web dashboard
- historical search
- subscriptions
- multiple delivery channels
- high-volume processing
