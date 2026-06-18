# 🧠 BRAIN.md — Telegram News Bot Automation System
> This file is the single source of truth for the project.
> Every layer, decision, term, tool, and open question lives here.
> Update this file as the project evolves.
>

---

## 📌 PROJECT IDENTITY

| Field | Value |
|---|---|
| **Project name** | Telegram News Bot Automation System |
| **Type** | Backend automation + admin dashboard |
| **Goal** | Scrape crypto news → clean → classify → AI rephrase → post to Telegram automatically |
| **Operation mode** | Starts automatically when server starts. Runs continuously. |
| **Milestones** | 2 (equal weight, 50% each) |
| **Deployment** | Localhost only |
| **Budget** | Free tiers only (Supabase, Groq, Gemini, Telegram) |

---

## 🧱 SYSTEM LAYERS (in execution order)

```
[Server Start]
    ↓ triggers immediately on startup
[Scheduler]
    ↓ runs pipeline on startup + every N minutes after
[Scraping Layer]        → fetches articles from last 24 hours from 2 websites
    ↓
[Cleaning Layer]        → strips HTML, normalizes timestamps
    ↓
[Deduplication]         → skips any URL already in DB
    ↓
[Classification Layer]  → matches keywords → single category assigned
    ↓                     if no match → log error, mark "unknown"
[Storage Layer]         → saves to Supabase (PostgreSQL)
    ↓
[AI Rephrasing]         → Gemini first → Groq fallback → raw text fallback
    ↓                     always outputs English
[Dispatch Logic]        → article source_name must match channel's source_filter
    ↓                     + unposted + valid category + active channel
[Delivery Layer]        → posts to the matching Telegram channel
    ↓                     posts all eligible articles (no hourly cap)
[Logging Layer]         → records every event, success, failure with reason
    ↓
[Admin Dashboard]       → Streamlit public localhost UI
```

---

## 🗓️ MILESTONE BREAKDOWN

### Milestone 1 — Data Pipeline & Core System (50%)
**Goal:** Fetch, clean, store, classify articles. Admin can configure without code changes.

| # | Task | Status |
|---|---|---|
| 1 | Project folder structure + .env + requirements.txt | ⬜ |
| 2 | Supabase schema (6 tables, constraints, indexes) | ⬜ |
| 3 | Supabase Python client + 4 core query functions | ⬜ |
| 4 | BaseScraper abstract class + CoinTelegraph scraper (last 24hrs) | ⬜ |
| 5 | Blockworks scraper (last 24hrs) | ⬜ |
| 6 | Data cleaner (HTML strip, timestamp normalize) | ⬜ |
| 7 | Classifier (keyword → single category, log if unmatched) | ⬜ |
| 8 | FastAPI CRUD routes (sources, categories, keywords, channels, articles) | ⬜ |
| 9 | Admin dashboard — Streamlit (manage config + view articles) | ⬜ |

### Milestone 2 — Processing, Posting & Automation (50%)
**Goal:** Full end-to-end pipeline, runs automatically on server start, handles failures.

| # | Task | Status |
|---|---|---|
| 10 | AI rephraser (Gemini → Groq → raw fallback, English output) | ⬜ |
| 11 | Telegram poster (Bot API + retry logic) | ⬜ |
| 12 | Dispatcher (source-to-channel matching + eligibility rules) | ⬜ |
| 13 | Posting history + logs table writes (with failure reasons) | ⬜ |
| 14 | Scheduler starts on server boot (APScheduler lifespan event) | ⬜ |
| 15 | Error handling across all layers with reason logging | ⬜ |
| 16 | Streamlit dashboard — monitoring (logs, stats, posting history) | ⬜ |
| 17 | End-to-end tests (pipeline, duplicates, API failures, inactive channels) | ⬜ |

---

## 🗄️ DATABASE SCHEMA

