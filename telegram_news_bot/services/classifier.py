from ..database.queries import get_all_keywords_with_categories
from ..utils.logger import get_logger

log = get_logger(__name__)


class Classifier:
    """
    Keyword-based article classifier.

    Loads keyword\u2192category mappings from DB into memory.
    Classifies article content by checking if any keyword appears in the text.
    Falls back to Uncategorized if no keyword matches.
    """

    def __init__(self):
        self._keywords: list[dict] = []
        self._uncategorized_id: int = 6
        self.load_cache()

    def load_cache(self) -> None:
        """Load all keywords and their category mappings from database."""
        try:
            data = get_all_keywords_with_categories()
            self._keywords = data or []
            log.info(f"Loaded {len(self._keywords)} keyword mappings into cache")
        except Exception as e:
            log.error(f"Failed to load keyword cache: {e}")
            self._keywords = []

    def classify(self, content: str) -> int:
        """
        Classify content by keyword matching.
        Longer keywords are matched first (more specific = higher priority).
        """
        if not content:
            return self._uncategorized_id

        content_lower = content.lower()
        sorted_kw = sorted(self._keywords, key=lambda k: len(k.get('word', '')), reverse=True)

        for kw in sorted_kw:
            word = kw.get('word', '').lower()
            if word and word in content_lower:
                category_id = kw.get('category_id')
                log.debug(f"Matched keyword '{word}' \u2192 category_id {category_id}")
                return category_id

        return self._uncategorized_id

    def refresh(self) -> None:
        """Reload keyword cache from database."""
        log.info("Refreshing keyword cache...")
        self.load_cache()


classifier = Classifier()


def classify(content: str) -> int:
    """Module-level classify function using singleton classifier."""
    return classifier.classify(content)
