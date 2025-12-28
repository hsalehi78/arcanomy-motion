# Deterministic Verification Gate (v2)

This replaces “LLM verified ✅” with an actual gate.

## Inputs

- `blog.json` (immutable source store with paragraph IDs)
- `claim_locked.json` (includes `proof_anchor_ids`)
- `script_v1.json`

## What counts as a “claim to verify”

Flag any line that contains:

- **numbers** (including percent, currency, “half”, “double”, ranges)
- “research shows”, “studies”, “data says”
- causal phrasing (“causes”, “leads to”, “results in”)

## Verification algorithm (MVP)

- For each flagged claim:
  - locate the anchor paragraphs by ID
  - build a “proof snippet” by concatenating those paragraph texts
  - check if the claim can be matched against the snippet using:
    - exact number match (normalized)
    - keyword overlap for the subject of the claim

If it fails:
- rewrite the line to be weaker and explicitly anchored (“In this article…”, “In this example…”, “One estimate in the blog…”)
- or remove it

Stop conditions:
- max 2 rewrite cycles
- if still failing, drop the stat/claim

## Output

- `script_verified.json` includes:
  - `verification_pass: true|false`
  - `dropped_claims[]`
  - `verification_notes[]`

**Schema:** validate the wrapper file against `schemas/script_verified.schema.json`. The embedded `script` must validate against `schemas/script.schema.json`.

## Note on future upgrades

You can add a secondary verifier LLM later, but the hard rule stays:

**No anchored proof → no claim.**

