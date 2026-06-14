# 📦 PHASE 1 — Foundation & Setup
> **Scope:** Project scaffold, environment config, database design, seed data
> **Milestone:** 1 (tasks 1–2)
> **Outcome:** A running Supabase database with all tables, constraints, and seed data. A clean project skeleton ready for code.
> **Estimated effort:** Day 1

---

## 🎯 GOAL OF THIS PHASE

Before writing a single line of application logic, the foundation must be solid:
- Every folder exists
- Every dependency is declared
- Every secret is in `.env`
- The database is live with all 6 tables

Nothing works without this phase. Everything else builds on top of it.

---

## ✅ TASK CHECKLIST

- [ ] 1.1 — Create full folder structure
- [ ] 1.2 — Write `requirements.txt`
- [ ] 1.3 — Write `.env.example`
- [ ] 1.4 — Write `app/utils/config.py`
- [ ] 1.5 — Write `migrations/schema.sql`
- [ ] 1.6 — Deploy schema in Supabase SQL editor
- [ ] 1.7 — Insert all seed data
- [ ] 1.8 — Verify tables exist and seed rows are present

---

## 📁 FOLDER STRUCTURE TO CREATE

```
telegram-news-bot/
│
├── .env                          ← copy from .env.example, fill real values
├── .env.example                  ← committed to git, no real secrets
├── requirements.txt
├── README.md
├── BRAIN.md
│
├── app/
│   ├── main.py                   ← empty for now, filled in Phase 5
│   ├── scrapers/
│   │   └── __init__.py
│   ├── services/
│   │   └── __init__.py
│   ├── database/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       └── __init__.py
│   ├── scheduler/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py             ← loads all .env values as typed constants
│       └── logger.py             ← filled in Phase 5
│
├── dashboard/
│   └── streamlit_app.py          ← empty for now, filled in Phase 4
│
├── migrations/
│   └── schema.sql                ← write and run this in Phase 1
│
└── tests/
    └── __init__.py
```

---

## 📄 FILE: `requirements.txt`

```txt
# Web framework
fastapi
uvicorn[standard]

# Database
supabase

# Scraping
requests
beautifulsoup4
lxml

# Scheduling
apscheduler

# AI APIs
google-generativeai
groq

# Utilities
python-dotenv
pydantic

# Dashboard
streamlit

# Testing
pytest
pytest-asyncio
httpx
```

---

## 📄 FILE: `.env.example`

```env
# ── Database ──────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_service_role_key

# ── Telegram ──────────────────────────────────────
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
# Channels are stored in Supabase, not here

# ── AI (tried in order: Gemini → Groq → raw) ─────
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key

# ── Scheduler ────────────────────────────────────
SCRAPE_INTERVAL_MINUTES=60

# ── Logging ───────────────────────────────────────
LOG_LEVEL=INFO
```

---

## 📄 FILE: `app/utils/config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

# Database
SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# AI
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY: str   = os.getenv("GROQ_API_KEY", "")