### Table: `articles`
```sql
id            UUID PRIMARY KEY DEFAULT gen_random_uuid()
title         TEXT NOT NULL
url           TEXT UNIQUE NOT NULL        -- deduplication key (skip if exists)
content       TEXT
source_name   TEXT                        -- 'CoinTelegraph' or 'Blockworks'
category_id   UUID REFERENCES categories(id)
is_posted     BOOLEAN DEFAULT FALSE
created_at    TIMESTAMPTZ DEFAULT now()
published_at  TIMESTAMPTZ                 -- original article publish time
```

### Table: `sources`
```sql
id         UUID PRIMARY KEY DEFAULT gen_random_uuid()
name       TEXT NOT NULL                  -- 'CoinTelegraph' or 'Blockworks'
url        TEXT NOT NULL
is_active  BOOLEAN DEFAULT TRUE
```

### Table: `categories`
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
name         TEXT UNIQUE NOT NULL
description  TEXT
```

### Table: `keywords`
```sql
id           UUID PRIMARY KEY DEFAULT gen_random_uuid()
word         TEXT NOT NULL
category_id  UUID REFERENCES categories(id)
```

### Table: `channels`
```sql
id               UUID PRIMARY KEY DEFAULT gen_random_uuid()
telegram_id      TEXT NOT NULL          -- e.g. @cointelegraph_bot_feed
name             TEXT
is_active        BOOLEAN DEFAULT TRUE
source_filter    TEXT NOT NULL          -- 'CoinTelegraph' or 'Blockworks'
                                        -- each channel is tied to one source
```

### Table: `logs`
```sql
id          UUID PRIMARY KEY DEFAULT gen_random_uuid()
event_type  TEXT                        -- SCRAPE, POST, ERROR, CLASSIFY, AI
message     TEXT                        -- includes failure reason when applicable
article_id  UUID REFERENCES articles(id) NULL
created_at  TIMESTAMPTZ DEFAULT now()
```

> **Key constraints:**
> - `articles.url` UNIQUE → duplicate URLs are silently skipped at DB level
> - `articles.published_at` → used to filter last 24 hours on each run
> - `channels.source_filter` → ties each channel to exactly one news source
> - Index on `articles.is_posted`, `articles.category_id`, `articles.published_at`

---

## 📡 CHANNEL ARCHITECTURE (CONFIRMED: 2 CHANNELS)

| Channel | Telegram ID | Source | Posts from |
|---|---|---|---|
| Channel 1 | `@your_cointelegraph_channel` | CoinTelegraph | cointelegraph.com only |
| Channel 2 | `@your_blockworks_channel` | Blockworks | blockworks.co/news only |

**How it works:**
- Every article has a `source_name` field
- Every channel has a `source_filter` field
- Dispatcher matches: article `source_name` == channel `source_filter`
- CoinTelegraph articles → Channel 1 only
- Blockworks articles → Channel 2 only
- No cross-posting

**Seed data for `channels` table:**
```sql
INSERT INTO channels (telegram_id, name, is_active, source_filter) VALUES
  ('@your_ct_channel',  'CoinTelegraph Feed', TRUE, 'CoinTelegraph'),
  ('@your_bw_channel',  'Blockworks Feed',    TRUE, 'Blockworks');
