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
        return cat.get("name", "—")
    return "—"


# ══════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Pipeline Overview")

    articles = api_get("/articles/?limit=1000")
    total = len(articles)
    posted = sum(1 for a in articles if a.get("is_posted"))
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
        display_cols = [c for c in ["title", "source_name", "category", "is_posted", "published_at"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "title": "Title",
            "source_name": "Source",
            "category": "Category",
            "is_posted": "Posted",
            "published_at": "Published At",
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
        posted_filter = st.selectbox("Filter by status", ["All", "Posted", "Not Posted"])
    with col3:
        limit = st.number_input("Limit", min_value=10, max_value=500, value=100)

    params = f"?limit={limit}"
    if source_filter != "All":
        params += f"&source={source_filter}"
    if posted_filter == "Posted":
        params += "&is_posted=true"
    elif posted_filter == "Not Posted":
        params += "&is_posted=false"

    articles = api_get(f"/articles/{params}")

    if articles:
        df = pd.DataFrame(articles)
        df["category"] = df.apply(extract_category, axis=1)
        display_cols = [c for c in ["title", "source_name", "category", "is_posted", "published_at"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "title": "Title",
            "source_name": "Source",
            "category": "Category",
            "is_posted": "Posted",
            "published_at": "Published At",
        })
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(articles)} articles shown")
    else:
        st.info("No articles found.")

# ══════════════════════════════════════════════════
# PAGE: Posting History
# ══════════════════════════════════════════════════
elif page == "📤 Posting History":
    st.title("📤 Posting History")

    logs = api_get("/logs/?event_type=POST&limit=200")

    if logs:
        df = pd.DataFrame(logs)
        display_cols = [c for c in ["created_at", "message", "article_id"] if c in df.columns]
        df = df[display_cols].rename(columns={
            "created_at": "Timestamp",
            "message": "Result",
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

    event_types = ["ALL", "SCRAPE", "POST", "ERROR", "CLASSIFY", "AI"]
    col1, col2 = st.columns([1, 3])
    with col1:
        selected = st.selectbox("Event type", event_types)
    with col2:
        limit = st.number_input("Limit", min_value=50, max_value=2000, value=300)

    params = f"?limit={limit}"
    if selected != "ALL":
        params += f"&event_type={selected}"

    logs = api_get(f"/logs/{params}")

    if logs:
        df = pd.DataFrame(logs)
        display_cols = [c for c in ["created_at", "event_type", "message"] if c in df.columns]
        df = df[display_cols]

        event_icons = {"ERROR": "🔴", "POST": "🟢", "SCRAPE": "🔵", "AI": "🟡", "CLASSIFY": "🟠"}
        df["event_type"] = df["event_type"].apply(
            lambda v: f"{event_icons.get(v, '⚪')} {v}"
        )
        df = df.rename(columns={
            "created_at": "Timestamp",
            "event_type": "Event",
            "message": "Message",
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
        display_cols = [c for c in ["name", "type", "is_active"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)
        st.caption(f"{len(sources)} sources")

    st.divider()
    st.subheader("Add Source")
    with st.form("add_source"):
        name = st.text_input("Source name (e.g. CertiK, Chainalysis)")
        src_type = st.selectbox("Type", ["research", "exchange", "protocol", "media", "government", "other"])
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Add"):
            if name:
                api_post("/sources/", {"name": name, "type": src_type, "is_active": active})
                st.success(f"Source '{name}' added")
                st.rerun()
            else:
                st.warning("Source name is required.")

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

    st.divider()
    st.subheader("Add Category")
    with st.form("add_cat"):
        name = st.text_input("Category name")
        desc = st.text_input("Description (optional)")
        if st.form_submit_button("Add"):
            if name:
                api_post("/categories/", {"name": name, "description": desc or None})
                st.success(f"Category '{name}' added")
                st.rerun()
            else:
                st.warning("Category name is required.")

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

        st.subheader("Delete Keyword")
        kw_options = {
            f"{k['word']} ({k.get('categories', {}).get('name', '?') if isinstance(k.get('categories'), dict) else '?'})": k["id"]
            for k in keywords
        }
        to_delete = st.selectbox("Select keyword to delete", list(kw_options.keys()))
        if st.button("Delete selected keyword"):
            api_delete(f"/keywords/{kw_options[to_delete]}")
            st.success("Keyword deleted")
            st.rerun()

    st.divider()
    st.subheader("Add Keyword")
    with st.form("add_kw"):
        word = st.text_input("Keyword (e.g. bitcoin)")
        if cat_map:
            cat_sel = st.selectbox("Category", list(cat_map.keys()))
            if st.form_submit_button("Add"):
                if word and cat_sel:
                    api_post("/keywords/", {"word": word.lower().strip(), "category_id": cat_map[cat_sel]})
                    st.success(f"Keyword '{word}' added")
                    st.rerun()
                else:
                    st.warning("Keyword and category are required.")
        else:
            st.warning("No categories found. Add categories first.")

# ══════════════════════════════════════════════════
# PAGE: Channels
# ══════════════════════════════════════════════════
elif page == "📡 Channels":
    st.title("📡 Telegram Channels")
    channels = api_get("/channels/")

    if channels:
        df = pd.DataFrame(channels)
        display_cols = [c for c in ["name", "telegram_id", "source_filter", "is_active"] if c in df.columns]
        st.dataframe(df[display_cols], use_container_width=True)

    st.divider()
    st.subheader("Add Channel")
    with st.form("add_ch"):
        tg_id = st.text_input("Telegram Channel ID (e.g. -1001234567890 or @my_channel)")
        name = st.text_input("Display Name")
        src = st.selectbox("Source Filter", ["CoinTelegraph", "Blockworks"])
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Add"):
            if tg_id:
                api_post("/channels/", {
                    "telegram_id": tg_id,
                    "name": name or None,
                    "source_filter": src,
                    "is_active": active,
                })
                st.success(f"Channel '{tg_id}' added")
                st.rerun()
            else:
                st.warning("Telegram ID is required.")
