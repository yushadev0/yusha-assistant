from __future__ import annotations

import html

_UNITS = ["B", "KiB", "MiB", "GiB", "TiB", "PiB"]


def human_bytes(n: float) -> str:
    value = float(n)
    for unit in _UNITS:
        if abs(value) < 1024 or unit == _UNITS[-1]:
            if unit == "B":
                return f"{int(value)} B"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} {_UNITS[-1]}"


def human_duration(seconds: float) -> str:
    total = int(seconds)
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, secs = divmod(rem, 60)
    if days:
        return f"{days}g {hours}sa" if hours else f"{days}g"
    if hours:
        return f"{hours}sa {minutes}dk" if minutes else f"{hours}sa"
    if minutes:
        return f"{minutes}dk"
    return f"{secs}sn"


def state_emoji(state: str) -> str:
    return {
        "running": "🟢",
        "restarting": "🟡",
        "paused": "⏸️",
        "exited": "🔴",
        "dead": "💀",
        "created": "⚪",
    }.get(state, "❔")


def esc(text: object) -> str:
    """Telegram HTML parse mode için kaçış."""
    return html.escape(str(text), quote=False)


def code_block(text: str) -> str:
    return f"<pre>{esc(text) if text else '(boş)'}</pre>"