```

---

## 📁 FOLDER STRUCTURE

```
telegram-news-bot/
│
├── .env                          # secrets (never commit)
├── .env.example                  # template for new devs
├── requirements.txt
├── README.md
├── BRAIN.md                      # ← this file
│
├── app/
│   ├── main.py                   # FastAPI entry point + scheduler startup on boot
│   │
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py       # Abstract class: scrape() → list[dict]
│   │   ├── cointelegraph.py      # Scraper: last 24hrs from cointelegraph.com
│   │   └── blockworks.py         # Scraper: last 24hrs from blockworks.co/news
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── cleaner.py            # HTML strip, timestamp normalize to UTC
│   │   ├── classifier.py         # Keyword → single category (log if unmatched)
│   │   ├── rephraser.py          # Gemini → Groq → raw fallback (English only)
│   │   ├── dispatcher.py         # source_name match + eligibility + post loop
│   │   └── poster.py             # Telegram Bot API + 3x retry
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── client.py             # Supabase client init from .env
│   │   ├── models.py             # Pydantic models / schemas
│   │   └── queries.py            # All DB functions (see below)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── sources.py        # CRUD /sources
│   │       ├── categories.py     # CRUD /categories
│   │       ├── keywords.py       # CRUD /keywords
│   │       ├── channels.py       # CRUD /channels
│   │       └── articles.py       # GET /articles (filter by source, category, status)
│   │
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── jobs.py               # run_pipeline() — called on boot + every N mins
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py             # Centralized logging → console + DB logs table
│       └── config.py             # All .env values as typed constants
│
├── dashboard/
│   └── streamlit_app.py          # Streamlit UI — public, localhost, no auth
│
├── migrations/
│   └── schema.sql                # Full Supabase SQL — run once in SQL editor
│
└── tests/
    ├── test_scrapers.py
    ├── test_classifier.py
    ├── test_poster.py
    └── test_pipeline.py
```

---

## 🔧 TOOLS & TECHNOLOGIES

| Tool | Role | Tier |
|---|---|---|
| **Python** | Core language | Free |
| **FastAPI** | REST API layer | Free |
| **Supabase** | PostgreSQL database | Free tier |
| **BeautifulSoup4** | HTML parsing for scrapers | Free |
| **Requests** | HTTP calls | Free |
| **APScheduler** | Job scheduler (starts on server boot) | Free |
| **Telegram Bot API** | Posting to 2 channels | Free |
| **Google Gemini API** | AI rephrasing — primary | Free tier |
| **Groq API** | AI rephrasing — fallback (Llama3) | Free tier |
| **Streamlit** | Admin dashboard — localhost | Free |
| **python-dotenv** | .env loader | Free |
| **Pydantic** | Data validation | Free |
| **pytest** | Testing | Free |

---

## 🌐 DATA SOURCES

| Source | URL | Channel | Time filter |
|---|---|---|---|
| CoinTelegraph | https://cointelegraph.com | Channel 1 | Last 24 hours |
| Blockworks | https://blockworks.co/news | Channel 2 | Last 24 hours |

**Scraper output format (standardized for both):**
```python
{
  "title":       "Article headline",
  "url":         "https://full-article-url.com/slug",   # dedup key
  "content":     "Full article body text (HTML stripped)",
  "timestamp":   "2025-01-15T10:30:00Z",               # ISO 8601 UTC
  "source_name": "CoinTelegraph"                        # or "Blockworks"
}
```

**Scraper method:** `requests` + `BeautifulSoup` (confirmed sufficient, no Playwright needed)

**24-hour filter logic:**
```python
from datetime import datetime, timedelta, timezone
cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
# only keep articles where published_at >= cutoff
```

---

## 🤖 AI REPHRASING

**Priority chain (try in order):**
1. **Gemini** (Google free tier) — primary
2. **Groq** (Llama3-8b-8192 free tier) — fallback if Gemini fails
3. **Raw content** (first 300 chars) — final fallback if both AI APIs fail

**Rules:**
- Output language: **English only**
- Output format: 3 sentences, Telegram-suitable, factual, concise
- Input limit: max 2000 chars of article content sent to AI
- On any API error: log the error with reason, try next provider

**Prompt template:**
```
Summarize the following crypto news article in exactly 3 sentences in English.
Be concise, factual, and suitable for a Telegram news channel.
Title: {title}
Content: {content[:2000]}
```

**.env keys for AI:**
```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

---

## 📤 TELEGRAM POST FORMAT

```
📰 {title}

{ai_generated_summary_in_english}

🔗 {source_url}
```

