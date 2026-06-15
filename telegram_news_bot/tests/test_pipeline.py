import pytest
from unittest.mock import patch, MagicMock
from telegram_news_bot.services.cleaner import strip_html, normalize_text, clean_article
from telegram_news_bot.services.classifier import Classifier
from telegram_news_bot.services.rephraser import rephrase
from telegram_news_bot.services.dispatcher import format_message
from telegram_news_bot.database.queries import insert_article


def test_strip_html():
    result = strip_html("<p>Hello <b>world</b></p>")
    assert "Hello" in result
    assert "world" in result


def test_normalize_text():
    result = normalize_text("  hello   world  ")
    assert result == "hello world"


def test_classify_match():
    classifier = Classifier()
    classifier._keywords = [{"word": "bitcoin", "category_id": 3}]
    classifier._uncategorized_id = 6
    result = classifier.classify("bitcoin price surges")
    assert result == 3


def test_classify_no_match():
    classifier = Classifier()
    classifier._keywords = [{"word": "bitcoin", "category_id": 3}]
    classifier._uncategorized_id = 6
    result = classifier.classify("nothing about crypto here")
    assert result == 6


def test_clean_article():
    article = {
        "title": "<b>Title</b>",
        "content": "  Lots   of   <i>HTML</i>  ",
        "source_name": "Test",
        "url": "http://example.com",
    }
    cleaned = clean_article(article)
    assert cleaned["title"] == "Title"
    assert cleaned["content"] == "Lots of HTML"
    assert cleaned["source_name"] == "Test"


@patch("telegram_news_bot.database.queries.supabase")
def test_insert_duplicate(mock_supabase):
    mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key")
    data = {
        "title": "Test",
        "url": "http://example.com/dup",
        "content": "Content",
        "source_id": 1,
        "category_id": 1,
        "scraped_at": "2025-01-01T00:00:00",
    }
    result = insert_article(data)
    assert result is None


@patch("telegram_news_bot.services.rephraser._try_openrouter", return_value=None)
@patch("telegram_news_bot.services.rephraser.genai.Client")
def test_rephraser_fallback(mock_genai_client, mock_openrouter):
    mock_genai_client.side_effect = Exception("API error")
    content = "A" * 300
    result = rephrase("Test Title", content)
    assert result == content[:280] + "..."


@patch("telegram_news_bot.services.dispatcher.get_active_channels")
@patch("telegram_news_bot.services.dispatcher.get_unposted_articles")
def test_dispatch_no_channels(mock_get_unposted, mock_get_channels):
    mock_get_channels.return_value = []
    mock_get_unposted.return_value = [{"id": 1}]
    from telegram_news_bot.services.dispatcher import dispatch_all
    result = dispatch_all()
    assert result == {"attempted": 0, "success": 0, "failed": 0, "skipped": 0}


def test_format_message():
    article = {
        "title": "Test Title",
        "url": "http://example.com",
        "rephrased_content": "Summary here.",
        "category_name": "Technology",
        "source_name": "TestSource",
    }
    msg = format_message(article)
    assert "Test Title" in msg
    assert "Summary here" in msg
    assert "Read more" in msg
    assert "http://example" in msg
