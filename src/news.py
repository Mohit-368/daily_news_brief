from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

import feedparser
import requests

from .config import settings


IST = ZoneInfo("Asia/Kolkata")

RSS_FEEDS = [
    ("PIB", "https://www.pib.gov.in/RssMain.aspx"),
    (
        "Google News Defence",
        "https://news.google.com/rss/search?q=India+defence+military+DRDO+IAF+Indian+Navy+Indian+Army&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News International",
        "https://news.google.com/rss/search?q=India+international+relations+geopolitics&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News National",
        "https://news.google.com/rss/search?q=India+government+policy+economy+science+technology&hl=en-IN&gl=IN:en",
    ),
]

# Keep this list focused. Six News API calls/day is comfortably below
# the normal free Developer-plan daily request allowance.
NEWS_API_QUERIES = [
    "India defence military",
    "DRDO ISRO",
    "Indian Army Navy Air Force",
    "India diplomacy geopolitics",
    "India national security",
]


def _parse_datetime(value: str) -> datetime | None:
    """Parse common RSS/ISO timestamps and return an aware datetime."""
    if not value:
        return None

    try:
        # Handles News API values such as 2026-09-25T08:12:00Z.
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pass

    try:
        parsed = feedparser._parse_date(value)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    except Exception:
        pass

    return None


def _entry_published(entry: Any) -> str:
    """Return the best available publication timestamp from an RSS entry."""
    published = getattr(entry, "published", "") or getattr(entry, "updated", "")
    return str(published).strip()


def is_today(published: str) -> bool:
    """Return True when a timestamp falls on today's date in India."""
    dt = _parse_datetime(published)
    if dt is None:
        return False

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST).date() == datetime.now(IST).date()


def fetch_rss() -> list[dict[str, Any]]:
    articles: list[dict[str, Any]] = []

    for source, url in RSS_FEEDS:
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "SSB-Daily-Brief/1.1"},
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:30]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                summary = getattr(entry, "summary", "").strip()
                published = _entry_published(entry)

                # Do not let old RSS stories enter today's briefing.
                if not title or not link or not is_today(published):
                    continue

                articles.append(
                    {
                        "source": source,
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "published": published,
                    }
                )
        except Exception as exc:
            print(f"[WARN] Failed RSS source {source}: {exc}")

    print(f"[INFO] Today's RSS articles: {len(articles)}")
    return articles


def _news_api_request(params: dict[str, Any]) -> list[dict[str, Any]]:
    response = requests.get(
        "https://newsapi.org/v2/top-headlines",
        params=params,
        headers={"X-Api-Key": settings.news_api_key},
        timeout=20,
    )
    response.raise_for_status()

    data = response.json()

    if data.get("status") != "ok":
        raise RuntimeError(data.get("message", "News API returned an error."))

    return data.get("articles", [])


def fetch_news_api() -> list[dict[str, Any]]:
    """Fetch current Indian headlines, rather than delayed /everything results."""
    if not settings.news_api_key:
        print("[INFO] NEWS_API_KEY not configured. Skipping News API.")
        return []

    articles: list[dict[str, Any]] = []

    # First get general Indian headlines.
    queries: list[str | None] = [None, *NEWS_API_QUERIES]

    for query in queries:
        try:
            params: dict[str, Any] = {
                "country": "in",
                "language": "en",
                "pageSize": 20,
            }
            if query:
                params["q"] = query

            raw_articles = _news_api_request(params)

            for article in raw_articles:
                published = article.get("publishedAt", "")

                # News API returns publishedAt in UTC. Convert to IST before
                # deciding whether the story belongs to today's briefing.
                if not is_today(published):
                    continue

                title = article.get("title") or ""
                url = article.get("url") or ""

                if not title or not url:
                    continue

                articles.append(
                    {
                        "source": article.get("source", {}).get("name") or "News API",
                        "title": title,
                        "url": url,
                        "summary": article.get("description") or "",
                        "published": published,
                    }
                )
        except Exception as exc:
            label = query or "general India headlines"
            print(f"[WARN] News API query failed ({label}): {exc}")

    print(f"[INFO] Today's News API articles: {len(articles)}")
    return articles


def _deduplicate(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicates using URL first and normalized title second."""
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    unique: list[dict[str, Any]] = []

    for article in articles:
        url = article.get("url", "").strip().lower()
        title = " ".join(article.get("title", "").lower().split())

        if url and url in seen_urls:
            continue
        if title and title in seen_titles:
            continue

        if url:
            seen_urls.add(url)
        if title:
            seen_titles.add(title)

        unique.append(article)

    return unique


def fetch_all_news() -> list[dict[str, Any]]:
    articles = fetch_rss() + fetch_news_api()
    unique = _deduplicate(articles)

    # Most recent first. Missing/invalid timestamps naturally fall to the end.
    unique.sort(
        key=lambda article: _parse_datetime(article.get("published", ""))
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    print(f"[INFO] Collected {len(unique)} unique articles published today (IST).")

    for article in unique[:10]:
        print(
            f"[NEWS] {article['published']} | "
            f"{article['source']} | {article['title']}"
        )

    return unique
