from datetime import datetime, timezone, timedelta
from typing import Any
from zoneinfo import ZoneInfo
import html
import re

import feedparser
import requests


IST = ZoneInfo("Asia/Kolkata")

RSS_FEEDS = {
    "PIB": "https://www.pib.gov.in/RssMain.aspx",

    "Google News Defence": (
        "https://news.google.com/rss/search?"
        "q=India+defence+military+DRDO+IAF+Indian+Navy+Indian+Army"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),

    "Google News International": (
        "https://news.google.com/rss/search?"
        "q=India+international+relations+geopolitics+diplomacy"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),

    "Google News National": (
        "https://news.google.com/rss/search?"
        "q=India+government+policy+national+security"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),

    "Google News Economy": (
        "https://news.google.com/rss/search?"
        "q=India+economy+RBI+GDP+inflation+trade"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),

    "Google News Science": (
        "https://news.google.com/rss/search?"
        "q=ISRO+space+science+technology+India"
        "&hl=en-IN&gl=IN&ceid=IN:en"
    ),
}


def _parse_datetime(value: Any) -> datetime | None:
    """
    Convert feedparser datetime values to timezone-aware datetime.
    """

    if value is None:
        return None

    try:
        if isinstance(value, datetime):
            dt = value

            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            return dt.astimezone(IST)

        # feedparser often gives struct_time
        if hasattr(value, "tm_year"):
            dt = datetime(
                value.tm_year,
                value.tm_mon,
                value.tm_mday,
                value.tm_hour,
                value.tm_min,
                value.tm_sec,
                tzinfo=timezone.utc,
            )

            return dt.astimezone(IST)

    except Exception:
        return None

    return None


def _entry_published(entry: Any) -> datetime | None:
    """
    Try all common feedparser date fields.
    """

    for field in (
        "published_parsed",
        "updated_parsed",
        "created_parsed",
    ):
        value = entry.get(field)

        dt = _parse_datetime(value)

        if dt:
            return dt

    return None


def _clean_text(text: str) -> str:
    """
    Remove HTML and normalize whitespace.
    """

    if not text:
        return ""

    text = html.unescape(text)

    text = re.sub(r"<[^>]+>", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def _is_recent(dt: datetime | None) -> bool:
    """
    Accept articles published within the last 24 hours.

    This is more reliable for a morning daily brief than requiring
    the article's calendar date to exactly match today.
    """

    if dt is None:
        return False

    now = datetime.now(IST)

    age = now - dt

    return timedelta(hours=-1) <= age <= timedelta(hours=24)


def fetch_rss() -> list[dict[str, Any]]:
    """
    Fetch articles from all RSS feeds.
    """

    articles: list[dict[str, Any]] = []

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(X11; Linux x86_64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/120 Safari/537.36"
        )
    }

    for source, url in RSS_FEEDS.items():

        try:
            response = requests.get(
                url,
                headers=headers,
                timeout=20,
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if feed.bozo:
                print(
                    f"[WARN] RSS parser warning for {source}: "
                    f"{feed.bozo_exception}"
                )

            source_count = 0

            for entry in feed.entries:

                published = _entry_published(entry)

                if not published:
                    continue

                if not _is_recent(published):
                    continue

                title = _clean_text(
                    entry.get("title", "")
                )

                link = entry.get("link", "")

                summary = _clean_text(
                    entry.get("summary", "")
                )

                if not title or not link:
                    continue

                articles.append(
                    {
                        "title": title,
                        "link": link,
                        "summary": summary,
                        "source": source,
                        "published": published.isoformat(),
                    }
                )

                source_count += 1

            print(
                f"[INFO] {source}: "
                f"{source_count} recent articles"
            )

        except Exception as e:

            print(
                f"[ERROR] Failed to fetch {source}: {e}"
            )

    return articles


def _deduplicate(
    articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    seen: set[str] = set()

    unique: list[dict[str, Any]] = []

    for article in articles:

        link = article.get("link", "").strip()

        if not link:
            continue

        if link in seen:
            continue

        seen.add(link)

        unique.append(article)

    return unique


def _sort_key(article: dict[str, Any]) -> str:
    return article.get("published", "")


def fetch_all_news() -> list[dict[str, Any]]:
    """
    Main news collection function.
    """

    articles = fetch_rss()

    articles = _deduplicate(articles)

    articles.sort(
        key=_sort_key,
        reverse=True,
    )

    print(
        f"[INFO] Collected "
        f"{len(articles)} unique recent RSS articles."
    )

    return articles