
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo
import html
import re

import feedparser
import requests

IST = ZoneInfo("Asia/Kolkata")

# RSS sources for SSB-relevant current affairs.
# Google News RSS aggregates current articles from multiple publishers.
RSS_FEEDS = [
    (
        "PIB",
        "https://www.pib.gov.in/RssMain.aspx",
    ),
    (
        "Google News Defence",
        "https://news.google.com/rss/search?"
        "q=India+defence+military+DRDO+IAF+Indian+Navy+Indian+Army"
        "&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News International",
        "https://news.google.com/rss/search?"
        "q=India+international+relations+geopolitics+diplomacy"
        "&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News National",
        "https://news.google.com/rss/search?"
        "q=India+government+policy+national+security"
        "&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News Economy",
        "https://news.google.com/rss/search?"
        "q=India+economy+RBI+GDP+inflation+trade"
        "&hl=en-IN&gl=IN&ceid=IN:en",
    ),
    (
        "Google News Science",
        "https://news.google.com/rss/search?"
        "q=ISRO+space+science+technology+India"
        "&hl=en-IN&gl=IN&ceid=IN:en",
    ),
]


def _parse_datetime(value: str) -> datetime | None:
    """
    Parse common RSS timestamps.

    Returns an aware datetime.
    """
    if not value:
        return None

    value = str(value).strip()

    # Handle ISO timestamps.
    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError:
        pass

    # Handle RSS timestamps.
    try:
        parsed = feedparser._parse_date(value)

        if parsed:
            return datetime(
                *parsed[:6],
                tzinfo=timezone.utc,
            )
    except Exception:
        pass

    return None


def _entry_published(entry: Any) -> str:
    """
    Return the best available publication timestamp.
    """
    published = (
        getattr(entry, "published", "")
        or getattr(entry, "updated", "")
        or ""
    )

    return str(published).strip()


def is_today(published: str) -> bool:
    """
    Return True when the article was published today in India.
    """
    dt = _parse_datetime(published)

    if dt is None:
        return False

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(IST).date() == datetime.now(IST).date()


def _clean_text(value: str) -> str:
    """
    Remove HTML from RSS summaries.
    """
    if not value:
        return ""

    value = html.unescape(value)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)

    return value.strip()


def fetch_rss() -> list[dict[str, Any]]:
    """
    Fetch today's articles from PIB and Google News RSS feeds.
    """
    articles: list[dict[str, Any]] = []

    for source, url in RSS_FEEDS:
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={
                    "User-Agent": "SSB-Daily-Brief/2.0"
                },
            )

            response.raise_for_status()

            feed = feedparser.parse(response.content)

            if getattr(feed, "bozo", False):
                print(
                    f"[WARN] RSS parser warning for {source}: "
                    f"{getattr(feed, 'bozo_exception', '')}"
                )

            source_count = 0

            for entry in feed.entries[:50]:
                title = (
                    getattr(entry, "title", "")
                    or ""
                ).strip()

                link = (
                    getattr(entry, "link", "")
                    or ""
                ).strip()

                summary = _clean_text(
                    getattr(entry, "summary", "")
                    or ""
                )

                published = _entry_published(entry)

                # Only include articles published today in IST.
                if not title or not link:
                    continue

                if not is_today(published):
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

                source_count += 1

            print(
                f"[INFO] {source}: "
                f"{source_count} today's articles"
            )

        except requests.RequestException as exc:
            print(
                f"[WARN] Network error for RSS source "
                f"{source}: {exc}"
            )

        except Exception as exc:
            print(
                f"[WARN] Failed RSS source "
                f"{source}: {exc}"
            )

    print(
        f"[INFO] Total today's RSS articles: "
        f"{len(articles)}"
    )

    return articles


def _deduplicate(
    articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """
    Remove duplicate articles using URL first
    and normalized title second.
    """
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()

    unique: list[dict[str, Any]] = []

    for article in articles:
        url = (
            article.get("url", "")
            .strip()
            .lower()
        )

        title = " ".join(
            article.get("title", "")
            .lower()
            .split()
        )

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


def _sort_key(article: dict[str, Any]) -> datetime:
    """
    Return a sortable datetime.

    Articles without valid timestamps are placed at the end.
    """
    dt = _parse_datetime(
        article.get("published", "")
    )

    if dt is None:
        return datetime.min.replace(
            tzinfo=timezone.utc
        )

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt


def fetch_all_news() -> list[dict[str, Any]]:
    """
    Fetch, filter, deduplicate and sort today's news.

    News API is intentionally NOT used.
    """
    articles = fetch_rss()

    unique = _deduplicate(articles)

    # Newest articles first.
    unique.sort(
        key=_sort_key,
        reverse=True,
    )

    print(
        f"[INFO] Collected "
        f"{len(unique)} unique articles "
        f"published today (IST)."
    )

    for article in unique[:10]:
        print(
            f"[NEWS] {article['published']} | "
            f"{article['source']} | "
            f"{article['title']}"
        )

    return unique
