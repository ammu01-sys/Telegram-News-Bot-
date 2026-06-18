import os
import re
import requests
import asyncio
import time
from telegram import Bot
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from ..utils.config import TELEGRAM_BOT_TOKEN, TELEGRAM_PROXY, MAX_RETRY_ATTEMPTS
from ..database.queries import (
    get_unposted_articles,
    get_active_channels,
    update_article_status,
    log_post_attempt,
    has_been_posted_to_channel,
    increment_pipeline_retries,
    deactivate_channel,
)
from ..services.rephraser import rephrase
from ..utils.logger import get_logger

log = get_logger(__name__)

def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def format_message(article: dict) -> str:
    title = escape_html(str(article.get('title', '')))
    content = escape_html(str(article.get('rephrased_content') or article.get('content', '')))
    url = str(article.get('url', ''))

    return (
        f"<b>{title}</b>\n\n"
        f"{content}\n\n"
        f'<a href="{url}">Click here</a>'
    )


def get_target_channels(article: dict, all_channels: list) -> list:
    """
    Route article to the channel matching its category_id.

    Rules:
    - Match article's category_id to a channel's category_id
    - If no match, fallback to unknown channel (category_id=6)
    - If unknown channel not found, return empty
    """
    article_category_id = article.get('category_id')
    article_id = article.get('id')
    source_name = str(article.get('source_name', '')).lower().strip()

    for ch in all_channels:
        if ch.get('category_id') == article_category_id:
            log.info(f"Article '{source_name}' (category_id={article_category_id}) -> '{ch['name']}'")
            return [ch]

    # Fallback to unknown
    for ch in all_channels:
        if ch.get('category_id') == 5:
            log.warning(f"No category match (category_id={article_category_id}), falling back to '{ch['name']}'")
            return [ch]

    log.error(f"No channel found for article {article_id} (category_id={article_category_id})")
    return []


def is_test_article(article: dict) -> bool:
    """Filter out test/fake/invalid articles."""
    title = str(article.get('title', '')).lower()
    url = str(article.get('url', '')).lower()
    test_indicators = [
        'test article', 'test post', 'example.com',
        'localhost', '127.0.0.1', 'test-article',
        'sample article', 'dummy', '/archive'
    ]
    return any(i in title or i in url for i in test_indicators)


def _make_bot() -> Bot:
    if TELEGRAM_PROXY:
        request = HTTPXRequest(proxy=TELEGRAM_PROXY, read_timeout=60, write_timeout=60, connect_timeout=60)
        return Bot(token=TELEGRAM_BOT_TOKEN, request=request)
    return Bot(token=TELEGRAM_BOT_TOKEN)


def _classify_telegram_error(status_code: int, description: str) -> dict:
    """
    Classify a Telegram API error into a structured response.

    Returns:
        {"success": False, "error_type": str, "error_message": str, "retry_after": int | None}
    """
    err_lower = description.lower()
    error_type = "unknown"
    retry_after = None

    if status_code == 400:
        error_type = "bad_request"
    elif status_code == 403:
        error_type = "forbidden"
    elif status_code == 420:
        error_type = "flood_wait"
        # Extract retry-after seconds if present (e.g. "FLOOD_WAIT_30")
        match = re.search(r'FLOOD_WAIT_(\d+)', description)
        if match:
            retry_after = int(match.group(1))
    elif status_code == 429:
        error_type = "rate_limited"
    elif status_code >= 500:
        error_type = "server_error"
    elif "connection" in err_lower or "timeout" in err_lower or "reset" in err_lower:
        error_type = "connection_error"

    return {
        "success": False,
        "error_type": error_type,
        "error_message": description[:200],
        "retry_after": retry_after,
    }


def _try_http_fallback(message: str, chat_id: str) -> dict:
    """Fallback to synchronous HTTP request when python-telegram-bot fails."""
    try:
        proxies = {"https": TELEGRAM_PROXY} if TELEGRAM_PROXY else None
        url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
        resp = requests.post(
            url,
            data={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': 'true'},
            proxies=proxies,
            timeout=30,
        )
        if resp.status_code == 200:
            result = resp.json()
            if result.get('ok'):
                return {"success": True, "error_type": None, "error_message": None, "retry_after": None}
            desc = result.get('description', 'Unknown error')
            return _classify_telegram_error(resp.status_code, desc)
        desc = resp.text[:200]
        return _classify_telegram_error(resp.status_code, desc)
    except Exception as e:
        err_str = str(e)
        err_lower = err_str.lower()
        if "connection" in err_lower or "timeout" in err_lower or "reset" in err_lower:
            return {"success": False, "error_type": "connection_error", "error_message": err_str[:200], "retry_after": None}
        return {"success": False, "error_type": "unknown", "error_message": err_str[:200], "retry_after": None}


async def _send_telegram(message: str, chat_id: str) -> bool:
    """Send message to Telegram. Tries direct connection first, then proxy fallback."""
    
    # Try direct connection first (when VPN is active)
    try:
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.HTML,
                read_timeout=15,
                write_timeout=15,
                connect_timeout=15,
                disable_web_page_preview=True
            )
        log.info(f"Sent via direct connection to {chat_id}")
        return True
    except Exception as e:
        log.warning(f"Direct connection failed: {e} — trying proxy fallback...")

    # Fallback: try phone proxy (SOCKS5)
    proxy_list = [
        os.getenv("PROXY_SOCKS5", ""),       # e.g. socks5://192.168.1.x:1080
        os.getenv("PROXY_HTTP", ""),          # e.g. http://192.168.1.x:8080
        os.getenv("PROXY_SOCKS5_2", ""),      # second proxy if any
    ]
    proxy_list = [p for p in proxy_list if p]  # remove empty

    for proxy in proxy_list:
        try:
            log.info(f"Trying proxy: {proxy}")
            from telegram.request import HTTPXRequest
            request = HTTPXRequest(proxy=proxy, connect_timeout=15, read_timeout=15)
            bot = Bot(token=TELEGRAM_BOT_TOKEN, request=request)
            async with bot:
                await bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=ParseMode.HTML,
                    read_timeout=15,
                    write_timeout=15,
                    connect_timeout=15,
                    disable_web_page_preview=True
                )
            log.info(f"Sent via proxy {proxy} to {chat_id}")
            return True
        except Exception as e:
            log.warning(f"Proxy {proxy} failed: {e}")
            continue

    log.error(f"All connection methods failed for {chat_id}")
    return False


