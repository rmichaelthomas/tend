"""Regenerates the README screenshots from the real render/engine code.

Not part of the `tend` package or its tests -- a repo-maintenance script.
Run with the dev venv: `venv/bin/python assets/generate.py`
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rich.console import Console
from rich.text import Text

from tend.render import render_frame
from tend.state import Stalk, World

ASSETS = Path(__file__).resolve().parent


def _shot(world: World, tier: int, name: str) -> None:
    console = Console(record=True, width=90, force_terminal=True, color_system="truecolor")
    console.print(Text.from_ansi(render_frame(world, tier=tier)))
    console.save_svg(str(ASSETS / name), title="tend")
    print(f"wrote {name}")


calm = World(
    day=22,
    spend=4_213_552,
    seeds=180,
    stalks=[
        Stalk(height=7, base=0, urchins=0),
        Stalk(height=5, base=0, urchins=0),
        Stalk(height=6, base=0, urchins=0),
        Stalk(height=3, base=0, urchins=0),
        Stalk(height=8, base=0, urchins=0),
        Stalk(height=4, base=0, urchins=0),
        Stalk(height=5, base=0, urchins=1),
    ],
)
calm.last_event = "quiet. 1, 3 and 5 are getting tall."
_shot(calm, tier=1, name="hero.svg")

trouble = World(
    day=22,
    spend=61_204_311,
    seeds=40,
    stalks=[
        Stalk(height=5, base=0, urchins=0),
        Stalk(height=0, base=3, urchins=0),
        Stalk(height=3, base=2, urchins=2),
        Stalk(height=4, base=1, urchins=1),
        Stalk(height=6, base=0, urchins=0),
        Stalk(height=2, base=0, urchins=0),
        Stalk(height=7, base=0, urchins=0),
    ],
    chewed_this_tick=[3],
)
trouble.last_event = "3 goes next tick unless you press 3."
_shot(trouble, tier=0, name="trouble.svg")
