-- migrations/seed.sql
-- Run this AFTER schema.sql in the Supabase SQL editor.
-- Seeds keywords mapped to the 5 categories defined in schema.sql.

-- Global News
INSERT INTO keywords (word, category_id) SELECT 'world',     id FROM categories WHERE name='Global News'
UNION ALL SELECT 'global',    id FROM categories WHERE name='Global News'
UNION ALL SELECT 'international', id FROM categories WHERE name='Global News'
UNION ALL SELECT 'united nations', id FROM categories WHERE name='Global News'
UNION ALL SELECT 'war',       id FROM categories WHERE name='Global News'
UNION ALL SELECT 'conflict',  id FROM categories WHERE name='Global News'
ON CONFLICT DO NOTHING;

-- Public Affairs
INSERT INTO keywords (word, category_id) SELECT 'Public Affairs',  id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'election',  id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'president', id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'congress',  id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'democrat',  id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'republican', id FROM categories WHERE name='Public Affairs'
UNION ALL SELECT 'policy',    id FROM categories WHERE name='Public Affairs'
ON CONFLICT DO NOTHING;

-- Tech News
INSERT INTO keywords (word, category_id) SELECT 'Tech News', id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'ai',        id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'artificial intelligence', id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'software',  id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'startup',   id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'chip',      id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'cyber',     id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'blockchain', id FROM categories WHERE name='Tech News'
UNION ALL SELECT 'crypto',    id FROM categories WHERE name='Tech News'
ON CONFLICT DO NOTHING;

-- Economy
INSERT INTO keywords (word, category_id) SELECT 'Economy',  id FROM categories WHERE name='Economy'
UNION ALL SELECT 'stock',     id FROM categories WHERE name='Economy'
UNION ALL SELECT 'market',    id FROM categories WHERE name='Economy'
UNION ALL SELECT 'economy',   id FROM categories WHERE name='Economy'
UNION ALL SELECT 'revenue',   id FROM categories WHERE name='Economy'
UNION ALL SELECT 'earnings',  id FROM categories WHERE name='Economy'
UNION ALL SELECT 'fed',       id FROM categories WHERE name='Economy'
UNION ALL SELECT 'inflation', id FROM categories WHERE name='Economy'
UNION ALL SELECT 'trade',     id FROM categories WHERE name='Economy'
UNION ALL SELECT 'tariff',    id FROM categories WHERE name='Economy'
ON CONFLICT DO NOTHING;

-- Broad catch-all → unknown
INSERT INTO keywords (word, category_id) SELECT 'breaking',  id FROM categories WHERE name='unknown'
UNION ALL SELECT 'says',      id FROM categories WHERE name='unknown'
UNION ALL SELECT 'news',      id FROM categories WHERE name='unknown'
ON CONFLICT DO NOTHING;
