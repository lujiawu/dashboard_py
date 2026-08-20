---
labels: [wayfinder:task]
status: closed
blocks: []
---

# T07 — chat-message-visual-hierarchy

## Question

Beyond the header/body split from T03, how should ownership and grouping read at a glance in the chat panel?

## Decision

Supersedes the visual treatment in T03. Self messages right-align (`Text.justify="right"`), consecutive same-`sender_id` messages merge into one group (header only at group head), colour encodes ownership: self `bright_blue`, others `grey74`. Conversations only; DING untouched. Recorded in `docs/adr/0001-chat-message-layout.md`.
