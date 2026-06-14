# 🖥️ PHASE 4 — FastAPI Routes & Streamlit Dashboard
> **Scope:** All CRUD API endpoints + full Streamlit admin and monitoring dashboard
> **Milestone:** 1 (task 8–9) + 2 (task 16)
> **Outcome:** A working web dashboard at localhost:8501 where the operator can manage config and monitor pipeline activity in real time
> **Estimated effort:** Day 6–7

---

## 🎯 GOAL OF THIS PHASE

Give humans a way to interact with the system without touching the database or code.

Two layers:
- **FastAPI** — the backend API that the dashboard talks to (and Swagger UI for direct testing)
- **Streamlit** — the frontend dashboard at `http://localhost:8501`

---

## ✅ TASK CHECKLIST

- [ ] 4.1 — FastAPI route: sources CRUD
- [ ] 4.2 — FastAPI route: categories CRUD
- [ ] 4.3 — FastAPI route: keywords CRUD
- [ ] 4.4 — FastAPI route: channels CRUD
- [ ] 4.5 — FastAPI route: articles (read-only, filterable)
- [ ] 4.6 — Streamlit: Overview page (metrics)
- [ ] 4.7 — Streamlit: Articles page (read-only table)
- [ ] 4.8 — Streamlit: Posting History page
- [ ] 4.9 — Streamlit: Logs page
- [ ] 4.10 — Streamlit: Sources management page
- [ ] 4.11 — Streamlit: Categories management page
- [ ] 4.12 — Streamlit: Keywords management page
- [ ] 4.13 — Streamlit: Channels management page

---

## 📄 FASTAPI ROUTES

### `app/api/routes/sources.py`
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database.client import get_client

router = APIRouter()

class SourceCreate(BaseModel):
    name:      str
    url:       str
    is_active: bool = True

@router.get("/")
def list_sources():
    db = get_client()
    return db.table("sources").select("*").execute().data

@router.post("/")
def create_source(body: SourceCreate):
    db = get_client()
    return db.table("sources").insert(body.dict()).execute().data

@router.put("/{source_id}")
def update_source(source_id: str, body: SourceCreate):
    db = get_client()
    return db.table("sources").update(body.dict()).eq("id", source_id).execute().data

@router.delete("/{source_id}")
def delete_source(source_id: str):
    db = get_client()
    db.table("sources").delete().eq("id", source_id).execute()
    return {"deleted": source_id}
```

### `app/api/routes/categories.py`
```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.database.client import get_client

router = APIRouter()

class CategoryCreate(BaseModel):
    name:        str
    description: Optional[str] = None

@router.get("/")
def list_categories():
    db = get_client()
    return db.table("categories").select("*").execute().data

@router.post("/")
def create_category(body: CategoryCreate):
    db = get_client()
    return db.table("categories").insert(body.dict()).execute().data

@router.put("/{cat_id}")
def update_category(cat_id: str, body: CategoryCreate):
    db = get_client()
    return db.table("categories").update(body.dict()).eq("id", cat_id).execute().data

@router.delete("/{cat_id}")
def delete_category(cat_id: str):
    db = get_client()
    db.table("categories").delete().eq("id", cat_id).execute()
    return {"deleted": cat_id}
```

### `app/api/routes/keywords.py`
```python
from fastapi import APIRouter
from pydantic import BaseModel
from app.database.client import get_client

router = APIRouter()

class KeywordCreate(BaseModel):
    word:        str
    category_id: str

@router.get("/")
def list_keywords():
    db = get_client()
    return db.table("keywords").select("*, categories(name)").execute().data

@router.post("/")
def create_keyword(body: KeywordCreate):
    db = get_client()
    return db.table("keywords").insert(body.dict()).execute().data

@router.delete("/{kw_id}")
def delete_keyword(kw_id: str):
    db = get_client()
    db.table("keywords").delete().eq("id", kw_id).execute()
    return {"deleted": kw_id}
```

### `app/api/routes/channels.py`
```python
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.database.client import get_client

router = APIRouter()

class ChannelCreate(BaseModel):
    telegram_id:   str
    name:          Optional[str] = None
    is_active:     bool = True
    source_filter: str            # 'CoinTelegraph' or 'Blockworks'

@router.get("/")
def list_channels():
    db = get_client()
    return db.table("channels").select("*").execute().data

@router.post("/")
def create_channel(body: ChannelCreate):
    db = get_client()
    return db.table("channels").insert(body.dict()).execute().data

@router.put("/{ch_id}")
def update_channel(ch_id: str, body: ChannelCreate):
    db = get_client()
    return db.table("channels").update(body.dict()).eq("id", ch_id).execute().data

