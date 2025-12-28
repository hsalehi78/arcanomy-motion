# Newsletter Implementation Checklist (2025 Architecture)

This document tracks the progress of the Newsletter 2025 "Text-First" architecture migration. Use this to resume work across sessions.

## Quick Start

Run `pnpm newsletter` to see all commands with the latest blog slug.

## Phase 1: Component Architecture
- [x] Create `src/lib/email/components/MarketSnapshot.tsx` (Text-based context box)
- [x] Create `src/lib/email/components/NewsBrief.tsx` (Round-up list component)
- [x] Create `src/lib/email/components/SponsorshipUnit.tsx` (Native ad unit with `isInternal` toggle)
- [x] Create `src/lib/email/components/QuoteOfDay.tsx` (dark box, quote + attribution)
- [x] Create `src/lib/email/components/SimpleFooter.tsx` (replaces UnsubscribeFooter)
- [x] Export all new components from `src/lib/email/components/index.tsx`

## Phase 2: Layout Engine Refactor
- [x] Refactor `src/lib/email/layouts/newsletter-layout.tsx`
  - [x] Header (1440 style) - **ALREADY DONE** (Dark bg, white logo, centered)
  - [x] Switched to SimpleFooter (replaces UnsubscribeFooter)

## Phase 3: AI Generator Pipeline
- [x] Update `src/lib/newsletter/ai-generator.ts`
  - [x] Added `Newsletter2025Content` interface
  - [x] Added `generateNewsletter2025()` function
- [x] Fix URL paths (use `/perspectives/` and `/knowledge/` instead of `/blog/`)
- [x] Fix slug format (clean slugs without `perspective-`/`knowledge-` prefix)

## Phase 4: Content Workflow
- [x] Create `src/app/newsletters/deep-dive/` folder (AI-generated body)
- [x] Create `src/app/newsletters/inventory/` folder (reusable sections)
  - [x] `market-snapshot.md` - Market context (optional)
  - [x] `round-up.md` - 3 curated links
  - [x] `quote-of-day.md` - Inspirational quote
  - [x] `ad-slot.md` - Calculator promo
- [x] Update `newsletter:from-blog` to output to `deep-dive/` folder
- [x] Create `newsletter:build` command to combine deep-dive + inventory
- [x] Create `pnpm newsletter` help command with latest slug

## Phase 5: Documentation
- [x] Update `CLAUDE.md` with new workflow
- [x] Update `docs/newsletter/A-CHEAT.md` (clean, focused version)
- [x] Update `docs/newsletter/NEWSLETTER_WORKFLOW.md`
- [x] Create `scripts/newsletter-help.js` for interactive help

## Phase 6: Verification & Launch
- [ ] Generate a test newsletter with new architecture
- [ ] Verify "Ad Slot 1" renders correctly with Internal Content (Warming Phase)
- [ ] Verify Mobile Responsiveness (320px check)
- [ ] Verify Dark Mode compatibility (Logo visibility)
- [ ] **HTML Audit** (CRITICAL for inbox placement):
  - [ ] Each component uses ≤5 HTML elements
  - [ ] Each component uses ≤10 inline style declarations
  - [ ] No tables outside header
  - [ ] No styled buttons (plain `<a>` links only)
  - [ ] No emoji anywhere
  - [ ] No images in body (logo in header only)
  - [ ] Total email HTML < 50KB (Gmail clips at 102KB)

## Current Status
- **Strategy Approved**: Yes
- **Plan File**: `docs/editorial/guidelines/newsletter-implementation-plan-final.md`
- **Current Phase**: Phase 6 - Verification
- **Last Updated**: Nov 26, 2025

## File Structure

```
src/app/newsletters/
├── deep-dive/              ← AI-generated body (from-blog --ai)
│   └── {slug}.mdx          ← Deep Dive editorial only
│
├── inventory/              ← Reusable sections (edit manually)
│   ├── market-snapshot.md  ← Market context (optional)
│   ├── round-up.md         ← 3 curated links
│   ├── quote-of-day.md     ← Inspirational quote
│   └── ad-slot.md          ← Calculator promo
│
└── current/                ← Final combined newsletter (build)
    └── {slug}.mdx          ← Complete, frozen, ready to send
```

## Commands

```bash
pnpm newsletter                              # Show help with latest slug
pnpm newsletter:from-blog --slug="X" --ai    # Generate Deep Dive
pnpm newsletter:build --slug="X"             # Combine deep-dive + inventory
pnpm newsletter:test:prod --slug="X"         # Test send
pnpm newsletter:live:prod --slug="X"         # Live send
```

## Files Created/Modified
- `src/lib/email/components/MarketSnapshot.tsx` - NEW
- `src/lib/email/components/NewsBrief.tsx` - NEW
- `src/lib/email/components/SponsorshipUnit.tsx` - NEW
- `src/lib/email/components/QuoteOfDay.tsx` - NEW
- `src/lib/email/components/SimpleFooter.tsx` - NEW
- `src/lib/email/components/index.tsx` - MODIFIED (added exports)
- `src/lib/email/layouts/newsletter-layout.tsx` - MODIFIED (uses SimpleFooter)
- `src/lib/newsletter/ai-generator.ts` - MODIFIED (added Newsletter2025Content)
- `src/lib/newsletter/blog-converter.ts` - MODIFIED (outputs to deep-dive/, fixed URLs)
- `scripts/newsletter-build.js` - NEW (combines deep-dive + inventory)
- `scripts/newsletter-help.js` - NEW (interactive help)
- `scripts/blog-recent-slugs.js` - MODIFIED (reads from JSON for correct slugs)
