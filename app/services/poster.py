import time
import requests
from app.utils.config import TELEGRAM_BOT_TOKEN
from app.utils.logger import logger
from app.database.queries import insert_log

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


def post_to_telegram(article: dict, channel_id: str, summary: str) -> bool:
    """
    Post article to a specific Telegram channel.
    Retries 3 times on failure.
    Returns True on success, False after all retries fail.
    """
    message = _format_message(article["title"], summary, article["url"])

    for attempt in range(1, 4):  # 3 attempts
        try:
            resp = requests.post(
                TELEGRAM_API,
                json={
                    "chat_id":    channel_id,
                    "text":       message,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("ok"):
                logger.info(f"Posted to {channel_id}: {article['title'][:50]}")
                return True
            else:
                raise Exception(f"Telegram API error: {data}")

        except Exception as e:
            logger.warning(f"Post attempt {attempt}/3 failed for {channel_id}: {e}")
            if attempt < 3:
                time.sleep(5)

    # All 3 attempts failed
    insert_log(
        "ERROR",
        f"POST FAILED after 3 retries — channel: {channel_id} — reason: final attempt failed",
        article.get("id"),
    )
    return False


def _format_message(title: str, summary: str, url: str) -> str:
    return f"📰 <b>{title}</b>\n\n{summary}\n\n🔗 {url}"
