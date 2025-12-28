# Testing Strategy (v2)

How to validate the pipeline before and during production use.

---

## 1. Schema Validation (automated)

Every JSON output must pass schema validation before the next phase runs.

| Artifact | Schema | Gate |
|----------|--------|------|
| `run_context.json` | `run_context.schema.json` | Phase 0 → 1 |
| `claim_candidates.json` | `claim_candidates.schema.json` | Phase 1 (internal) |
| `claim_locked.json` | `claim_locked.schema.json` | Phase 1 → 2 |
| `script_v1.json` | `script.schema.json` | Phase 2 (internal) |
| `beat_sheet_v1.json` | `beat_sheet.schema.json` | Phase 2 → 3 |
| `script_verified.json` | `script_verified.schema.json` | Phase 3 → 4 |
| `asset_manifest.json` | `asset_manifest.schema.json` | Phase 4 → 5 |

**Implementation:** Use `ajv` (Node) or `jsonschema` (Python) at phase boundaries. Fail fast on validation errors.

---

## 2. Verification Gate Correctness (unit tests)

The deterministic verification gate (Phase 3) is critical. Test it with:

### Test cases

| Input | Expected |
|-------|----------|
| Script with stat that exists in `blog.json` paragraph | Pass, stat retained |
| Script with fabricated stat (not in any paragraph) | Fail, stat removed or weakened |
| Script with "research shows" but no anchor | Fail, line rewritten |
| Script with correct anchor but wrong number | Fail, line corrected |

### Implementation

```python
def test_verification_gate_removes_hallucinated_stat():
    script = {"sections": [{"voice_text": "Studies show 99% of people fail."}]}
    blog = {"paragraphs": [{"id": "p_001", "text": "Only 20% succeed."}]}
    result = run_verification_gate(script, blog)
    assert "99%" not in result["sections"][0]["voice_text"]
```

---

## 3. Dedupe Logic (integration tests)

Dedupe depends on ledger queries. Test with a mock ledger:

| Scenario | Expected |
|----------|----------|
| No prior reels for this blog | All candidates pass tag check |
| Last reel used `primary_tag: money` | Candidates with `money` blocked |
| Last 14 reels used stat hash `abc123` | Candidates with same hash blocked |
| Semantic similarity to recent takeaway = 0.90 | Candidate blocked (> 0.85 threshold) |

---

## 4. Ledger Write Idempotency

Ledger writes must be idempotent on `run_id`. Test:

```python
def test_ledger_write_is_idempotent():
    entry = make_ledger_entry(run_id="run-123")
    write_ledger(entry)  # first write
    write_ledger(entry)  # duplicate write
    rows = query_ledger(run_id="run-123")
    assert len(rows) == 1  # no duplicate
```

**Implementation:** Use `ON CONFLICT (run_id) DO NOTHING` or equivalent upsert.

---

## 5. Asset Resolver Sufficiency (integration tests)

Before Phase 5, the asset resolver must fill all `BROLL_SLOT` entries. Test:

| Scenario | Expected |
|----------|----------|
| Library has enough clips | All slots filled |
| Library is thin, some tags missing | Fallback to transitions pack |
| Transitions pack also insufficient | `AI_SLOT` fallback triggered |

---

## 6. End-to-End Smoke Test

Run the full pipeline on a known blog + known library state. Assert:

- `07_capcut_kit/` exists
- `edit_plan.md` contains all required sections
- No unresolved `AI_SLOT` entries (unless library is genuinely empty)
- Ledger entry written

---

## 7. Manual QA Checklist (per reel)

Before publishing, human verifies:

- [ ] Hook caption is perfect (first 2 seconds)
- [ ] No number errors in script
- [ ] Chart values match blog source
- [ ] VO audio is clean (no artifacts)
- [ ] Music ducking is correct
- [ ] Total duration matches edit plan
- [ ] Sound reset is at the right moment

---

## 8. CI Integration (recommended)

| Check | Trigger |
|-------|---------|
| Schema validation | On every commit to `schemas/` |
| Verification gate unit tests | On every commit to pipeline code |
| Smoke test | Nightly or on PR to main |
