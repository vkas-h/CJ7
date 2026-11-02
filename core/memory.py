import json
import os
import re
import tempfile

from datetime import datetime
from pathlib import Path

from config.settings import config
from services.llm import generate_with_model


MEMORY_DIR = Path(config.get("data_dir", "data")) / "memory"

USER_MEMORY_FILE = MEMORY_DIR / "USER.md"
GENERAL_MEMORY_FILE = MEMORY_DIR / "MEMORY.md"

MAX_MEMORY_FILE_CHARS = 12000
MAX_NEW_FACTS = 12


def _read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
    except OSError:
        raise


def _atomic_write(path, content):
    """
    Write to a temporary file in the same directory, then replace
    the destination. This avoids partially written memory files.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, temporary_path = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent)
    )

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temporary_path, path)

    except Exception:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise


def read_life_memory():
    return {
        "user": _read_file(USER_MEMORY_FILE),
        "general": _read_file(GENERAL_MEMORY_FILE)
    }


def _clean_fact(value):
    if not isinstance(value, str):
        return ""

    value = re.sub(r"\s+", " ", value).strip()

    if len(value) < 8 or len(value) > 350:
        return ""

    if value.lower() in {
        "unknown",
        "none",
        "n/a",
        "not specified"
    }:
        return ""

    return value


def _validate_extraction(data):
    """
    Expected shape:
    {
        "user_facts": ["..."],
        "general_facts": ["..."]
    }
    """
    if not isinstance(data, dict):
        raise ValueError("Memory extraction must be a JSON object.")

    user_facts = data.get("user_facts", [])
    general_facts = data.get("general_facts", [])

    if not isinstance(user_facts, list):
        raise ValueError("user_facts must be a list.")

    if not isinstance(general_facts, list):
        raise ValueError("general_facts must be a list.")

    user_facts = [
        fact for fact in (_clean_fact(x) for x in user_facts)
        if fact
    ][:MAX_NEW_FACTS]

    general_facts = [
        fact for fact in (_clean_fact(x) for x in general_facts)
        if fact
    ][:MAX_NEW_FACTS]

    return user_facts, general_facts


def _append_facts(path, facts, provenance):
    if not facts:
        return 0

    existing = _read_file(path).strip()

    timestamp = datetime.now().isoformat(timespec="seconds")

    additions = [
        f"- {fact} "
        f"(source: session {provenance['session_id']}, "
        f"through message {provenance['message_position']}; "
        f"recorded {timestamp})"
        for fact in facts
    ]

    new_content = existing

    if not new_content:
        new_content = "# Persistent Memory"

    new_content += "\n" + "\n".join(additions) + "\n"

    if len(new_content) > MAX_MEMORY_FILE_CHARS:
        raise ValueError(
            f"{path.name} would exceed "
            f"{MAX_MEMORY_FILE_CHARS} characters."
        )

    _atomic_write(path, new_content)
    return len(facts)


def extract_and_save_memory(
    transcript,
    session_id,
    message_position
):
    """
    Extract durable, explicitly supported information from a transcript.

    The model is instructed not to infer sensitive traits, temporary
    emotions, guesses, or information merely mentioned about others.

    Returns a report. If extraction fails, existing memory is unchanged.
    """
    if not transcript:
        return {
            "saved": 0,
            "reason": "Empty transcript."
        }

    conversation = []

    for message in transcript:
        role = getattr(message, "role", "")
        content = getattr(message, "content", "")

        if role not in {"user", "assistant"}:
            continue

        if not content:
            continue

        conversation.append({
            "role": role,
            "content": str(content)[:4000]
        })

    if not conversation:
        return {
            "saved": 0,
            "reason": "No user or assistant messages."
        }

    prompt = """
You extract durable memory from a conversation.

Return only valid JSON with this exact structure:
{
  "user_facts": [],
  "general_facts": []
}

Rules:
- Save only stable facts explicitly stated by the USER.
- Do not infer facts from hints or assistant statements.
- Do not save temporary moods, one-time questions, guesses,
  passwords, account numbers, secrets, or sensitive personal data.
- Do not turn a fact about another person into a fact about the user.
- Prefer useful preferences, long-term projects, persistent goals,
  technical environment, and durable user constraints.
- Do not duplicate facts already present in the existing memory.
- Keep each fact concise and independently understandable.
- If nothing qualifies, return empty arrays.
- user_facts are about the user.
- general_facts are durable project or workflow facts.
"""

    existing = read_life_memory()

    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": (
                "EXISTING USER MEMORY:\n"
                + existing["user"][-6000:]
                + "\n\nEXISTING GENERAL MEMORY:\n"
                + existing["general"][-6000:]
                + "\n\nCONVERSATION:\n"
                + json.dumps(conversation, ensure_ascii=False)
            )
        }
    ]

    response = generate_with_model(
        messages,
        format="json",
        temperature=0.0,
        num_predict=1000
    )

    raw = getattr(response, "message", None)

    if raw is None:
        raise ValueError("Memory model returned no message.")

    raw_content = getattr(raw, "content", "")

    if not raw_content:
        raise ValueError("Memory model returned empty content.")

    data = json.loads(raw_content)
    user_facts, general_facts = _validate_extraction(data)

    provenance = {
        "session_id": str(session_id),
        "message_position": int(message_position)
    }

    # Validate both destination files before changing either one.
    user_existing = _read_file(USER_MEMORY_FILE).strip()
    general_existing = _read_file(GENERAL_MEMORY_FILE).strip()

    user_content = user_existing or "# Persistent User Memory"
    general_content = general_existing or "# Persistent Project Memory"

    timestamp = datetime.now().isoformat(timespec="seconds")

    user_additions = [
        f"- {fact} (source: session {session_id}, "
        f"through message {message_position}; recorded {timestamp})"
        for fact in user_facts
    ]

    general_additions = [
        f"- {fact} (source: session {session_id}, "
        f"through message {message_position}; recorded {timestamp})"
        for fact in general_facts
    ]

    if user_additions:
        user_content += "\n" + "\n".join(user_additions) + "\n"

    if general_additions:
        general_content += "\n" + "\n".join(general_additions) + "\n"

    if len(user_content) > MAX_MEMORY_FILE_CHARS:
        raise ValueError("USER.md would exceed its size limit.")

    if len(general_content) > MAX_MEMORY_FILE_CHARS:
        raise ValueError("MEMORY.md would exceed its size limit.")

    # Each file is replaced atomically. The original transcript remains safe.
    if user_additions:
        _atomic_write(USER_MEMORY_FILE, user_content)

    if general_additions:
        _atomic_write(GENERAL_MEMORY_FILE, general_content)

    return {
        "saved": len(user_facts) + len(general_facts),
        "user_facts": len(user_facts),
        "general_facts": len(general_facts),
        "provenance": provenance
    }