# Scheduler
SCRAPE_INTERVAL_MINUTES: int = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
```

---

## 📄 FILE: `migrations/schema.sql`

Run this **once** in the Supabase SQL editor. Never edit the live DB manually after this.

```sql
-- ─────────────────────────────────────────────────
-- Enable UUID generation
-- ─────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────────
-- TABLE: categories
-- Must be created before keywords and articles (FK dependency)
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: sources
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sources (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name       TEXT NOT NULL,          -- 'CoinTelegraph' or 'Blockworks'
    url        TEXT NOT NULL,
    is_active  BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: keywords
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS keywords (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    word        TEXT NOT NULL,
    category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: channels
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS channels (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id   TEXT NOT NULL,          -- e.g. @my_channel
    name          TEXT,
    is_active     BOOLEAN DEFAULT TRUE,
    source_filter TEXT NOT NULL,          -- 'CoinTelegraph' or 'Blockworks'
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: articles
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS articles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    url          TEXT UNIQUE NOT NULL,    -- deduplication key
    content      TEXT,
    source_name  TEXT,                    -- 'CoinTelegraph' or 'Blockworks'
    category_id  UUID REFERENCES categories(id) ON DELETE SET NULL,
    is_posted    BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,            -- original publish time (for 24hr filter)
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: logs
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT,                     -- SCRAPE | POST | ERROR | CLASSIFY | AI
    message    TEXT,                     -- human-readable description + failure reason
    article_id UUID REFERENCES articles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- INDEXES (for fast filtering)
-- ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_articles_is_posted    ON articles(is_posted);
CREATE INDEX IF NOT EXISTS idx_articles_category_id  ON articles(category_id);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_source_name  ON articles(source_name);
CREATE INDEX IF NOT EXISTS idx_logs_event_type       ON logs(event_type);
CREATE INDEX IF NOT EXISTS idx_logs_created_at       ON logs(created_at);
CREATE INDEX IF NOT EXISTS idx_keywords_category_id  ON keywords(category_id);
```

---

## 🌱 SEED DATA SQL

Run this **after** the schema, in the same SQL editor session.

```sql
-- ─────────────────────────────────────────────────
-- CATEGORIES
-- ─────────────────────────────────────────────────
INSERT INTO categories (name, description) VALUES
  ('Bitcoin',    'Bitcoin and BTC-related news'),
  ('Ethereum',   'Ethereum and ETH-related news'),
  ('DeFi',       'Decentralized Finance news'),
  ('NFT',        'Non-Fungible Token news'),
  ('Regulation', 'Crypto regulation and legal news'),
  ('Altcoin',    'Altcoin and general crypto news'),
  ('Markets',    'Crypto market analysis and prices'),
  ('Web3',       'Web3 and blockchain infrastructure news')
ON CONFLICT (name) DO NOTHING;

-- ─────────────────────────────────────────────────
-- KEYWORDS → mapped to categories
-- ─────────────────────────────────────────────────
-- Bitcoin
INSERT INTO keywords (word, category_id) SELECT 'bitcoin',  id FROM categories WHERE name='Bitcoin';
INSERT INTO keywords (word, category_id) SELECT 'btc',      id FROM categories WHERE name='Bitcoin';
INSERT INTO keywords (word, category_id) SELECT 'satoshi',  id FROM categories WHERE name='Bitcoin';
INSERT INTO keywords (word, category_id) SELECT 'halving',  id FROM categories WHERE name='Bitcoin';

-- Ethereum
INSERT INTO keywords (word, category_id) SELECT 'ethereum', id FROM categories WHERE name='Ethereum';
INSERT INTO keywords (word, category_id) SELECT 'eth',      id FROM categories WHERE name='Ethereum';
INSERT INTO keywords (word, category_id) SELECT 'solidity', id FROM categories WHERE name='Ethereum';
INSERT INTO keywords (word, category_id) SELECT 'vitalik',  id FROM categories WHERE name='Ethereum';

-- DeFi
INSERT INTO keywords (word, category_id) SELECT 'defi',         id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'uniswap',      id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'lending',      id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'yield',        id FROM categories WHERE name='DeFi';
INSERT INTO keywords (word, category_id) SELECT 'liquidity',    id FROM categories WHERE name='DeFi';

-- NFT
INSERT INTO keywords (word, category_id) SELECT 'nft',      id FROM categories WHERE name='NFT';
INSERT INTO keywords (word, category_id) SELECT 'opensea',  id FROM categories WHERE name='NFT';
INSERT INTO keywords (word, category_id) SELECT 'token',    id FROM categories WHERE name='NFT';

-- Regulation
INSERT INTO keywords (word, category_id) SELECT 'sec',        id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'regulation', id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'lawsuit',    id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'ban',        id FROM categories WHERE name='Regulation';
INSERT INTO keywords (word, category_id) SELECT 'legal',      id FROM categories WHERE name='Regulation';

-- Markets
INSERT INTO keywords (word, category_id) SELECT 'price',      id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'market cap', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'bull',       id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'bear',       id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'rally',      id FROM categories WHERE name='Markets';

-- Web3
INSERT INTO keywords (word, category_id) SELECT 'web3',       id FROM categories WHERE name='Web3';
INSERT INTO keywords (word, category_id) SELECT 'blockchain',  id FROM categories WHERE name='Web3';
INSERT INTO keywords (word, category_id) SELECT 'layer 2',    id FROM categories WHERE name='Web3';
INSERT INTO keywords (word, category_id) SELECT 'protocol',   id FROM categories WHERE name='Web3';

-- ─────────────────────────────────────────────────
-- SOURCES
-- ─────────────────────────────────────────────────
INSERT INTO sources (name, url, is_active) VALUES
  ('CoinTelegraph', 'https://cointelegraph.com',   TRUE),
  ('Blockworks',    'https://blockworks.co/news',  TRUE)
ON CONFLICT DO NOTHING;

-- ─────────────────────────────────────────────────
-- CHANNELS (update telegram_id with your real channel usernames)
-- ─────────────────────────────────────────────────
INSERT INTO channels (telegram_id, name, is_active, source_filter) VALUES
  ('@your_ct_channel', 'CoinTelegraph Feed', TRUE, 'CoinTelegraph'),
  ('@your_bw_channel', 'Blockworks Feed',    TRUE, 'Blockworks')
ON CONFLICT DO NOTHING;
```

---

## ✅ VERIFICATION STEPS

After running schema.sql and seed data, verify in Supabase Table Editor:

| Table | Expected rows |
|---|---|
| `categories` | 8 rows |
| `keywords` | ~30 rows |
| `sources` | 2 rows |
| `channels` | 2 rows (update telegram_id before going live) |
| `articles` | 0 rows (populated in Phase 2) |
| `logs` | 0 rows (populated in Phase 3+) |

---

## 🚦 EXIT CRITERIA (Phase 1 is done when)

- [ ] All 6 tables exist in Supabase with correct columns
- [ ] UNIQUE constraint on `articles.url` is confirmed
- [ ] All indexes are created
- [ ] Seed data is present in categories, keywords, sources, channels
- [ ] `.env` is filled with real keys (not committed to git)
- [ ] `config.py` loads all values without errors
- [ ] Folder structure matches exactly what is specified above

---

## ➡️ NEXT PHASE

Once this phase is done → move to **PHASE 2: Scraping & Data Pipeline**
