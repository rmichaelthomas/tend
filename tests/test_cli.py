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


def test_draw_increments_streak_only_when_stalk_had_urchins(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[2].urchins = 1
    state.save(world, state_path)

    monkeypatch.setattr(cli, "_read_key", lambda: "3")
    monkeypatch.setattr(cli.feel, "animate_squish", lambda *a, **k: None)

    cli.cmd_draw(state_path=state_path)

    updated = state.load(state_path)
    assert updated.streak == 1
    assert updated.stalks[2].urchins == 0


def test_draw_does_not_increment_streak_on_empty_squish(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    world = state.World()
    state.save(world, state_path)

    monkeypatch.setattr(cli, "_read_key", lambda: "1")

    cli.cmd_draw(state_path=state_path)

    updated = state.load(state_path)
    assert updated.streak == 0


def test_draw_never_calls_engine_tick(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[0].urchins = 1
    state.save(world, state_path)

    monkeypatch.setattr(cli, "_read_key", lambda: "1")
    monkeypatch.setattr(cli.feel, "animate_squish", lambda *a, **k: None)

    called = {"tick": False}

    def fake_tick(*a, **k):
        called["tick"] = True

    monkeypatch.setattr(cli.engine, "tick", fake_tick)

    cli.cmd_draw(state_path=state_path)
    assert called["tick"] is False


def test_draw_message_is_not_stale_after_clearing_the_only_chewed_stalk(tmp_path, monkeypatch):
    from tend import message
    from tend.state import CHEWED

    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[2].base = CHEWED
    world.stalks[2].urchins = 1
    world.chewed_this_tick = [2]
    state.save(world, state_path)

    monkeypatch.setattr(cli, "_read_key", lambda: "3")
    monkeypatch.setattr(cli.feel, "animate_squish", lambda *a, **k: None)

    cli.cmd_draw(state_path=state_path)

    updated = state.load(state_path)
    assert updated.last_event != "3 is being chewed. press 3."
    assert updated.last_event == message.build(updated)
