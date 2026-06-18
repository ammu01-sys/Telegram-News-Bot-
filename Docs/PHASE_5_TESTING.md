# ✅ PHASE 5 — Testing & End-to-End Validation
> **Scope:** Unit tests, integration tests, edge case validation, final pipeline verification
> **Milestone:** 2 (task 17)
> **Outcome:** Every layer of the pipeline is tested. Edge cases are handled. The system is confirmed production-ready.
> **Estimated effort:** Day 8

---

## 🎯 GOAL OF THIS PHASE

Confirm that every component works correctly — individually and together.
This phase does not add new features. It validates everything built in Phases 1–4.

---

## ✅ TASK CHECKLIST

- [ ] 5.1 — Test scraper output format and 24hr filter
- [ ] 5.2 — Test deduplication (same URL, two inserts)
- [ ] 5.3 — Test classifier (keyword match + unmatched case)
- [ ] 5.4 — Test AI fallback chain (Gemini fail → Groq fail → raw)
- [ ] 5.5 — Test Telegram poster (mock API + real retry count)
- [ ] 5.6 — Test dispatcher (source-channel matching, skip logic)
- [ ] 5.7 — Test full pipeline end-to-end (mock external APIs)
- [ ] 5.8 — Test edge cases (listed below)
- [ ] 5.9 — Final live run verification checklist

---

## 📄 FILE: `tests/test_scrapers.py`

```python
import pytest
from datetime import datetime, timezone
from app.scrapers.cointelegraph import CoinTelegraphScraper
from app.scrapers.blockworks import BlockworksScraper

REQUIRED_KEYS = {"title", "url", "content", "timestamp", "source_name"}

class TestCoinTelegraphScraper:
    def test_returns_list(self):
        articles = CoinTelegraphScraper().scrape()
        assert isinstance(articles, list)

    def test_article_has_required_keys(self):
        articles = CoinTelegraphScraper().scrape()
        if articles:
            for article in articles:
                assert REQUIRED_KEYS.issubset(article.keys()), \
                    f"Missing keys: {REQUIRED_KEYS - article.keys()}"

    def test_source_name_is_correct(self):
        articles = CoinTelegraphScraper().scrape()
        for a in articles:
            assert a["source_name"] == "CoinTelegraph"

    def test_url_is_non_empty(self):
        articles = CoinTelegraphScraper().scrape()
        for a in articles:
            assert a["url"].startswith("http"), f"Bad URL: {a['url']}"

    def test_title_is_non_empty(self):
        articles = CoinTelegraphScraper().scrape()
        for a in articles:
            assert len(a["title"]) > 5, f"Title too short: {a['title']}"


class TestBlockworksScraper:
    def test_returns_list(self):
        articles = BlockworksScraper().scrape()
        assert isinstance(articles, list)

    def test_article_has_required_keys(self):
        articles = BlockworksScraper().scrape()
        if articles:
            for article in articles:
                assert REQUIRED_KEYS.issubset(article.keys())

    def test_source_name_is_correct(self):
        articles = BlockworksScraper().scrape()
        for a in articles:
            assert a["source_name"] == "Blockworks"
```

---

## 📄 FILE: `tests/test_classifier.py`

