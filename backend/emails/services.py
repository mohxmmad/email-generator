import json
import os
from typing import Any

from groq import Groq


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


def _build_local_email(data: dict[str, Any]) -> dict[str, str]:
    sender_name = data["sender_name"].strip()
    sender_role = data.get("sender_role", "").strip()
    recipient_name = data["recipient_name"].strip()
    recipient_role = data.get("recipient_role", "").strip()
    company = data.get("company", "").strip()
    purpose = data["purpose"].strip()
    key_points = data["key_points"].strip()
    additional_context = data.get("additional_context", "").strip()
    call_to_action = data.get("call_to_action", "").strip()
    tone = data["tone"].strip()

    subject_target = company or purpose
    subject = f"{purpose[:60]} - {subject_target[:30]}".strip(" -")

    greeting = f"Hi {recipient_name},"
    if tone == "Formal":
        greeting = f"Dear {recipient_name},"

    opener = f"I hope you are doing well. I am reaching out regarding {purpose.lower()}."
    if tone == "Friendly":
        opener = f"I hope you're having a great day. I wanted to connect about {purpose.lower()}."
    if tone == "Concise":
        opener = f"I'm writing about {purpose.lower()}."

    role_line = ""
    if sender_role or recipient_role or company:
        role_bits = [bit for bit in [recipient_role, company] if bit]
        to_info = ", ".join(role_bits)
        from_info = sender_role if sender_role else "my role"
        role_line = (
            f"As {from_info}, I believe this is relevant for you"
            f"{f' as {to_info}' if to_info else ''}."
        )

    context_line = f"Additional context: {additional_context}" if additional_context else ""
    cta_line = call_to_action if call_to_action else "Please let me know your thoughts."

    body_parts = [
        greeting,
        "",
        opener,
        role_line,
        f"Key points:\n{key_points}",
        context_line,
        cta_line,
        "",
        f"Best regards,\n{sender_name}",
    ]
    body = "\n".join([part for part in body_parts if part != ""])
    return {"subject": subject, "body": body}


def generate_email(data: dict[str, Any]) -> dict[str, str]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _build_local_email(data)

    client = Groq(api_key=api_key)
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
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

    content = completion.choices[0].message.content
    if not content:
        raise ValueError("AI response was empty.")
    return _extract_generated_email(content)
