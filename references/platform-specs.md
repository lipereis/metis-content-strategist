# Platform Specifications & Best Practices

Reference for Module 1 caption formatting and Module 2 platform targeting.

---

## Instagram / Reels

| Spec | Detail |
|------|--------|
| **Caption limit** | 2,200 chars (truncates at ~125 in feed, "more" expands) |
| **Hashtags** | 5-15 optimal; mix niche (3-5), broad (2-3), branded (1) |
| **Line breaks** | Critical — use double line breaks for readability |
| **Emojis** | Moderate (3-8 per caption); bullet points, section dividers |
| **CTA placement** | End of caption + first comment (hashtag block) |
| **Tagging** | @mention collaborators, locations, products |
| **Algorithm signals** | Saves > Shares > Comments > Likes > Views |
| **Best hook position** | First 125 chars (before "more") |

**Caption Template:**
```
[Hook line — ≤125 chars]

[Value body — 2-4 short paragraphs, line breaks between]

[CTA — question or direct command]
👇 / 💬 / 🔗

#nichehashtag #broadhashtag #brandedhashtag
```

---

## TikTok

| Spec | Detail |
|------|--------|
| **Caption limit** | 2,200 chars (truncates at ~150) |
| **Hashtags** | 3-5 highly relevant; trending + niche |
| **Line breaks** | Single breaks OK; less critical than IG |
| **Emojis** | Heavy encouraged (8-15); native to platform culture |
| **CTA** | "Follow for more", "Comment [X]", "Stitch this" |
| **Algorithm signals** | Completion rate > Re-watches > Shares > Comments |
| **Best hook position** | First 3 seconds of VIDEO; caption secondary |

**Caption Template:**
```
[Hook + value teaser — 1-2 lines]

[CTA — engagement driver]
👇

#trending #niche #fyp #viral
```

### TikTok Enhanced (Production Specs)

The `tiktok_enhanced` formatter returns a complete production package:

| Component | Purpose | Key Fields |
|-----------|---------|------------|
| **caption** | Algorithm-optimized caption | Hook, value bullets, retention stats, CTA, tiered hashtags |
| **overlay_specs** | Text-on-screen for each beat | timestamp, text, position, style, animation, duration, font_size, color, background |
| **sound_clusters** | Targeted sound/hashtag groups | sound_id, sound_name, hashtags, trend_status, niche_relevance |
| **hashtag_strategy** | Tiered hashtag selection | trending, niche, branded, community |
| **retention_hooks** | Key retention moments | type, timestamp, technique, text |

**Overlay Positions:** `center`, `lower_third`, `top` (rotated for visual variety)
**Overlay Styles:** `bold`, `highlight`, `typewriter`, `handwritten`
**Overlay Animations:** `pop`, `slide_up`, `typewriter`, `fade_in`
**Font Sizes:** 56 (hook), 48 (value), 42 (body)

**Sound Cluster Trend Status:** `rising`, `peak`, `evergreen`, `niche`

---

## LinkedIn

| Spec | Detail |
|------|--------|
| **Post limit** | 3,000 chars (truncates at ~140, "see more") |
| **Hashtags** | 3-5 broad professional; placed at end |
| **Line breaks** | Double breaks for paragraphs; single for list items |
| **Emojis** | Minimal (0-3); section markers only (🎯, 💡, 📊) |
| **CTA** | Question for comments ("What's your experience?") |
| **Algorithm signals** | Dwell time > Comments > Shares > Reactions |
| **Best hook position** | First 140 chars (before "see more") |

**Caption Template:**
```
[Hook — professional insight or contrarian take — ≤140 chars]

[Story / lesson / framework — 3-5 paragraphs, narrative arc]

[Key takeaway — bold or bullet]

[Question CTA — open-ended, invites perspective]

#ProfessionalHashtag #IndustryTag
```

---

## Twitter / X (Thread Format)

| Spec | Detail |
|------|--------|
| **Tweet limit** | 280 chars each |
| **Thread length** | 5-15 tweets optimal |
| **Hashtags** | 1-2 per thread; in first or last tweet |
| **Line breaks** | Single breaks within tweet; thread = sequential tweets |
| **Emojis** | Moderate (1-3 per tweet); numbering (1/10, 2/10) |
| **CTA** | Last tweet: Follow, RT, Link, Question |
| **Algorithm signals** | RTs > Replies > Likes > Profile clicks |
| **Best hook position** | Tweet 1/10 — must stand alone |

**Thread Template:**
```
1/10 [Hook — bold claim or question] 🧵

2/10 [Context / problem]

3/10 [Insight 1]

4/10 [Insight 2]

5/10 [Insight 3 / framework]

6/10 [Proof / example / data]

7/10 [Counter-objection]

8/10 [Actionable step]

9/10 [Broader implication]

10/10 [CTA — Follow for more / Link / Question]
```

