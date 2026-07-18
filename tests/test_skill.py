from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "skill" / "SKILL.md"


def test_skill_file_exists_with_tend_frontmatter():
    content = SKILL.read_text()
    assert content.startswith("---")
    assert "name: tend" in content


def test_skill_does_not_mention_tick_or_explain_mechanics():
    content = SKILL.read_text().lower()
    assert "tend tick" not in content
    assert "urchin" not in content
    assert "seaweed" not in content
    assert "kelp" not in content
