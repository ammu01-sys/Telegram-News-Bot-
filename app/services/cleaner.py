import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from app.utils.logger import logger


# Expanded patterns to extract the original source/organization from article content.
# Ordered by specificity — first match wins.
_SOURCE_PATTERNS = [
    # Explicit attribution
    r'\bsource[:\s]+([A-Z][A-Za-z0-9 &.\'\-]+)',
    r'\baccording to\s+([A-Z][A-Za-z0-9 &.\'\-]+)',
    # Report/study patterns
    r'\ba (?:report|study|analysis|research|survey|review|audit) by\s+([A-Z][A-Za-z0-9 &.\'\-]+)',
    r'\b(?:revealed|published|announced|found|reported|released|disclosed|uncovered|highlighted) by\s+([A-Z][A-Za-z0-9 &.\'\-]+)',
    # Data/content attribution
    r'\bdata (?:from|provided by|compiled by)\s+([A-Z][A-Za-z0-9 &.\'\-]+)',
    r'\b(?:stated|noted|wrote|explained|confirmed|claimed|said)\s+([A-Z][A-Za-z0-9 &.\'\-]+?)(?:\s+in\s+|\s+that\s+|\s+on\s+|[,;])',
    # Organization as subject
    r'\b([A-Z][A-Za-z0-9 &.\'\-]+)\s+(?:report|study|research|data|analysis|findings|audit) (?:shows|suggests|reveals|finds|indicates|highlights|confirms)',
]

# Known crypto industry organizations — used as a secondary matching strategy
_KNOWN_SOURCES = {
    # Research & Analytics
    "certik", "chainalysis", "messari", "glassnode", "dune analytics",
    "delphi digital", "arkham", "elliptic", "trm labs", "kaiko", "nansen",
    "defi llama", "lookonchain", "onchain lens", "coinmetrics", "skew",
    # Exchanges
    "binance", "coinbase", "kraken", "bybit", "okx", "bitfinex", "kucoin",
    "gate.io", "htx", "mexc",
    # Protocols
    "ethereum foundation", "uniswap labs", "aave", "makerdao", "lido",
    "polygon", "arbitrum", "optimism", "chainlink", "circle", "tether",
    # Media
    "the block", "decrypt", "coindesk", "bloomberg", "reuters", "forbes",
    "financial times", "wall street journal", "cnbc", "techcrunch",
    # Government
    "sec", "cftc", "doj", "fbi", "irs", "treasury", "europol", "interpol",
}


def clean_article(article: dict) -> dict:
    """
    Input:  raw scraper dict {title, url, content, timestamp, source_name}
    Output: cleaned dict with published_at (datetime) and article_source added
    """
    article["title"]        = _clean_text(article.get("title", ""))
    article["content"]      = _clean_text(article.get("content", ""))
    article["published_at"] = _parse_timestamp(article.get("timestamp", ""))

    # Try extracting source from RSS content first
    article_source = _extract_source(
        article.get("title", ""), article.get("content", "")
    )

    # If not found, fetch the full article page and try again
    if not article_source and article.get("url"):
        full_text = _fetch_article_page(article["url"])
        if full_text:
            article_source = _extract_source(article.get("title", ""), full_text)

    article["article_source"] = article_source
    return article


def _fetch_article_page(url: str) -> str:
    """Fetch the full article page and extract text content."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
        }
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "lxml")

        # Try common article body selectors
        for selector in ["article", ".article-body", ".post-content",
                         ".article-content", ".entry-content", "main"]:
            el = soup.select_one(selector)
            if el:
                return el.get_text(separator=" ", strip=True)[:5000]

        # Fallback: all <p> tags
        paragraphs = soup.find_all("p")
        return " ".join(p.get_text(strip=True) for p in paragraphs)[:5000]

    except Exception as e:
        logger.warning(f"Failed to fetch article page {url}: {e}")
        return ""


def _clean_text(text: str) -> str:
    # Strip HTML tags if any slipped through
    text = BeautifulSoup(text, "lxml").get_text(separator=" ")
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _parse_timestamp(raw: str) -> str | None:
    """Normalize any ISO-8601 string to UTC ISO format."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return None


def _extract_source(title: str, content: str) -> str:
    """
    Try to find the original source/organization mentioned in the article.
    Uses regex patterns first, then falls back to known-source name matching.
    Returns the source name or empty string if not found.
    """
    text = title + ". " + content

    # Strategy 1: regex pattern matching
    for pattern in _SOURCE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            source = match.group(1).strip()
            # Trim trailing punctuation / filler words
            source = re.sub(r'[,;.\-:\'"]+\s*$', '', source)
            # Remove common trailing words that aren't part of the name
            source = re.sub(r'\s+(in|on|for|with|has|had|is|was|are|said|says)$', '', source, flags=re.IGNORECASE)
            # Cap length to avoid garbage captures
            if 2 <= len(source) <= 50:
                # Normalize capitalization
                return source

    # Strategy 2: scan for known source names in the text
    text_lower = text.lower()
    for known in _KNOWN_SOURCES:
        if known in text_lower:
            # Find the properly-cased version in the original text
            idx = text_lower.find(known)
            proper = text[idx:idx + len(known)]
            # Use title case as fallback
            return proper if proper[0].isupper() else known.title()

    return ""
