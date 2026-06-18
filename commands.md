# Commands to Run the Telegram News Bot

## Prerequisites
```powershell
cd "c:\Users\home\Desktop\PROJECTS\Telegram News Bot"
.venv\Scripts\activate
pip install -r requirements.txt
```

## Telegram Web Login (One-Time Setup)
Required before the bot can post via Selenium. Chrome opens, scan QR with Telegram mobile app.
```powershell
python run.py --login-telegram
```

## Run Everything (Single Command)
`run.py` starts the FastAPI backend, scheduler, and Streamlit dashboard together:
```powershell
cd "c:\Users\home\Desktop\PROJECTS\Telegram News Bot"
.venv\Scripts\activate
python run.py
```

### Flags
| Flag | Description |
|---|---|
| `--run-now` | Run the scrape, classify, dispatch pipeline immediately on startup |
| `--skip-telegram-check` | Skip the Telegram Bot API connectivity check at startup |
| `--login-telegram` | Launch Chrome for one-time Telegram Web QR login |

### Examples
```powershell
# Run pipeline immediately after startup (skip bot check if using Selenium)
python run.py --run-now --skip-telegram-check

# Run with Bot API connectivity check
python run.py --run-now
```

### Endpoints (after startup)
| Service | URL |
|---|---|
| API docs (Swagger) | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |
| Streamlit dashboard | http://localhost:8501 |

## Run Components Separately (Optional)

### Backend only (FastAPI + Scheduler)
```powershell
.venv\Scripts\activate
uvicorn telegram_news_bot.api.main:app --reload --port 8000
```

### Dashboard only (Streamlit)
Open a second terminal:
```powershell
.venv\Scripts\activate
streamlit run dashboard/streamlit_app.py --server.port 8501
```

## Database Setup (One-Time)
Run in Supabase SQL Editor (in order):
1. `migrations/schema.sql` — creates tables + seeds categories, sources, channels
2. `migrations/seed.sql` — seeds keywords

## Disable Selenium (Use Bot API Only)
Add to `.env`:
```
TELEGRAM_WEB_ENABLED=false
```

> Press `Ctrl+C` to stop the bot gracefully.
