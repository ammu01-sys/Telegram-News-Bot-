from app.database.queries import (
    get_unposted_articles,
    get_active_channels,
    mark_as_posted,
    insert_log,
)
from app.services.cleaner import _extract_source, _fetch_article_page
from app.services.rephraser import rephrase
from app.services.poster import post_to_telegram
from app.utils.logger import logger


def run_dispatch() -> None:
    """
    For each unposted article from the last 24hrs:
    1. Find the matching active channel (by source_filter == source_name)
    2. Rephrase with AI
    3. Post to Telegram
    4. Mark as posted + log result
    """
    articles = get_unposted_articles()
    channels = get_active_channels()

    if not articles:
        logger.info("Dispatcher: no unposted articles to process")
        return

    if not channels:
        logger.warning("Dispatcher: no active channels found")
        return

    logger.info(f"Dispatcher: {len(channels)} active channel(s) found: "
                f"{[ch.get('telegram_id') + ' (' + ch.get('source_filter', '?') + ')' for ch in channels]}")
    logger.info(f"Dispatcher: processing {len(articles)} article(s)")

    for article in articles:
        source = article.get("source_name", "")

        # Find the channel that matches this article's source
        matching_channels = [
            ch for ch in channels
            if ch.get("source_filter", "").lower() == source.lower()
        ]

        if not matching_channels:
            insert_log(
                "ERROR",
                f"No matching channel for source '{source}' — article skipped",
                article.get("id"),
            )
            continue

        # Validate category
        category = article.get("categories", {})
        category_name = category.get("name") if isinstance(category, dict) else None

        if not category_name or category_name == "Uncategorized":
            insert_log(
                "ERROR",
                f"Skipped — no valid category — title: {article['title'][:50]}",
                article.get("id"),
            )
            continue

        # Use stored article_source, or extract from content (with full page fetch)
        if not article.get("article_source"):
            article_source = _extract_source(
                article.get("title", ""), article.get("content", "")
            )
            if not article_source and article.get("url"):
                full_text = _fetch_article_page(article["url"])
                if full_text:
                    article_source = _extract_source(article.get("title", ""), full_text)
            article["article_source"] = article_source

        logger.info(f"Article source: '{article.get('article_source', '')}' for: {article['title'][:60]}")

        # Rephrase article
        summary = rephrase(
            title=article["title"],
            content=article.get("content", ""),
            article_id=article.get("id"),
        )

        # Post to each matching channel (should be exactly 1 per source)
        for channel in matching_channels:
            success = post_to_telegram(
                article=article,
                channel_id=channel["telegram_id"],
                summary=summary,
            )

            if success:
                mark_as_posted(article["id"])
                insert_log(
                    "POST",
                    f"SUCCESS — channel: {channel['telegram_id']} — {article['title'][:50]}",
                    article.get("id"),
                )
            # Failure is already logged inside post_to_telegram
