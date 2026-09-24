from datetime import datetime, timezone
from typing import Any

import feedparser
import requests

from .config import settings


RSS_FEEDS = [
    ("PIB", "https://www.pib.gov.in/RssMain.aspx"),
    ("Google News Defence", "https://news.google.com/rss/search?q=India+defence+military+DRDO+IAF+Indian+Navy+Indian+Army&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News International", "https://news.google.com/rss/search?q=India+international+relations+geopolitics&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News National", "https://news.google.com/rss/search?q=India+government+policy+economy+science+technology&hl=en-IN&gl=IN&ceid=IN:en"),
]


def fetch_rss() -> list[dict[str, Any]]:
    articles = []

    for source, url in RSS_FEEDS:
        try:
            response = requests.get(
                url,
                timeout=20,
                headers={"User-Agent": "SSB-Daily-Brief/1.0"},
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)

            for entry in feed.entries[:20]:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                summary = getattr(entry, "summary", "").strip()

                if title and link:
                    articles.append({
                        "source": source,
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "published": getattr(entry, "published", ""),
                    })
        except Exception as exc:
            print(f"[WARN] Failed RSS source {source}: {exc}")

    return articles


def fetch_news_api() -> list[dict[str, Any]]:
    if not settings.news_api_key:
        return []

    query = (
        "India defence OR military OR DRDO OR ISRO OR geopolitics "
        "OR diplomacy OR national security OR economy OR science"
    )

    try:
        response = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 50,
                "apiKey": settings.news_api_key,
            },
            timeout=20,
        )
        response.raise_for_status()

        data = response.json()
        return [
            {
                "source": article.get("source", {}).get("name", "News API"),
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "summary": article.get("description", ""),
                "published": article.get("publishedAt", ""),
            }
            for article in data.get("articles", [])
            if article.get("title") and article.get("url")
        ]
    except Exception as exc:
        print(f"[WARN] News API failed: {exc}")
        return []


def fetch_all_news() -> list[dict[str, Any]]:
    articles = fetch_rss() + fetch_news_api()

    seen = set()
    unique = []

    for article in articles:
        key = article["title"].lower().strip()
        if key not in seen:
            seen.add(key)
            unique.append(article)

    print(f"[INFO] Collected {len(unique)} unique articles.")
    return unique
