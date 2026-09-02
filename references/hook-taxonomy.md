# Hook Taxonomy — 25 Templates by Psychological Trigger

Used by Module 1 Step 3 to generate 5 categorized hooks per input.

---

## 1. CURIOSITY (Information Gap)

| # | Template | Fill-in Example |
|---|----------|-----------------|
| 1.1 | "The [specific thing] [authority/stat] don't want you to know" | "The editing trick top 1% creators hide" |
| 1.2 | "Why [common practice] is actually [counter-fact]" | "Why posting daily kills your reach" |
| 1.3 | "What [successful entity] does at [specific time] that you don't" | "What MrBeast does at 3 AM" |
| 1.4 | "The hidden [metric/signal] behind every viral [format]" | "The hidden retention signal behind every viral Reel" |
| 1.5 | "[Number] things about [topic] that [authority] never mentions" | "3 things about the algorithm TikTok never mentions" |

**Psychology:** Zeigarnik effect — open loops demand closure.

---

## 2. CONTRARIAN / COUNTER-INTUITIVE

| # | Template | Fill-in Example |
|---|----------|-----------------|
| 2.1 | "Stop [universal advice]. Start [alternative] instead." | "Stop optimizing for watch time. Optimize for re-watches." |
| 2.2 | "Everyone says [X]. The data says [Y]." | "Everyone says hook first. The data says context first." |
| 2.3 | "[Popular strategy] is a trap. Here's why." | "Content calendars are a trap. Here's why." |
| 2.4 | "The [adjective] truth about [sacred cow]" | "The uncomfortable truth about 'consistency'" |
| 2.5 | "You're not [failing because of X]. You're [failing because of Y]." | "You're not failing because of the algorithm. You're failing because of your structure." |

**Psychology:** Cognitive dissonance + authority positioning.

---

## 3. PAIN POINT / PROBLEM-FIRST

| # | Template | Fill-in Example |
|---|----------|-----------------|
| 3.1 | "Why your [output] [fails specific way] (and the fix)" | "Why your scripts flop in the first 3 seconds" |
| 3.2 | "[Specific frustration]? You're missing [one element]." | "Getting 200 views? You're missing the 're-watch trigger'." |
| 3.3 | "The real reason [effort] doesn't equal [result]" | "The real reason 3-hour scripts get 50 views" |
| 3.4 | "[Symptom] is not the problem. [Root cause] is." | "Low retention isn't the problem. Weak structure is." |
| 3.5 | "If you're [doing X] but [result Y], read this." | "If you're posting daily but not growing, read this." |

**Psychology:** Identification → relief → trust.

---

## 4. SOCIAL PROOF / AUTHORITY / RESULTS

| # | Template | Fill-in Example |
|---|----------|-----------------|
| 4.1 | "How [client/creator] [result] in [timeframe] with [method]" | "How a 5k creator hit 1M views in 7 days with this framework" |
| 4.2 | "[Authority] uses this [framework/tool]. Here's the breakdown." | "Ali Abdaal uses this script structure. Here's the breakdown." |
| 4.3 | "[Number] creators tested this. [Number] saw [result]." | "50 creators tested this hook formula. 47 saw 2x retention." |
| 4.4 | "The exact [script/structure] that got [result] for [niche]" | "The exact script structure that got 10M views for tech reviewers" |
| 4.5 | "Steal the [asset] that [top performer] uses for [outcome]" | "Steal the outline template top LinkedIn creators use" |

**Psychology:** Mimetic desire + proof reduces risk.

---

## 5. BOLD STATEMENT / PROVOCATIVE CLAIM

| # | Template | Fill-in Example |
|---|----------|-----------------|
| 5.1 | "[Industry standard] is dead. [New paradigm] wins." | "The content calendar is dead. Dynamic systems win." |
| 5.2 | "You don't need [expensive thing]. You need [simple thing]." | "You don't need a $5k camera. You need a 3-act structure." |
| 5.3 | "Most [role] waste [time/money] on [activity]. Don't." | "Most creators waste hours on editing. Don't." |
| 5.4 | "The [adjective] [number] rule that changes everything." | "The brutal 3-second rule that changes everything." |
| 5.5 | "[Year]: If you're not [doing X], you're [consequence]." | "2026: If you're not using AI for scripts, you're invisible." |

**Psychology:** Urgency + identity threat + clear alternative.

---

## Platform-Hook Fit Matrix

| Hook Type | Reels/TikTok | LinkedIn | Twitter/X | YouTube |
|-----------|--------------|----------|-----------|---------|
| Curiosity | ★★★★★ | ★★★☆☆ | ★★★★☆ | ★★★★☆ |
| Contrarian | ★★★★☆ | ★★★★★ | ★★★★★ | ★★★☆☆ |
| Pain Point | ★★★★☆ | ★★★★★ | ★★★☆☆ | ★★★★☆ |
| Social Proof | ★★★☆☆ | ★★★★★ | ★★★★☆ | ★★★★★ |
| Bold Statement | ★★★★★ | ★★★☆☆ | ★★★★★ | ★★★★☆ |

★ = effectiveness for platform-native consumption patterns.

---

## Generation Rules for Module 1

1. **Extract 3-5 distinct insights** from cleaned transcript (Step 1 output)
2. **Map each insight** to 1 hook type (cycle through all 5 types)
3. **Instantiate template** with specific nouns/numbers from the insight
4. **Apply tone filter**: Remove `forbidden_words`, enforce `emoji_usage`, `line_break_density`
5. **Score & rank**: Internal heuristic — specificity > generality, quantified > vague, visual > abstract
6. **Output top 5** (one per type) with type label attached

---

## Example: Input Insight → 5 Hooks

**Insight:** "Client reduced script writing from 3 hours to 12 minutes using AI agent, views went from 200 avg to 15k avg."

| Type | Generated Hook |
|------|----------------|
| Curiosity | "The 12-minute script workflow that 10x'd a creator's views" |
| Contrarian | "Stop spending 3 hours on scripts. This AI does it in 12 minutes." |
| Pain Point | "Stuck at 200 views? Your script process is the bottleneck." |
| Social Proof | "How one creator went 200→15k views by changing ONLY their script structure" |
| Bold Statement | "Manual scriptwriting is obsolete. The 12-minute AI workflow wins." |

---

## Quality Gates (Auto-Check)

- [ ] Each hook ≤ 160 chars (Twitter-safe) / ≤ 125 chars (TikTok caption-safe)
- [ ] Zero `forbidden_words` from tone config
- [ ] At least 1 specific number or proper noun per hook
- [ ] No duplicate template structure across the 5
- [ ] Visual language present in ≥3 hooks ("see", "watch", "visual", "screen", "frame")