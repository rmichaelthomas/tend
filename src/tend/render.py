"""The textual/rich view. One frame in, one string out."""
from __future__ import annotations

import io

from rich.console import Console
from rich.text import Text

from tend.state import DEAD, MAX_HEIGHT, STALK_COUNT, World

BLOCK_WIDTH = 4
GAP = " "

SHALLOW = "#12587a"
DEEP = "#0a2f47"
ABYSS = "#04141f"
KELP = "#6fd66f"
URCHIN_COLOR = "#c9d94a"
CHEWED_COLOR = "#e8a33d"
DYING_COLOR = "#e0523f"
SEED_COLOR = "#5fe3d6"
BURNT = "#3c1f1c"

BASE_SYMBOLS = {0: "▓", 1: "▒", 2: "░", 3: "×"}
BASE_COLORS = {0: KELP, 1: CHEWED_COLOR, 2: DYING_COLOR, 3: BURNT}

SPEND_WARM = 10_000_000
SPEND_HOT = 50_000_000

TIER_BRIGHTEN = {0: 0.0, 1: 0.06, 2: 0.12, 3: 0.18}


def _brighten(hex_color: str, amount: float) -> str:
    amount = max(0.0, min(1.0, amount))
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    r = min(255, round(r + (255 - r) * amount))
    g = min(255, round(g + (255 - g) * amount))
    b = min(255, round(b + (255 - b) * amount))
    return f"#{r:02x}{g:02x}{b:02x}"


def _spend_color(spend: int) -> str:
    if spend >= SPEND_HOT:
        return DYING_COLOR
    if spend >= SPEND_WARM:
        return CHEWED_COLOR
    return KELP


def _water_row_color(row_from_top: int, tier: int) -> str:
    stop = row_from_top * 3 // MAX_HEIGHT
    base = [SHALLOW, DEEP, ABYSS][min(stop, 2)]
    return _brighten(base, TIER_BRIGHTEN.get(tier, 0.0))


def render_frame(
    world: World,
    tier: int = 0,
    brightness: dict[int, float] | None = None,
    loss_index: int | None = None,
    loss_progress: float = 0.0,
) -> str:
    brightness = brightness or {}
    console = Console(file=io.StringIO(), force_terminal=True, color_system="truecolor", width=80)
    text = Text()

    spend_str = f"{world.spend:,}"
    header_left = f" day {world.day}"
    header_right = f"tokens {spend_str} · seeds {world.seeds}"
    total_width = STALK_COUNT * BLOCK_WIDTH + (STALK_COUNT - 1)
    pad = max(1, total_width + 12 - len(header_left) - len(header_right))
    text.append(header_left)
    text.append(" " * pad)
    text.append("tokens ")
    text.append(spend_str, style=_spend_color(world.spend))
    text.append(" · seeds ")
    text.append(str(world.seeds), style=SEED_COLOR)
    text.append("\n\n")

    for row_from_top in range(MAX_HEIGHT):
        height_level = MAX_HEIGHT - row_from_top
        water_style = f"on {_water_row_color(row_from_top, tier)}"
        for i in range(STALK_COUNT):
            stalk = world.stalks[i]
            show_stem = stalk.base != DEAD and stalk.height >= height_level
            cell = "|".center(BLOCK_WIDTH) if show_stem else " " * BLOCK_WIDTH
            style = f"{KELP} {water_style}" if show_stem else water_style
            text.append(cell, style=style)
            if i < STALK_COUNT - 1:
                text.append(GAP, style=water_style)
        text.append("\n")

    for i in range(STALK_COUNT):
        stalk = world.stalks[i]
        symbol = BASE_SYMBOLS[stalk.base]
        color = BASE_COLORS[stalk.base]
        if loss_index == i and loss_progress:
            color = _brighten(BURNT, 0.0)
        else:
            color = _brighten(color, brightness.get(i, 0.0))
        text.append(symbol * BLOCK_WIDTH, style=color)
        if i < STALK_COUNT - 1:
            text.append(GAP)
    text.append("\n")

    for i in range(STALK_COUNT):
        text.append(str(i + 1).center(BLOCK_WIDTH))
        if i < STALK_COUNT - 1:
            text.append(GAP)
    text.append("\n")

    for i in range(STALK_COUNT):
        stalk = world.stalks[i]
        count = min(stalk.urchins, BLOCK_WIDTH)
        cell = ("●" * count).center(BLOCK_WIDTH) if count else " " * BLOCK_WIDTH
        style = URCHIN_COLOR if count else ""
        text.append(cell, style=style)
        if i < STALK_COUNT - 1:
            text.append(GAP)
    text.append("\n\n")

    text.append(f" {world.last_event}")

    console.print(text)
    return console.file.getvalue()
