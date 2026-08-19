---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T03 — chat-layout

## Question

DING / 聊天消息的时间、发送者、正文混在同一视觉层级，扫描成本高。如何重排？

## Decision

`store/dws_client.py` 的 `format_message_blocks` / `format_ding_blocks` 改为「一行头（时间·发送者）+ 缩进正文」；DING 条目间在 `chat_panel._load_dings` 加一条 dim 分隔线。时间保持 `dim`，发送者正常色（自己绿色）。
