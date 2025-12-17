# Vision & Reel Types

## Why we’re building this
Arcanomy needs a discovery engine that is:
- **high-trust** (finance punishes “fake” visuals)
- **repeatable** (system > inspiration)
- **brand-consistent** (editorial, serious, emotionally grounded)
- **auditable** (numbers can be traced back to files you own)

Short-form video is distribution, not “content.” The reel’s job is to:
1) stop the scroll,  
2) deliver one sharp idea,  
3) earn curiosity.

---

## Length model: 10-second blocks (non-negotiable)

**All reels are built from 10-second blocks.**  
This aligns with AI video generation constraints and enforces editorial discipline.

Do not think in “seconds.”  
Think in **earned blocks**.

> If an idea doesn’t earn the next 10 seconds, it doesn’t belong in the reel.

---

## Length bands (block-based)

### **1 block (10s)** — Micro Insight
**Use when:**
- Naming a psychological trap
- A single confronting statement
- Text-first cinematic reels

**Characteristics:**
- No charts, or extremely minimal visual
- 1–2 spoken sentences max
- Optimized for completion and saves

This is not an explainer.  
It’s a narrative hook.

---

### **2 blocks (20s)** — Core Explainer *(Default)*
**This is the workhorse format.**

**Structure:**
- Block 1 (10s): Hook + framing
- Block 2 (10s): Chart reveal + implication

**Use when:**
- One dataset
- One insight
- One behavioral takeaway

If Arcanomy only shipped one reel length, this would be it.

---

### **3 blocks (30s)** — Expanded Explainer
**Structure:**
- Block 1: Hook + setup
- Block 2: Chart + explanation
- Block 3: Consequence or reframing

**Use when:**
- The chart needs narration
- The “so what” matters
- You want a calmer, reflective ending

Still very safe for short-form distribution.

---

### **4 blocks (40s)** — Transitional Essay *(Optional)*
**Structure:**
- 10s × 4 blocks

**Use when:**
- Combining psychology + data
- One chart plus deeper narrative
- Too rich for 20–30s, not quite a mini-essay

Support architecturally, use sparingly.

---

### **6 blocks (60s)** — Mini Essay *(Rare)*
**Structure:**
- 10s × 6 blocks
- Every block must earn its existence

**Use when:**
- Perspective-grade insight
- You are comfortable trading completion rate for depth
- The reel feels like a compressed essay, not a tip

---

## Reel types (v1)
Each reel has a `type` in `reel.yaml`.  
This routes prompts, scene planning, and Remotion templates.

### 1) Animated Chart Explainer (primary)
**Best for:** “show, don’t tell” money truths; tool + essay loop  
**Default length:** 2–3 blocks  
**Visual core:** deterministic chart layer (Remotion)

---

### 2) Psychological Trap Reveal
**Best for:** Perspectives-style insights; behavior reframes  
**Default length:** 1–2 blocks  
**Visual core:** typography-first, minimal motion

---

### 3) Text-Only Cinematic Statement
**Best for:** sharp thesis statements that feel premium  
**Default length:** 1 block  
**Visual core:** typography + subtle background motion

---

## What “winning” looks like
- The claim is clear **without reading comments**
- Charts and numbers are stable and readable
- The reel feels like a footnote to a serious essay
- You could reproduce it tomorrow without creative reinvention
