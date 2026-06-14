"""
Run this manually to test the pipeline end-to-end.
python run_pipeline_test.py
"""
from app.scrapers.cointelegraph import CoinTelegraphScraper
from app.scrapers.blockworks import BlockworksScraper
from app.services.cleaner import clean_article
from app.database.queries import insert_article, insert_log, get_all_keywords


def run():
    # Fetch keywords ONCE — each entry has word, category_id, categories(name)
    keywords = get_all_keywords()

    scrapers = [CoinTelegraphScraper(), BlockworksScraper()]

    for scraper in scrapers:
        articles = scraper.scrape()

        for raw in articles:
            # 1. Clean
            cleaned = clean_article(raw)

            # 2. Classify — combine title + content, lowercase once
            text = (cleaned["title"] + " " + cleaned["content"]).lower()

            # First keyword match wins — maps directly to category UUID
            category_id = None
            for kw in keywords:
                if kw.get("word", "").lower() in text:
                    category_id = kw["category_id"]
                    break

            if not category_id:
                insert_log("CLASSIFY", f"No category match for: {cleaned['title'][:60]}")

            # 3. Store (skip if duplicate)
            payload = {
                "title":        cleaned["title"],
                "url":          cleaned["url"],
                "content":      cleaned["content"],
                "source_name":  cleaned["source_name"],
                "category_id":  category_id,
                "published_at": cleaned["published_at"],
            }
            inserted = insert_article(payload)
            status = "inserted" if inserted else "duplicate/skipped"
            print(f"[{status}] {cleaned['title'][:60]}")

        insert_log("SCRAPE", f"{scraper.source_name}: {len(articles)} articles scraped")


if __name__ == "__main__":
    run()