@router.delete("/{ch_id}")
def delete_channel(ch_id: str):
    db = get_client()
    db.table("channels").delete().eq("id", ch_id).execute()
    return {"deleted": ch_id}
```

### `app/api/routes/articles.py`
```python
from fastapi import APIRouter, Query
from typing import Optional
from app.database.client import get_client

router = APIRouter()

@router.get("/")
def list_articles(
    source:    Optional[str]  = Query(None),
    category:  Optional[str]  = Query(None),
    is_posted: Optional[bool] = Query(None),
    limit:     int            = Query(50),
):
    db = get_client()
    q  = db.table("articles").select("*, categories(name)").limit(limit).order("published_at", desc=True)

    if source:
        q = q.eq("source_name", source)
    if is_posted is not None:
        q = q.eq("is_posted", is_posted)

    return q.execute().data
```

---

## 📄 FILE: `dashboard/streamlit_app.py`

```python
import streamlit as st
import requests
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

def api_get(path: str) -> list:
    try:
        r = requests.get(f"{API_BASE}{path}", timeout=5)
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return []

def api_post(path: str, data: dict):
    try:
        r = requests.post(f"{API_BASE}{path}", json=data, timeout=5)
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")

def api_delete(path: str):
    try:
        requests.delete(f"{API_BASE}{path}", timeout=5)
    except Exception as e:
        st.error(f"API error: {e}")

# ══════════════════════════════════════════════════
# PAGE: Overview
# ══════════════════════════════════════════════════
if page == "📊 Overview":
    st.title("📊 Pipeline Overview")

    articles = api_get("/articles/?limit=1000")
    logs     = api_get("/logs/") if False else []  # placeholder

    total    = len(articles)
    posted   = sum(1 for a in articles if a.get("is_posted"))
    unposted = total - posted

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Articles",   total)
    col2.metric("Posted",           posted)
    col3.metric("Pending / Failed", unposted)

    st.divider()
    st.subheader("Recent Articles")
    if articles:
        import pandas as pd
        df = pd.DataFrame(articles[:20])[["title", "source_name", "is_posted", "published_at"]]
        df.columns = ["Title", "Source", "Posted", "Published At"]
        st.dataframe(df, use_container_width=True)

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
        import pandas as pd
        df = pd.DataFrame(articles)
        cols = ["title", "source_name", "is_posted", "published_at"]
        if "categories" in df.columns:
            df["category"] = df["categories"].apply(
                lambda x: x.get("name", "—") if isinstance(x, dict) else "—"
            )
            cols = ["title", "source_name", "category", "is_posted", "published_at"]
        st.dataframe(df[cols], use_container_width=True)
        st.caption(f"{len(articles)} articles shown")
    else:
        st.info("No articles found.")

