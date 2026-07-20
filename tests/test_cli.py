import json
import subprocess
import time
from pathlib import Path

from tend import cli, state
from tend.state import DEAD

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
    assert updated.offsets[str(FIXTURE)] == FIXTURE.stat().st_size
    assert updated.last_event != ""


def test_tick_is_idempotent_once_offset_reaches_eof(tmp_path):
    state_path = tmp_path / "state.json"
    state.save(state.World(), state_path)
    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    first = state.load(state_path)

    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    second = state.load(state_path)

    assert second.spend == first.spend


def test_tick_tracks_offset_per_transcript_not_globally(tmp_path):
    """A new Claude Code session gets its own transcript file starting at
    byte 0. If tend tracked one global offset, ticking a long-lived
    session's transcript first (advancing the offset past this short one's
    total length) would make every later tick against the new transcript
    read zero bytes -- seek() past EOF returns no data, not an error -- so
    real usage in the new session would never be recorded."""
    state_path = tmp_path / "state.json"
    state.save(state.World(), state_path)

    cli.cmd_tick(str(FIXTURE), state_path=state_path)
    after_first = state.load(state_path)
    assert after_first.spend > 0

    other_session = tmp_path / "other_session.jsonl"
    other_session.write_text(
        '{"type":"assistant","message":{"usage":{"input_tokens":10,"output_tokens":1000}}}\n'
    )
    assert other_session.stat().st_size < FIXTURE.stat().st_size

    cli.cmd_tick(str(other_session), state_path=state_path)
    after_second = state.load(state_path)

    assert after_second.spend > after_first.spend


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


def test_read_key_falls_back_gracefully_when_stdin_is_not_a_tty(monkeypatch):
    import io

    import termios

    def fake_tcgetattr(fd):
        raise termios.error(19, "Operation not supported by device")

    monkeypatch.setattr("termios.tcgetattr", fake_tcgetattr)
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO(""))

    assert cli._read_key() == ""


def test_draw_header_not_corrupted_by_large_spend_number(tmp_path, monkeypatch, capsys):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.spend = 78_488_588
    world.seeds = 7635
    state.save(world, state_path)

    monkeypatch.setattr(cli, "_read_key", lambda: "x")

    cli.cmd_draw(state_path=state_path)

    captured = capsys.readouterr()
    first_line = captured.out.splitlines()[0]
    assert "78,488,588" in first_line
    assert "seeds" in first_line
    assert "7635" in first_line


def test_squish_command_clears_urchins_and_increments_streak(tmp_path, capsys):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[2].urchins = 2
    state.save(world, state_path)

    cli.cmd_squish(2, state_path=state_path)

    updated = state.load(state_path)
    assert updated.stalks[2].urchins == 0
    assert updated.streak == 1
    captured = capsys.readouterr()
    assert captured.out != ""


def test_squish_command_does_not_increment_streak_on_empty_stalk(tmp_path):
    state_path = tmp_path / "state.json"
    state.save(state.World(), state_path)

    cli.cmd_squish(0, state_path=state_path)

    updated = state.load(state_path)
    assert updated.streak == 0


def test_squish_command_out_of_range_index_is_a_noop(tmp_path, capsys):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[0].urchins = 1
    state.save(world, state_path)

    cli.cmd_squish(99, state_path=state_path)

    updated = state.load(state_path)
    assert updated.stalks[0].urchins == 1
    captured = capsys.readouterr()
    assert captured.out == ""


def test_squish_command_does_not_stale_the_message_it_clears(tmp_path):
    from tend import message
    from tend.state import CHEWED

    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[4].base = CHEWED
    world.stalks[4].urchins = 1
    world.chewed_this_tick = [4]
    state.save(world, state_path)

    cli.cmd_squish(4, state_path=state_path)

    updated = state.load(state_path)
    assert updated.last_event != "5 is being chewed. press 5."
    assert updated.last_event == message.build(updated)