---

## Threads (Meta)

| Spec | Detail |
|------|--------|
| **Post limit** | 500 chars each |
| **Thread length** | 8-15 posts optimal |
| **Hashtags** | 3-5 per thread; can be inline or at end |
| **Line breaks** | Natural paragraphs; conversational tone |
| **Emojis** | Moderate (2-5 per post); organic usage |
| **CTA** | Reply prompts, questions, "What's your take?" |
| **Algorithm signals** | Replies > Reposts > Likes > Profile clicks |
| **Best hook position** | Post 1 — must be compelling standalone |

**Thread Structure:**
```
Post 1: Hook + thread announcement 🧵
Post 2: Problem + context (reply to 1)
Post 3: Framework/Insight 1 (reply to 2)
Post 4: Framework/Insight 2 (reply to 3)
Post 5: Framework/Insight 3 (reply to 4)
Post 6: Visual/Structural proof (reply to 5)
Post 7: Multi-platform distribution (reply to 6)
Post 8: Data/Results (reply to 7)
Post 9: Counter-intuitive truth (reply to 8)
Post 10: CTA + engagement hook (reply to 9)
```

**Engagement Hooks (Reply Prompts):**
- "What's your current process for X?"
- "Which framework would you try first?"
- "How long does your [workflow] take?"
- "What's your biggest [pain point]?"
- "Manual or AI-assisted for you?"
- "Ready to test this?"

**Hashtag Strategy:**
- Broad: `#ContentStrategy #AITools #CreatorEconomy`
- Niche: `#Scriptwriting #ViralVideo #ContentAutomation`
- Branded: `#YourBrand`

---

## YouTube (Description + Metadata)

| Spec | Detail |
|------|--------|
| **Description limit** | 5,000 chars |
| **First 2 lines** | Critical for search snippet (≈150 chars) |
| **Timestamps** | Required for chapters; format `0:00 Title` |
| **Hashtags** | 3-5 above title (auto-extracted from description) |
| **Tags (backend)** | 10-15 tags; mix specific + broad |
| **CTA placement** | First 2 lines + pinned comment + end screen |
| **Algorithm signals** | AVD (avg view duration) > CTR > Engagement |

**Description Template:**
```
[SEO-optimized hook + keyword-rich summary — 2 lines max]

[Timestamps / Chapters]
0:00 Hook
0:45 The Problem
2:30 The Framework
5:15 Real Example
8:30 Results
10:00 Your Action Plan

[Expanded value — 2-3 paragraphs with keywords]

[CTA — Subscribe / Link / Resource]

[Hashtags]
#Keyword1 #Keyword2 #Branded

[Links — Socials, Course, Tool, Affiliate]
```

---

## Email Newsletter

| Spec | Detail |
|------|--------|
| **Subject line** | 30-50 chars optimal; A/B test 5 variants |
| **Preview text** | 40-100 chars; complements subject |
| **Preheader** | Hidden preview; 100 chars max |
| **Headline** | Hook-driven; mirrors subject promise |
| **Curated takeaway** | 2-3 sentence TL;DR for skim readers |
| **Main content** | 800-2000 words; scannable with headers |
| **Module highlights** | Module 1 + Module 2 sections |
| **CTA placement** | Primary (above fold) + Secondary (mid) + Footer |
| **Footer** | Unsubscribe, reply-to, social links |

**Newsletter Structure:**
```
Subject: [Hook — ≤50 chars]
Preview: [Value promise — ≤100 chars]

Preheader: [Hidden context]

Headline: [Hook — mirrors subject]

Curated Takeaway: [2-3 sentence TL;DR]

## Module 1 Highlight: [Topic]
[Scannable sections with headers, bullets, data]

## Module 2 Highlight: [Trend Radar]
[Top 3 trends with scores, insights, approval links]

CTA Primary: [Button — main action]
CTA Secondary: [Link — supporting action]

Footer: [Unsubscribe | Reply-to | Social | Preferences]
```

**Subject Line A/B Test Variants (5):**
1. Direct hook from content
2. Transformation promise (3h → 12min)
3. Pain point + fix ("costing you 90% retention")
4. Social proof ("47/50 creators doubled retention")
5. Framework reveal ("4 frameworks behind every viral video")

---

## Platform Algorithm Signals Summary (2024-2025)

| Platform | Primary Signal | Secondary | Tertiary | Content Half-Life |
|----------|----------------|-----------|----------|-------------------|
| **Reels** | Saves | Shares | Comments | 24-72 hrs |
| **TikTok** | Completion % | Re-watches | Shares | 6-48 hrs |
| **LinkedIn** | Dwell time | Comments | Shares | 7-14 days |
| **Twitter/X** | RTs | Replies | Profile visits | 15 min - 6 hrs |
| **Threads** | Replies | Reposts | Likes | 1-6 hrs |
| **YouTube** | AVD | CTR | Subs gained | Years (evergreen) |
| **Newsletter** | Open rate | Click rate | Reply rate | Days-weeks (archive) |

