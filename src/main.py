from .archive import save_brief
from .ai import generate_brief
from .emailer import send_email
from .news import fetch_all_news


def main():
    articles = fetch_all_news()

    if not articles:
        raise RuntimeError("No news articles were collected.")

    brief = generate_brief(articles)

    path = save_brief(brief)
    print(f"[INFO] Brief archived at {path}")

    send_email(brief)

    print("[INFO] SSB Daily Brief completed successfully.")


if __name__ == "__main__":
    main()
