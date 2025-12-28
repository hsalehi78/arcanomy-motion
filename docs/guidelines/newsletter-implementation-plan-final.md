# Newsletter Architecture Plan: The "Inbox-Native" Engine

**Objective**: Deploy the final, monetization-ready newsletter structure immediately.
**Strategy**: "Warm" the ad slots with internal content to build deliverability reputation before selling sponsorships.

---

## 1. The Fixed Architecture (Day 1)

Every newsletter will follow this exact vertical stack. No deviations.

### A. The Header (1440 Style)

- **Background**: Dark (`#111827`) - matches 1440's actual header.
- **Layout**: Centered logo (simple, clean).
- **Logo**: White Arcanomy logo (`arcanomy-logo-white.png`), 200px width.
- **Tagline**: "Financial Independence & Wealth Building" below logo.
- **Constraint**: Max height 150px. Zero distractions.
- **Status**: **ALREADY IMPLEMENTED** - Current system matches this spec.

### B. Section 1: "The Market Snapshot" (Context)

- **Position**: Immediately after header.
- **Component**: `<MarketSnapshot />`
- **Content**:
  - 3-sentence summary of market vibe.
  - 1-sentence "Arcanomy Insight".
- **Goal**: Instant value. Proves this isn't just a link dump.

### C. Section 2: "The Deep Dive" (The Blog Post)

- **Position**: Core Anchor.
- **Component**: `<MainContent />` (Standard text block).
- **Content**:
  - 300-word standalone editorial.
  - **NOT** a teaser. A story.
  - **CTA**: "Read Full Analysis" (Button).

### D. Ad Slot 1: "The Prime Slot"

- **Position**: _Between_ Deep Dive and Round-Up.
- **Component**: `<SponsorshipUnit position="primary" />`
- **Day 1 Content**: **Internal Lead Gen** (e.g., Mortgage Calculator, FIRE Tool).
- **Future Content**: High-CPM Sponsor ($40+).
- **Technical**:
  - Rendered as a distinct "Box" with light gray bg (`#f9fafb`).
  - Labeled "Presented by Arcanomy" (initially) -> "Presented by [Sponsor]" (later).

### E. Section 3: "The Round-Up" (Briefs)

- **Position**: Lower body.
- **Component**: `<NewsBrief />`
- **Content**:
  - List of 3 items.
  - Format: **Headline** - One sentence summary. Link.
  - **Mix**: 2 External Market News + 1 Internal Evergreen Post.

### F. Ad Slot 2: "The Closer"

- **Position**: Pre-Footer.
- **Component**: `<SponsorshipUnit position="secondary" />`
- **Day 1 Content**: **Referral Program** ("Share & Earn").
- **Future Content**: Affiliate Link / Secondary Sponsor.

### G. Quote of the Day (Pre-Footer)

- **Component**: `<QuoteOfDay />` (NEW)
- **Props**: `quote` (string), `attribution` (string)
- **Style**: Dark box (`#111827`), white italic text, centered
- **Position**: After last content section, before footer

### H. Footer (Hustle-Inspired - Minimal + Personality)

- **Component**: `<SimpleFooter />` (REPLACES current `UnsubscribeFooter`)
- **Design Goal**: Minimal HTML, maximum personality (like The Hustle)
- **Structure** (3 lines of plain text):

  ```
  Follow Arcanomy on X, Instagram, TikTok, and LinkedIn.

  Arcanomy • 1575 Westwood Blvd Ste 302 #2055, Los Angeles, CA 90024
  Never want to hear from us again? Break our hearts and Unsubscribe. | Privacy
  ```

- **Key Decisions**:
  - **Keep "Break our hearts"** - Good voice, matches Hustle style
  - **Plain text social links** - X, Instagram, TikTok, LinkedIn (underlined, no buttons)
  - **Remove emoji** - Cleaner rendering across clients
  - **Single paragraph legal** - Address + Unsubscribe + Privacy together
- **What Gets Removed**:
  - Styled social button boxes
  - Dark background section
  - "Forward to a Friend" styled button
  - Heart emoji (💔)
  - YouTube link
- **Why**: ~80% reduction in HTML. Better inbox placement. Personality preserved.

---

## 2. Technical Implementation Specs

