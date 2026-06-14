-- migrations/schema.sql
-- Run this ONCE in the Supabase SQL editor. Never edit the live DB manually after this.

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
    name       TEXT NOT NULL,
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
    telegram_id   TEXT NOT NULL,
    name          TEXT,
    is_active     BOOLEAN DEFAULT TRUE,
    source_filter TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: articles
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS articles (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        TEXT NOT NULL,
    url          TEXT UNIQUE NOT NULL,
    content      TEXT,
    source_name  TEXT,
    category_id  UUID REFERENCES categories(id) ON DELETE SET NULL,
    is_posted    BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT now()
);

-- ─────────────────────────────────────────────────
-- TABLE: logs
-- ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT,
    message    TEXT,
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
