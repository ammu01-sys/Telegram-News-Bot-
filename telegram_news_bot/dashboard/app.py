import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys, os, time, io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from telegram_news_bot.database.queries import (
    get_posting_stats, get_all_articles, get_posting_history,
    get_all_sources, get_all_categories_with_keywords,
    get_all_channels, toggle_source_active, toggle_channel_active,
    create_keyword, delete_record
)

st.set_page_config(
    page_title="NewsBot Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css');

*, *::before, *::after {
    font-family: 'Inter', sans-serif !important;
    box-sizing: border-box;
}

.stApp {
    background: #070B14 !important;
}
[data-testid="stAppViewContainer"] {
    background: #070B14;
    position: relative;
    overflow: auto !important;
}
.stApp {
    overflow: auto !important;
}
[data-testid="stAppViewContainer"] > .main {
    overflow: auto !important;
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stHeader"] { display: none; }

/* ── ANIMATED BACKGROUND ── */
@keyframes float {
    0%, 100% { transform: translateY(0px) rotate(0deg); }
    33% { transform: translateY(-20px) rotate(1deg); }
    66% { transform: translateY(10px) rotate(-1deg); }
}
@keyframes pulse-glow {
    0%, 100% { opacity: 0.3; transform: scale(1); }
    50% { opacity: 0.6; transform: scale(1.05); }
}
@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes count-up {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes slide-in {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes border-dance {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.bg-orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
}
.bg-orb-1 {
    width: 600px; height: 600px;
    background: radial-gradient(circle, rgba(0,212,255,0.08) 0%, transparent 70%);
    top: -200px; right: -200px;
    animation: float 12s ease-in-out infinite;
}
.bg-orb-2 {
    width: 500px; height: 500px;
    background: radial-gradient(circle, rgba(123,47,190,0.06) 0%, transparent 70%);
    bottom: -150px; left: -150px;
    animation: float 15s ease-in-out infinite reverse;
}
.bg-orb-3 {
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,255,136,0.04) 0%, transparent 70%);
    top: 40%; left: 50%;
    animation: pulse-glow 8s ease-in-out infinite;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #00D4FF, #7B2FBE); border-radius: 3px; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(13,17,23,0.95) 0%, rgba(7,11,20,0.98) 100%) !important;
    border-right: 1px solid rgba(0,212,255,0.1) !important;
    min-width: 270px !important;
    max-width: 270px !important;
    backdrop-filter: blur(20px) !important;
}
[data-testid="stSidebar"] * { color: #FFFFFF !important; }
section[data-testid="stSidebar"] > div { padding: 0 !important; }

/* ── METRICS ── */
[data-testid="metric-container"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 20px !important;
    padding: 24px !important;
    backdrop-filter: blur(20px);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00D4FF, #7B2FBE, #FF4B4B, #FFB800, #00D4FF);
    background-size: 300% 100%;
    animation: border-dance 4s linear infinite;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-4px) !important;
    border-color: rgba(0,212,255,0.3) !important;
    box-shadow: 0 20px 60px rgba(0,212,255,0.15) !important;
}
[data-testid="stMetricLabel"] p {
    color: #6B7280 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 2px !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 36px !important;
    font-weight: 900 !important;
    line-height: 1.1 !important;
}

/* ── BUTTONS ── */
.stButton > button {
    background: linear-gradient(135deg, #00D4FF 0%, #7B2FBE 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    width: 100% !important;
    position: relative !important;
    overflow: hidden !important;
}
.stButton > button::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.1) 45%, transparent 50%);
    background-size: 200% 200%;
    animation: shimmer 3s infinite;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 35px rgba(0,212,255,0.5) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] {
    border-radius: 20px !important;
    overflow: hidden !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    background: rgba(255,255,255,0.02) !important;
    backdrop-filter: blur(10px);
}
.dvn-scroller { background: transparent !important; }
.dvg-table-row:nth-child(even) { background: rgba(255,255,255,0.02) !important; }
.dvg-table-row:hover { background: rgba(0,212,255,0.05) !important; }

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    transition: all 0.2s ease;
}
[data-testid="stSelectbox"] > div > div:hover {
    border-color: rgba(0,212,255,0.4) !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.1) !important;
}

/* ── RADIO ── */
[data-testid="stRadio"] div[role="radiogroup"] {
    gap: 4px !important;
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stRadio"] div[role="radiogroup"] label {
    background: transparent !important;
    border-radius: 10px !important;
    padding: 11px 16px !important;
    transition: all 0.2s ease !important;
    color: #6B7280 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border: 1px solid transparent !important;
    cursor: pointer !important;
}
[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background: rgba(0,212,255,0.08) !important;
    color: #00D4FF !important;
    border-color: rgba(0,212,255,0.15) !important;
}
[data-testid="stRadio"] div[role="radiogroup"] label[data-checked="true"] {
    background: rgba(0,212,255,0.12) !important;
    color: #00D4FF !important;
    border-color: rgba(0,212,255,0.3) !important;
    font-weight: 700 !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.08) !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: #00D4FF !important; }

/* ── HR ── */
hr { border: none !important; border-top: 1px solid rgba(255,255,255,0.05) !important; margin: 16px 0 !important; }

