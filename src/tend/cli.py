"""CLI entry points: tick, draw. Only these touch the terminal or the state file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tend import engine, feel, message, render, state, transcript


def cmd_tick(transcript_path: str, state_path: Path | None = None) -> None:
    world = state.load(state_path)
    delta, new_offset = transcript.read_delta(transcript_path, world.last_offset)
    world.last_offset = new_offset
    engine.tick(world, delta)
    world.streak = max(0, world.streak - 1)
    world.last_event = message.build(world)
    state.save(world, state_path)
    sys.stdout.write("\a")
    sys.stdout.flush()


def _read_key() -> str:
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return ch


def cmd_draw(state_path: Path | None = None) -> None:
    from rich.console import Console

    world = state.load(state_path)
    console = Console()
    tier = feel.streak_tier(world.streak)
    console.print(render.render_frame(world, tier=tier))

    key = _read_key()
    if key in "1234567":
        index = int(key) - 1
        had_urchins = world.stalks[index].urchins > 0
        engine.squish(world, index)
        if had_urchins:
            world.streak += 1
            feel.animate_squish(console, world, index, render.render_frame, cleared_count=1)
        world.last_event = message.build(world)
        state.save(world, state_path)
        tier = feel.streak_tier(world.streak)
        console.print(render.render_frame(world, tier=tier))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tend")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tick_parser = subparsers.add_parser("tick")
    tick_parser.add_argument("--transcript", default=None)

    subparsers.add_parser("draw")

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

    return 1


if __name__ == "__main__":
    sys.exit(main())
