# Thread Lock Split Implementation Plan

> Execute inline with the existing workspace changes preserved. The user approved splitting unit 28 into Lock and RLock in the preceding conversation.

**Goal:** Publish 28.1 Lock and 28.2 RLock with one formal introduction per API, preserving the existing Lock URL and old reference pages.

**Architecture:** Extend `curriculum.json` with two parts and the existing navigation-group mechanism. Add `threading.RLock` to `current-api-plan.json` (98 APIs); regenerate curriculum and frequency outputs. Teach RLock through a minimal nested acquisition and the real Slime accelerator registration call chain. Keep relationship summaries separate from full teaching.

**Tech Stack:** Hugo Extended 0.166.0, Markdown, Python 3.12 standard library.

**Spec:** Approved proposal in this conversation: unit 27 → 28.1 Lock → 28.2 RLock → unit 29; independent teaching, Lock/RLock relationship summary, Slime frequency and curriculum updates.

## Constraints and review focus

- Preserve uncommitted work, existing URLs/downloads, and 41 main unit numbers; do not commit or publish.
- Reuse the verified current-workspace preview; all examples must terminate without timing-based ordering assumptions.
- Keep Condition and Timer in the old reference page; introduce only the RLock constructor formally.
- Verify nested acquisition, partial release, exception cleanup, and the boundary between thread ownership and asyncio tasks.
- Recalculate coverage from the frozen inventories, preserving historical 82/97-API statements where explicitly historical.

## Tasks

- [x] Add focused regression checks for the 28.1/28.2 course mapping and RLock's Slime frequency; observe missing-feature failures.
- [x] Create RLock teaching/examples and relationship summary; adjust 28.1 and adjacent navigation while preserving old references.
- [x] Extend the formal API scope and expansion metadata; regenerate derived reports and update current totals and documentation.
- [x] Run the lesson examples, curriculum/frequency checks, relevant Python tests, Hugo build and rendered navigation checks; review the final diff.

## Execution record

- Preview: original Lock URL responds with HTTP 200 (outside the shell sandbox).
- Scope: user approved the placement and the 98-item consequence before this implementation request.
- Workspace: reuse the current working tree to preserve and extend the ongoing course edits; no branch integration or deployment requested.

- Review: independent reviewer verified RLock semantics and Slime sources; current-scope prose, lesson manifest and current-reading links were corrected from the findings.

- Verification: Lock and both RLock examples match documented output; curriculum 98/98, frequency and API-plan checks pass; Hugo production build passes; published navigation/download test passes; three Chrome checks pass for RLock desktop, mobile/focus, and page switching; reference suite 40/40 passes.
- Whole repository: 250 tests run, one Node-dependent check skipped. The Miles generated selected-API count was refreshed to 98 and all four Miles checks pass on rerun. The remaining S16 workflow-source mismatch is unrelated: its test, JSON excerpt library and assets match HEAD, and the HEAD excerpt already differs from the external local source. Leave this separate chapter untouched.
