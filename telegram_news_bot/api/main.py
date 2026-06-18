from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import sources, categories, keywords, channels, articles, logs

app = FastAPI(title="Telegram News Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@app.get("/")
def root():
    return {"message": "Telegram News Bot API", "docs": "/docs"}


app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(keywords.router, prefix="/keywords", tags=["keywords"])
app.include_router(channels.router, prefix="/channels", tags=["channels"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
