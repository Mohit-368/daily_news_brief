import json
from typing import Any

from google import genai

from .config import settings
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """
You are an expert current-affairs editor for Indian SSB aspirants.

Turn recent news into a factual, concise and useful daily briefing.

Prioritize:
1. Defence and national security
2. Indian foreign relations and geopolitics
3. Major national policy/government decisions
4. DRDO, ISRO, science and strategic technology
5. Important military exercises, operations and appointments
6. Major economy/social issues that can become SSB discussion topics

Avoid celebrity news, entertainment, clickbait, rumors and duplicate stories.

Do not invent facts. Use only the supplied article information.

Return ONLY valid JSON with this structure:
{
  "date": "YYYY-MM-DD",
  "stories": [
    {
      "category": "...",
      "title": "...",
      "summary": "...",
      "why_it_matters_for_ssb": "...",
      "key_facts": ["...", "..."],
      "ssb_questions": ["...", "..."],
      "source": "...",
      "url": "..."
    }
  ],
  "gd_topics": ["...", "..."],
  "lecturette_topics": ["...", "..."],
  "quick_revision": ["...", "...", "...", "...", "..."]
}

Select around 6-8 high-value stories.
Keep each story concise enough for an email.
"""


def generate_brief(articles: list[dict[str, Any]]) -> dict[str, Any]:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")

    client = genai.Client(api_key=settings.gemini_api_key)

    compact_articles = [
        {
            "source": article["source"],
            "title": article["title"],
            "summary": article["summary"][:1500],
            "url": article["url"],
            "published": article["published"],
        }
        for article in articles[:100]
    ]

    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        "Create today's SSB daily briefing from these articles. "
        "Use the current execution date for the date field.\n\n"
        + json.dumps(compact_articles, ensure_ascii=False)
    )

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=prompt,
        config={
            "temperature": 0.2,
            "response_mime_type": "application/json",
        },
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return json.loads(response.text)