### HTML Constraints (MANDATORY for all components)

Every component MUST follow these rules to ensure inbox placement:

| Rule                     | Constraint                                   | Why                                  |
| ------------------------ | -------------------------------------------- | ------------------------------------ |
| **Max Elements**         | ≤5 HTML elements per component               | Reduces nesting, improves parsing    |
| **Max Inline Styles**    | ≤10 style declarations per component         | Gmail clips emails >102KB            |
| **No Tables**            | Use `<div>` or `<p>` only (except header)    | Tables trigger "promotional" filters |
| **No Background Colors** | White/transparent only (except header/quote) | Dark sections = marketing email      |
| **No Styled Buttons**    | Plain `<a>` links with underline             | Buttons = promotional                |
| **No Emoji**             | Zero emoji in any component                  | Inconsistent rendering, spam signal  |
| **No Images**            | Text only (except logo in header)            | Images hurt deliverability           |

### Component Library (`src/lib/email/components/`)

1.  **`MarketSnapshot.tsx`**

    - **Props**: `context` (string), `insight` (string).
    - **Style**: Light gray border-left accent, italicized insight.
    - **HTML Budget**: 2 `<p>` tags, ~6 inline styles max.

2.  **`SponsorshipUnit.tsx`** (The Money Maker)

    - **Props**:
      - `sponsorName` (string)
      - `copy` (string)
      - `ctaText` (string)
      - `ctaUrl` (string)
      - `isInternal` (boolean) - _toggles "Sponsored" label vs "Recommended Resource"_
    - **Design**: Native look. Matches body font. Light border to satisfy "Ad" disclosure rules without screaming "Banner Ad".
    - **HTML Budget**: 3 `<p>` tags + 1 `<a>`, ~8 inline styles max.

3.  **`NewsBrief.tsx`**

    - **Props**: `items` (Array of `{ headline, summary, url }`).
    - **Style**: Clean list, bold headers, plain links.
    - **HTML Budget**: 1 `<div>` + 3 `<p>` (one per item), ~6 inline styles max.

4.  **`QuoteOfDay.tsx`**

    - **Props**: `quote` (string), `attribution` (string).
    - **Style**: Dark box (`#111827`), white italic text, centered.
    - **HTML Budget**: 1 `<div>` + 2 `<p>`, ~6 inline styles max.
    - **Exception**: Dark background allowed (matches header aesthetic).

5.  **`SimpleFooter.tsx`**
    - **Props**: `unsubscribeToken` (string), `baseUrl` (string).
    - **Style**: Plain text, underlined links only.
    - **HTML Budget**: 3 `<p>` + 6 `<a>`, ~8 inline styles max.
    - **No**: Buttons, emoji, dark background, styled boxes.

### Layout Engine (`newsletter-layout.tsx`)

- **Refactor**: Switch from "Hero Image" layout to "Text Stack" layout.
- **Logic**:
  - Header (Fixed)
  - Content Stack (Dynamic children)
  - Footer (Fixed)

---

## 3. AI Generator Logic (`ai-generator.ts`)

The AI must populate _all_ sections from the single Blog Post input + Context.

**Input**: Blog Post Markdown.
**Output JSON**:

```json
{
  "subject": "Clickbait-y Subject",
  "preheader": "Value-add preheader",
  "snapshot": {
    "context": "Market is doing X...",
    "insight": "This means you should Y..."
  },
  "deepDive": "300 word summary...",
  "roundUp": [
    { "headline": "Related News 1", "summary": "...", "url": "..." },
    { "headline": "Related News 2", "summary": "...", "url": "..." }
  ],
  "adSlot1": { "type": "internal", "tool": "mortgage-calculator" } // AI picks relevant internal tool
}
```

---

## 4. Execution Checklist

- [ ] **Step 1**: Build `<SponsorshipUnit />` with `isInternal` toggle.
- [ ] **Step 2**: Build `<MarketSnapshot />` and `<NewsBrief />`.
- [ ] **Step 3**: Rebuild `NewsletterLayout` header (Black Logo/White BG).
- [ ] **Step 4**: Update AI Prompt to generate the full JSON structure.
- [ ] **Step 5**: Verify "Slot Warming" (Ensure Ad Slot 1 renders correctly with internal content).
