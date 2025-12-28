# Reference Management Guidelines

**Version:** 1.0  
**Last Updated:** November 15, 2025  
**Purpose:** Standards for managing citations and references in blog content

---

## Core Principle

**The `lastUpdated` date means ALL references were verified as working and accurate on that date.**

When you update a blog post and change the `lastUpdated` field, you are certifying that:
1. Every reference link has been tested and works
2. The source content is still relevant and accurate
3. No better/newer sources exist for the cited information

---

## Reference Verification Workflow

### When Creating New Content

1. **As You Write**
   - Add inline citations `[1]`, `[2]`, etc. as you make claims
   - Build the References section incrementally
   - Verify each link as you add it

2. **Before Publishing**
   - Click every reference link to confirm it loads
   - Verify the URL points to the intended content
   - Check that statistics/data match what you cited
   - Ensure publication dates are included where applicable

3. **Set Initial Dates**
   - `date:` Publication date
   - `lastUpdated:` Same as publication date initially

### When Updating Existing Content

**MANDATORY CHECKLIST:**

- [ ] Click EVERY reference link in the References section
- [ ] Verify each URL still works (200 OK status)
- [ ] Confirm cited data is still current (not superseded)
- [ ] Check for moved content (301 redirects)
- [ ] Fix or replace any broken links
- [ ] ONLY THEN update `lastUpdated` field

**Do NOT update `lastUpdated` without completing this checklist.**

---

## What To Do When Links Break

### Scenario 1: Temporary Outage
**Signs:** Server error (500), timeout, or DNS issues  
**Action:** Wait 24 hours, retry. If still broken, proceed to Scenario 2.

### Scenario 2: Page Moved (301/302 Redirect)
**Signs:** Redirect status, new URL  
**Action:** 
1. Update reference to new URL
2. Verify content is identical
3. Note if URL structure changed

### Scenario 3: Page Deleted (404)
**Signs:** 404 Not Found, "page doesn't exist"  
**Action:**
1. Check Wayback Machine: https://web.archive.org/
2. If archived version exists:
   - Use archived URL: `https://web.archive.org/web/[timestamp]/[original-url]`
   - Add note: "(Archived)" after the reference
3. If no archive exists:
   - Search for equivalent source
   - If none found, remove citation and rework claim

### Scenario 4: Source Updated/Superseded
**Signs:** Data looks old, newer reports available  
**Action:**
1. Find latest version of report/data
2. Update reference to new source
3. Verify numbers in your content match new source
4. Update your content if data changed materially

---

## Using the Wayback Machine

**When to use:**
- Original source is gone (404)
- Website shutdown/domain expired
- Content removed but still valuable

**How to use:**
1. Go to: https://web.archive.org/
2. Enter original URL
3. Select closest date to your publication date
4. Verify content is the same
5. Use the Wayback URL in your reference

**Format:**
```markdown
[Original Title]. Archived at: https://web.archive.org/web/20250115120000/https://example.com/article
```

---

## Reference Quality Standards

### Preferred Sources (Tier 1)
✅ Government agencies (Federal Reserve, BLS, Census, etc.)  
✅ Academic institutions (.edu domains)  
✅ Peer-reviewed journals  
✅ Major financial institutions (Vanguard, Fidelity)  
✅ Reputable news (WSJ, Bloomberg, Reuters)

### Acceptable Sources (Tier 2)
⚠️ Industry reports (verify methodology)  
⚠️ Established blogs (Mr. Money Mustache, White Coat Investor)  
⚠️ Company research (if transparent about methods)  
⚠️ Non-profit organizations (with clear mission)

### Avoid (Tier 3)
❌ Social media posts (unless primary source)  
❌ Anonymous blogs  
❌ Content mills  
❌ Promotional material disguised as research  
❌ Sources with obvious conflicts of interest

---

## Automated Tools

### Check All Blog References
```bash
# Check all posts
pnpm check:references

# Check specific post
pnpm check:references --slug trump-50-year-mortgage

# Check posts older than 6 months
pnpm check:references --stale 180

# Generate detailed report
pnpm check:references --report
```

**Recommended Schedule:**
- Run weekly on all content
- Fix broken links within 48 hours
- Review "stale" warnings (>12 months) monthly

### What the Script Checks
- HTTP status codes (200, 301, 404, 500, etc.)
- Response times (flags slow > 2 seconds)
- SSL certificate validity
- Basic accessibility

**What it DOESN'T check:**
- Content accuracy (you must verify manually)
- Paywalls (may report as "working" even if inaccessible)
- JavaScript-required pages (may not load properly)

---

## Publication Date vs Last Updated

### Publication Date (`date`)
- Original publish date
- **NEVER changes**
- Used for sorting/chronology
- Shows readers when content was created