# ══════════════════════════════════════════════════
# PAGE: Posting History
# ══════════════════════════════════════════════════
elif page == "📤 Posting History":
    st.title("📤 Posting History")

    from app.database.client import get_client
    db = get_client()
    logs = db.table("logs").select("*").eq("event_type", "POST").order("created_at", desc=True).limit(200).execute().data

    if logs:
        import pandas as pd
        df = pd.DataFrame(logs)[["created_at", "message", "article_id"]]
        df.columns = ["Timestamp", "Result", "Article ID"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No posting history yet.")

# ══════════════════════════════════════════════════
# PAGE: Logs
# ══════════════════════════════════════════════════
elif page == "📋 Logs":
    st.title("📋 System Logs")

    from app.database.client import get_client
    db = get_client()

    event_types = ["ALL", "SCRAPE", "POST", "ERROR", "CLASSIFY", "AI"]
    selected = st.selectbox("Filter by event type", event_types)

    q = db.table("logs").select("*").order("created_at", desc=True).limit(300)
    if selected != "ALL":
        q = q.eq("event_type", selected)

    logs = q.execute().data

    if logs:
        import pandas as pd
        df = pd.DataFrame(logs)[["created_at", "event_type", "message"]]
        df.columns = ["Timestamp", "Event", "Message"]

        def color_event(val):
            colors = {"ERROR": "🔴", "POST": "🟢", "SCRAPE": "🔵", "AI": "🟡", "CLASSIFY": "🟠"}
            return colors.get(val, "⚪") + " " + val

        df["Event"] = df["Event"].apply(color_event)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No logs found.")

# ══════════════════════════════════════════════════
# PAGE: Sources
# ══════════════════════════════════════════════════
elif page == "🌐 Sources":
    st.title("🌐 Sources")
    sources = api_get("/sources/")

    if sources:
        import pandas as pd
        st.dataframe(
            pd.DataFrame(sources)[["name", "url", "is_active"]],
            use_container_width=True,
        )

    st.divider()
    st.subheader("Add Source")
    with st.form("add_source"):
        name   = st.text_input("Name (e.g. CoinTelegraph)")
        url    = st.text_input("URL")
        active = st.checkbox("Active", value=True)
        if st.form_submit_button("Add"):
            if name and url:
                api_post("/sources/", {"name": name, "url": url, "is_active": active})
                st.success(f"Source '{name}' added")
                st.rerun()

# ══════════════════════════════════════════════════
# PAGE: Categories
# ══════════════════════════════════════════════════
elif page == "🏷️ Categories":
    st.title("🏷️ Categories")
    cats = api_get("/categories/")

    if cats:
        import pandas as pd
        st.dataframe(
            pd.DataFrame(cats)[["name", "description"]],
            use_container_width=True,
        )

    st.divider()
    st.subheader("Add Category")
    with st.form("add_cat"):
        name = st.text_input("Category name")
        desc = st.text_input("Description (optional)")
        if st.form_submit_button("Add"):
            if name:
                api_post("/categories/", {"name": name, "description": desc})
                st.success(f"Category '{name}' added")
                st.rerun()

# ══════════════════════════════════════════════════
# PAGE: Keywords
# ══════════════════════════════════════════════════
elif page == "🔑 Keywords":
    st.title("🔑 Keywords")
    keywords = api_get("/keywords/")
    cats     = api_get("/categories/")
    cat_map  = {c["name"]: c["id"] for c in cats}

    if keywords:
        import pandas as pd
        df = pd.DataFrame(keywords)
        df["category"] = df["categories"].apply(
            lambda x: x.get("name", "—") if isinstance(x, dict) else "—"
        )
        st.dataframe(df[["word", "category"]], use_container_width=True)

        st.subheader("Delete Keyword")
        kw_options = {f"{k['word']} ({k.get('categories', {}).get('name', '?')})": k["id"] for k in keywords}
        to_delete  = st.selectbox("Select keyword to delete", list(kw_options.keys()))
        if st.button("Delete"):
            api_delete(f"/keywords/{kw_options[to_delete]}")
            st.success("Keyword deleted")
            st.rerun()

    st.divider()
    st.subheader("Add Keyword")
    with st.form("add_kw"):
        word    = st.text_input("Keyword (e.g. bitcoin)")
        cat_sel = st.selectbox("Category", list(cat_map.keys()))
        if st.form_submit_button("Add"):
            if word and cat_sel:
                api_post("/keywords/", {"word": word.lower(), "category_id": cat_map[cat_sel]})
                st.success(f"Keyword '{word}' added")
                st.rerun()

# ══════════════════════════════════════════════════
# PAGE: Channels
# ══════════════════════════════════════════════════
elif page == "📡 Channels":
    st.title("📡 Telegram Channels")
    channels = api_get("/channels/")

    if channels:
        import pandas as pd
        st.dataframe(
            pd.DataFrame(channels)[["name", "telegram_id", "source_filter", "is_active"]],
            use_container_width=True,
        )

    st.divider()
    st.subheader("Add Channel")
    with st.form("add_ch"):
        tg_id   = st.text_input("Telegram Channel ID (e.g. @my_channel)")
        name    = st.text_input("Display Name")
        src     = st.selectbox("Source Filter", ["CoinTelegraph", "Blockworks"])
        active  = st.checkbox("Active", value=True)
        if st.form_submit_button("Add"):
            if tg_id:
                api_post("/channels/", {
                    "telegram_id":   tg_id,
                    "name":          name,
                    "source_filter": src,
                    "is_active":     active,
                })
                st.success(f"Channel '{tg_id}' added")
                st.rerun()
```

---

## 🚀 HOW TO RUN BOTH SERVICES

```bash
# Terminal 1 — FastAPI backend
uvicorn app.main:app --reload --port 8000

# Terminal 2 — Streamlit dashboard
streamlit run dashboard/streamlit_app.py --server.port 8501
```

Access:
- Dashboard: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`

---

## 🚦 EXIT CRITERIA (Phase 4 is done when)

- [ ] All 5 API routes respond correctly in Swagger (`/docs`)
- [ ] Overview page shows correct article counts
- [ ] Articles table shows all stored articles with filters working
- [ ] Posting history shows POST events from logs
- [ ] System logs show all event types with color indicators
- [ ] Can add a new keyword from dashboard and it appears in DB
- [ ] Can toggle a channel active/inactive from dashboard
- [ ] Dashboard loads without errors at `http://localhost:8501`

---

## ➡️ NEXT PHASE

Once this phase is done → move to **PHASE 5: Testing & End-to-End Validation**
