import html
import smtplib
from email.message import EmailMessage

from .config import settings


def _escape(value: str) -> str:
    return html.escape(str(value))


def render_html(brief: dict) -> str:
    date = _escape(brief.get("date", ""))

    parts = [
        f"<h1>SSB Daily Brief</h1><p><b>{date}</b></p>",
        "<p>Important current affairs selected for SSB preparation.</p>",
    ]

    for index, story in enumerate(brief.get("stories", []), start=1):
        parts.append(
            f"""
            <hr>
            <h2>{index}. {_escape(story.get("title", ""))}</h2>
            <p><b>Category:</b> {_escape(story.get("category", ""))}</p>
            <p>{_escape(story.get("summary", ""))}</p>
            <p><b>Why it matters for SSB:</b>
            {_escape(story.get("why_it_matters_for_ssb", ""))}</p>
            <p><b>Key facts:</b></p>
            <ul>
            {''.join(f"<li>{_escape(x)}</li>" for x in story.get("key_facts", []))}
            </ul>
            <p><b>Possible SSB questions:</b></p>
            <ul>
            {''.join(f"<li>{_escape(x)}</li>" for x in story.get("ssb_questions", []))}
            </ul>
            <p><a href="{_escape(story.get("url", ""))}">Read source</a>
            | Source: {_escape(story.get("source", ""))}</p>
            """
        )

    parts.append("<hr><h2>GD Topics</h2><ul>")
    parts.append("".join(f"<li>{_escape(x)}</li>" for x in brief.get("gd_topics", [])))
    parts.append("</ul>")

    parts.append("<h2>Lecturette Topics</h2><ul>")
    parts.append(
        "".join(f"<li>{_escape(x)}</li>" for x in brief.get("lecturette_topics", []))
    )
    parts.append("</ul>")

    parts.append("<h2>Quick Revision</h2><ol>")
    parts.append(
        "".join(f"<li>{_escape(x)}</li>" for x in brief.get("quick_revision", []))
    )
    parts.append("</ol>")

    return "\n".join(parts)


def render_text(brief: dict) -> str:
    lines = [
        "SSB DAILY BRIEF",
        brief.get("date", ""),
        "",
    ]

    for i, story in enumerate(brief.get("stories", []), 1):
        lines += [
            f"{i}. {story.get('title', '')}",
            f"Category: {story.get('category', '')}",
            story.get("summary", ""),
            f"SSB Angle: {story.get('why_it_matters_for_ssb', '')}",
            "Key facts:",
            *[f"- {x}" for x in story.get("key_facts", [])],
            "Questions:",
            *[f"- {x}" for x in story.get("ssb_questions", [])],
            f"Source: {story.get('source', '')} | {story.get('url', '')}",
            "",
        ]

    lines += ["GD Topics:", *[f"- {x}" for x in brief.get("gd_topics", [])], ""]
    lines += [
        "Lecturette Topics:",
        *[f"- {x}" for x in brief.get("lecturette_topics", [])],
        "",
    ]
    lines += [
        "Quick Revision:",
        *[f"- {x}" for x in brief.get("quick_revision", [])],
    ]

    return "\n".join(lines)


def send_email(brief: dict) -> None:
    required = [
        settings.smtp_host,
        settings.smtp_username,
        settings.smtp_password,
        settings.email_from,
        settings.email_to,
    ]

    if not all(required):
        raise RuntimeError("Email/SMTP configuration is incomplete.")

    msg = EmailMessage()
    msg["Subject"] = f"SSB Daily Brief | {brief.get('date', 'Today')}"
    msg["From"] = settings.email_from
    msg["To"] = settings.email_to

    msg.set_content(render_text(brief))
    msg.add_alternative(render_html(brief), subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(msg)

    print(f"[INFO] Email sent to {settings.email_to}")
