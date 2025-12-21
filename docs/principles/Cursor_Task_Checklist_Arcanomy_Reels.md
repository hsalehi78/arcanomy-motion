
# Cursor Task Checklist — Arcanomy Claim → Reel Automation System

This checklist maps implementation tasks directly to repository files.
Follow in order. Do not improvise.

---

## PHASE 0 — Orientation (Read Only)
- Read `Arcanomy_Claim_to_Reel_PRD.md`
- Read `CapCut_Assembly_Guide.md`

---

## PHASE 1 — Claim Input System
- Create `src/reels/schema/claim.schema.ts`
- Create `src/reels/validators/supportingDataValidator.ts`

---

## PHASE 2 — Script System
- Refactor `src/reels/script/`
- Enforce 3–4 segment rule in `segmentBuilder.ts`
- Output `script.json`

---

## PHASE 3 — Visual Plan System
- Create `src/reels/schema/visualPlan.schema.ts`
- Implement `visualPlanner.ts`
- Lock immutability in `pipeline/run.ts`

---

## PHASE 4 — Chart Generation (Remotion)
- Isolate charts in `src/reels/charts/`
- Implement `renderChart.tsx`
- Output `chart_seg-*.mp4`

---

## PHASE 5 — Assets
- Create `backgroundGenerator.ts`
- Create `thumbnailGenerator.ts`

---

## PHASE 6 — Voice
- Create `voiceGenerator.ts`
- One WAV per segment

---

## PHASE 7 — Assembly Instructions
- Create `capcutGuideGenerator.ts`
- Create `retentionChecklist.ts`

---

## PHASE 8 — Output Packaging
- Standardize `/reel/` output structure

---

## PHASE 9 — Quality Gate
- Implement `hormoziGate.ts`

---

## PHASE 10 — Cleanup
- Remove deprecated video prompt systems

---

## FINAL CHECK
- Claims immutable
- Visual plan immutable
- Remotion = charts only
- CapCut = assembly only
- 3–2–1 rule enforced
