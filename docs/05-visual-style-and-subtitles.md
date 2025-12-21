# 05 — Visual Style & Subtitles (Viral Specs)

> **Legacy notice (important):** This doc includes a v1 Remotion karaoke-caption system.  
> **Canonical v2 captions** are **CapCut preset style** per `docs/principles/arcanomy-reels-operating-system.md` and `docs/REFRACTOR_RFC.md`. V2 outputs `captions.srt` (line-level, voice-aligned) and CapCut applies styling.

## Core Philosophy: "Stop the Scroll"

This document defines the **Arcanomy Viral Visual System**. These are not just aesthetic choices; they are functional requirements for performance on Instagram Reels, TikTok, and YouTube Shorts.

---

## 1. The "First Frame" Rule (Thumbnail)

Social platforms often use the first frame of the video as the static thumbnail before autoplay begins.

- **Constraint:** The first frame **must be readable as a still image**.
- **Rule:** No fade-ins. The "Hook" text must be fully visible at Frame 0.
- **Test:** Can you read the text when the video preview is 150px wide?
- **Contrast:** High contrast (White/Gold on Black). No mid-tones.

---

## 2. Text & Typography

Text is the primary visual. If they can't read it instantly, they scroll.

### Hierarchy
| Element | Font | Weight | Size (Height %) | Color |
| :--- | :--- | :--- | :--- | :--- |
| **Hook / Headline** | Inter / Montserrat | **Bold** | **15%+** | `#F5F5F5` (Off-White) |
| **Subtitles** | Inter / SF Pro | Medium | **8%+** | `#FFFFFF` (White) |
| **Highlight** | - | **Bold** | - | `#FFD700` (Gold) |

### Rules
- **No Thin Fonts:** They disappear on mobile screens outdoors.
- **Positioning:**
    - **Safe Zone:** Keep all text within center 80% width.
    - **Bottom 15%:** Reserved for Platform UI (Likes, Comments, Captions). **DO NOT PUT TEXT HERE.**

---

## 3. Subtitles (Retention Engine)

Subtitles are not just for accessibility; they are for **pacing**.

- **Style:** "Karaoke" style (active word highlighted).
- **Highlighting:**
    - Active word color: `#FFD700` (Gold) or `#FFFFFF` (Bright White).
    - Animation: Scale active word to **110%**.
- **Background:** Semi-transparent black pill (`#000000` @ 70% opacity). **NO full-width bars.**
- **Position:** Bottom 20% of frame, centered.

---

## 4. Color Palette (Premium High-Contrast)

| Usage | Color | Hex | Rationale |
| :--- | :--- | :--- | :--- |
| **Background** | Pure Black | `#000000` | Maximum OLED contrast, premium feel. |
| **Secondary BG** | Near Black | `#0A0A0A` | Subtle depth for layering. |
| **Primary Text** | Off-White | `#F5F5F5` | Easier on eyes than pure white. |
| **Highlight** | Gold | `#FFD700` | Signals value/wealth. Pops on black. |
| **Tension/Danger**| Signal Red | `#FF3B30` | Universal "Stop/Warning". |
| **Charts** | Gold Line | `#FFB800` | Consistent with highlight. |

---

## 5. Motion & Pacing

Speed implies confidence. Slowness implies boredom.

- **Text Entrance:** **SNAP IN** (0-2 frames). No easing. No fades.
- **Text Exit:** **HARD CUT**.
- **Transitions:** Hard cuts or fast zooms (0.1s).
- **Prohibited:** Slide-ins, bounces, spins, "PowerPoint" presets.
- **Visual Rhythm:** Something new must happen every **2-3 seconds** (new text, chart update, zoom).
- **Charts:** Draw-on animation (0.5s - 1.0s duration). Creates anticipation.

---

## 6. Remotion Implementation Specs

When building the React components, use these constants:

```typescript
export const COLORS = {
  bg: "#000000",
  bgSecondary: "#0A0A0A",
  textPrimary: "#F5F5F5",
  textSecondary: "#FFFFFF",
  highlight: "#FFD700",
  chartLine: "#FFB800",
  danger: "#FF3B30",
};

export const SIZES = {
  hookHeightPercent: 0.15, // 15% of screen height
  subtitleHeightPercent: 0.08, // 8% of screen height
  safeZoneBottomPercent: 0.15, // Reserve bottom 15% for UI
};

export const ANIMATION = {
  textInFrames: 0, // Instant
  zoomDuration: 3, // Frames (at 30fps = 0.1s)
  chartDrawDuration: 30, // Frames (1s)
};
```

---

## Checklist for Review
1.  [ ] **Frame 0:** Is the hook text visible?
2.  [ ] **Mobile Test:** Is the text readable at 25% scale?
3.  [ ] **Safe Zone:** Is the bottom 15% empty?
4.  [ ] **Pacing:** Does the screen change every 3 seconds?
5.  [ ] **Contrast:** Is it Black/White/Gold?