### Last Updated (`lastUpdated`)
- Date content was last reviewed/modified
- **Changes with every significant update**
- Signals freshness to readers
- Implies all references verified as of this date

### When to Update `lastUpdated`

**YES - Update the date:**
- Fixed broken reference links
- Updated statistics with newer data
- Added new sections or significant content
- Corrected factual errors
- Verified all references still work

**NO - Don't update the date:**
- Fixed typos or grammar
- Minor wording improvements
- Formatting changes only
- No reference verification performed

---

## Link Rot Prevention Strategy

### Short-term (Manual - Now)
1. Verify references when updating posts
2. Use Wayback Machine for dead links
3. Track broken links in issue queue

### Medium-term (Semi-automated - Month 1)
1. Run weekly link checks
2. Get alerts for broken links
3. Fix systematically, starting with most-viewed posts

### Long-term (Automated - Month 3+)
1. Auto-archive references when published
2. Continuous link health monitoring
3. Dashboard for link health by post
4. Proactive alerts before readers notice

---

## Examples

### Good Reference
```markdown
1. Federal Reserve. (2024). Distribution of Household Wealth in the U.S. 
   Board of Governors of the Federal Reserve System. 
   https://www.federalreserve.gov/releases/z1/dataviz/dfa/distribute
```
✅ Clear source, full URL, publication date

### Reference with Archive
```markdown
2. Munger, C. (1998). "The First $100,000 is a Bitch." Speech at USC Business School. 
   (As referenced in Poor Charlie's Almanack). 
   Archived: https://web.archive.org/web/20230115120000/https://original-source.com
```
✅ Original citation + archive fallback

### Reference After 301 Redirect
```markdown
3. Investopedia. (2024). Lifestyle Creep Definition and Examples. 
   https://www.investopedia.com/terms/l/lifestyle-creep.asp 
   (Updated from previous URL: /lifestyle-creep-definition)
```
✅ Shows URL changed, provides transparency

---

## Common Questions

**Q: What if I can't verify all references due to paywalls?**  
A: If you originally had access, note "(Subscription required)" in the reference. Don't cite paywalled content you can't verify.

**Q: How often should I update `lastUpdated` on old posts?**  
A: Minimum every 12 months for evergreen content. More frequently (6 months) for data-heavy posts.

**Q: What if a source has multiple broken links?**  
A: Fix them all in one update, then change `lastUpdated` once. Don't update the date multiple times in one day.

**Q: Should I update dates for minor fixes?**  
A: No. Reserve `lastUpdated` for substantial changes and reference verification. Typo fixes don't count.

**Q: What about references to books?**  
A: Include publisher, year, and ISBN if possible. Link to Library of Congress or Amazon (in that order).

---

## Maintenance Cadence

| Content Age | Check Frequency | Priority |
|------------|----------------|----------|
| 0-3 months | On update only | Low |
| 3-6 months | On update only | Low |
| 6-12 months | Quarterly | Medium |
| 12-24 months | Every 6 months | High |
| 24+ months | Every 6 months | Critical |

**High-traffic posts:** Check every 6 months regardless of age

---

## Red Flags That Require Immediate Action

🚨 **Fix within 24 hours:**
- Hero post has broken references
- Featured post has broken references  
- More than 20% of references broken in any post
- Government/academic source returns 404

⚠️ **Fix within 1 week:**
- Any post with 1-2 broken links
- Redirects that changed domain
- Sources that moved behind paywalls

📅 **Fix within 1 month:**
- Slow-loading references (>3 seconds)
- Sources with expired SSL certificates
- Posts older than 18 months without verification

---

## Implementation Checklist

**Phase 1: Today**
- [ ] Review this document
- [ ] Understand `lastUpdated` convention
- [ ] Know how to use Wayback Machine

**Phase 2: This Week**  
- [ ] Run `pnpm check:references` for first time
- [ ] Create issue for each broken link
- [ ] Fix critical broken links (hero/featured posts)

**Phase 3: This Month**
- [ ] Set up weekly automated checks
- [ ] Establish workflow for handling alerts
- [ ] Review and update oldest posts (24+ months)

---

## Tools & Resources

- **Wayback Machine**: https://web.archive.org/
- **Link Checker Script**: `pnpm check:references`
- **HTTP Status Reference**: https://httpstatuses.com/
- **Archive.org Save API**: https://docs.google.com/document/d/1Nsv52MvSjbLb2PCpHlat0gkzw0EvtSgpKHu4mk0MnrA/

---

**Remember:** Every reference is a promise to your readers that the information is verifiable and credible. Broken links break that promise. Take reference management seriously—it's part of your editorial integrity.

