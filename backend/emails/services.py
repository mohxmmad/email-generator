import json
import os
from typing import Any

from groq import Groq
from groq import APIError

from .local_ai import generate_local_ai_email


def _strip_code_fences(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3:
            cleaned = "\n".join(lines[1:-1]).strip()
    return cleaned


def _extract_generated_email(raw_content: str) -> dict[str, str]:
    cleaned = _strip_code_fences(raw_content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("AI response was not valid JSON.") from exc
    subject = parsed.get("subject", "").strip()
    body = parsed.get("body", "").strip()
    if not subject or not body:
        raise ValueError("AI response is missing subject or body.")
    return {"subject": subject, "body": body}


def _build_prompt(data: dict[str, Any]) -> str:
    return (
        "Create a polished email based on this brief.\n"
        f"Sender name: {data['sender_name']}\n"
        f"Sender role: {data.get('sender_role') or 'N/A'}\n"
        f"Recipient name: {data['recipient_name']}\n"
        f"Recipient role: {data.get('recipient_role') or 'N/A'}\n"
        f"Company: {data.get('company') or 'N/A'}\n"
        f"Purpose: {data['purpose']}\n"
        f"Key points: {data['key_points']}\n"
        f"Additional context: {data.get('additional_context') or 'N/A'}\n"
        f"Call to action: {data.get('call_to_action') or 'N/A'}\n"
        f"Tone: {data['tone']}\n"
        f"Length target: {data['length']}\n"
        f"Language: {data.get('language') or 'English'}\n\n"
        "Output strictly as JSON with this exact shape:\n"
        '{"subject":"...","body":"..."}'
    )


def generate_email(data: dict[str, Any]) -> dict[str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return generate_local_ai_email(data)

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
    try:
        completion = client.chat.completions.create(
            model=model,
            temperature=0.7,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert communications assistant. "
                        "Write high-quality emails and follow the requested JSON output strictly."
                    ),
                },
                {"role": "user", "content": _build_prompt(data)},
            ],
        )
    except APIError as exc:
        if os.getenv("LOCAL_FALLBACK_ON_PROVIDER_ERROR", "True").lower() == "true":
            return generate_local_ai_email(data)
        raise exc

    content = completion.choices[0].message.content
    if not content:
        raise ValueError("AI response was empty.")
    return _extract_generated_email(content)