**Rules:**
- Max ~4000 characters per message
- `parse_mode=HTML`
- Only post to channels where `is_active = TRUE`
- Never post the same article twice (`is_posted = TRUE` blocks re-posting)
- No hourly cap — post all eligible articles from the last 24 hours immediately
- Post 24/7, no time restrictions

---

## ⚙️ ENVIRONMENT VARIABLES (.env)

```env
# Database
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_service_role_key

# Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
# Note: channel IDs are stored in Supabase channels table, NOT here

# AI — multiple keys, tried in order
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# Scheduler
SCRAPE_INTERVAL_MINUTES=60

# Logging
LOG_LEVEL=INFO
```

---

## 🔄 DISPATCHER RULES (eligibility for posting)

An article is posted to a channel if ALL conditions are true:

1. `article.is_posted = FALSE`
2. `article.category_id IS NOT NULL`
3. `article.category_name != 'unknown'`
4. Channel `is_active = TRUE`
5. `article.source_name == channel.source_filter` ← **source must match channel**
6. `article.published_at >= now() - 24 hours`

**If article has no matching channel** (source_filter mismatch) → log warning, skip.

---

## 🔁 RETRY & FALLBACK LOGIC

| Layer | Retries | Wait | On final failure |
|---|---|---|---|
| Scraper (HTTP) | 2 | 3s | Log error with reason, return empty list |
| Scraper (0 articles) | — | — | Log: "No articles found in last 24hrs" |
| AI — Gemini | 1 | 3s | Try Groq |
| AI — Groq | 1 | 3s | Use raw content fallback |
| Telegram poster | 3 | 5s | Log failure with reason, skip (don't mark posted) |

**Failure logging format:**
```
event_type: ERROR
message: "[Layer] [reason] — article_id: {id} — source: {source}"
```

---

## 📊 STREAMLIT DASHBOARD PAGES

| Page | What it shows | Can edit? |
|---|---|---|
| **Overview** | Total articles, posted count, failure count, last run time | No |
| **Articles** | All articles, filter by source/category/status | No (read-only) |
| **Posting History** | What posted, when, to which channel, success/fail | No |
| **Logs** | Full event log with reasons — ERROR, SCRAPE, POST, AI events | No |
| **Sources** | Add/edit/toggle scraping sources | Yes |
| **Categories** | Add/edit categories | Yes |
| **Keywords** | Add/edit/delete keywords → category mappings | Yes |
| **Channels** | Add/toggle channels, set source_filter | Yes |

**Access:** Public localhost URL — `http://localhost:8501`
**Auth:** None required
**Manual trigger button:** Not included

---

## 🌱 SEED DATA (insert on first run)

### Categories
```sql
INSERT INTO categories (name, description) VALUES
  ('Bitcoin',     'Bitcoin and BTC-related news'),
  ('Ethereum',    'Ethereum and ETH-related news'),
  ('DeFi',        'Decentralized Finance news'),
  ('NFT',         'Non-Fungible Token news'),
  ('Regulation',  'Crypto regulation and legal news'),
  ('Altcoin',     'Altcoin and general crypto news'),
  ('Markets',     'Crypto market analysis and prices'),
  ('Web3',        'Web3, blockchain infrastructure news');
```

### Keywords (sample — expand as needed)
```sql
-- Bitcoin
INSERT INTO keywords (word, category_id) SELECT 'bitcoin', id FROM categories WHERE name='Bitcoin';
INSERT INTO keywords (word, category_id) SELECT 'BTC', id FROM categories WHERE name='Bitcoin';
INSERT INTO keywords (word, category_id) SELECT 'satoshi', id FROM categories WHERE name='Bitcoin';

-- Ethereum
INSERT INTO keywords (word, category_id) SELECT 'ethereum', id FROM categories WHERE name='Ethereum';
INSERT INTO keywords (word, category_id) SELECT 'ETH', id FROM categories WHERE name='Ethereum';
INSERT INTO keywords (word, category_id) SELECT 'solidity', id FROM categories WHERE name='Ethereum';

-- DeFi
INSERT INTO keywords (word, category_id) SELECT 'defi', id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'uniswap', id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'lending', id FROM categories WHERE name='DeFi';

-- NFT
INSERT INTO keywords (word, category_id) SELECT 'nft', id FROM categories WHERE name='NFT';
INSERT INTO keywords (word, category_id) SELECT 'opensea', id FROM categories WHERE name='NFT';

-- Regulation
INSERT INTO keywords (word, category_id) SELECT 'sec', id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'regulation', id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'lawsuit', id FROM categories WHERE name='Regulation';

-- Markets
INSERT INTO keywords (word, category_id) SELECT 'price', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'market cap', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'bull', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'bear', id FROM categories WHERE name='Markets';
```

### Sources
```sql
INSERT INTO sources (name, url, is_active) VALUES
  ('CoinTelegraph', 'https://cointelegraph.com', TRUE),
  ('Blockworks',    'https://blockworks.co/news', TRUE);
```

### Channels
```sql
INSERT INTO channels (telegram_id, name, is_active, source_filter) VALUES
  ('@your_ct_channel', 'CoinTelegraph Feed', TRUE, 'CoinTelegraph'),
  ('@your_bw_channel', 'Blockworks Feed',    TRUE, 'Blockworks');
```

---

## ✅ SUCCESS CRITERIA CHECKLIST

### Milestone 1
- [ ] Both scrapers fetch articles published in last 24 hours only
- [ ] Duplicate URLs are silently skipped, not re-inserted
- [ ] Every article gets exactly one category (or "unknown" with log)
- [ ] Admin can manage sources, categories, keywords, channels via Streamlit
- [ ] FastAPI endpoints return correct filtered data

### Milestone 2
- [ ] Pipeline starts automatically when server boots
- [ ] Each article is posted to its source-matched channel exactly once
- [ ] Every failure is logged with a specific reason
- [ ] Gemini → Groq → raw fallback chain works correctly
- [ ] Dashboard reflects live system activity
- [ ] Edge cases handled: 0 articles scraped, both AI APIs down, channel inactive

---

## 📝 DECISIONS LOG (all questions answered)

| # | Question | Answer | Impact |
|---|---|---|---|
| 1 | Scraper tech | `requests + BeautifulSoup` sufficient | No Playwright needed |
| 2 | Article time window | Last 24 hours only, skip existing URLs | Filter by `published_at >= now()-24h` |
| 3 | Scraper returns 0 articles | Log the failure with reason | Add log entry, no alert needed |
| 4 | Channel count & mapping | 2 channels, each tied to one website | `source_filter` column on channels table |
| 5 | Multi-category articles | Single category only (first keyword match wins) | Classifier stops at first match |
| 6 | Channel usernames | 2 channels to be created by owner, stored in DB | Seed channels table with real usernames |
| 7 | Posting frequency cap | No cap — post all last-24hr articles immediately | No rate limiter in dispatcher |
| 8 | Bot activation | Starts when server starts (FastAPI lifespan) | APScheduler starts in lifespan startup |
| 9 | AI provider strategy | Gemini first, Groq fallback, raw text final fallback | Multi-key .env, try chain in rephraser.py |
| 10 | Output language | English only | Hardcoded in AI prompt |
| 11 | Dashboard access | Public localhost, no auth | Streamlit default, no login needed |
| 12 | Manual run button | Not required | Omit from dashboard |
| 13 | Deployment target | Localhost only | APScheduler sufficient, no cloud cron needed |
| 14 | API budget | Free tiers only | Gemini free, Groq free, Supabase free, Telegram free |

---

*Last updated: All 14 owner questions answered and locked*
*Next update: After Milestone 1 tasks 1–3 completed*
