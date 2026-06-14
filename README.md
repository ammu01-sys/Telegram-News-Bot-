# Telegram News Bot

An automated crypto news aggregation bot that scrapes articles from CoinTelegraph and Blockworks, classifies them by category using keyword matching, summarizes them with AI, and posts to Telegram channels — all running automatically on a schedule.

## Features

- **RSS-based scraping** — fetches the latest 24 hours of articles from CoinTelegraph and Blockworks via RSS/Atom feeds
- **Keyword classification** — matches articles to one of 8 crypto categories (Bitcoin, Ethereum, DeFi, NFT, Regulation, Altcoin, Markets, Web3)
- **AI summarization** — rephrases articles into 3-sentence Telegram-ready summaries using Gemini (with Groq fallback)
- **Source-to-channel dispatch** — CoinTelegraph articles go to Channel 1, Blockworks articles go to Channel 2
- **Deduplication** — articles are never posted twice (URL-based unique constraint)
- **Automatic scheduling** — pipeline runs on server boot and every 60 minutes via APScheduler
- **Full event logging** — every scrape, classify, AI call, and post is logged to Supabase with reasons

## Tech Stack

| Tool | Role |
|---|---|
| Python 3.11+ | Core language |
| FastAPI + Uvicorn | REST API + ASGI server |
| Supabase (PostgreSQL) | Database |
| BeautifulSoup4 + feedparser | RSS parsing |
| APScheduler | Job scheduling |
| Google Gemini API | AI summarization (primary) |
| Groq API | AI summarization (fallback) |
| Telegram Bot API | Channel posting |
| Streamlit | Admin dashboard (Phase 4) |

## Project Structure

```
telegram-news-bot/
├── app/
│   ├── main.py                 # FastAPI entry point + scheduler lifespan
│   ├── scrapers/
│   │   ├── base_scraper.py     # Abstract scraper with retry logic
│   │   ├── cointelegraph.py    # CoinTelegraph RSS scraper
│   │   └── blockworks.py       # Blockworks Atom feed scraper
│   ├── services/
│   │   ├── cleaner.py          # HTML stripping + timestamp normalization
│   │   ├── classifier.py       # Keyword-to-category matching
│   │   ├── rephraser.py        # Gemini → Groq → raw fallback AI
│   │   ├── dispatcher.py       # Source-to-channel matching + posting
│   │   └── poster.py           # Telegram Bot API with 3x retry
│   ├── database/
│   │   ├── client.py           # Supabase client singleton
│   │   ├── models.py           # Pydantic models
│   │   └── queries.py          # All database operations
│   ├── scheduler/
│   │   └── jobs.py             # Pipeline runner + APScheduler setup
│   ├── api/routes/             # FastAPI route stubs (Phase 4)
│   └── utils/
│       ├── config.py           # Environment variable loader
│       └── logger.py           # Centralized logging
├── migrations/
│   ├── schema.sql              # Full database schema (6 tables + indexes)
│   └── seed.sql                # Seed data (categories, keywords, sources, channels)
├── dashboard/
│   └── streamlit_app.py        # Streamlit admin UI (Phase 4)
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
└── run_pipeline_test.py        # Manual pipeline test script
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/ammu01-sys/Telegram-News-Bot-.git
cd Telegram-News-Bot-
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_service_role_key
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
SCRAPE_INTERVAL_MINUTES=60
LOG_LEVEL=INFO
```

### 3. Set up Supabase database

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run `migrations/schema.sql`
3. Then run `migrations/seed.sql`
4. Disable RLS on all tables:

```sql
ALTER TABLE categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE sources    DISABLE ROW LEVEL SECURITY;
ALTER TABLE keywords   DISABLE ROW LEVEL SECURITY;
ALTER TABLE channels   DISABLE ROW LEVEL SECURITY;
ALTER TABLE articles   DISABLE ROW LEVEL SECURITY;
ALTER TABLE logs       DISABLE ROW LEVEL SECURITY;
```

5. Update channel IDs with your real Telegram channels:

```sql
UPDATE channels SET telegram_id = '@your_channel_1' WHERE source_filter = 'CoinTelegraph';
UPDATE channels SET telegram_id = '@your_channel_2' WHERE source_filter = 'Blockworks';
```

### 4. Run

```bash
uvicorn app.main:app --reload
```

The pipeline starts immediately on boot, then repeats every 60 minutes.

## API Keys (all free tier)

- **Supabase** — [supabase.com](https://supabase.com) (Settings → API → service_role key)
- **Telegram Bot** — Message [@BotFather](https://t.me/BotFather) on Telegram
- **Gemini** — [aistudio.google.com](https://aistudio.google.com/apikey)
- **Groq** — [console.groq.com](https://console.groq.com/keys)

## How It Works

```
Server starts → Pipeline runs immediately
  → Scrape CoinTelegraph (RSS) + Blockworks (Atom)
  → Clean HTML, normalize timestamps to UTC
  → Classify by keyword matching (first match wins)
  → Store in Supabase (skip duplicates via UNIQUE url)
  → Dispatch unposted articles to matching channels
  → AI rephrase (Gemini → Groq → raw fallback)
  → Post to Telegram (3x retry)
  → Mark as posted + log everything
  → Scheduler repeats every 60 minutes
```

## License

MIT — see [LICENSE](LICENSE) for details.
