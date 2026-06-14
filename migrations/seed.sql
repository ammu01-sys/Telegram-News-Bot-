-- migrations/seed.sql
-- Run this AFTER schema.sql in the Supabase SQL editor.

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

-- Altcoin
INSERT INTO keywords (word, category_id) SELECT 'altcoin',  id FROM categories WHERE name='Altcoin';
INSERT INTO keywords (word, category_id) SELECT 'solana',   id FROM categories WHERE name='Altcoin';
INSERT INTO keywords (word, category_id) SELECT 'cardano',  id FROM categories WHERE name='Altcoin';
INSERT INTO keywords (word, category_id) SELECT 'ripple',   id FROM categories WHERE name='Altcoin';
INSERT INTO keywords (word, category_id) SELECT 'xrp',      id FROM categories WHERE name='Altcoin';

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
-- Add to Markets or Web3 to catch broad financial/macro news
INSERT INTO keywords (word, category_id) SELECT 'says', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'crypto', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'warning', id FROM categories WHERE name='Markets';
INSERT INTO keywords (word, category_id) SELECT 'news', id FROM categories WHERE name='Markets';
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
  ('-1004429663293', 'CoinTelegraph News', TRUE, 'CoinTelegraph'),
  ('-1004423446478', 'BlockWorks News',    TRUE, 'Blockworks')
ON CONFLICT DO NOTHING;