def test_main_squish_subcommand_parses_stalk_and_squishes(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[5].urchins = 1
    state.save(world, state_path)

    captured_index = {}

    def fake_cmd_squish(index, state_path=None):
        captured_index["index"] = index

    monkeypatch.setattr(cli, "cmd_squish", fake_cmd_squish)
    cli.main(["squish", "6"])

    assert captured_index["index"] == 5


def test_status_text_mode_never_mutates_state(tmp_path, capsys):
    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[1].urchins = 2
    state.save(world, state_path)
    before = state.load(state_path)

    cli.cmd_status(False, state_path=state_path)

    after = state.load(state_path)
    assert after == before
    captured = capsys.readouterr()
    assert captured.out != ""


def test_status_json_mode_never_mutates_state_and_reports_total_urchins(tmp_path, capsys):
    state_path = tmp_path / "state.json"
    history_path = tmp_path / "history.json"
    world = state.World()
    world.stalks[1].urchins = 2
    world.stalks[4].urchins = 3
    state.save(world, state_path)
    before = state.load(state_path)

    cli.cmd_status(True, state_path=state_path, history_path=history_path)

    after = state.load(state_path)
    assert after == before
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["total_urchins"] == 5
    assert payload["world"]["day"] == before.day
    assert "history" in payload
    assert payload["history"]["total_ticks"] == 0


def test_tick_records_history_across_deaths_revivals_and_urchins(tmp_path):
    state_path = tmp_path / "state.json"
    history_path = tmp_path / "history.json"
    world = state.World()
    world.stalks[0].base = DEAD
    world.stalks[0].height = 0
    world.seeds = 100
    state.save(world, state_path)

    cli.cmd_tick(str(FIXTURE), state_path=state_path, history_path=history_path)

    history = state.load_history(history_path)
    assert history.total_ticks == 1
    updated = state.load(state_path)
    assert history.total_revivals == len(updated.revived_this_tick)
    assert history.total_urchins_spawned == len(updated.spawned_indices_this_tick)


def test_tick_records_biggest_dieoff(tmp_path):
    state_path = tmp_path / "state.json"
    history_path = tmp_path / "history.json"
    world = state.World()
    world.stalks[0].base = DEAD
    world.stalks[0].height = 3
    world.stalks[1].base = DEAD
    world.stalks[1].height = 2
    state.save(world, state_path)

    empty_fixture = tmp_path / "empty.jsonl"
    empty_fixture.write_text("")
    cli.cmd_tick(str(empty_fixture), state_path=state_path, history_path=history_path)

    history = state.load_history(history_path)
    updated = state.load(state_path)
    assert history.biggest_dieoff == len(updated.died_this_tick)
    assert history.biggest_dieoff == 2
    assert history.biggest_dieoff_day == updated.day


def test_squish_records_history_only_when_had_urchins(tmp_path):
    state_path = tmp_path / "state.json"
    history_path = tmp_path / "history.json"
    world = state.World()
    world.stalks[2].urchins = 1
    state.save(world, state_path)

    cli.cmd_squish(2, state_path=state_path, history_path=history_path)

    history = state.load_history(history_path)
    assert history.total_squishes == 1
    assert history.longest_squish_streak == 1

    cli.cmd_squish(0, state_path=state_path, history_path=history_path)
    history_again = state.load_history(history_path)
    assert history_again.total_squishes == 1


def test_main_status_subcommand_parses_json_flag(monkeypatch):
    captured = {}

    def fake_cmd_status(as_json, **kwargs):
        captured["as_json"] = as_json

    monkeypatch.setattr(cli, "cmd_status", fake_cmd_status)
    cli.main(["status", "--json"])

    assert captured["as_json"] is True


def test_draw_does_not_crash_and_does_not_squish_when_stdin_is_not_a_tty(tmp_path, monkeypatch):
    import io

    import termios

    state_path = tmp_path / "state.json"
    world = state.World()
    world.stalks[0].urchins = 1
    state.save(world, state_path)

    def fake_tcgetattr(fd):
        raise termios.error(19, "Operation not supported by device")

    monkeypatch.setattr("termios.tcgetattr", fake_tcgetattr)
    monkeypatch.setattr(cli.sys, "stdin", io.StringIO(""))

    cli.cmd_draw(state_path=state_path)

    updated = state.load(state_path)
    assert updated.stalks[0].urchins == 1
