"""Parsing helpers for user-entered list values."""

from __future__ import annotations

import re

_LIST_SEPARATOR_RE = re.compile(r"[,，;；\r\n]+")


def parse_user_list(value: str, *, limit: int | None = None) -> list[str]:
    """Parse comma, semicolon, or newline separated user input.

    The web UI accepts pasted text files, which naturally contain one item per
    line.  Keeping this parser at the API boundary gives every client the same
    contract and avoids treating a whole text file as one field name.
    """

    items = list(dict.fromkeys(item.strip() for item in _LIST_SEPARATOR_RE.split(value) if item.strip()))
    return items if limit is None else items[:limit]