---

## Cross-Posting Adaptation Rules

| Element | IG → LinkedIn | IG → Threads | IG → Newsletter | IG → YouTube |
|---------|---------------|--------------|-----------------|--------------|
| **Hook** | Professionalize slang | Keep conversational | Expand to subject line | Expand to 2-line SEO summary |
| **Body** | Narrative paragraphs | Conversational replies | Scannable sections | Timestamped chapters |
| **CTA** | Question for comments | Reply prompt | Button + link | Subscribe/Link/Chapters |
| **Hashtags** | 3-5 broad pro | 3-5 inline/end | Inline tags | 3-5 SEO tags |
| **Emojis** | Reduce to 0-3 | Organic 2-5 | Minimal (0-2) | Remove from desc |
| **Line breaks** | Double paragraphs | Reply threading | Section headers | Timestamp lines |

---

## Character Limits Quick Ref

| Field | Instagram | TikTok | LinkedIn | Twitter | Threads | YouTube | Newsletter |
|-------|-----------|--------|----------|---------|---------|---------|------------|
| Caption/Post | 2,200 | 2,200 | 3,000 | 280/tweet | 500/post | 5,000 | ~2,000 words |
| Visible w/o click | 125 | 150 | 140 | 280 | 500 | 150 (snippet) | Subject: 50 |
| Hashtag count | 30 max | 100 max | 30 max | 2-3/thread | 3-5 | 15 max | N/A |
| Bio/Profile | 150 | 80 | 2,600 | 160 | 160 | 1,000 | N/A |

---

## Hashtag Strategy by Platform

| Platform | Niche Tags | Broad Tags | Branded | Trending |
|----------|------------|------------|---------|----------|
| **IG** | 3-5 | 2-3 | 1 | 0-1 (in first comment) |
| **TikTok** | 2-3 | 1-2 | 0 | 1-2 (use Discover page) |
| **LinkedIn** | 1-2 | 3-4 | 0 | 0 |
| **Twitter** | 1-2 (thread) | 0 | 0 | 0 |
| **Threads** | 2-3 | 2-3 | 1 | 0 |
| **YouTube** | 5-8 (tags) | 3-5 (desc) | 1 | 0 |
| **Newsletter** | Inline | Inline | Inline | N/A |

---

## Module 1 Formatter Integration Notes

The `utils/formatting.py` module implements platform-specific formatters that:
1. Accept structured script + hooks + tone config
2. Apply platform template above
3. Enforce char limits (truncate with `…` if needed)
4. Inject `tone.emoji_usage` and `tone.line_break_density`
5. Output ready-to-paste Markdown blocks

**Function signatures:**
```python
def format_instagram(script_data: ScriptData, tone: ToneProfile) -> str
def format_tiktok(script_data: ScriptData, tone: ToneProfile) -> str
def format_tiktok_enhanced(script_data: ScriptData, tone: ToneProfile) -> dict
def format_linkedin(script_data: ScriptData, tone: ToneProfile) -> str
def format_twitter_thread(script_data: ScriptData, tone: ToneProfile) -> list[str]
def format_threads(script_data: ScriptData, tone: ToneProfile) -> dict
def format_youtube(script_data: ScriptData, tone: ToneProfile) -> str
def format_newsletter(script_data: ScriptData, tone: ToneProfile, module2_items: list[dict] = None) -> dict
def format_for_platform(platform: str, script_data: ScriptData, tone: ToneProfile, **kwargs) -> Any
```

---

## Tone Profile Platform Overrides (Extended)

Add to `tone_of_voice.yaml` for new platforms:

```yaml
platform_overrides:
  linkedin:
    cta_style: "question_driven"
    emoji_usage: "minimal"
    hook_style: "contrarian_insight"
  instagram:
    emoji_usage: "moderate"
    hook_style: "visual_curiosity"
    line_break_density: "high"
  tiktok:
    emoji_usage: "heavy"
    hook_style: "visual_curiosity"
    line_break_density: "medium"
  threads:
    emoji_usage: "moderate"
    hook_style: "curiosity"
    cta_style: "question_driven"
    line_break_density: "high"
  twitter:
    cta_style: "direct_command"
    line_break_density: "medium"
    hook_style: "bold_statement"
  youtube:
    hook_style: "bold_statement"
    emoji_usage: "minimal"
  newsletter:
    emoji_usage: "minimal"
    hook_style: "curiosity"
    cta_style: "direct_command"
    line_break_density: "medium"
```