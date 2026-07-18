import json
import subprocess
import time
from pathlib import Path

from tend import cli, state

FIXTURE = Path(__file__).parent / "fixtures" / "transcript_fixture.jsonl"
HOOK = Path(__file__).resolve().parents[1] / "hooks" / "stop_hook.sh"


def test_tick_advances_state_and_stays_under_100ms(tmp_path):
    state_path = tmp_path / "state.json"
    state.save(state.World(), state_path)

    start = time.monotonic()
    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    elapsed_ms = (time.monotonic() - start) * 1000

    assert elapsed_ms < 100
    updated = state.load(state_path)
    assert updated.spend > 0
    assert updated.last_offset == FIXTURE.stat().st_size
    assert updated.last_event != ""


def test_tick_is_idempotent_once_offset_reaches_eof(tmp_path):
    state_path = tmp_path / "state.json"
    state.save(state.World(), state_path)
    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    first = state.load(state_path)

    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    second = state.load(state_path)

    assert second.spend == first.spend


def test_stop_hook_exits_zero_even_without_tend_on_path(tmp_path):
    payload = json.dumps({"transcript_path": str(tmp_path / "missing.jsonl")})
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/bin:/bin"},
        timeout=5,
    )
    assert result.returncode == 0


def test_stop_hook_exits_zero_with_empty_stdin():
    result = subprocess.run(
        ["bash", str(HOOK)],
        input="",
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0
