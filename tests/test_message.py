from tend.message import build
from tend.state import CHEWED, DEAD, DYING, HEALTHY, World


def _world(**overrides):
    world = World()
    for key, value in overrides.items():
        setattr(world, key, value)
    return world


def test_priority_1_death_no_seeds():
    world = _world(died_this_tick=[4], revived_this_tick=[], seeds_spent_this_tick=0)
    assert build(world) == "5 washed out. no seeds left. it stays gone."


def test_priority_2_death_with_seeds_spent():
    world = _world(died_this_tick=[4], revived_this_tick=[4], seeds_spent_this_tick=100)
    world.stalks[4].base = HEALTHY
    world.stalks[4].height = 1
    world.stalks[1].base = DEAD
    assert build(world) == "5 washed out. seeds -100. 2 is next."


def test_priority_1_wins_over_priority_2_when_both_hold():
    world = _world(died_this_tick=[0, 1], revived_this_tick=[0], seeds_spent_this_tick=100)
    world.stalks[0].base = HEALTHY
    world.stalks[0].height = 1
    world.stalks[1].base = DEAD
    assert build(world) == "2 washed out. no seeds left. it stays gone."


def test_priority_3_dying():
    world = _world()
    world.stalks[3].base = DYING
    assert build(world) == "4 goes next tick unless you press 4."


def test_priority_4_many_urchins_spawned():
    world = _world(spawned_indices_this_tick=[3, 4, 5, 4, 5])
    assert build(world) == "five urchins landed at once. 4, 5, 6. pick one."


def test_priority_5_two_chewed():
    world = _world(chewed_this_tick=[1, 5])
    world.stalks[1].base = CHEWED
    world.stalks[5].base = DYING
    assert build(world) == "2 and 6 both chewed. 6 is worse."


def test_priority_6_one_chewed():
    world = _world(chewed_this_tick=[1])
    world.stalks[1].base = CHEWED
    assert build(world) == "2 is being chewed. press 2."


def test_priority_7_quiet_no_activity():
    world = _world(quiet_ticks=5)
    assert build(world) == "quiet. nothing's happened in a while."


def test_priority_8_default_tall_stalks():
    world = _world()
    world.stalks[2].height = 6
    world.stalks[5].height = 7
    assert build(world) == "quiet. 3 and 6 are getting tall."


def test_priority_8_default_no_tall_stalks():
    world = _world()
    assert build(world) == "quiet."
