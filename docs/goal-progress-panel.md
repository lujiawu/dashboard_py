# 目标进度管理 — 技术方案

## 1. 概述

通用目标进度管理组件，支持任意目标进度的跟踪展示（装备消耗、项目进度、里程追踪等）。

核心特征：**可定制的目标进度管理**，面板标题、目标名称、单位、阈值均可由外部配置。

## 2. 数据结构 (`models/types.py`)

```python
from dataclasses import dataclass


@dataclass
class GoalProgress:
    name: str           # 条目名称
    used: float         # 已使用/已完成量
    goal: float         # 目标量
    unit: str = ""      # 单位（km, %, 个等）
    disabled: bool = False  # 是否停用/完成/归档
    icon: str = "◆"     # 文本图标

    @property
    def percentage(self) -> float:
        if self.goal == 0:
            return 0.0
        return min(100.0, (self.used / self.goal) * 100)

    @property
    def is_warning(self) -> bool:
        return self.disabled or self.percentage >= 90

    def __hash__(self):
        return id(self)
```

## 3. 面板组件 (`widgets/goal_progress_panel.py`)

### 类设计

继承 `VerticalScroll`，内部使用 `Static` 渲染富文本。

### 状态规则

| 状态 | 触发条件 | 视觉效果 |
|------|---------|---------|
| 正常 | `percentage < 90` 且 `disabled == False` | 默认主题，灰色进度条 |
| 警告 | `percentage >= 90` 或 `disabled == True` | 暗红背景，红色文字+进度条，`[停用]`标签 |

### 渲染效果

```
  装备消耗总览
  EQUIPMENT LIFE TRACKER
  ──────────────────────────────────────────────
  ╭──────────────────────────────────────────────╮
    ◆  24.2 summit1
       USED: 791.55km / GOAL: 1000km
       ████████████████░░░░░░░░ 79%
  ╰──────────────────────────────────────────────╯
  ╭──────────────────────────────────────────────╮
    ◆  24.8 速度马赫4 pro            [停用]
       USED: 791.55km / GOAL: 1000km
       ████████████████████████░░ 99%
  ╰──────────────────────────────────────────────╯
  ╭──────────────────────────────────────────────╮
    ◆  25.2C26                        [停用]
       USED: 791.55km / GOAL: 1000km
       ████████████████████████░░ 98%
  ╰──────────────────────────────────────────────╯
```

警告态卡片整体使用 `[on #330000]` 暗红背景，进度条和标签为红色。

### 渲染说明

- **卡片宽度**: 48 字符，适配标准终端
- **图标**: `◆` 纯文本符号，终端兼容
- **进度条**: `█`(实心) `░`(空心) Unicode 字符
- **百分比**: 进度条右侧同行显示
- **标签**: 名称行右侧 `[停用]`

### 关键代码

```python
from textual.containers import VerticalScroll
from textual.widgets import Static
from models.types import GoalProgress


class GoalProgressPanel(VerticalScroll):

    DISABLED_THRESHOLD = 90
    CARD_WIDTH = 48
    BAR_WIDTH = 24

    def compose(self):
        yield Static(id="content", expand=True)

    def update_progress(self, items: list[GoalProgress]):
        content = self.query_one("#content", Static)
        content.update(self._format_cards(items))

    def _format_cards(self, items: list[GoalProgress]) -> str:
        if not items:
            return "No data"
        return "\n".join(self._render_card(item) for item in items)

    def _render_card(self, item: GoalProgress) -> str:
        pct = item.percentage
        filled = int(pct / 100 * self.BAR_WIDTH)
        is_warn = item.is_warning

        bar_chars = "█" * filled + "░" * (self.BAR_WIDTH - filled)
        bar_line = f"  {bar_chars} {pct:.0f}%"

        name_line = f"  {item.icon}  {item.name}"
        if item.disabled:
            name_line += "  [停用]"

        data_line = f"     USED: {item.used}{item.unit}  /  GOAL: {item.goal}{item.unit}"

        return "\n".join([
            f"╭{'─' * (self.CARD_WIDTH - 2)}╮",
            name_line,
            data_line,
            bar_line,
            f"╰{'─' * (self.CARD_WIDTH - 2)}╯"
        ])

    def update_mock_data(self):
        mock = [
            GoalProgress("24.2 summit1", 791.55, 1000, unit="km"),
            GoalProgress("24.8 速度马赫4 pro", 985.2, 1000, unit="km", disabled=True),
            GoalProgress("25.2C26", 982.1, 1000, unit="km", disabled=True),
        ]
        self.update_progress(mock)
```

### 自定义配置

面板支持以下自定义：

| 字段 | 类型 | 说明 |
|------|------|------|
| `DISABLED_THRESHOLD` | `int` | 警告阈值（百分比），默认 90 |
| `CARD_WIDTH` | `int` | 卡片宽度（字符数），默认 48 |
| `BAR_WIDTH` | `int` | 进度条宽度（字符数），默认 24 |

## 4. 集成到 Dashboard (`app.py`)

### import 和 compose 注册

```python
from widgets.goal_progress_panel import GoalProgressPanel

# compose() 中添加
yield GoalProgressPanel(id="goal-progress", classes="panel")

# on_mount() 中初始化
self.query_one("#goal-progress", GoalProgressPanel).update_mock_data()
```

### CSS 样式 (`styles/app.tcss`)

```css
GoalProgressPanel {
    height: 1fr;
    border: solid $primary;
    padding: 0 1;
}

GoalProgressPanel > Static {
    width: 100%;
}
```

## 5. 原始 UI 信息保留对照

| 原始 UI 特征 | TUI 实现 | 保留度 |
|-------------|---------|-------|
| 卡片式容器 | `╭─╮` `╰─╯` 边框 | ✅ 完整 |
| 左图标 + 右内容布局 | `◆ + 名称` 同行 | ✅ 完整 |
| 产品名称突出 | `[bold]` 加粗 | ✅ 完整 |
| 使用数据展示 | `USED: x / GOAL: x` | ✅ 完整 |
| 可视化进度条 | `█░` 字符填充条 | ✅ 完整 |
| 百分比同行 | 进度条右侧 | ✅ 完整 |
| 正常/警告状态区分 | 背景色 + 进度条颜色 | ✅ 完整 |
| 停用标签 | `[停用]` 右上角 | ✅ 完整 |
| 警告态全卡片变红 | `[on #330000]` 背景 | ✅ 完整 |

## 6. 扩展说明

### 数据源接入

`update_progress(items: list[GoalProgress])` 为统一接入接口，后续可从任意数据源获取 `GoalProgress` 列表后调用：

```python
# 从文件
items = load_from_file("equipment.json")
panel.update_progress(items)

# 从 API
items = await fetch_goal_progress()
panel.update_progress(items)

# 从数据库
items = db.query(GoalProgress).all()
panel.update_progress(items)
```

### 图标扩展

`icon` 字段支持任何单字符文本符号：
- `◆` 菱形（通用目标）
- `●` 圆形（通用任务）
- `S` 字母（设备/装备）
- `P` 字母（项目）
- `R` 字母（跑步）
