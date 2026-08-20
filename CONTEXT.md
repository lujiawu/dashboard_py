# Dashboard

A Textual terminal dashboard that aggregates DingTalk/IM, todos, and system signals into one screen.

## Language

**Message Group**:
Consecutive chat messages sharing the same `sender_id`, rendered as a single block with the sender and time shown only at its head.
_Avoid_: thread, cluster

**Self Message**:
A chat message whose `sender_id` equals the local user; rendered right-aligned in blue.
_Avoid_: my message, outgoing

**Other Message**:
A chat message from any other participant; rendered left-aligned in grey.
_Avoid_: their message, incoming
