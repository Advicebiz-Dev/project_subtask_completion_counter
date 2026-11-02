# Project Sub-task Completion Counter — Odoo 19

Version: **19.0.1.5.0** (upgrade from 19.0.1.4.0)

## What changes

- Keeps the completed/total/percentage counter and the existing CSS.
- Uses `default_order="sequence asc, id asc"` on the subtask list so Odoo 19 enables the native drag handle.
- Keeps `id` immutable. Drag-and-drop changes `sequence` only and is not automatically undone on page refresh.
- When a subtask is **marked Done**, moves it after the remaining open tasks and after already-completed tasks.
- When a subtask is **reopened**, moves it to the end of the open tasks, before Done tasks.
- When adding a new subtask, inserts it after existing tasks in its own Done/open group.
- When changing `parent_id`, reorders the old and the new parent's child lists.
- Uses `sudo()` only on automatic sequence updates (never on the status write). Automatic sequence-only writes disable native mail tracking.
- An **upgrade migration** aligns the preexisting subtasks with the new sequence-first display (preserving the order within completed/open groups). This does not modify IDs.

## Manual order vs. Done grouping

Explicit manual dragging **has precedence**: dragging a Done subtask above an open one is saved and survives refresh. Whenever a subtask is marked Done/reopened, reparented or created, the automatic grouping runs and places all Done tasks at the end again. This avoids overwriting manual drags immediately while preserving the automatic behavior on status changes.

The native Odoo handle can still become disabled for unrela
