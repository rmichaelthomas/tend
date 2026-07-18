"""Feel-pass timing constants and the bounded animation loop.

Setting every *_MS constant to zero collapses every animation to a no-op,
producing the static §7 render. This module is cosmetic only: it never
imports tend.engine and never influences any World field engine.py reads.
"""
from __future__ import annotations

import time

from rich.live import Live

STREAK_TIERS = [3, 6, 10]

TICK_MS = 120
THUMP_MS = 200
THUMP_NEIGHBOR_MS = 150
LOSS_COLUMN_MS = 400
LOSS_WATER_MS = 600
STEP_MS = 20


def streak_tier(streak: int) -> int:
    tier = 0
    for threshold in STREAK_TIERS:
        if streak >= threshold:
            tier += 1
    return tier


def lerp_hex(a: str, b: str, t: float) -> str:
    t = max(0.0, min(1.0, t))
    ar, ag, ab = int(a[1:3], 16), int(a[3:5], 16), int(a[5:7], 16)
    br, bg, bb = int(b[1:3], 16), int(b[3:5], 16), int(b[5:7], 16)
    r = round(ar + (br - ar) * t)
    g = round(ag + (bg - ag) * t)
    bl = round(ab + (bb - ab) * t)
    return f"#{r:02x}{g:02x}{bl:02x}"


def _ease_out_steps(duration_ms: int, step_ms: int | None = None) -> list[float]:
    step = step_ms if step_ms is not None else STEP_MS
    if duration_ms <= 0 or step <= 0:
        return []
    n = max(1, duration_ms // step)
    return [1.0 - (i / n) ** 2 for i in range(n + 1)]


def animate_squish(console, world, index, render_frame, cleared_count: int) -> None:
    duration = THUMP_MS if cleared_count >= 3 else TICK_MS
    steps = _ease_out_steps(duration)
    if not steps:
        return

    neighbors = [i for i in (index - 1, index + 1) if 0 <= i < len(world.stalks)]

    with Live(console=console, transient=True, refresh_per_second=max(1, 1000 // max(STEP_MS, 1))) as live:
        elapsed_ms = 0
        for t in steps:
            brightness = {index: t}
            if cleared_count >= 3 and elapsed_ms <= THUMP_NEIGHBOR_MS:
                for n in neighbors:
                    brightness[n] = t * 0.4
            live.update(render_frame(world, brightness=brightness))
            time.sleep(STEP_MS / 1000)
            elapsed_ms += STEP_MS


def animate_loss(console, world, index, render_frame) -> None:
    steps = _ease_out_steps(max(LOSS_COLUMN_MS, LOSS_WATER_MS))
    if not steps:
        return

    with Live(console=console, transient=True, refresh_per_second=max(1, 1000 // max(STEP_MS, 1))) as live:
        for t in steps:
            live.update(render_frame(world, loss_index=index, loss_progress=1 - t))
            time.sleep(STEP_MS / 1000)