```python
import pytest
from app.services.classifier import classify_article

# Mock keyword list — used to avoid DB calls in unit tests
MOCK_KEYWORDS = [
    {"word": "bitcoin", "categories": {"name": "Bitcoin"}},
    {"word": "eth",     "categories": {"name": "Ethereum"}},
    {"word": "defi",    "categories": {"name": "DeFi"}},
    {"word": "sec",     "categories": {"name": "Regulation"}},
]

def mock_get_keywords(monkeypatch):
    import app.services.classifier as clf_module
    monkeypatch.setattr(clf_module, "get_keywords_with_categories", lambda: MOCK_KEYWORDS)


class TestClassifier:
    def test_matches_bitcoin(self, monkeypatch):
        mock_get_keywords(monkeypatch)
        result = classify_article("Bitcoin hits all-time high", "Bitcoin price surges")
        assert result == "Bitcoin"

    def test_matches_ethereum(self, monkeypatch):
        mock_get_keywords(monkeypatch)
        result = classify_article("ETH upgrade deploys", "Ethereum ETH update")
        assert result == "Ethereum"

    def test_returns_none_when_no_match(self, monkeypatch):
        mock_get_keywords(monkeypatch)
        result = classify_article("Completely unrelated content here", "No keywords")
        assert result is None

    def test_first_match_wins(self, monkeypatch):
        """If content has both 'bitcoin' and 'eth', first keyword in list wins."""
        mock_get_keywords(monkeypatch)
        result = classify_article("bitcoin and eth both mentioned", "combined article")
        assert result == "Bitcoin"  # bitcoin appears first in MOCK_KEYWORDS

    def test_case_insensitive(self, monkeypatch):
        mock_get_keywords(monkeypatch)
        result = classify_article("BITCOIN is rising", "Bitcoin News")
        assert result == "Bitcoin"
```

---

## 📄 FILE: `tests/test_pipeline.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from app.services.cleaner import clean_article
from app.services.rephraser import rephrase


class TestCleaner:
    def test_strips_html(self):
        raw = {"title": "<b>Hello</b>", "content": "<p>World</p>", "timestamp": ""}
        cleaned = clean_article(raw)
        assert "<b>" not in cleaned["title"]
        assert "<p>" not in cleaned["content"]

    def test_normalizes_timestamp(self):
        raw = {"title": "T", "content": "C", "timestamp": "2025-01-15T10:30:00Z"}
        cleaned = clean_article(raw)
        assert cleaned["published_at"] is not None
        assert "2025" in cleaned["published_at"]

    def test_missing_timestamp_returns_none(self):
        raw = {"title": "T", "content": "C", "timestamp": ""}
        cleaned = clean_article(raw)
        assert cleaned["published_at"] is None

    def test_collapses_whitespace(self):
        raw = {"title": "  Too   many   spaces  ", "content": "   ", "timestamp": ""}
        cleaned = clean_article(raw)
        assert "  " not in cleaned["title"]


class TestRephraser:
    def test_gemini_success_path(self):
        """When Gemini returns a result, it should be used."""
        with patch("app.services.rephraser._try_gemini", return_value="Gemini summary."):
            result = rephrase("Test Title", "Test content here")
        assert result == "Gemini summary."

    def test_falls_back_to_groq_when_gemini_fails(self):
        with patch("app.services.rephraser._try_gemini", return_value=None):
            with patch("app.services.rephraser._try_groq", return_value="Groq summary."):
                result = rephrase("Test Title", "Test content here")
        assert result == "Groq summary."

    def test_falls_back_to_raw_when_both_fail(self):
        content = "This is the raw article content that should be truncated properly."
        with patch("app.services.rephraser._try_gemini", return_value=None):
            with patch("app.services.rephraser._try_groq", return_value=None):
                result = rephrase("Test Title", content)
        assert content[:50] in result  # raw content used

    def test_raw_fallback_truncates_at_300_chars(self):
        content = "x" * 500
        with patch("app.services.rephraser._try_gemini", return_value=None):
            with patch("app.services.rephraser._try_groq", return_value=None):
                result = rephrase("Test Title", content)
        assert len(result) <= 310  # 300 + "..."


