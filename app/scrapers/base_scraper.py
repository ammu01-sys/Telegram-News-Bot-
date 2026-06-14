from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """
    All scrapers inherit from this.
    scrape() must return a list of dicts with these exact keys:
      - title       (str)
      - url         (str)   ← unique identifier, used for deduplication
      - content     (str)   ← full article body, HTML stripped by cleaner later
      - timestamp   (str)   ← raw timestamp string, normalized by cleaner later
      - source_name (str)   ← hardcoded per scraper, e.g. 'CoinTelegraph'
    """

    @abstractmethod
    def scrape(self) -> list[dict]:
        pass

    def _safe_get(self, url: str, headers: dict = None, retries: int = 2) -> object | None:
        """HTTP GET with retry. Returns Response or None."""
        import requests, time
        for attempt in range(retries + 1):
            try:
                resp = requests.get(url, headers=headers or {}, timeout=15)
                resp.raise_for_status()
                return resp
            except Exception as e:
                if attempt < retries:
                    time.sleep(3)
                else:
                    return None
