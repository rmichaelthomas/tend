"""Tick logic: growth, spawn, chew, death, revival."""
from __future__ import annotations

import random

from tend.state import CHEWED, DEAD, DYING, HEALTHY, MAX_HEIGHT, World

TOKENS_PER_SEGMENT = 20_000
TOKENS_PER_URCHIN = 15_000
TOKENS_PER_SEED = 10_000
REVIVAL_COST = 100
SHADE_THRESHOLD = 150_000


def tick(world: World, delta: dict) -> World:
    input_tokens = delta.get("input", 0)
    output_tokens = delta.get("output", 0)
    cache_read = delta.get("cache_read", 0)
    cache_write = delta.get("cache_write", 0)

    # 1. Accrue
    world.spend += input_tokens + output_tokens + cache_read + cache_write

    # 2. Grow
    segments = output_tokens // TOKENS_PER_SEGMENT
    if input_tokens > SHADE_THRESHOLD:
        segments //= 2
    living = [s for s in world.stalks if s.base != DEAD]
    for _ in range(segments):
        if not living:
            break
        stalk = random.choice(living)
        if stalk.height < MAX_HEIGHT:
            stalk.height += 1

    # 3. Seed
    world.seeds += cache_read // TOKENS_PER_SEED

    # 4. Spawn
    urchin_count = cache_write // TOKENS_PER_URCHIN
    spawned_indices: list[int] = []
    living_indexed = [(i, s) for i, s in enumerate(world.stalks) if s.base != DEAD]
    for _ in range(urchin_count):
        if not living_indexed:
            break
        weights = [max(s.height, 1) for _, s in living_indexed]
        idx, stalk = random.choices(living_indexed, weights=weights, k=1)[0]
        stalk.urchins += 1
        spawned_indices.append(idx)

    # 5. Chew
    chewed_indices = []
    for i, stalk in enumerate(world.stalks):
        if stalk.urchins > 0 and stalk.base != DEAD:
            stalk.base += 1
            chewed_indices.append(i)

    # 6. Die
    died_indices = []
    for i, stalk in enumerate(world.stalks):
        if stalk.base >= DEAD and stalk.height > 0:
            died_indices.append(i)
            stalk.height = 0

    # 7. Revive
    revived_indices = []
    seeds_spent = 0
    for i, stalk in enumerate(world.stalks):
        if stalk.base == DEAD and world.seeds >= REVIVAL_COST:
            world.seeds -= REVIVAL_COST
            seeds_spent += REVIVAL_COST
            stalk.base = HEALTHY
            stalk.height = 1
            stalk.urchins = 0
            revived_indices.append(i)

    # 8. Advance
    world.day += 1
    world.spawned_indices_this_tick = spawned_indices
    world.chewed_this_tick = chewed_indices
    world.died_this_tick = died_indices
    world.revived_this_tick = revived_indices
    world.seeds_spent_this_tick = seeds_spent

    if segments == 0 and not spawned_indices and not chewed_indices:
        world.quiet_ticks += 1
    else:
        world.quiet_ticks = 0

    return world


def squish(world: World, index: int) -> World:
    world.stalks[index].urchins = 0
    return world
