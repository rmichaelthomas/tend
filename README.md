# tend

A small terminal toy for a Claude Code session. Grows quietly in the
background while you work; check in with `/tend`, press a key, move on.

## Install

```bash
pip install -e .
```

## Use

Add the Stop hook (`hooks/stop_hook.sh`) to your Claude Code settings, then
install the `/tend` skill from `skill/SKILL.md`. Run `/tend` any time to see
the current picture and clear one stalk.

## Development

```bash
pip install -e ".[dev]"
pytest
```
