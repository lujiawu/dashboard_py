---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T02 — unify-borders

## Question

四块面板当前用不同装饰色边框（`$warning`/`$error`/`$secondary`），颜色像装饰而非状态语义。如何统一？

## Decision

三块装饰边框统一为中性 `$surface-lighten-2`（与基础 `.panel` 一致）；保留 `$text-accent` 仅作 focus/选中高亮。改动 `styles/app.tcss:63-83`。
