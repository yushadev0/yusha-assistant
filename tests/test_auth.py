from __future__ import annotations

import pytest
from telegram.ext import ApplicationHandlerStop

from yusha.auth import make_guard


class _User:
    def __init__(self, uid: int) -> None:
        self.id = uid
        self.username = f"user{uid}"


class _Msg:
    def __init__(self) -> None:
        self.replies: list[str] = []

    async def reply_text(self, text: str, **_: object) -> None:
        self.replies.append(text)


class _Update:
    def __init__(self, uid: int | None) -> None:
        self.effective_user = _User(uid) if uid is not None else None
        self.effective_message = _Msg()


async def test_guard_blocks_stranger() -> None:
    guard = make_guard({111})
    upd = _Update(999)
    with pytest.raises(ApplicationHandlerStop):
        await guard(upd, None)  # type: ignore[arg-type]
    assert upd.effective_message.replies == ["⛔ Yetkin yok."]


async def test_guard_blocks_missing_user() -> None:
    guard = make_guard({111})
    with pytest.raises(ApplicationHandlerStop):
        await guard(_Update(None), None)  # type: ignore[arg-type]


async def test_guard_allows_admin() -> None:
    guard = make_guard({111})
    upd = _Update(111)
    await guard(upd, None)  # type: ignore[arg-type]
    assert upd.effective_message.replies == []
