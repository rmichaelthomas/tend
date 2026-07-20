"""CLI entry points: tick, draw. Only these touch the terminal or the state file."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from tend import engine, feel, message, render, state, transcript


def _record_tick_history(world: state.World, history: state.History) -> None:
    history.total_ticks += 1
    history.total_deaths += len(world.died_this_tick)
    history.total_revivals += len(world.revived_this_tick)
    history.total_urchins_spawned += len(world.spawned_indices_this_tick)
    history.longest_quiet_streak = max(history.longest_quiet_streak, world.quiet_ticks)
    dieoff = len(world.died_this_tick)
    if dieoff > history.biggest_dieoff:
        history.biggest_dieoff = dieoff
        history.biggest_dieoff_day = world.day


def cmd_tick(transcript_path: str, state_path: Path | None = None, history_path: Path | None = None) -> None:
    world = state.load(state_path)
    delta, new_offset = transcript.read_delta(transcript_path, world.offsets.get(transcript_path, 0))
    world.offsets[transcript_path] = new_offset
    engine.tick(world, delta)
    world.streak = max(0, world.streak - 1)
    world.last_event = message.build(world)
    state.save(world, state_path)

    history = state.load_history(history_path)
    _record_tick_history(world, history)
    state.save_history(history, history_path)

    sys.stdout.write("\a")
    sys.stdout.flush()


def _read_key() -> str:
    import termios
    import tty

    try:
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
    except (termios.error, OSError):
        # stdin isn't a real TTY (e.g. run non-interactively) — no raw mode
        # possible, so no live keypress is available. Read whatever's there
        # (EOF on a closed/redirected stdin returns "" without blocking).
        return sys.stdin.read(1)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def _apply_squish(
    world: state.World,
    index: int,
    console=None,
    history: state.History | None = None,
) -> None:
    had_urchins = world.stalks[index].urchins > 0
    engine.squish(world, index)
    if had_urchins:
        world.streak += 1
        if history is not None:
            history.total_squishes += 1
            history.longest_squish_streak = max(history.longest_squish_streak, world.streak)
        if console is not None:
            feel.animate_squish(console, world, index, render.render_frame, cleared_count=1)
    world.chewed_this_tick = [i for i in world.chewed_this_tick if i != index]
    world.spawned_indices_this_tick = [i for i in world.spawned_indices_this_tick if i != index]
    world.last_event = message.build(world)


def cmd_draw(state_path: Path | None = None, history_path: Path | None = None) -> None:
    from rich.console import Console

    world = state.load(state_path)
    console = Console()
    tier = feel.streak_tier(world.streak)
    sys.stdout.write(render.render_frame(world, tier=tier))

    key = _read_key()
    if key and key in "1234567":
        index = int(key) - 1
        history = state.load_history(history_path)
        _apply_squish(world, index, console=console, history=history)
        state.save(world, state_path)
        state.save_history(history, history_path)
        tier = feel.streak_tier(world.streak)
        sys.stdout.write(render.render_frame(world, tier=tier))


def cmd_squish(index: int, state_path: Path | None = None, history_path: Path | None = None) -> None:
    """Non-interactive squish: no keypress, no animation. For a caller (e.g.
    an assistant relaying a chat reply) that has no live terminal to read a
    key from or animate into."""
    world = state.load(state_path)
    if not (0 <= index < len(world.stalks)):
        return

    history = state.load_history(history_path)
    _apply_squish(world, index, history=history)
    state.save(world, state_path)
    state.save_history(history, history_path)
    tier = feel.streak_tier(world.streak)
    sys.stdout.write(render.render_frame(world, tier=tier))


def cmd_status(as_json: bool, state_path: Path | None = None, history_path: Path | None = None) -> None:
    """Read-only peek: never mutates state, never waits for a key. The JSON
    form also includes lifetime history -- diagnostic data for whoever asks,
    never rendered in the ASCII art itself."""
    world = state.load(state_path)
    if as_json:
        history = state.load_history(history_path)
        payload = {
            "world": asdict(world),
            "history": asdict(history),
            "total_urchins": sum(s.urchins for s in world.stalks),
        }
        print(json.dumps(payload))
        return

    tier = feel.streak_tier(world.streak)
    sys.stdout.write(render.render_frame(world, tier=tier))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tick_parser = subparsers.add_parser("tick")
    tick_parser.add_argument("--transcript", default=None)

    subparsers.add_parser("draw")

    squish_parser = subparsers.add_parser("squish")
    squish_parser.add_argument("stalk", type=int)

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "tick":
        transcript_path = args.transcript
        if not transcript_path:
            try:
                payload = json.load(sys.stdin)
                transcript_path = payload.get("transcript_path")
            except Exception:
                transcript_path = None
        if transcript_path:
            cmd_tick(transcript_path)
        return 0

    if args.command == "draw":
        cmd_draw()
        return 0

    if args.command == "squish":
        cmd_squish(args.stalk - 1)
        return 0

    if args.command == "status":
        cmd_status(args.json)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
