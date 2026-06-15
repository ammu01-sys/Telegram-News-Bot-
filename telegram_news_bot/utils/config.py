import os
from pathlib import Path
from dotenv import load_dotenv

# Determine project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env if it exists, otherwise fallback to default loading
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()

# Required environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISABLE_REPHRASE = bool(os.getenv("DISABLE_REPHRASE"))

# Optional proxy for Telegram API (e.g. http://127.0.0.1:8080 or socks5://127.0.0.1:1080)
TELEGRAM_PROXY = os.getenv("TELEGRAM_PROXY") or os.getenv("HTTPS_PROXY") or os.getenv("ALL_PROXY")

# Convert to appropriate types with defaults
SCRAPE_INTERVAL_MINUTES = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "60"))
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))
MAX_PIPELINE_RETRIES = int(os.getenv("MAX_PIPELINE_RETRIES", "3"))

# Validate mandatory values
missing = []
if not SUPABASE_URL:
    missing.append("SUPABASE_URL")
if not SUPABASE_KEY:
    missing.append("SUPABASE_KEY")
if not TELEGRAM_BOT_TOKEN:
    missing.append("TELEGRAM_BOT_TOKEN")
if missing:
    raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
