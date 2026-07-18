"""JSONL transcript parsing: sum token usage across five classes."""
from __future__ import annotations

import json
from pathlib import Path


def read_delta(transcript_path: str, last_offset: int) -> tuple[dict, int]:
    totals = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}

    try:
        with open(Path(transcript_path), "rb") as f:
            f.seek(last_offset)
            data = f.read()
    except OSError:
        return totals, last_offset

    new_offset = last_offset + len(data)

    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue

        usage = obj.get("usage")
        if usage is None:
            message = obj.get("message")
            if isinstance(message, dict):
                usage = message.get("usage")
        if not isinstance(usage, dict):
            continue

        totals["input"] += usage.get("input_tokens", 0) or 0
        totals["output"] += usage.get("output_tokens", 0) or 0
        totals["cache_read"] += usage.get("cache_read_input_tokens", 0) or 0

        cache_creation = usage.get("cache_creation")
        if isinstance(cache_creation, dict):
            totals["cache_write"] += cache_creation.get("ephemeral_5m_input_tokens", 0) or 0
            totals["cache_write"] += cache_creation.get("ephemeral_1h_input_tokens", 0) or 0
        else:
            totals["cache_write"] += usage.get("cache_creation_input_tokens", 0) or 0

    return totals, new_offset
