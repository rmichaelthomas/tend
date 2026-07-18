import re

from tend.render import render_frame
from tend.state import DEAD, STALK_COUNT, World

BLOCK = 5  # 4-char block + 1 gap


def _strip(s: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", s)


def test_all_seven_stalks_render_aligned_at_every_base_state():
    for base in range(4):
        world = World()
        for s in world.stalks:
            s.base = base
        frame = _strip(render_frame(world))
        lines = frame.splitlines()
        base_line = next(
            line for line in lines if any(ch in line for ch in "▓▒░×")
        )
        blocks = [b for b in base_line.split(" ") if b]
        assert len(blocks) == STALK_COUNT
        assert all(len(b) == 4 for b in blocks)


def test_dead_stalk_shows_burnt_symbol_with_no_stem_above():
    world = World()
    world.stalks[4].base = DEAD
    world.stalks[4].height = 0
    frame = _strip(render_frame(world))
    lines = frame.splitlines()
    base_line = next(line for line in lines if any(ch in line for ch in "▓▒░×"))
    col_start = 4 * BLOCK
    assert base_line[col_start:col_start + 4] == "××××"

    stem_lines = [line for line in lines if "|" in line]
    for line in stem_lines:
        assert "|" not in line[col_start:col_start + 4]


def test_urchins_render_under_correct_stalk_only():
    world = World()
    world.stalks[2].urchins = 2
    frame = _strip(render_frame(world))
    lines = frame.splitlines()
    urchin_line = next(line for line in lines if "●" in line)
    for i in range(STALK_COUNT):
        col_start = i * BLOCK
        segment = urchin_line[col_start:col_start + 4]
        if i == 2:
            assert "●" in segment
        else:
            assert "●" not in segment


def test_render_frame_accepts_feel_pass_kwargs_without_error():
    world = World()
    frame = render_frame(world, tier=2, brightness={0: 0.5}, loss_index=1, loss_progress=0.3)
    assert isinstance(frame, str)
    assert len(frame) > 0
