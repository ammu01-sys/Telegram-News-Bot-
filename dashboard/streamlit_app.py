import streamlit as st
import requests
import pandas as pd
from datetime import datetime

API_BASE = "http://localhost:8000"

st.set_page_config(
    page_title="Telegram News Bot",
    page_icon="📰",
    layout="wide",
)

# ── Sidebar navigation ────────────────────────────
page = st.sidebar.radio("Navigation", [
    "📊 Overview",
    "📰 Articles",
    "📤 Posting History",
    "📋 Logs",
    "🌐 Sources",
    "🏷️ Categories",
    "🔑 Keywords",
    "📡 Channels",
])


# ── API helpers ───────────────────────────────────
def api_get(path: str) -> list | dict:
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []


def api_post(path: str, data: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_put(path: str, data: dict):
    try:
        r = requests.put(f"{API_BASE}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_delete(path: str):
    try:
        requests.delete(f"{API_BASE}{path}", timeout=10)
        return True
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def extract_category(row: dict) -> str:
    """Safely extract category name from a joined article row."""
    cat = row.get("categories")
    if isinstance(cat, dict):
        return cat.get("name", "\u2014")
    return "\u2014"


def extract_source(row: dict) -> str:
    """Safely extract source name from a joined article row."""
    src = row.get("sources")
    if isinstance(src, dict):
        return src.get("name", "\u2014")
    return row.get("source_name", "\u2014")


# ══════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Pipeline Overview")

    articles = api_get("/articles/?limit=1000")
    total = len(articles)
    posted = sum(1 for a in articles if a.get("status") == "posted")
    unposted = total - posted

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles", total)
    col2.metric("Posted", posted)
    col3.metric("Pending / Failed", unposted)

    st.divider()
    st.subheader("Recent Articles")
    if articles:
        df = pd.DataFrame(articles[:20])
        df["category"] = df.apply(extract_category, axis=1)
        df["source"] = df.apply(extract_source, axis=1)
        display_cols = [c for c in ["title", "source", "category", "status", "scraped_at"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "title": "Title",
            "source": "Source",
            "category": "Category",
            "status": "Status",
            "scraped_at": "Scraped At",
        })
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No articles found.")

# ══════════════════════════════════════════════════
# PAGE: Articles
# ══════════════════════════════════════════════════
elif page == "📰 Articles":
    st.title("📰 All Articles")

    col1, col2, col3 = st.columns(3)
    with col1:
        source_filter = st.selectbox("Filter by source", ["All", "CoinTelegraph", "Blockworks"])
    with col2:
        posted_filter = st.selectbox("Filter by status", ["All", "posted", "classified", "failed"])
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=100)

    params = f"?limit={limit}"
    if posted_filter != "All":
        params += f"&status={posted_filter}"

    articles = api_get(f"/articles/{params}")

    if articles:
        df = pd.DataFrame(articles)
        df["category"] = df.apply(extract_category, axis=1)
        df["source"] = df.apply(extract_source, axis=1)

        # Client-side source filter
        if source_filter != "All":
            df = df[df["source"] == source_filter]

        display_cols = [c for c in ["title", "source", "category", "status", "scraped_at"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "title": "Title",
            "source": "Source",
            "category": "Category",
            "status": "Status",
            "scraped_at": "Scraped At",
        })
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} articles shown")
    else:
        st.info("No articles found.")

# ══════════════════════════════════════════════════
# PAGE: Posting History
# ══════════════════════════════════════════════════
elif page == "📤 Posting History":
    st.title("📤 Posting History")

    logs = api_get("/logs/?event_type=success&limit=200")

    if logs:
        df = pd.DataFrame(logs)
        display_cols = [c for c in ["posted_at", "status", "error", "article_id"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "posted_at": "Timestamp",
            "status": "Result",
            "error": "Error",
            "article_id": "Article ID",
        })
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(logs)} posting events")
    else:
        st.info("No posting history yet.")

# ══════════════════════════════════════════════════
# PAGE: Logs
# ══════════════════════════════════════════════════
elif page == "📋 Logs":
    st.title("📋 System Logs")

    event_types = ["ALL", "success", "failed"]
    col1, col2 = st.columns([1, 3])
    with col1:
        selected = st.selectbox("Status", event_types)
    with col2:
        limit = st.number_input("Limit", min_value=50, max_value=2000, value=300)

    params = f"?limit={limit}"
    if selected != "ALL":
        params += f"&event_type={selected}"

    logs = api_get(f"/logs/{params}")

    if logs:
        df = pd.DataFrame(logs)
        display_cols = [c for c in ["posted_at", "status", "error", "retry_count"] if c in df.columns]
        df = df[display_cols]

        event_icons = {"failed": "🔴", "success": "🟢"}
        df["status"] = df["status"].apply(
            lambda v: f"{event_icons.get(v, '⚪')} {v}"
        )
        df = df.rename(columns={
            "posted_at": "Timestamp",
            "status": "Status",
            "error": "Error",
            "retry_count": "Retries",
        })
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(logs)} log entries")
    else:
        st.info("No logs found.")

# ══════════════════════════════════════════════════
# PAGE: Sources
# ══════════════════════════════════════════════════
elif page == "🌐 Sources":
    st.title("🌐 Article Sources")
    sources = api_get("/sources/")

    if sources:
        df = pd.DataFrame(sources)
        display_cols = [c for c in ["name", "url", "is_active"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        st.caption(f"{len(sources)} sources")

# ══════════════════════════════════════════════════
# PAGE: Categories
# ══════════════════════════════════════════════════
elif page == "🏷️ Categories":
    st.title("🏷️ Categories")
    cats = api_get("/categories/")

    if cats:
        df = pd.DataFrame(cats)
        display_cols = [c for c in ["name", "description"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)

# ══════════════════════════════════════════════════
# PAGE: Keywords
# ══════════════════════════════════════════════════
elif page == "🔑 Keywords":
    st.title("🔑 Keywords")
    keywords = api_get("/keywords/")
    cats = api_get("/categories/")
    cat_map = {c["name"]: c["id"] for c in cats} if cats else {}

    if keywords:
        df = pd.DataFrame(keywords)
        df["category"] = df["categories"].apply(
            lambda x: x.get("name", "—") if isinstance(x, dict) else "—"
        )
        st.dataframe(df[["word", "category"]], use_container_width=True)
        st.caption(f"{len(keywords)} keywords")

# ══════════════════════════════════════════════════
# PAGE: Channels
# ══════════════════════════════════════════════════
elif page == "📡 Channels":
    st.title("📡 Telegram Channels")
    channels = api_get("/channels/")

    if channels:
        df = pd.DataFrame(channels)
        display_cols = [c for c in ["name", "telegram_chat_id", "is_active"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
