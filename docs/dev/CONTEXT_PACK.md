# CONTEXT PACK

## Generated entries

### [docs/prd/GDD_M1_dynamic_interactive_story_engine.md](./docs/prd/GDD_M1_dynamic_interactive_story_engine.md)

```
# Product Requirements Document
## Introduction
- One-liner
  - Build a Unity runtime narrative engine for story-first games, starting with a text-only Ink-powered MVP that runs on desktop, mobile, and WebGL.
- Problem statement
  - We need a repeatable way to ship immersive interactive stories with a runtime-ready vertical slice (story runtime + player UX + save/load + runtime telemetry) that supports fast iteration.
- Goals
  - MVP (M1) delivers a complete playable text-only story with branching choices.
  - Provide VN-style player UX for reading + choice selection.
  - Support single-slot autosave + manual save/load (best-effort portability in M1; portable in later milestones).
```

### [docs/prd/README.md](./docs/prd/README.md)

```
# PRDs / GDDs
This directory contains Product Requirements Documents (PRDs) / Game Design Documents (GDDs) that define what we’re building and how to judge success.
## Active document
- **Dynamic Interactive Story Engine (M1)**
  - Tracking bead: **ge-hch** (“Dynamic Interactive Story Engine”)
  - Document: [GDD_M1_dynamic_interactive_story_engine.md](GDD_M1_dynamic_interactive_story_engine.md)
## What this document covers (M1)
The M1 scope is a text-only, Ink-powered vertical slice:
- Run one Ink story end-to-end at runtime with branching choices
- VN-style reading + choice UI (mouse/touch/keyboard/controller)
```

## How to query live state

- Beads issues: bd ready --json
- Current in-progress: bd list --status=in_progress --json