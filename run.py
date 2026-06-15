import sys, os, signal, subprocess, threading, time, argparse
from pathlib import Path

import requests

from telegram_news_bot.utils.logger import get_logger
from telegram_news_bot.database.client import supabase
from telegram_news_bot.scheduler.jobs import start_scheduler, stop_scheduler, run_pipeline
from telegram_news_bot.utils.config import TELEGRAM_BOT_TOKEN, TELEGRAM_PROXY
import uvicorn
from uvicorn import Config, Server

log = get_logger("run")
_streamlit_proc = None


def run_streamlit():
    global _streamlit_proc
    try:
        dashboard_path = Path(__file__).resolve().parent / "telegram_news_bot" / "dashboard" / "app.py"
        _streamlit_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", str(dashboard_path),
             "--server.port", "8501", "--server.headless", "true"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        log.info(f"Streamlit dashboard started on http://localhost:8501 (PID {_streamlit_proc.pid})")
    except Exception as e:
        log.warning(f"Failed to start Streamlit dashboard: {e}")


def handle_shutdown(sig, frame):
    log.info("Shutting down...")
    global _streamlit_proc
    if _streamlit_proc:
        _streamlit_proc.terminate()
        _streamlit_proc.wait(timeout=5)
    stop_scheduler()
    sys.exit(0)


def run_api():
    from telegram_news_bot.api.main import app
    config = Config(app, host="0.0.0.0", port=8000, log_level="warning")
    Server(config).run()


def check_telegram_connectivity() -> bool:
    """Test connectivity to Telegram API and warn if unreachable."""
    try:
        proxies = {"https": TELEGRAM_PROXY} if TELEGRAM_PROXY else None
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        resp = requests.get(url, proxies=proxies, timeout=15)
        if resp.status_code == 200:
            bot_name = resp.json().get("result", {}).get("first_name", "unknown")
            log.info(f"Telegram API OK — bot @{resp.json()['result']['username']}")
            return True
        else:
            log.error(f"Telegram API returned {resp.status_code}: {resp.text}")
            return False
    except requests.exceptions.ConnectTimeout:
        log.error("Cannot reach Telegram API — connection timed out after 15s.")
        log.error("Telegram is blocked on this network. Quick fixes:")
        log.error("  1. Install Cloudflare WARP (free): https://1.1.1.1")
        log.error("  2. Install ProtonVPN (free): https://protonvpn.com/download")
        log.error("  3. Or set TELEGRAM_PROXY in .env to a working HTTP/SOCKS proxy")
        return False
    except requests.exceptions.ConnectionError as e:
        log.error(f"Cannot reach Telegram API — connection failed: {e}")
        log.error("Telegram is blocked on this network. Quick fixes:")
        log.error("  1. Install Cloudflare WARP (free): https://1.1.1.1")
        log.error("  2. Install ProtonVPN (free): https://protonvpn.com/download")
        return False
    except Exception as e:
        log.warning(f"Telegram connectivity check failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-now", action="store_true")
    parser.add_argument("--skip-telegram-check", action="store_true", help="Skip Telegram connectivity check")
    args = parser.parse_args()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        supabase.table("sources").select("id").limit(1).execute()
        log.info("Database OK")
    except Exception as e:
        log.error(f"Database failed: {e}")
        sys.exit(1)

    if not args.skip_telegram_check:
        check_telegram_connectivity()

    start_scheduler()

    threading.Thread(target=run_api, daemon=True).start()
    threading.Thread(target=run_streamlit, daemon=True).start()
    log.info("Bot running. Ctrl+C to stop.")

    if args.run_now:
        run_pipeline()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        handle_shutdown(None, None)
