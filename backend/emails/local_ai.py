import csv
import json
import random
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlretrieve


APP_DIR = Path(__file__).resolve().parent
MODEL_PATH = APP_DIR / "model" / "local_email_model.json"
SEED_DATA_PATH = APP_DIR / "data" / "seed_email_corpus.jsonl"


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9']+", text.lower())


def _split_sentences(text: str) -> list[str]:
    chunks = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    return chunks or [text.strip()]


def _line_items(value: str) -> list[str]:
    lines = [line.strip(" -*\t") for line in value.splitlines() if line.strip()]
    if len(lines) == 1:
        semi = [part.strip() for part in lines[0].split(";") if part.strip()]
        return semi or lines
    return lines


def _weighted_choice(counter_map: dict[str, int], rng: random.Random) -> str:
    keys = list(counter_map.keys())
    weights = list(counter_map.values())
    return rng.choices(keys, weights=weights, k=1)[0]


def _generate_chain(
    starts: dict[str, int], transitions: dict[str, dict[str, int]], target_len: int, rng: random.Random
) -> str:
    if not starts:
        return ""
    current = _weighted_choice(starts, rng)
    words = [current]
    while len(words) < max(4, target_len):
        next_map = transitions.get(current)
        if not next_map:
            break
        nxt = _weighted_choice(next_map, rng)
        words.append(nxt)
        current = nxt
    return " ".join(words).strip()


def _to_serializable(counter_dict: dict[str, Counter]) -> dict[str, dict[str, int]]:
    return {k: dict(v) for k, v in counter_dict.items()}


def _train_from_records(records: list[dict[str, str]]) -> dict[str, Any]:
    subject_starts: Counter[str] = Counter()
    body_starts_by_tone: dict[str, Counter[str]] = defaultdict(Counter)
    subject_transitions: dict[str, Counter[str]] = defaultdict(Counter)
    body_transitions_by_tone: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    openers_by_tone: dict[str, Counter[str]] = defaultdict(Counter)
    closings_by_tone: dict[str, Counter[str]] = defaultdict(Counter)

    for row in records:
        tone = row.get("tone", "Professional").strip() or "Professional"
        subject_tokens = _tokenize(row.get("subject", ""))
        body_text = row.get("body", "").strip()
        body_tokens = _tokenize(body_text)

        if subject_tokens:
            subject_starts.update([subject_tokens[0]])
            for i in range(len(subject_tokens) - 1):
                subject_transitions[subject_tokens[i]].update([subject_tokens[i + 1]])

        if body_tokens:
            body_starts_by_tone[tone].update([body_tokens[0]])
            for i in range(len(body_tokens) - 1):
                body_transitions_by_tone[tone][body_tokens[i]].update([body_tokens[i + 1]])

        if body_text:
            sentences = _split_sentences(body_text)
            openers_by_tone[tone].update([sentences[0]])
            if len(sentences) > 1:
                closings_by_tone[tone].update([sentences[-1]])

    model = {
        "subject_starts": dict(subject_starts),
        "subject_transitions": _to_serializable(subject_transitions),
        "body_starts_by_tone": {tone: dict(counter) for tone, counter in body_starts_by_tone.items()},
        "body_transitions_by_tone": {
            tone: _to_serializable(next_map) for tone, next_map in body_transitions_by_tone.items()
        },
        "openers_by_tone": {tone: dict(counter) for tone, counter in openers_by_tone.items()},
        "closings_by_tone": {tone: dict(counter) for tone, counter in closings_by_tone.items()},
    }
    return model