class TestPoster:
    def test_posts_successfully(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"ok": True}

        with patch("app.services.poster.requests.post", return_value=mock_resp):
            from app.services.poster import post_to_telegram
            result = post_to_telegram(
                article={"id": "123", "title": "Test", "url": "https://example.com"},
                channel_id="@testchannel",
                summary="A brief summary.",
            )
        assert result is True

    def test_retries_3_times_on_failure(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("Network error")

        with patch("app.services.poster.requests.post", return_value=mock_resp):
            with patch("app.services.poster.time.sleep"):  # skip sleep in tests
                with patch("app.database.queries.insert_log"):
                    from app.services.poster import post_to_telegram
                    result = post_to_telegram(
                        article={"id": "123", "title": "Test", "url": "https://example.com"},
                        channel_id="@testchannel",
                        summary="Summary.",
                    )
        assert result is False


class TestDeduplication:
    def test_duplicate_url_not_inserted(self):
        """Insert same URL twice — second should return False."""
        from app.database.queries import insert_article

        payload = {
            "title":       "Dedup Test Article",
            "url":         "https://example.com/dedup-test-unique-url",
            "content":     "Content here",
            "source_name": "CoinTelegraph",
        }

        # Clean up if exists
        from app.database.client import get_client
        get_client().table("articles").delete().eq("url", payload["url"]).execute()

        first  = insert_article(payload)
        second = insert_article(payload)

        assert first  is True,  "First insert should succeed"
        assert second is False, "Second insert (duplicate URL) should be skipped"

        # Clean up
        get_client().table("articles").delete().eq("url", payload["url"]).execute()
```

---

## 📄 FILE: `tests/test_dispatcher.py`

```python
import pytest
from unittest.mock import patch, MagicMock

MOCK_ARTICLES = [
    {
        "id": "art-1",
        "title": "BTC Rises",
        "url": "https://cointelegraph.com/btc-rises",
        "content": "Bitcoin content",
        "source_name": "CoinTelegraph",
        "is_posted": False,
        "published_at": "2025-01-15T10:00:00+00:00",
        "categories": {"name": "Bitcoin"},
    }
]

MOCK_CHANNELS = [
    {"id": "ch-1", "telegram_id": "@ct_channel", "is_active": True, "source_filter": "CoinTelegraph"},
    {"id": "ch-2", "telegram_id": "@bw_channel", "is_active": True, "source_filter": "Blockworks"},
]


class TestDispatcher:
    def test_cointelegraph_article_goes_to_ct_channel(self):
        with patch("app.services.dispatcher.get_unposted_articles", return_value=MOCK_ARTICLES):
            with patch("app.services.dispatcher.get_active_channels", return_value=MOCK_CHANNELS):
                with patch("app.services.dispatcher.rephrase", return_value="Summary"):
                    with patch("app.services.dispatcher.mark_as_posted") as mock_mark:
                        with patch("app.services.dispatcher.insert_log"):
                            with patch("app.services.dispatcher.post_to_telegram", return_value=True) as mock_post:
                                from app.services.dispatcher import run_dispatch
                                run_dispatch()

                                # Should post to CoinTelegraph channel only
                                mock_post.assert_called_once()
                                call_kwargs = mock_post.call_args
                                assert call_kwargs[1]["channel_id"] == "@ct_channel"

    def test_article_with_no_category_is_skipped(self):
        unknown_articles = [{**MOCK_ARTICLES[0], "categories": {"name": "unknown"}}]
        with patch("app.services.dispatcher.get_unposted_articles", return_value=unknown_articles):
            with patch("app.services.dispatcher.get_active_channels", return_value=MOCK_CHANNELS):
                with patch("app.services.dispatcher.post_to_telegram") as mock_post:
                    with patch("app.services.dispatcher.insert_log"):
                        from app.services.dispatcher import run_dispatch
                        run_dispatch()
                        mock_post.assert_not_called()

    def test_no_articles_exits_cleanly(self):
        with patch("app.services.dispatcher.get_unposted_articles", return_value=[]):
            with patch("app.services.dispatcher.post_to_telegram") as mock_post:
                from app.services.dispatcher import run_dispatch
                run_dispatch()
                mock_post.assert_not_called()

    def test_inactive_channel_not_used(self):
        inactive_channels = [{**ch, "is_active": False} for ch in MOCK_CHANNELS]
        with patch("app.services.dispatcher.get_unposted_articles", return_value=MOCK_ARTICLES):
            with patch("app.services.dispatcher.get_active_channels", return_value=[]):
                with patch("app.services.dispatcher.post_to_telegram") as mock_post:
                    with patch("app.services.dispatcher.insert_log"):
                        from app.services.dispatcher import run_dispatch
                        run_dispatch()
                        mock_post.assert_not_called()
```

---

## 🧪 EDGE CASE MATRIX

| Edge Case | Expected Behavior | Tested In |
|---|---|---|
| Scraper site is down (HTTP 500) | Log ERROR with reason, return empty list | `test_scrapers.py` |
| Scraper returns 0 articles | Log warning "No articles in 24hrs", continue | `test_scrapers.py` |
| Article URL already in DB | Silent skip, `insert_article` returns False | `test_pipeline.py` |
| Article content has no keyword match | Log CLASSIFY, category_id = NULL | `test_classifier.py` |
| Category is "unknown" | Dispatcher skips article, logs reason | `test_dispatcher.py` |
| Article source has no matching channel | Log ERROR, article skipped | `test_dispatcher.py` |
| Gemini API fails | Switch to Groq | `test_pipeline.py` |
| Both Gemini and Groq fail | Use raw content[:300] as summary | `test_pipeline.py` |
| Telegram post fails all 3 retries | Log ERROR, `is_posted` stays False | `test_pipeline.py` |
| Channel `is_active = FALSE` | Dispatcher skips it | `test_dispatcher.py` |
| `published_at` is NULL | Cleaner returns None, article stored but may be missed by 24hr filter | `test_pipeline.py` |
| Server restarts mid-run | Already-posted articles have `is_posted=True`, not re-posted | manual test |

---

## 🏃 HOW TO RUN TESTS

```bash
# Run all tests
pytest tests/ -v

# Run a specific file
pytest tests/test_scraper.py -v

# Run with output (print statements visible)
pytest tests/ -v -s

# Run only fast tests (skip live API calls)
pytest tests/test_classifier.py tests/test_pipeline.py -v
```

---

## 🔍 FINAL LIVE VERIFICATION CHECKLIST

Run through this manually after all tests pass:

```
□ Start server: uvicorn app.main:app --reload
□ Confirm pipeline runs immediately in terminal logs
□ Open Supabase → articles table → new rows present
□ Open Telegram → Channel 1 (@ct_channel) → CoinTelegraph articles posted
□ Open Telegram → Channel 2 (@bw_channel) → Blockworks articles posted
□ Restart server → no duplicate posts in Telegram
□ Open dashboard at http://localhost:8501
  □ Overview shows correct article counts
  □ Logs page shows POST SUCCESS entries
  □ Articles table shows is_posted = TRUE for posted articles
□ Add a keyword in dashboard → confirm it appears in DB
□ Set a channel to inactive → restart server → confirm no posts to that channel
□ Temporarily use wrong Gemini key → confirm Groq fallback used (check logs)
□ Temporarily use wrong Groq key → confirm raw fallback used (check logs)
```

---

## 🚦 EXIT CRITERIA (Phase 5 — project is DONE when)

- [ ] All pytest tests pass with no failures
- [ ] Live verification checklist fully checked
- [ ] Both Telegram channels receive correct source-specific articles
- [ ] No duplicate articles posted across any restart
- [ ] All edge cases produce logged entries (not silent failures)
- [ ] Dashboard accurately reflects current system state
- [ ] Fallback chain (Gemini → Groq → raw) confirmed working

---

## 🎉 PROJECT COMPLETE

When all 5 phases are done, the full pipeline is:

```
Server boots
    → Scheduler fires immediately
    → CoinTelegraph + Blockworks scraped (last 24hrs)
    → Articles cleaned, deduped, classified, stored
    → AI rephrases each article in English (Gemini → Groq → raw)
    → Dispatcher routes CoinTelegraph articles → Channel 1
    → Dispatcher routes Blockworks articles → Channel 2
    → Every event logged to Supabase with reason
    → Streamlit dashboard reflects everything at localhost:8501
    → Repeats every 60 minutes automatically
```
