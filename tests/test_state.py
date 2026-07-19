from tend.state import STALK_COUNT, History, Stalk, World, load, load_history, save, save_history


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


def test_load_history_missing_file_returns_default_history(tmp_path):
    path = tmp_path / "history.json"
    history = load_history(path)
    assert history == History()
    assert history.total_ticks == 0


def test_save_then_load_history_round_trips(tmp_path):
    path = tmp_path / "history.json"
    history = History()
    history.total_ticks = 42
    history.total_squishes = 7
    history.total_deaths = 3
    history.total_revivals = 2
    history.total_urchins_spawned = 55
    history.longest_quiet_streak = 9
    history.longest_squish_streak = 5
    history.biggest_dieoff = 4
    history.biggest_dieoff_day = 11
    save_history(history, path)
    loaded = load_history(path)
    assert loaded == history


def test_load_history_corrupt_file_returns_default_history(tmp_path):
    path = tmp_path / "history.json"
    path.write_text("not json{{{")
    history = load_history(path)
    assert history == History()
