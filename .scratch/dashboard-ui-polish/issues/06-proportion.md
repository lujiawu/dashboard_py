---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T06 — proportion

## Question

底部行中 Git 面板内容少却占满高度，Yunxiao 内容多却空间不足。如何重平衡？

## Decision

`styles/app.tcss` 中 `#git-status` 由 `height: 1fr` 改为 `height: auto`（内容自适应），`#yunxiao` 保持 `1fr` 填满底部行，从而把多余垂直空间让给 Yunxiao。
