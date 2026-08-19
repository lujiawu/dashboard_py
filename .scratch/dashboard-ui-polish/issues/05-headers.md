---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T05 — headers

## Question

四块面板标题层级不一致（仅 Git 有标题）。如何统一？

## Decision

四块均加 `border_title`，统一格式 `NAME · N`：TodoPanel `TODO · N`、ChatPanel `CHAT · N unread`、YunxiaoPanel `WORK ITEMS · N`、GitStatusPanel 改为 `GIT STATUS`。计数在各自 refresh 时更新。
