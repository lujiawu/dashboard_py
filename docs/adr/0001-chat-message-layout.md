# Chat message layout: right-aligned self, grouped, blue/grey

Chat messages render in a `RichLog`. Self messages are right-aligned via Rich `Text.justify="right"` (not a bubble widget), consecutive messages from the same `sender_id` merge into one group with the sender/time shown only at the group head, and colour encodes ownership: self = `bright_blue`, others = `grey74`. Scope is conversation messages only; DING reminders are untouched.

**Considered options**
- Bubble layout via `ListView` rows (self right + background panel): strongest visual, but rewrites the message renderer and loses `RichLog` auto-scroll/streaming. Rejected to keep the existing architecture.
- Per-message left-aligned lines (status quo): simplest, but no ownership cue at a glance. Rejected per the requested visual hierarchy.

**Consequences**
- Right-alignment tracks the `RichLog` width automatically, so no manual padding and no narrow-screen drift; wrapped long lines justify per logical line.
- Grouping breaks only on `sender_id` change (not on date boundary), so a sender talking across midnight stays one group.
- `format_message_blocks` now returns `list[Text]` instead of `list[str]`; callers must accept `Text` renderables.
