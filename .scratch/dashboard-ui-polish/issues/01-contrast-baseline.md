---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T01 — contrast-baseline

## Question

正文与背景对比度偏低，长时间阅读易疲劳。如何在不破坏深色终端风格的前提下提亮基础文字？

## Decision

面板默认文字提亮到 `#d8dee9`；`dim` 仅保留给时间戳、提示等次级元数据。在 `styles/app.tcss` 的 `#main-layout`、`DataTable`、`RichLog` 上设置该颜色，确保 DataTable 单元格与聊天日志继承。