/* ── PROGRESS ── */
.stProgress > div > div { background: linear-gradient(90deg, #00D4FF, #7B2FBE) !important; border-radius: 4px !important; }

/* ── SUCCESS/ERROR/INFO ── */
.stSuccess { background: rgba(0,255,136,0.1) !important; border: 1px solid rgba(0,255,136,0.3) !important; border-radius: 12px !important; color: #00FF88 !important; backdrop-filter: blur(10px); }
.stError { background: rgba(255,75,75,0.1) !important; border: 1px solid rgba(255,75,75,0.3) !important; border-radius: 12px !important; backdrop-filter: blur(10px); }
.stInfo { background: rgba(0,212,255,0.1) !important; border: 1px solid rgba(0,212,255,0.3) !important; border-radius: 12px !important; color: #00D4FF !important; backdrop-filter: blur(10px); }

/* ── MARKDOWN CONTAINERS ── */
.element-container:has(.glow-card),
.element-container:has(.hero-section) {
    animation: slide-in 0.6s ease forwards;
}
</style>

<div class="bg-orb bg-orb-1"></div>
<div class="bg-orb bg-orb-2"></div>
<div class="bg-orb bg-orb-3"></div>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════

def badge(text, color="#00D4FF"):
    bg = color + "22"
    return f'<span style="background:{bg};color:{color};padding:3px 10px;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:0.5px;border:1px solid {color}33;backdrop-filter:blur(4px);">{text.upper()}</span>'

STATUS_COLORS = {
    "posted": "#00FF88", "success": "#00FF88", "active": "#00FF88",
    "classified": "#00D4FF", "info": "#00D4FF",
    "failed": "#FF4B4B", "error": "#FF4B4B", "inactive": "#FF4B4B",
    "raw": "#8892A4",
}
STATUS_ICONS = {
    "posted": "✅", "success": "✅", "active": "🟢",
    "classified": "🔵", "info": "ℹ️",
    "failed": "❌", "error": "⚠️", "inactive": "⏸",
    "raw": "⚪",
}

def status_badge(status):
    s = str(status).lower()
    color = STATUS_COLORS.get(s, "#8892A4")
    icon = STATUS_ICONS.get(s, "📄")
    return f'<span style="background:{color}15;color:{color};padding:4px 12px;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:0.5px;border:1px solid {color}30;backdrop-filter:blur(4px);">{icon} {status}</span>'

def glow_card(icon, label, value, color, subtitle="", delay="0s"):
    return f"""<div class="glow-card" style="background:linear-gradient(135deg,{color}10 0%,{color}04 100%);border:1px solid {color}20;border-radius:20px;padding:26px 22px;position:relative;overflow:hidden;transition:all 0.4s cubic-bezier(0.175,0.885,0.32,1.275);cursor:default;backdrop-filter:blur(10px);animation:slide-in 0.5s ease {delay} forwards;opacity:0;">
<div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,{color},{color}44);"></div>
<div style="position:absolute;bottom:-30px;right:-20px;font-size:90px;opacity:0.05;line-height:1;">{icon}</div>
<div style="font-size:26px;margin-bottom:10px;">{icon}</div>
<div style="font-size:10px;color:#6B7280;font-weight:700;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">{label}</div>
<div style="font-size:44px;font-weight:900;color:{color};line-height:1;margin-bottom:6px;text-shadow:0 0 30px {color}33;">{value}</div>
{f'<div style="font-size:11px;color:#6B7280;margin-top:8px;">{subtitle}</div>' if subtitle else ''}
<div style="position:absolute;inset:0;border-radius:20px;border:1px solid {color}10;pointer-events:none;"></div>
</div>"""

def page_hero(icon, title, subtitle, color1="#00D4FF", color2="#7B2FBE"):
    return f"""<div class="hero-section" style="background:linear-gradient(135deg,{color1}0D 0%,{color2}0D 100%);border:1px solid {color1}15;border-radius:24px;padding:32px 36px;margin-bottom:32px;position:relative;overflow:hidden;backdrop-filter:blur(10px);">
<div style="position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,{color1},{color2},#FF4B4B,#FFB800,{color1});background-size:300% 100%;animation:border-dance 6s linear infinite;"></div>
<div style="position:absolute;top:-40px;right:40px;font-size:160px;opacity:0.03;">{icon}</div>
<div style="position:absolute;inset:0;border-radius:24px;border:1px solid {color1}08;pointer-events:none;"></div>
<div style="font-size:44px;margin-bottom:12px;filter:drop-shadow(0 0 20px {color1}44);">{icon}</div>
<div style="font-size:30px;font-weight:900;color:#FFFFFF;margin-bottom:8px;letter-spacing:-0.5px;">{title}</div>
<div style="font-size:14px;color:#6B7280;font-weight:400;">{subtitle}</div>
</div>"""

def section_title(text, subtitle=""):
    return f"""<div style="margin:28px 0 16px 0;animation:slide-in 0.4s ease forwards;">
<div style="display:flex;align-items:center;gap:12px;margin-bottom:{'6px' if subtitle else '0'};">
<div style="width:3px;height:20px;background:linear-gradient(180deg,#00D4FF,#7B2FBE);border-radius:2px;flex-shrink:0;"></div>
<div style="font-size:15px;font-weight:700;color:#FFFFFF;letter-spacing:-0.2px;">{text}</div>
</div>
{f'<div style="font-size:12px;color:#6B7280;padding-left:15px;">{subtitle}</div>' if subtitle else ''}
</div>"""

def article_row(a, delay="0s"):
    status = a.get("status", "raw")
    color = STATUS_COLORS.get(status, "#8892A4")
    src = a.get("sources", {})
    src_name = src.get("name", "") if isinstance(src, dict) else str(a.get("source_name", ""))
    title = str(a.get("title", "No title"))[:72]
    scraped = str(a.get("scraped_at", ""))[:16]
    return f"""<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);border-left:3px solid {color};border-radius:12px;padding:13px 16px;margin:5px 0;transition:all 0.3s ease;animation:slide-in 0.4s ease {delay} forwards;opacity:0;backdrop-filter:blur(4px);" onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'">
<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
<div style="flex:1;min-width:0;">
<div style="font-size:13px;font-weight:600;color:#E2E8F0;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{title}</div>
<div style="font-size:11px;color:#6B7280;display:flex;gap:12px;">
<span>📡 {src_name}</span>
<span>🕐 {scraped}</span>
</div>
</div>
<div style="flex-shrink:0;">{status_badge(status)}</div>
</div>
</div>"""

def progress_bar(label, count, total, color):
    pct = (count / total * 100) if total > 0 else 0
    return f"""<div style="margin:10px 0;animation:slide-in 0.4s ease forwards;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
<span style="font-size:12px;color:#CBD5E0;font-weight:500;">{label}</span>
<div style="display:flex;align-items:center;gap:8px;">
<span style="font-size:13px;color:{color};font-weight:700;">{count}</span>
<span style="font-size:10px;color:#4A5568;background:rgba(255,255,255,0.05);padding:2px 7px;border-radius:10px;border:1px solid rgba(255,255,255,0.05);">{pct:.0f}%</span>
</div>
</div>
<div style="background:rgba(255,255,255,0.05);border-radius:6px;height:7px;overflow:hidden;border:1px solid rgba(255,255,255,0.03);">
<div style="background:linear-gradient(90deg,{color},{color}66);width:{pct}%;height:7px;border-radius:6px;transition:width 1.5s cubic-bezier(0.175,0.885,0.32,1.275);box-shadow:0 0 10px {color}44;"></div>
</div>
</div>"""

def source_card(source):
    is_active = source.get('is_active', True)
    color = "#00FF88" if is_active else "#FF4B4B"
    name = source.get('name', '')
    url = source.get('url', '')
    return f"""<div style="background:rgba(255,255,255,0.02);border:1px solid {color}15;border-left:3px solid {color};border-radius:14px;padding:16px 20px;margin:8px 0;transition:all 0.3s ease;backdrop-filter:blur(4px);" onmouseover="this.style.borderColor='{color}40';this.style.transform='translateX(4px)'" onmouseout="this.style.borderColor='{color}15';this.style.transform='translateX(0)'">
<div style="display:flex;justify-content:space-between;align-items:center;">
<div>
<div style="font-size:15px;font-weight:700;color:#FFFFFF;margin-bottom:4px;">🌐 {name}</div>
<div style="font-size:12px;color:#6B7280;font-family:monospace;">{url}</div>
</div>
{status_badge('active' if is_active else 'inactive')}
</div>
</div>"""

def channel_card(channel):
    is_active = channel.get('is_active', True)
    color = "#00D4FF" if is_active else "#FF4B4B"
    cat = channel.get('categories')
    cat_name = cat.get('name', 'All Categories') if isinstance(cat, dict) else 'All Categories'
    return f"""<div style="background:rgba(255,255,255,0.02);border:1px solid {color}15;border-left:3px solid {color};border-radius:14px;padding:18px 20px;margin:8px 0;transition:all 0.3s ease;backdrop-filter:blur(4px);" onmouseover="this.style.borderColor='{color}40';this.style.transform='translateX(4px)'" onmouseout="this.style.borderColor='{color}15';this.style.transform='translateX(0)'">
<div style="display:flex;justify-content:space-between;align-items:flex-start;">
<div>
<div style="font-size:15px;font-weight:700;color:#FFFFFF;margin-bottom:6px;">📡 {channel.get('name','')}</div>
<div style="font-size:12px;color:#6B7280;font-family:monospace;margin-bottom:6px;">{channel.get('telegram_chat_id','')}</div>
<div style="font-size:11px;background:rgba(255,184,0,0.08);color:#FFB800;padding:3px 10px;border-radius:20px;display:inline-block;border:1px solid rgba(255,184,0,0.15);">🏷️ {cat_name}</div>
</div>
{status_badge('active' if is_active else 'inactive')}
</div>
</div>"""

def kw_chip(word, color):
    return f'<span style="background:{color}12;color:{color};border:1px solid {color}25;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;margin:3px;display:inline-block;transition:all 0.2s ease;backdrop-filter:blur(4px);" onmouseover="this.style.background=\'{color}25\'" onmouseout="this.style.background=\'{color}12\'">{word}</span>'

def timeline_item(log, delay="0s"):
    status = log.get('status', '')
    color = STATUS_COLORS.get(status, "#8892A4")
    icon = STATUS_ICONS.get(status, "📄")
    title = str(log.get('title', ''))[:60]
    channel = log.get('channel', '')
    time_str = str(log.get('posted_at', ''))[:16]
    cat = log.get('categories', {})
    cat_name = cat.get('name', '') if isinstance(cat, dict) else ''
    return f"""<div style="display:flex;gap:16px;padding:12px 0;border-left:2px solid {color}30;padding-left:20px;margin-left:8px;position:relative;animation:slide-in 0.4s ease {delay} forwards;opacity:0;">
<div style="position:absolute;left:-7px;top:16px;width:12px;height:12px;border-radius:50%;background:{color};border:2px solid #070B14;box-shadow:0 0 10px {color}44;"></div>
<div style="flex:1;">
<div style="font-size:12px;font-weight:600;color:#E2E8F0;margin-bottom:4px;">{icon} {title}</div>
<div style="font-size:11px;color:#6B7280;display:flex;gap:12px;">
<span>📡 {channel}</span>
<span>🕐 {time_str}</span>
</div>
</div>
<div style="flex-shrink:0;">{status_badge(status)}</div>
</div>"""

# ═══════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(0,212,255,0.12) 0%, rgba(123,47,190,0.12) 100%);
        border-bottom: 1px solid rgba(0,212,255,0.1);
        padding: 28px 20px 24px;
        text-align: center;
        margin: -1rem -1rem 0 -1rem;
        position: relative;
        overflow: hidden;
    ">
        <div style="position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00D4FF,#7B2FBE,transparent);"></div>
        <div style="font-size:52px;margin-bottom:8px;filter:drop-shadow(0 0 25px rgba(0,212,255,0.5));animation:pulse-glow 3s ease-in-out infinite;">🚀</div>
        <div style="font-size:22px;font-weight:900;background:linear-gradient(135deg,#00D4FF,#7B2FBE);-webkit-background-clip:text;-webkit-text-fill-color:transparent;letter-spacing:-0.5px;">
            NewsBot Pro
        </div>
        <div style="font-size:10px;color:#4A5568;letter-spacing:3px;text-transform:uppercase;margin-top:4px;font-weight:600;">
            v2.0 · Automation Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:9px;color:#4A5568;text-transform:uppercase;letter-spacing:2.5px;padding:0 8px;margin-bottom:6px;font-weight:700;">
        <i class="fas fa-compass" style="margin-right:6px;"></i> Main Menu
    </div>
    """, unsafe_allow_html=True)

    if "nav_page" not in st.session_state:
        st.session_state.nav_page = "🏠  Overview"

    nav_items = [
        "🏠  Overview", "📰  Articles", "📬  Post History",
        "🌐  Sources", "🏷️  Categories", "📡  Channels"
    ]
    for item in nav_items:
        active = item == st.session_state.nav_page
        if st.button(
            item,
            key=f"nav_{item}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state.nav_page = item
            st.rerun()

    page = st.session_state.nav_page

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div style="font-size:9px;color:#4A5568;text-transform:uppercase;letter-spacing:2.5px;padding:0 8px;margin-bottom:10px;font-weight:700;">
        <i class="fas fa-bolt" style="margin-right:6px;"></i> Actions
    </div>
    """, unsafe_allow_html=True)

    if st.button("▶  Run Pipeline Now", use_container_width=True):
        with st.spinner("Running pipeline..."):
            try:
                from telegram_news_bot.scheduler.jobs import run_pipeline
                run_pipeline()
                st.toast("✅ Pipeline complete!", icon="✅")
            except Exception as e:
                st.toast(f"❌ Error: {e}", icon="❌")

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col_b:
        auto_refresh = st.toggle("Auto", value=False, key="auto_refresh_toggle")
        if auto_refresh:
            if "auto_timer" not in st.session_state:
                st.session_state.auto_timer = time.time()
            if time.time() - st.session_state.auto_timer >= 15:
                st.session_state.auto_timer = time.time()
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)

    now = datetime.now()
    st.markdown(f"""
    <div style="
        background: rgba(255,255,255,0.02);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin: 0 4px;
        backdrop-filter: blur(10px);
    ">
        <div style="font-size:9px;color:#4A5568;text-transform:uppercase;letter-spacing:2px;font-weight:700;margin-bottom:8px;">
            <i class="far fa-clock" style="margin-right:4px;"></i> Last Refresh
        </div>
        <div style="font-size:26px;font-weight:800;color:#00D4FF;letter-spacing:2px;font-variant-numeric:tabular-nums;">{now.strftime('%H:%M:%S')}</div>
        <div style="font-size:11px;color:#4A5568;margin-top:4px;">{now.strftime('%d %B %Y')}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="padding: 0 4px;">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">
            <div style="width:8px;height:8px;background:#00FF88;border-radius:50%;box-shadow:0 0 8px #00FF88;flex-shrink:0;animation:pulse-glow 2s ease-in-out infinite;"></div>
            <div style="font-size:12px;color:#8892A4;"><i class="fas fa-database" style="margin-right:4px;color:#4A5568;"></i> Database Connected</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:8px;height:8px;background:#00FF88;border-radius:50%;box-shadow:0 0 8px #00FF88;flex-shrink:0;animation:pulse-glow 2s ease-in-out infinite 0.5s;"></div>
            <div style="font-size:12px;color:#8892A4;"><i class="fas fa-clock" style="margin-right:4px;color:#4A5568;"></i> Scheduler Running</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════
# OVERVIEW
# ═══════════════════════════════════════════════════

if "Overview" in page:
    st.markdown(page_hero("📊", "Dashboard Overview", "Real-time monitoring of your Telegram news automation pipeline"), unsafe_allow_html=True)

    try:
        stats = get_posting_stats()
    except:
        stats = {"total_articles": 0, "posted_today": 0, "failed_today": 0, "active_sources": 0}

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(glow_card("📄", "Total Articles", stats.get("total_articles", 0), "#00D4FF", subtitle="In database", delay="0.1s"), unsafe_allow_html=True)
    with c2:
        st.markdown(glow_card("✅", "Posted Today", stats.get("posted_today", 0), "#00FF88", subtitle="Successfully sent", delay="0.2s"), unsafe_allow_html=True)
    with c3:
        st.markdown(glow_card("❌", "Failed Today", stats.get("failed_today", 0), "#FF4B4B", subtitle="Need attention", delay="0.3s"), unsafe_allow_html=True)
    with c4:
        st.markdown(glow_card("🌐", "Active Sources", stats.get("active_sources", 0), "#FFB800", subtitle="Scraping now", delay="0.4s"), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(section_title("📰 Latest Articles", "Most recently scraped content"), unsafe_allow_html=True)
        try:
            articles = get_all_articles(10)
            if articles:
                for i, a in enumerate(articles):
                    title = str(a.get("title", "No title"))[:72]
                    src = a.get("sources", {})
                    src_name = src.get("name", "") if isinstance(src, dict) else ""
                    status = a.get("status", "raw")
                    content = str(a.get("content", "") or "")[:300]
                    scraped = str(a.get("scraped_at", ""))[:16]
                    icon = STATUS_ICONS.get(status, "📄")
                    with st.expander(f"{icon} {title}", expanded=False):
                        cols = st.columns([3, 1])
                        cols[0].markdown(f"**Source:** {src_name}  |  **Scraped:** {scraped}")
                        if content:
                            cols[0].caption(content)
                        cols[1].markdown(f"<div style='text-align:right'>{status_badge(status)}</div>", unsafe_allow_html=True)
            else:
                st.info("No articles yet. Click 'Run Pipeline Now' to start scraping.")
        except Exception as e:
            st.error(str(e))

    with col2:
        st.markdown(section_title("📈 Pipeline Health", "Article status breakdown"), unsafe_allow_html=True)
        try:
            all_arts = get_all_articles(1000)
            if all_arts:
                df = pd.DataFrame(all_arts)
                sc = df['status'].value_counts().to_dict() if 'status' in df.columns else {}
                total = sum(sc.values()) or 1

                # Donut chart with Plotly
                labels = []
                values = []
                colors = []
                for k, lbl, col in [("posted","Posted","#00FF88"),("classified","Classified","#00D4FF"),("failed","Failed","#FF4B4B"),("raw","Raw","#8892A4")]:
                    if sc.get(k, 0) > 0:
                        labels.append(lbl)
                        values.append(sc.get(k, 0))
                        colors.append(col)

                if values:
                    fig = go.Figure(data=[go.Pie(
                        labels=labels, values=values,
                        hole=0.65,
                        marker=dict(colors=colors, line=dict(color='#070B14', width=3)),
                        textinfo='label+percent',
                        textfont=dict(color='#CBD5E0', size=11, family='Inter'),
                        hoverinfo='label+value',
                        hovertemplate='<b>%{label}</b>: %{value} articles<extra></extra>',
                    )])
                    fig.update_layout(
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(t=0, b=0, l=0, r=0),
                        height=220,
                        showlegend=False,
                        annotations=[dict(
                            text=f"<b>{total}</b>",
                            x=0.5, y=0.5,
                            font=dict(size=28, color='#FFFFFF', family='Inter'),
                            showarrow=False
                        )]
                    )
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

                # Progress bars
                configs = [
                    ("posted",     "✅ Posted",     "#00FF88"),
                    ("classified", "🔵 Classified", "#00D4FF"),
                    ("failed",     "❌ Failed",     "#FF4B4B"),
                    ("raw",        "⚪ Raw",        "#8892A4"),
                ]
                for k, lbl, col in configs:
                    st.markdown(progress_bar(lbl, sc.get(k,0), total, col), unsafe_allow_html=True)

                # Source breakdown
                st.markdown(section_title("📡 By Source"), unsafe_allow_html=True)
                df['src_name'] = df['sources'].apply(lambda x: x.get('name','Unknown') if isinstance(x, dict) else 'Unknown')
                src_counts = df['src_name'].value_counts().to_dict()
                for src, cnt in src_counts.items():
                    pct = cnt / total * 100
                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.04);transition:all 0.2s ease;" onmouseover="this.style.background='rgba(255,255,255,0.02)'" onmouseout="this.style.background='transparent'">
                        <span style="font-size:13px;color:#CBD5E0;font-weight:500;">📡 {src}</span>
                        <div style="display:flex;align-items:center;gap:8px;">
                            <div style="width:60px;background:rgba(255,255,255,0.05);border-radius:4px;height:5px;overflow:hidden;">
                                <div style="background:linear-gradient(90deg,#00D4FF,#7B2FBE);width:{pct}%;height:5px;border-radius:4px;transition:width 1s ease;"></div>
                            </div>
                            <span style="font-size:13px;color:#00D4FF;font-weight:700;width:30px;text-align:right;">{cnt}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        except Exception as e:
            st.error(str(e))


# ═══════════════════════════════════════════════════
# ARTICLES
# ═══════════════════════════════════════════════════

elif "Articles" in page:
    st.markdown(page_hero("📰", "Articles", "All scraped and processed news articles", "#00D4FF", "#0096B7"), unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "raw", "classified", "posted", "failed"])
    with col2:
        source_names = ["All"] + [s["name"] for s in get_all_sources()]
        source_filter = st.selectbox("Filter by Source", source_names)
    with col3:
        limit = st.selectbox("Limit", [50, 100, 200, 500])
    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", use_container_width=True):
            st.rerun()
    with col5:
        st.markdown("<br>", unsafe_allow_html=True)

    try:
        articles = get_all_articles(limit)
        if articles:
            df = pd.DataFrame(articles)
            if 'categories' in df.columns:
                df['category'] = df['categories'].apply(lambda x: x.get('name','?') if isinstance(x, dict) else '?')
            if 'sources' in df.columns:
                df['source'] = df['sources'].apply(lambda x: x.get('name','?') if isinstance(x, dict) else '?')
            if status_filter != "All" and 'status' in df.columns:
                df = df[df['status'] == status_filter]
            if source_filter != "All" and 'source' in df.columns:
                df = df[df['source'] == source_filter]

            cols_show = [c for c in ['id','title','source','category','status','scraped_at'] if c in df.columns]
            df_show = df[cols_show].copy()
            if 'title' in df_show.columns:
                df_show['title'] = df_show['title'].str[:70] + '...'

            total = len(df_show)
            posted = len(df[df['status']=='posted']) if 'status' in df.columns else 0
            failed = len(df[df['status']=='failed']) if 'status' in df.columns else 0
            classified = len(df[df['status']=='classified']) if 'status' in df.columns else 0

            m1,m2,m3,m4 = st.columns(4)
            with m1: st.markdown(glow_card("📊","Showing",total,"#00D4FF",delay="0s"), unsafe_allow_html=True)
            with m2: st.markdown(glow_card("✅","Posted",posted,"#00FF88",delay="0.05s"), unsafe_allow_html=True)
            with m3: st.markdown(glow_card("🔵","Classified",classified,"#00D4FF",delay="0.1s"), unsafe_allow_html=True)
            with m4: st.markdown(glow_card("❌","Failed",failed,"#FF4B4B",delay="0.15s"), unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # Bar chart
            if 'status' in df.columns:
                status_counts = df['status'].value_counts().reset_index()
                status_counts.columns = ['status', 'count']
                fig = px.bar(
                    status_counts, x='status', y='count', color='status',
                    color_discrete_map={
                        'posted':'#00FF88', 'classified':'#00D4FF',
                        'failed':'#FF4B4B', 'raw':'#8892A4'
                    },
                    text='count',
                )
                fig.update_traces(
                    textposition='outside', textfont=dict(color='#CBD5E0', size=12),
                    marker=dict(line=dict(color='#070B14', width=2)),
                    hovertemplate='<b>%{x}</b>: %{y} articles<extra></extra>',
                )
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=10, b=0, l=0, r=0),
                    height=200,
                    showlegend=False,
                    xaxis=dict(showgrid=False, title=None, tickfont=dict(color='#6B7280', size=11)),
                    yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.04)', title=None, tickfont=dict(color='#6B7280', size=10)),
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            csv = df.to_csv(index=False).encode("utf-8")
            st.markdown("""
            <style>
            .art-table { width:100%; border-collapse:collapse; font-size:13px; }
            .art-table th { text-align:left; padding:10px 12px; color:#6B7280; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; border-bottom:1px solid rgba(255,255,255,0.06); }
            .art-table td { padding:10px 12px; border-bottom:1px solid rgba(255,255,255,0.04); color:#CBD5E0; }
            .art-table tr:hover td { background:rgba(0,212,255,0.04); }
            .art-table .ttl { max-width:300px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-weight:600; color:#E2E8F0; }
            </style>
            """, unsafe_allow_html=True)
            rows_html = ""
            for _, row in df_show.iterrows():
                s = row.get("status", "")
                sc = str(row.get("source", ""))
                cat = str(row.get("category", ""))
                sa = str(row.get("scraped_at", ""))[:16]
                tid = row.get("id", "")
                ttl = str(row.get("title", ""))[:70]
                rows_html += f"<tr><td class='ttl' title='{ttl}'>{ttl}</td><td>{sc}</td><td>{cat}</td><td>{status_badge(s)}</td><td style='color:#6B7280;font-size:12px'>{sa}</td></tr>"
            st.markdown(f"""
            <div style="border:1px solid rgba(255,255,255,0.06);border-radius:16px;overflow:auto;max-height:480px;background:rgba(255,255,255,0.01);">
            <table class="art-table"><thead><tr><th>Title</th><th>Source</th><th>Category</th><th>Status</th><th>Scraped</th></tr></thead><tbody>{rows_html}</tbody></table>
            </div>
            """, unsafe_allow_html=True)
            st.download_button("📥 Download CSV", data=csv, file_name=f"articles_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("No articles found.")
    except Exception as e:
        st.error(str(e))


# ═══════════════════════════════════════════════════
# POST HISTORY
# ═══════════════════════════════════════════════════

elif "History" in page:
    st.markdown(page_hero("📬", "Post History", "Complete audit trail of all Telegram posting attempts", "#7B2FBE", "#FF4B4B"), unsafe_allow_html=True)

    try:
        logs = get_posting_history(500)
        if logs:
            df = pd.DataFrame(logs)
            if 'articles' in df.columns:
                df['title'] = df['articles'].apply(lambda x: str(x.get('title','?'))[:60] if isinstance(x, dict) else '?')
            if 'channels' in df.columns:
                df['channel'] = df['channels'].apply(lambda x: x.get('name','?') if isinstance(x, dict) else '?')

            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                if 'posted_at' in df.columns:
                    df['posted_at_dt'] = pd.to_datetime(df['posted_at'], errors='coerce')
                    min_d = df['posted_at_dt'].min().date() if not df['posted_at_dt'].isna().all() else datetime.today().date()
                    max_d = df['posted_at_dt'].max().date() if not df['posted_at_dt'].isna().all() else datetime.today().date()
                    date_range = st.date_input("Filter by date", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                    if len(date_range) == 2:
                        start_d, end_d = date_range
                        df = df[(df['posted_at_dt'].dt.date >= start_d) & (df['posted_at_dt'].dt.date <= end_d)]
            with c2:
                status_opts = ["All", "success", "failed"]
                history_status_filter = st.selectbox("Filter by status", status_opts, key="hist_status")
                if history_status_filter != "All" and 'status' in df.columns:
                    df = df[df['status'] == history_status_filter]
            with c3:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🔄", use_container_width=True, key="hist_refresh"):
                    st.rerun()

            total = len(df)
            success = len(df[df['status']=='success']) if 'status' in df.columns else 0
            failed_cnt = len(df[df['status']=='failed']) if 'status' in df.columns else 0
            rate = f"{(success/total*100):.1f}%" if total > 0 else "0%"

            c1,c2,c3,c4 = st.columns(4)
            with c1: st.markdown(glow_card("📊","Total Logs",total,"#00D4FF",delay="0.05s"), unsafe_allow_html=True)
            with c2: st.markdown(glow_card("✅","Successful",success,"#00FF88",delay="0.1s"), unsafe_allow_html=True)
            with c3: st.markdown(glow_card("❌","Failed",failed_cnt,"#FF4B4B",delay="0.15s"), unsafe_allow_html=True)
            with c4: st.markdown(glow_card("📈","Success Rate",rate,"#FFB800",delay="0.2s"), unsafe_allow_html=True)

            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["📋 Table View", "⏱ Timeline"])
            with tab1:
                cols_show = [c for c in ['id','title','channel','status','retry_count','error_message','posted_at'] if c in df.columns]
                df_show = df[cols_show].copy()
                csv = df_show.to_csv(index=False).encode("utf-8")
                st.markdown("""
                <style>
                .log-table { width:100%; border-collapse:collapse; font-size:13px; }
                .log-table th { text-align:left; padding:10px 12px; color:#6B7280; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:1.5px; border-bottom:1px solid rgba(255,255,255,0.06); }
                .log-table td { padding:10px 12px; border-bottom:1px solid rgba(255,255,255,0.04); color:#CBD5E0; max-width:240px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
                .log-table tr:hover td { background:rgba(0,212,255,0.04); }
                .log-table .err-cell { color:#FF4B4B; font-size:12px; max-width:180px; }
                </style>
                """, unsafe_allow_html=True)
                rows_html = ""
                for _, row in df_show.iterrows():
                    s = row.get("status", "")
                    ch = str(row.get("channel", ""))
                    err = str(row.get("error_message", "") or "")[:80]
                    pa = str(row.get("posted_at", ""))[:16]
                    rc = int(row.get("retry_count", 0))
                    ttl = str(row.get("title", ""))[:60]
                    rows_html += f"<tr><td style='font-weight:600;color:#E2E8F0'>{ttl}</td><td>{ch}</td><td>{status_badge(s)}</td><td>{rc}</td><td class='err-cell' title='{err}'>{err}</td><td style='color:#6B7280;font-size:12px'>{pa}</td></tr>"
                st.markdown(f"""
                <div style="border:1px solid rgba(255,255,255,0.06);border-radius:16px;overflow:auto;max-height:520px;background:rgba(255,255,255,0.01);">
                <table class="log-table"><thead><tr><th>Article</th><th>Channel</th><th>Status</th><th>Retries</th><th>Error</th><th>Posted At</th></tr></thead><tbody>{rows_html}</tbody></table>
                </div>
                """, unsafe_allow_html=True)
                st.download_button("📥 Download CSV", data=csv, file_name=f"post_history_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)
            with tab2:
                st.markdown('<div style="margin:10px 0 20px 0;padding:8px 12px;background:rgba(255,255,255,0.02);border-radius:12px;border:1px solid rgba(255,255,255,0.05);">', unsafe_allow_html=True)
                recent = df.sort_values('posted_at', ascending=False).head(20).to_dict('records') if 'posted_at' in df.columns else logs[:20]
                if recent:
                    for i, log in enumerate(recent):
                        st.markdown(timeline_item(log, delay=f"{i*0.04}s"), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No posting history yet. Run the pipeline to start posting!")
    except Exception as e:
        st.error(str(e))


# ═══════════════════════════════════════════════════
# SOURCES
# ═══════════════════════════════════════════════════

elif "Sources" in page:
    st.markdown(page_hero("🌐", "News Sources", "Manage and monitor your scraping sources", "#00FF88", "#00D4FF"), unsafe_allow_html=True)

    try:
        sources = get_all_sources()
        if sources:
            active_count = sum(1 for s in sources if s.get('is_active'))

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(glow_card("🌐","Total Sources",len(sources),"#00D4FF",delay="0.05s"), unsafe_allow_html=True)
            with c2: st.markdown(glow_card("✅","Active",active_count,"#00FF88",delay="0.1s"), unsafe_allow_html=True)
            with c3: st.markdown(glow_card("⏸","Paused",len(sources)-active_count,"#FF4B4B",delay="0.15s"), unsafe_allow_html=True)

            st.markdown(section_title("📋 Source Management", "Toggle sources on/off without restarting"), unsafe_allow_html=True)

            csv_src = pd.DataFrame(sources).to_csv(index=False).encode("utf-8")
            col_csv, _ = st.columns([1, 5])
            with col_csv:
                st.download_button("📥 CSV", data=csv_src, file_name=f"sources_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)

            for source in sources:
                is_active = source.get('is_active', True)
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(source_card(source), unsafe_allow_html=True)
                with col2:
                    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
                    btn = "⏸ Pause" if is_active else "▶ Start"
                    pop_key = f"pop_src_{source['id']}"
                    with st.popover(btn, use_container_width=True):
                        st.markdown(f"{'Pause' if is_active else 'Start'} **{source['name']}**?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Yes", key=f"yes_src_{source['id']}", use_container_width=True):
                                toggle_source_active(source['id'], not is_active)
                                st.rerun()
                        with c2:
                            if st.button("No", key=f"no_src_{source['id']}", use_container_width=True):
                                st.rerun()
        else:
            st.info("No sources configured.")
    except Exception as e:
        st.error(str(e))


# ═══════════════════════════════════════════════════
# CATEGORIES
# ═══════════════════════════════════════════════════

elif "Categories" in page:
    st.markdown(page_hero("🏷️", "Categories & Keywords", "Keyword rules that classify articles and route them to channels", "#FFB800", "#FF6B9D"), unsafe_allow_html=True)

    try:
        categories = get_all_categories_with_keywords()
        if categories:
            palette = [
                ("#00D4FF","#0096B7"), ("#00FF88","#00B860"),
                ("#7B2FBE","#5A1F8A"), ("#FFB800","#B88200"),
                ("#FF4B4B","#B83535"), ("#FF6B9D","#B84870"),
            ]
            total_keywords = sum(len(cat.get('keywords') or []) for cat in categories)
            c1, c2 = st.columns(2)
            c1.markdown(glow_card("📂","Categories",len(categories),"#00D4FF",delay="0.05s"), unsafe_allow_html=True)
            c2.markdown(glow_card("🔑","Total Keywords",total_keywords,"#FFB800",delay="0.1s"), unsafe_allow_html=True)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            cols = st.columns(2)
            for i, cat in enumerate(categories):
                color1, color2 = palette[i % len(palette)]
                cat_id = cat.get('id')
                cat_name = cat.get('name', 'Unknown')
                keywords = cat.get('keywords', []) or []
                if keywords and isinstance(keywords[0], dict):
                    kw_list = [(k.get('id'), k.get('word','')) for k in keywords if k.get('word')]
                else:
                    kw_list = [(None, k) for k in keywords if k]

                with cols[i % 2]:
                    st.markdown(f"""<div style="background:linear-gradient(135deg,{color1}0D 0%,{color2}06 100%);border:1px solid {color1}20;border-top:3px solid {color1};border-radius:20px;padding:22px;margin:8px 0;backdrop-filter:blur(10px);">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                            <div style="font-size:16px;font-weight:800;color:#FFFFFF;">{cat_name}</div>
                            <div style="background:{color1}15;color:{color1};border:1px solid {color1}25;padding:4px 12px;border-radius:20px;font-size:10px;font-weight:800;letter-spacing:0.5px;">{len(kw_list)} KEYWORDS</div>
                        </div>
                    </div>""", unsafe_allow_html=True)

                    if kw_list:
                        for kw_id, kw_word in kw_list:
                            c1, c2 = st.columns([5, 1])
                            with c1:
                                st.markdown(kw_chip(kw_word, color1), unsafe_allow_html=True)
                            with c2:
                                if kw_id and st.button("✕", key=f"del_kw_{kw_id}", use_container_width=True):
                                    delete_record("keywords", kw_id)
                                    st.rerun()
                    else:
                        st.markdown(f'<span style="color:#4A5568;font-size:13px;font-style:italic;">No keywords assigned</span>', unsafe_allow_html=True)

                    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                    ac1, ac2 = st.columns([3, 1])
                    with ac1:
                        new_kw = st.text_input("", placeholder="Add keyword...", key=f"new_kw_{cat_id}", label_visibility="collapsed")
                    with ac2:
                        if st.button("+ Add", key=f"add_kw_{cat_id}", use_container_width=True):
                            if new_kw.strip():
                                create_keyword(new_kw.strip().lower(), cat_id)
                                st.rerun()
        else:
            st.info("No categories found.")
    except Exception as e:
        st.error(str(e))


# ═══════════════════════════════════════════════════
# CHANNELS
# ═══════════════════════════════════════════════════

elif "Channels" in page:
    st.markdown(page_hero("📡", "Telegram Channels", "Manage your Telegram posting destinations", "#00D4FF", "#7B2FBE"), unsafe_allow_html=True)

    try:
        channels = get_all_channels()
        if channels:
            active_count = sum(1 for c in channels if c.get('is_active'))

            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(glow_card("📡","Total Channels",len(channels),"#00D4FF",delay="0.05s"), unsafe_allow_html=True)
            with c2: st.markdown(glow_card("✅","Active",active_count,"#00FF88",delay="0.1s"), unsafe_allow_html=True)
            with c3: st.markdown(glow_card("⏸","Inactive",len(channels)-active_count,"#FF4B4B",delay="0.15s"), unsafe_allow_html=True)

            st.markdown(section_title("📋 Channel Management", "Control which channels receive posts"), unsafe_allow_html=True)

            csv_ch = pd.DataFrame(channels).to_csv(index=False).encode("utf-8")
            col_csv, _ = st.columns([1, 5])
            with col_csv:
                st.download_button("📥 CSV", data=csv_ch, file_name=f"channels_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv", use_container_width=True)

            for channel in channels:
                is_active = channel.get('is_active', True)
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(channel_card(channel), unsafe_allow_html=True)
                with col2:
                    st.markdown("<div style='height:22px'></div>", unsafe_allow_html=True)
                    btn = "⏸ Pause" if is_active else "▶ Start"
                    with st.popover(btn, use_container_width=True):
                        st.markdown(f"{'Pause' if is_active else 'Start'} **{channel.get('name', '')}**?")
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("Yes", key=f"yes_ch_{channel['id']}", use_container_width=True):
                                toggle_channel_active(channel['id'], not is_active)
                                st.rerun()
                        with c2:
                            if st.button("No", key=f"no_ch_{channel['id']}", use_container_width=True):
                                st.rerun()
        else:
            st.info("No channels configured.")
    except Exception as e:
        st.error(str(e))