def post_to_telegram(message: str, chat_id: str) -> dict:
    """Returns a result dict: {success, error_type, error_message, retry_after}.
    Attempts python-telegram-bot async, falls back to HTTP on failure."""
    try:
        ok = asyncio.run(_send_telegram(message, chat_id))
        if ok:
            return {"success": True, "error_type": None, "error_message": None, "retry_after": None}
        return {"success": False, "error_type": "unknown", "error_message": "All send methods failed", "retry_after": None}
    except Exception as e:
        err_str = str(e)
        log.error(f"post_to_telegram asyncio exception: {err_str[:120]}")
        return _try_http_fallback(message, chat_id)


def dispatch_all() -> dict:
    """
    Main dispatch function.
    Routes each article to the channel matching its category_id.
    Falls back to unknown channel if no match.
    No duplicates. Skips test articles.
    """
    attempted = success = failed = skipped = 0

    articles = get_unposted_articles()
    channels = get_active_channels()

    if not channels:
        log.warning("No active channels found - aborting dispatch.")
        return {"attempted": 0, "success": 0, "failed": 0, "skipped": 0}

    if not articles:
        log.info("No unposted articles found.")
        return {"attempted": 0, "success": 0, "failed": 0, "skipped": 0}

    log.info(f"Dispatching {len(articles)} articles to {len(channels)} active channels")

    for article in articles:
        article_id = article['id']

        # Skip test articles
        if is_test_article(article):
            log.info(f"Skipping test article: {article.get('title', '')[:50]}")
            update_article_status(article_id, 'posted')
            skipped += 1
            continue

        # Skip articles with no real content
        if not article.get('content') or len(str(article.get('content', ''))) < 50:
            log.info(f"Skipping empty article {article_id}")
            update_article_status(article_id, 'failed')
            skipped += 1
            continue

        attempted += 1

        try:
            # Rephrase
            rephrased = rephrase(
                article.get('title', ''),
                article.get('content', '')
            )
            update_article_status(article_id, 'classified', rephrased)

            # Format
            message = format_message({**article, 'rephrased_content': rephrased})

            # Route to correct channel based on source
            target_channels = get_target_channels(article, channels)

            if not target_channels:
                log.warning(f"No target channel for article {article_id}")
                update_article_status(article_id, 'failed')
                failed += 1
                continue

            article_success = True

            for channel in target_channels:
                chat_id = channel['telegram_chat_id']
                channel_id = channel['id']

                # Deduplication check
                if has_been_posted_to_channel(article_id, channel_id):
                    log.info(f"Already posted article {article_id} to {channel['name']} - skip")
                    continue

                post_success = False
                last_result = {"success": False, "error_type": None, "error_message": None, "retry_after": None}

                for attempt in range(MAX_RETRY_ATTEMPTS):
                    result = post_to_telegram(message, chat_id)
                    last_result = result

                    if result["success"]:
                        post_success = True
                        log.info(f"Posted article {article_id} -> '{channel['name']}'")
                        break

                    err_type = result["error_type"]
                    err_msg = result["error_message"]
                    retry_after = result.get("retry_after")

                    if err_type == "bad_request":
                        log.error(f"Bad request for article {article_id}: {err_msg} — not retrying")
                        break

                    if err_type == "forbidden":
                        log.error(f"Bot forbidden from channel '{channel['name']}' — deactivating")
                        deactivate_channel(channel_id)
                        break

                    if err_type == "flood_wait":
                        wait = retry_after or 30
                        log.warning(f"Flood wait for article {article_id}: sleeping {wait}s")
                        time.sleep(wait)
                        continue

                    if err_type == "rate_limited":
                        wait = retry_after or 30
                        log.warning(f"Rate limited for article {article_id}: sleeping {wait}s")
                        time.sleep(wait)
                        continue

                    # server_error / connection_error / unknown — normal retry
                    log.warning(f"Retry {attempt + 1}/{MAX_RETRY_ATTEMPTS} for article {article_id}: {err_type} — {err_msg[:80]}")
                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        time.sleep(2 ** attempt)

                last_error = last_result["error_message"] if not post_success else None
                log_post_attempt(
                    article_id,
                    chat_id,
                    'success' if post_success else 'failed',
                    last_error,
                    attempt + 1
                )

                if not post_success:
                    article_success = False

            final_status = 'posted' if article_success else 'failed'
            update_article_status(article_id, final_status)
            if not article_success:
                increment_pipeline_retries(article_id)

            if article_success:
                success += 1
            else:
                failed += 1

        except Exception as e:
            log.error(f"Dispatch error for article {article_id}: {e}")
            update_article_status(article_id, 'failed')
            failed += 1

    log.info(
        f"Dispatch complete: {attempted} attempted, "
        f"{success} success, {failed} failed, {skipped} skipped"
    )
    return {"attempted": attempted, "success": success, "failed": failed, "skipped": skipped}
