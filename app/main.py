from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.scheduler.jobs import create_scheduler, run_pipeline
from app.utils.config import SCRAPE_INTERVAL_MINUTES
from app.utils.logger import logger

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────
    global scheduler
    logger.info("Server starting — launching pipeline and scheduler")

    # Run immediately on boot
    run_pipeline()

    # Then schedule recurring runs
    scheduler = create_scheduler()
    scheduler.start()
    logger.info(f"Scheduler started — running every {SCRAPE_INTERVAL_MINUTES} minutes")

    yield  # app is live here

    # ── Shutdown ─────────────────────────────────────
    if scheduler:
        scheduler.shutdown()
    logger.info("Server shutting down — scheduler stopped")


app = FastAPI(title="Telegram News Bot API", lifespan=lifespan)

# Register API routes
from app.api.routes import sources, categories, keywords, channels, articles, logs
app.include_router(sources.router,    prefix="/sources",    tags=["Sources"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(keywords.router,   prefix="/keywords",   tags=["Keywords"])
app.include_router(channels.router,   prefix="/channels",   tags=["Channels"])
app.include_router(articles.router,   prefix="/articles",   tags=["Articles"])
app.include_router(logs.router,       prefix="/logs",       tags=["Logs"])


@app.get("/")
def health():
    return {"status": "running"}
