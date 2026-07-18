from tend.state import STALK_COUNT, Stalk, World, load, save


def test_load_missing_file_returns_default_world(tmp_path):
    path = tmp_path / "state.json"
    world = load(path)
    assert world.day == 1
    assert world.spend == 0
    assert len(world.stalks) == STALK_COUNT
    assert all(isinstance(s, Stalk) and s.height == 3 for s in world.stalks)


def test_save_then_load_round_trips(tmp_path):
    path = tmp_path / "state.json"
    world = World()
    world.day = 5
    world.spend = 12345
    world.stalks[0].height = 7
    world.stalks[0].urchins = 2
    world.streak = 4
    save(world, path)
    loaded = load(path)
    assert loaded == world


def test_load_corrupt_file_returns_default_world(tmp_path):
    path = tmp_path / "state.json"
    path.write_text("not json{{{")
    world = load(path)
    assert world == World()


def test_load_missing_directory_does_not_crash(tmp_path):
    path = tmp_path / "nested" / "dir" / "state.json"
    world = load(path)
    assert world == World()
    save(world, path)
    assert path.exists()
