from __future__ import annotations

import re


def safe_display_username(username: str | None) -> str:
    return f"@{username}" if username else "—"


def valid_name(value: str) -> bool:
    cleaned = re.sub(r"\s+", " ", value.strip())
    return 2 <= len(cleaned) <= 80 and not any(char.isdigit() for char in cleaned)
