-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    url TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Keywords table
CREATE TABLE IF NOT EXISTS keywords (
    id SERIAL PRIMARY KEY,
    word VARCHAR(255) NOT NULL,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(word, category_id)
);

-- Channels table
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    telegram_chat_id VARCHAR(255) NOT NULL UNIQUE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    content TEXT,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    status VARCHAR(50) DEFAULT 'raw',
    rephrased_content TEXT,
    published_at TIMESTAMP,
    scraped_at TIMESTAMP,
    pipeline_retries INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Logs table
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id) ON DELETE CASCADE,
    channel_id INTEGER REFERENCES channels(id) ON DELETE SET NULL,
    status VARCHAR(50) NOT NULL,
    error TEXT,
    retry_count INTEGER DEFAULT 0,
    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_articles_url ON articles(url);
CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
CREATE INDEX IF NOT EXISTS idx_articles_category_id ON articles(category_id);
CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id);
CREATE INDEX IF NOT EXISTS idx_articles_scraped_at ON articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_pipeline_retries ON articles(pipeline_retries);
CREATE INDEX IF NOT EXISTS idx_keywords_category_id ON keywords(category_id);
CREATE INDEX IF NOT EXISTS idx_channels_category_id ON channels(category_id);
CREATE INDEX IF NOT EXISTS idx_logs_article_id ON logs(article_id);
CREATE INDEX IF NOT EXISTS idx_logs_channel_id ON logs(channel_id);
CREATE INDEX IF NOT EXISTS idx_logs_posted_at ON logs(posted_at);
CREATE INDEX IF NOT EXISTS idx_logs_status ON logs(status);

-- Seed categories (keywords are synced via scripts/sync_keywords.py)
INSERT INTO categories (name) VALUES
    ('World News'),
    ('Politics'),
    ('Technology'),
    ('Business'),
    ('Health'),
    ('Uncategorized')
ON CONFLICT (name) DO NOTHING;

-- Seed sources
INSERT INTO sources (name, url) VALUES
    ('CoinTelegraph', 'https://cointelegraph.com'),
    ('Blockworks', 'https://blockworks.co/news')
ON CONFLICT (name) DO NOTHING;

-- Seed channels for all 6 categories (match .env values)
INSERT INTO channels (name, telegram_chat_id, category_id, is_active)
SELECT 'World News', '-1003947420847', id, true FROM categories WHERE name = 'World News'
UNION ALL
SELECT 'Politics', '-1003923156255', id, true FROM categories WHERE name = 'Politics'
UNION ALL
SELECT 'Technology', '-1003720230197', id, true FROM categories WHERE name = 'Technology'
UNION ALL
SELECT 'Business', '-1004113587922', id, true FROM categories WHERE name = 'Business'
UNION ALL
SELECT 'Health', '-1003977030607', id, true FROM categories WHERE name = 'Health'
UNION ALL
SELECT 'Uncategorized', '-1003960868410', id, true FROM categories WHERE name = 'Uncategorized'
ON CONFLICT (telegram_chat_id) DO NOTHING;

-- Migration for existing databases (run in Supabase SQL Editor if upgrading)
-- ALTER TABLE articles ADD COLUMN IF NOT EXISTS published_at TIMESTAMP;
-- ALTER TABLE articles ADD COLUMN IF NOT EXISTS pipeline_retries INTEGER DEFAULT 0;
-- ALTER TABLE sources ADD COLUMN IF NOT EXISTS last_scraped_at TIMESTAMP;
-- CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);
-- CREATE INDEX IF NOT EXISTS idx_articles_pipeline_retries ON articles(pipeline_retries);
