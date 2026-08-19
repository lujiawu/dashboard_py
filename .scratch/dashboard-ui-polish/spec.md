---
labels: [wayfinder:map]
status: open
---

# Dashboard UI 增量打磨

## Destination

增量打磨 `dashboard_py` 的 4 面板 UI，提升可读性与可扫描性，同时保持深色终端风格。不重建主题、不改布局结构、不加新功能。

## Notes

- 栈：Python Textual 8.x；样式在 `styles/app.tcss`，面板在 `widgets/`，聊天渲染在 `store/dws_client.py`。
- 本地 markdown 追踪器（matt-default-config）：地图 = `spec.md`，子 ticket = `issues/NN-slug.md`，含 `Status:` 行。
- 遵循 ponytail：每处最小改动，颜色只表达状态不表达装饰。

## Decisions so far

- [T01 contrast-baseline](issues/01-contrast-baseline.md) — 正文提亮 `#d8dee9`，`dim` 仅用于时间戳/提示等次级元数据
- [T02 unify-borders](issues/02-unify-borders.md) — 三块装饰边框统一为 `$surface-lighten-2`，`$text-accent` 仅作 focus 高亮
- [T03 chat-layout](issues/03-chat-layout.md) — 消息改为「一行头 + 缩进正文」，DING 条目间加 dim 分隔线
- [T04 truncation](issues/04-truncation.md) — Todo Description 固定宽 24 截断，Type/Date 永不截断
- [T05 headers](issues/05-headers.md) — 四块均加 `border_title`（`NAME · N`），计数随 refresh 更新
- [T06 proportion](issues/06-proportion.md) — `#git-status` 改 `height: auto`，底部垂直空间让给 Yunxiao

## Not yet specified

- 截断内容是否需要 hover/展开查看（本次增量范围先不做）。
- 是否引入统一颜色变量（`$text-strong` 等）——若 T01 提亮不够再议。

## Out of scope

- 浅色主题 / 明暗切换。
- 布局重组（1 列 / 卡片式）。
- 新交互 / 动画 / 图标库。
- Git 面板内容语义着色（冲突/未跟踪用红）——属数据层，不在本次。
