# The Core Primitive (v2)

## The old mistake

The v1-style primitive (even if implemented differently) tends to be:

**Plan → generate assets → (later) discover you needed different assets**

That makes the system “fail by default” because the deliverable still requires invention.

## The v2 primitive

**Beat Sheet → Asset Resolver → CapCut Kit**

### Beat Sheet (control plane)

The beat sheet is the source of truth. It is a timed, asset-complete spec describing:

- voiceover text
- caption text + emphasis
- the visual slot type per beat (B-roll, chart overlay, math card, AI fallback)
- required tags/composition constraints
- explicit events (zoom, sound reset, overlay in/out)

### Asset Resolver (deterministic)

Resolves the beat sheet into concrete files and clip windows:

- pick b-roll clips from a **local indexed library**
- pick music from a **local indexed library**
- render chart overlays only when the beat sheet demands it
- apply dedupe rules against the Concept Ledger

### CapCut Kit (daily deliverable)

A folder that imports cleanly into CapCut and includes an `edit_plan.md` that maps:

`t_start–t_end → clip → source_in/out → events → caption emphasis`

## Why this fixes your failure mode

- The system does not “hope” the generated assets are usable.
- The editor does not have to invent visuals.
- Dedupe is real because usage is logged and enforced.

