"""Regenerates the README screenshots and the social-preview banner.

Not part of the `tend` package or its tests -- a repo-maintenance script.
Run with the dev venv: `venv/bin/python assets/generate.py`
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rich.console import Console
from rich.text import Text

from tend.render import ABYSS, DEEP, KELP, SHALLOW, URCHIN_COLOR, render_frame
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


def _social_banner_svg() -> str:
    """A readable-at-thumbnail-size OG/social-preview card -- not a terminal
    screenshot. Same palette as the real render, composed as a wordmark plus
    a decorative kelp row instead of literal (illegible-at-small-size) text."""
    heights = [90, 60, 130, 40, 170, 70, 110]
    bar_width, gap, x0, baseline = 125, 30, 100, 590
    bars = "".join(
        f'<rect x="{x0 + i * (bar_width + gap)}" y="{baseline - h}" '
        f'width="{bar_width}" height="{h}" rx="10" fill="{KELP}"/>'
        for i, h in enumerate(heights)
    )
    urchins = "".join(
        f'<circle cx="{x0 + i * (bar_width + gap) + bar_width / 2}" '
        f'cy="{baseline - heights[i] - 22}" r="11" fill="{URCHIN_COLOR}"/>'
        for i in (2, 4)
    )
    font = "ui-monospace, Menlo, 'Fira Code', monospace"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640">
  <defs>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{SHALLOW}"/>
      <stop offset="55%" stop-color="{DEEP}"/>
      <stop offset="100%" stop-color="{ABYSS}"/>
    </linearGradient>
  </defs>
  <rect width="1280" height="640" fill="{ABYSS}"/>
  <text x="112" y="230" font-family="{font}" font-size="150" font-weight="700" fill="{KELP}">tend</text>
  <text x="114" y="300" font-family="{font}" font-size="32" fill="#c9d8de">A kelp garden that grows from your Claude Code</text>
  <text x="114" y="344" font-family="{font}" font-size="32" fill="#c9d8de">session's own token usage. No score, just a glance.</text>
  <rect x="90" y="380" width="1100" height="230" rx="24" fill="url(#water)"/>
  {bars}
  {urchins}
</svg>'''


svg_path = ASSETS / "social-preview.svg"
svg_path.write_text(_social_banner_svg())
print("wrote social-preview.svg")

png_path = ASSETS / "social-preview.png"
env = dict(os.environ, DYLD_FALLBACK_LIBRARY_PATH="/opt/homebrew/lib")
try:
    subprocess.run(
        ["cairosvg", str(svg_path), "-o", str(png_path), "--output-width", "1280"],
        env=env,
        check=True,
    )
    print("wrote social-preview.png")
except (FileNotFoundError, subprocess.CalledProcessError) as e:
    print(f"skipped social-preview.png ({e}); cairosvg + libcairo required")
