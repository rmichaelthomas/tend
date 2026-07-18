import io

from rich.console import Console

from tend import feel
from tend.state import World


def test_streak_tier_boundaries():
    assert feel.streak_tier(0) == 0
    assert feel.streak_tier(2) == 0
    assert feel.streak_tier(3) == 1
    assert feel.streak_tier(5) == 1
    assert feel.streak_tier(6) == 2
    assert feel.streak_tier(9) == 2
    assert feel.streak_tier(10) == 3
    assert feel.streak_tier(999) == 3


def test_lerp_hex_at_endpoints():
    assert feel.lerp_hex("#000000", "#ffffff", 0.0) == "#000000"
    assert feel.lerp_hex("#000000", "#ffffff", 1.0) == "#ffffff"


def test_ease_out_steps_empty_when_duration_zero():
    assert feel._ease_out_steps(0) == []


def test_animate_squish_with_zero_duration_never_sleeps_or_renders(monkeypatch):
    calls = []

    def fake_render(world, **kwargs):
        calls.append(kwargs)
        return "frame"

    def fail_sleep(_seconds):
        raise AssertionError("should not sleep when duration is zero")

    monkeypatch.setattr(feel.time, "sleep", fail_sleep)
    monkeypatch.setattr(feel, "TICK_MS", 0)
    monkeypatch.setattr(feel, "THUMP_MS", 0)

    console = Console(file=io.StringIO())
    world = World()
    feel.animate_squish(console, world, 0, fake_render, cleared_count=1)
    assert calls == []


def test_animate_squish_runs_steps_when_duration_positive(monkeypatch):
    calls = []

    def fake_render(world, **kwargs):
        calls.append(kwargs)
        return "frame"

    monkeypatch.setattr(feel.time, "sleep", lambda _s: None)
    monkeypatch.setattr(feel, "TICK_MS", 40)
    monkeypatch.setattr(feel, "STEP_MS", 20)

    console = Console(file=io.StringIO())
    world = World()
    feel.animate_squish(console, world, 3, fake_render, cleared_count=1)
    assert len(calls) >= 1
    assert all(3 in c["brightness"] for c in calls)


def test_streak_module_never_imported_by_engine():
    import inspect

    import tend.engine as engine_module

    source = inspect.getsource(engine_module)
    assert "feel" not in source
