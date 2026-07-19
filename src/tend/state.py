"""World and Stalk state, persisted to ~/.tend/state.json."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

STALK_COUNT = 7
MAX_HEIGHT = 8
BASE_STATES = ["healthy", "chewed", "dying", "dead"]
HEALTHY, CHEWED, DYING, DEAD = range(4)

STATE_PATH = Path.home() / ".tend" / "state.json"
HISTORY_PATH = Path.home() / ".tend" / "history.json"


@dataclass
class Stalk:
    height: int = 3
    base: int = 0
    urchins: int = 0


@dataclass
class World:
    day: int = 1
    spend: int = 0
    seeds: int = 0
    stalks: list[Stalk] = field(default_factory=lambda: [Stalk() for _ in range(STALK_COUNT)])
    last_offset: int = 0
    last_event: str = ""
    spawned_indices_this_tick: list[int] = field(default_factory=list)
    chewed_this_tick: list[int] = field(default_factory=list)
    died_this_tick: list[int] = field(default_factory=list)
    revived_this_tick: list[int] = field(default_factory=list)
    seeds_spent_this_tick: int = 0
    quiet_ticks: int = 0
    streak: int = 0


@dataclass
class History:
    """Lifetime trends across sessions. Never rendered in the ASCII art —
    diagnostic data for whoever asks for it via `tend status --json`, not a
    score or achievement ladder."""

    total_ticks: int = 0
    total_squishes: int = 0
    total_deaths: int = 0
    total_revivals: int = 0
    total_urchins_spawned: int = 0
    longest_quiet_streak: int = 0
    longest_squish_streak: int = 0
    biggest_dieoff: int = 0
    biggest_dieoff_day: int = 0


def _stalk_from_dict(data: dict) -> Stalk:
    return Stalk(
        height=data.get("height", 3),
        base=data.get("base", 0),
        urchins=data.get("urchins", 0),
    )


def _world_from_dict(data: dict) -> World:
    stalks_data = data.get("stalks", [])
    stalks = [_stalk_from_dict(s) for s in stalks_data]
    if len(stalks) != STALK_COUNT:
        stalks = [Stalk() for _ in range(STALK_COUNT)]
    return World(
        day=data.get("day", 1),
        spend=data.get("spend", 0),
        seeds=data.get("seeds", 0),
        stalks=stalks,
        last_offset=data.get("last_offset", 0),
        last_event=data.get("last_event", ""),
        spawned_indices_this_tick=data.get("spawned_indices_this_tick", []),
        chewed_this_tick=data.get("chewed_this_tick", []),
        died_this_tick=data.get("died_this_tick", []),
        revived_this_tick=data.get("revived_this_tick", []),
        seeds_spent_this_tick=data.get("seeds_spent_this_tick", 0),
        quiet_ticks=data.get("quiet_ticks", 0),
        streak=data.get("streak", 0),
    )


def load(path: Path | None = None) -> World:
    target = path or STATE_PATH
    try:
        with open(target) as f:
            data = json.load(f)
        return _world_from_dict(data)
    except Exception:
        return World()


def save(world: World, path: Path | None = None) -> None:
    target = path or STATE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w") as f:
        json.dump(asdict(world), f)


def _history_from_dict(data: dict) -> History:
    return History(
        total_ticks=data.get("total_ticks", 0),
        total_squishes=data.get("total_squishes", 0),
        total_deaths=data.get("total_deaths", 0),
        total_revivals=data.get("total_revivals", 0),
        total_urchins_spawned=data.get("total_urchins_spawned", 0),
        longest_quiet_streak=data.get("longest_quiet_streak", 0),
        longest_squish_streak=data.get("longest_squish_streak", 0),
        biggest_dieoff=data.get("biggest_dieoff", 0),
        biggest_dieoff_day=data.get("biggest_dieoff_day", 0),
    )


def load_history(path: Path | None = None) -> History:
    target = path or HISTORY_PATH
    try:
        with open(target) as f:
            data = json.load(f)
        return _history_from_dict(data)
    except Exception:
        return History()


def save_history(history: History, path: Path | None = None) -> None:
    target = path or HISTORY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w") as f:
        json.dump(asdict(history), f)
