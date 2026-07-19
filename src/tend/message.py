"""The one-line message grammar. Name the stalk, then the verb. Worst first."""
from __future__ import annotations

from tend.state import DEAD, DYING, World

TALL_THRESHOLD = 6
QUIET_TICKS_THRESHOLD = 5
MANY_URCHINS_THRESHOLD = 3

NUMBER_WORDS = {3: "three", 4: "four", 5: "five", 6: "six", 7: "seven"}


def _join(names: list[str]) -> str:
    if not names:
        return ""
    if len(names) == 1:
        return names[0]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return f"{', '.join(names[:-1])} and {names[-1]}"


def build(world: World) -> str:
    died = world.died_this_tick
    if died:
        not_revived = [i for i in died if i not in world.revived_this_tick]
        if not_revived:
            n = min(not_revived) + 1
            return f"{n} washed out. no seeds left. it stays gone."

        idx = min(died)
        n = idx + 1
        others = [
            i
            for i, s in enumerate(world.stalks)
            if s.base == DEAD and i not in world.revived_this_tick
        ]
        if others:
            m = min(others) + 1
            return f"{n} washed out. seeds -{world.seeds_spent_this_tick}. {m} is next."
        return f"{n} washed out. seeds -{world.seeds_spent_this_tick}."

    # Only claims imminent death when the stalk is actually still being
    # chewed — dying with zero urchins can't advance to dead next tick,
    # so the warning would be a false promise.
    dying = [i for i, s in enumerate(world.stalks) if s.base == DYING and s.urchins > 0]
    if dying:
        n = min(dying) + 1
        return f"{n} goes next tick unless you press {n}."

    if len(world.spawned_indices_this_tick) >= MANY_URCHINS_THRESHOLD:
        count = len(world.spawned_indices_this_tick)
        word = NUMBER_WORDS.get(count, str(count))
        stalks = sorted({i + 1 for i in world.spawned_indices_this_tick})
        names = ", ".join(str(i) for i in stalks)
        return f"{word} urchins landed at once. {names}. pick one."

    chewed = sorted(world.chewed_this_tick)
    if len(chewed) >= 2:
        worst = max(chewed, key=lambda i: world.stalks[i].urchins)
        names = _join([str(i + 1) for i in chewed])
        verb = "both" if len(chewed) == 2 else "all"
        return f"{names} {verb} chewed. {worst + 1} is worse."

    if len(chewed) == 1:
        n = chewed[0] + 1
        return f"{n} is being chewed. press {n}."

    if world.quiet_ticks >= QUIET_TICKS_THRESHOLD:
        return "quiet. nothing's happened in a while."

    fragile = sorted(i for i, s in enumerate(world.stalks) if s.base == DYING and s.urchins == 0)
    if fragile:
        n = min(fragile) + 1
        return f"quiet. {n} is still fragile."

    tall = sorted(i for i, s in enumerate(world.stalks) if s.height >= TALL_THRESHOLD)
    if tall:
        names = _join([str(i + 1) for i in tall])
        return f"quiet. {names} are getting tall."
    return "quiet."
