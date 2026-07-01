# Mihomo Panel Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Mihomo panel denser and easier to scan by moving status to the first line, splitting flow into two lines, and limiting sparkline width to 10 points.

**Architecture:** Keep the existing plain-text `Static` rendering path. Only reshape strings inside `widgets/mihomo_panel.py` and extend `test_mihomo_panel.py` so the panel stays dependency-free and consistent with the rest of the TUI.

**Tech Stack:** Python, unittest, Textual Static widget markup

## Global Constraints

- Do not add dependencies or new widgets.
- Keep data collection unchanged; only change Mihomo panel formatting.
- Curve length must be 10 samples.
- Preserve existing proxy/route semantics from the previous change.

---

### Task 1: Compact Mihomo Text Layout

**Files:**
- Modify: `widgets/mihomo_panel.py`
- Modify: `test_mihomo_panel.py`

**Interfaces:**
- Consumes: `MihomoPanel._format(data: dict) -> str`
- Produces: compact multiline output with `Speed`, two-line `Flow`, first-line status, and 10-point sparklines

- [ ] **Step 1: Write the failing test**

```python
def test_format_compacts_layout_and_limits_curves_to_ten_points(self):
    text = MihomoPanel()._format({...})
    lines = text.splitlines()
    assert lines[0] == "[bold]Proxy[/bold]  🇭🇰香港HY🚀   [green]OK[/]"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest test_mihomo_panel.py`
Expected: FAIL because status is still on the LAN line and flow is still one line.

- [ ] **Step 3: Write minimal implementation**

```python
def sparkline(values: list[int | float], width: int = 10) -> str:
    values = values[-width:]

def _format(self, data: dict) -> str:
    return "\n".join([
        f"[bold]Proxy[/bold]  {current_proxy}   {status}",
        f"[bold]Route[/bold]  {route_text}",
        "",
        f"[bold]Speed[/bold]  HK  62ms  {curve}",
        f"       US  215ms  {curve}",
        "",
        f"[bold]Flow[/bold]   ↓ ...",
        f"       ↑ ...",
    ])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest test_mihomo_panel.py`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add test_mihomo_panel.py widgets/mihomo_panel.py docs/superpowers/plans/2026-07-01-mihomo-panel-polish.md
git commit -m "feat: polish mihomo panel layout"
```
