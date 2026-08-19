---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T04 — truncation

## Question

部分内容横向截断丢失关键信息，部分字段（Type/Date）应始终可见。截断策略如何统一？

## Decision

Yunxiao 标题保持 88 截断（已有）；Todo 的 Description 列设固定宽度 24 以截断并避免挤压 Subject；Type/Date 列宽度固定且永不截断。改动 `widgets/todo_panel.py:55`。