def _load_seed_records() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with SEED_DATA_PATH.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _parse_dataset(path: Path) -> list[dict[str, str]]:
    if path.suffix.lower() == ".jsonl":
        rows = []
        with path.open("r", encoding="utf-8") as file_obj:
            for line in file_obj:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                rows.append(
                    {
                        "subject": str(row.get("subject", "")),
                        "body": str(row.get("body", row.get("email", row.get("text", "")))),
                        "tone": str(row.get("tone", "Professional")),
                    }
                )
        return rows

    if path.suffix.lower() == ".csv":
        rows = []
        with path.open("r", encoding="utf-8", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            for raw in reader:
                row = {k.lower(): (v or "") for k, v in raw.items()}
                body = row.get("body") or row.get("email") or row.get("message") or row.get("text") or ""
                subject = row.get("subject") or row.get("title") or ""
                if not body.strip():
                    continue
                rows.append(
                    {
                        "subject": subject,
                        "body": body,
                        "tone": row.get("tone", "Professional") or "Professional",
                    }
                )
        return rows

    raise ValueError("Supported dataset formats are .csv and .jsonl")


def train_local_model(dataset_path: str | None = None, dataset_url: str | None = None) -> dict[str, Any]:
    if dataset_path and dataset_url:
        raise ValueError("Provide either dataset_path or dataset_url, not both.")

    records: list[dict[str, str]]
    if dataset_path:
        records = _parse_dataset(Path(dataset_path))
    elif dataset_url:
        parsed = urlparse(dataset_url)
        suffix = Path(parsed.path).suffix.lower() or ".csv"
        download_path = APP_DIR / "data" / f"downloaded_dataset{suffix}"
        download_path.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(dataset_url, download_path)
        records = _parse_dataset(download_path)
    else:
        records = _load_seed_records()

    if not records:
        raise ValueError("No usable rows found for training.")

    model = _train_from_records(records)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MODEL_PATH.open("w", encoding="utf-8") as model_file:
        json.dump(model, model_file)
    _load_model.cache_clear()
    return model


@lru_cache(maxsize=1)
def _load_model() -> dict[str, Any]:
    if MODEL_PATH.exists():
        with MODEL_PATH.open("r", encoding="utf-8") as model_file:
            return json.load(model_file)
    return _train_from_records(_load_seed_records())


def _tone_variant(tone: str) -> str:
    normalized = tone.strip() if tone else "Professional"
    return normalized if normalized in {"Professional", "Friendly", "Persuasive", "Formal", "Concise"} else "Professional"


def _formal_greeting(tone: str, recipient: str) -> str:
    if tone == "Formal":
        return f"Dear {recipient},"
    return f"Hi {recipient},"


def _signoff(tone: str, sender_name: str) -> str:
    if tone == "Formal":
        return f"Kind regards,\n{sender_name}"
    if tone == "Friendly":
        return f"Warm regards,\n{sender_name}"
    return f"Best regards,\n{sender_name}"


def generate_local_ai_email(data: dict[str, Any]) -> dict[str, str]:
    model = _load_model()
    tone = _tone_variant(str(data.get("tone", "Professional")))
    seed = "|".join(
        [
            str(data.get("sender_name", "")),
            str(data.get("recipient_name", "")),
            str(data.get("purpose", "")),
            str(data.get("key_points", "")),
            tone,
            str(data.get("length", "Medium")),
        ]
    )
    rng = random.Random(seed)

    subject_core = _generate_chain(
        model.get("subject_starts", {}),
        model.get("subject_transitions", {}),
        7 if str(data.get("length", "Medium")) == "Short" else 10,
        rng,
    ).title()
    if not subject_core:
        subject_core = "Following Up On Next Steps"
    subject = f"{subject_core}: {str(data.get('purpose', '')).strip()[:48]}".strip(": ")

    starts_by_tone = model.get("body_starts_by_tone", {}).get(tone) or model.get("body_starts_by_tone", {}).get("Professional", {})
    transitions_by_tone = model.get("body_transitions_by_tone", {}).get(tone) or model.get("body_transitions_by_tone", {}).get("Professional", {})

    length = str(data.get("length", "Medium"))
    body_words = 55 if length == "Short" else 90 if length == "Medium" else 130
    generated_paragraph = _generate_chain(starts_by_tone, transitions_by_tone, body_words, rng)
    if generated_paragraph:
        generated_paragraph = generated_paragraph[0].upper() + generated_paragraph[1:] + "."
    else:
        generated_paragraph = "I wanted to follow up with a clear summary and next steps."

    openers = model.get("openers_by_tone", {}).get(tone) or model.get("openers_by_tone", {}).get("Professional", {})
    opener = _weighted_choice(openers, rng) if openers else "I hope you are doing well."

    recipient = str(data.get("recipient_name", "there")).strip() or "there"
    sender_name = str(data.get("sender_name", "Sender")).strip() or "Sender"
    key_points = _line_items(str(data.get("key_points", "")))
    key_points_text = "\n".join(f"- {point}" for point in key_points[:5]) if key_points else "- Share the latest update\n- Align on next steps"

    context = str(data.get("additional_context", "")).strip()
    context_line = f"\n\nAdditional context: {context}" if context else ""
    cta = str(data.get("call_to_action", "")).strip() or "Please let me know a good time to continue this discussion."

    body = (
        f"{_formal_greeting(tone, recipient)}\n\n"
        f"{opener}\n\n"
        f"I'm reaching out regarding {str(data.get('purpose', 'our discussion')).strip().lower()}.\n"
        f"{generated_paragraph}\n\n"
        f"Key points:\n{key_points_text}"
        f"{context_line}\n\n"
        f"{cta}\n\n"
        f"{_signoff(tone, sender_name)}"
    )
    return {"subject": subject, "body": body}
