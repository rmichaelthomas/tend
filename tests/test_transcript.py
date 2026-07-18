from pathlib import Path

from tend.transcript import read_delta

FIXTURE = Path(__file__).parent / "fixtures" / "transcript_fixture.jsonl"


def test_read_delta_sums_usage_across_lines():
    delta, offset = read_delta(str(FIXTURE), 0)
    assert delta == {"input": 160, "output": 10000, "cache_read": 3500, "cache_write": 2600}
    assert offset == FIXTURE.stat().st_size


def test_read_delta_returns_zeros_after_full_read():
    _, offset = read_delta(str(FIXTURE), 0)
    delta, new_offset = read_delta(str(FIXTURE), offset)
    assert delta == {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    assert new_offset == offset


def test_read_delta_missing_file_returns_zeros():
    delta, offset = read_delta("/nonexistent/path.jsonl", 0)
    assert delta == {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    assert offset == 0


def test_read_delta_skips_malformed_and_usageless_lines(tmp_path):
    path = tmp_path / "t.jsonl"
    path.write_text(
        '{"type":"user"}\n'
        "not json\n"
        '{"type":"assistant","message":{"usage":{"output_tokens":1}}}\n'
    )
    delta, offset = read_delta(str(path), 0)
    assert delta["output"] == 1
    assert offset == path.stat().st_size
