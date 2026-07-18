import inspect
from dataclasses import asdict

from tend.engine import (
    REVIVAL_COST,
    SHADE_THRESHOLD,
    TOKENS_PER_SEED,
    TOKENS_PER_SEGMENT,
    squish,
    tick,
)
from tend.state import CHEWED, DEAD, DYING, HEALTHY, MAX_HEIGHT, World


def _delta(**overrides):
    d = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    d.update(overrides)
    return d


def test_chew_cycle_kills_then_revives_on_fourth_tick():
    world = World()
    world.stalks[0].urchins = 1
    world.seeds = 0

    tick(world, _delta())
    assert world.stalks[0].base == CHEWED

    tick(world, _delta())
    assert world.stalks[0].base == DYING

    tick(world, _delta(cache_read=TOKENS_PER_SEED * 99))
    assert world.stalks[0].base == DEAD
    assert world.stalks[0].height == 0
    assert world.seeds == 99
    assert 0 in world.died_this_tick

    tick(world, _delta(cache_read=TOKENS_PER_SEED))
    assert world.stalks[0].base == HEALTHY
    assert world.stalks[0].height == 1
    assert world.stalks[0].urchins == 0
    assert world.seeds == 0
    assert 0 in world.revived_this_tick


def test_squish_clears_urchins_without_side_effects():
    world = World()
    world.stalks[2].urchins = 3
    world.day = 9
    world.spend = 500
    other_before = [s.urchins for i, s in enumerate(world.stalks) if i != 2]

    squish(world, 2)

    assert world.stalks[2].urchins == 0
    assert world.day == 9
    assert world.spend == 500
    assert [s.urchins for i, s in enumerate(world.stalks) if i != 2] == other_before


def test_spend_is_monotonic():
    world = World()
    tick(world, _delta(input=10, output=10, cache_read=10, cache_write=10))
    assert world.spend == 40
    tick(world, _delta())
    assert world.spend == 40


def test_growth_caps_at_max_height_with_single_living_stalk():
    world = World()
    for s in world.stalks[1:]:
        s.base = DEAD
        s.height = 0
    world.stalks[0].height = MAX_HEIGHT - 1

    tick(world, _delta(output=TOKENS_PER_SEGMENT * 5))

    assert world.stalks[0].height == MAX_HEIGHT


def test_shade_halves_growth_above_threshold():
    world = World()
    for s in world.stalks[1:]:
        s.base = DEAD
        s.height = 0
    world.stalks[0].height = 0

    tick(world, _delta(output=TOKENS_PER_SEGMENT * 4, input=SHADE_THRESHOLD + 1))

    assert world.stalks[0].height == 2


def test_streak_never_referenced_inside_engine_module():
    import tend.engine as engine_module

    source = inspect.getsource(engine_module)
    assert "streak" not in source


def test_identical_world_state_at_streak_0_and_streak_12_except_streak_itself():
    world_a = World()
    world_a.stalks[0].urchins = 1
    world_a.streak = 0

    world_b = World()
    world_b.stalks[0].urchins = 1
    world_b.streak = 12

    delta = _delta(output=TOKENS_PER_SEGMENT, cache_read=TOKENS_PER_SEED)
    tick(world_a, delta)
    tick(world_b, delta)

    dict_a = asdict(world_a)
    dict_b = asdict(world_b)
    del dict_a["streak"]
    del dict_b["streak"]
    assert dict_a == dict_b
