from __future__ import annotations

from yusha.formatting import (
    code_block,
    esc,
    human_bytes,
    human_duration,
    state_emoji,
)


def test_human_bytes() -> None:
    assert human_bytes(0) == "0 B"
    assert human_bytes(512) == "512 B"
    assert human_bytes(1024) == "1.0 KiB"
    assert human_bytes(1536) == "1.5 KiB"
    assert human_bytes(5 * 1024**3) == "5.0 GiB"


def test_human_duration() -> None:
    assert human_duration(45) == "45sn"
    assert human_duration(90) == "1dk"
    assert human_duration(3600) == "1sa"
    assert human_duration(3660) == "1sa 1dk"
    assert human_duration(90000) == "1g 1sa"
    assert human_duration(86400) == "1g"


def test_state_emoji() -> None:
    assert state_emoji("running") == "🟢"
    assert state_emoji("exited") == "🔴"
    assert state_emoji("bilinmeyen") == "❔"


def test_esc_and_code_block() -> None:
    assert esc("<a> & <b>") == "&lt;a&gt; &amp; &lt;b&gt;"
    assert code_block("") == "<pre>(boş)</pre>"
    assert code_block("x<y") == "<pre>x&lt;y</pre>"
