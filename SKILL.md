---
name: metis-content-strategist
description: "End-to-end content strategy, viral scriptwriting, and trend monitoring agent for B2B creators."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [content-strategy, viral-scriptwriting, trend-monitoring, social-media, b2b-marketing, storytelling, copywriting]
    related_skills: [la-vague-radar-curator, movie_scriptwriting, humanizer, competitor-news-monitor, blogwatcher, cronjob]
---

# Metis — The Content Strategist & Viral Scriptwriter Agent

An end-to-end B2B content production agent with two operational modules: **(1) Raw-to-Ready Pipeline** — transforms raw audio/transcripts into polished, multi-platform scripts and captions using proven copywriting frameworks; **(2) Automated Trend Radar** — monitors RSS/YouTube/Twitter feeds for niche-relevant trends, produces executive summaries and publication-ready posts, and delivers approval-ready payloads to Slack/Telegram via webhook.

Both modules share a configurable `tone_of_voice` profile and output structured Markdown/JSON for seamless CI/CD integration.

---

## When to Use

- **Module 1 (Pipeline):** You have a meeting recording, voice note, podcast transcript, or rough notes and need publication-ready scripts + captions for Reels/TikTok/Shorts, LinkedIn, X/Twitter threads, and YouTube descriptions.
- **Module 2 (Radar):** You want a scheduled (cron) or on-demand sweep of configured feeds (RSS, YouTube trending, X lists, Google Trends) in your niche, with filtered insights and "approve/edit/discard" cards sent to your team chat.
- **Shared:** You need consistent brand voice across all outputs via a `tone_of_voice` config file (Formal, Provocative, B2B Corporate, etc.).
- **Don't use for:** Long-form cinematic screenplays (use `movie_scriptwriting`), one-off cultural trend essays (use `la-vague-radar-curator`), or generic competitor tracking without content output (use `competitor-news-monitor`).

---

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Hermes Agent** | Desktop app with `terminal`, `web_search`, `web_extract`, `cronjob`, `delegate_task` tools enabled |
| **Python 3.10+** | For helper scripts in `scripts/` |
| **Optional APIs** | YouTube Data API v3 key, X/Twitter API Bearer token, Google Trends (unofficial), Slack/Telegram webhook URLs |
| **RSS Feeds** | Curated list of niche-relevant RSS/Atom feeds (stored in `config/feeds.yaml`) |
| **Tone Config** | `config/tone_of_voice.yaml` defining voice parameters (see Templates) |

---

## Quick Reference

| Action | Command / Invocation |
|--------|----------------------|
| **Run Module 1 (Pipeline)** | `python scripts/module1_pipeline.py --input "transcript.txt" --tone "B2B Corporate" --platforms "instagram,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter"` |
| **Run Module 2 (Radar) once** | `python scripts/module2_radar.py --feeds config/feeds.yaml --niche "AI automation for creators" --webhook-url $SLACK_WEBHOOK` |
| **Schedule Module 2 (cron)** | `cronjob(action="create", schedule="every 4h", prompt="Load content-strategist-viral-scriptwriter and run Module 2 Radar for niche 'AI automation for creators' with webhook $SLACK_WEBHOOK", skills=["content-strategist-viral-scriptwriter"])` |
| **Validate tone config** | `python scripts/validate_tone.py config/tone_of_voice.yaml` |
| **Test webhook payload** | `python scripts/test_webhook.py --url $SLACK_WEBHOOK --sample` |

---

## Configuration Files

### `config/tone_of_voice.yaml` — Voice Profile Schema

```yaml
tone_id: "b2b_corporate"              # unique slug
display_name: "B2B Corporativo"       # human label
language: "pt-BR"                     # output language
persona:
  archetype: "Expert Mentor"          # e.g., "Provocative Analyst", "Friendly Peer"
  traits: ["authoritative", "data-driven", "actionable", "concise"]
  forbidden_words: ["vibes", "game-changer", "unlock", "skyrocket", "masterclass"]
  preferred_phrases: ["In practice,", "The data shows", "Key takeaway:", "Action item:"]
structure_preferences:
  hook_style: "contrarian_insight"    # curiosity, contrarian, pain_point, social_proof, bold_statement
  cta_style: "question_driven"        # question, direct_command, resource_link
  emoji_usage: "minimal"              # none, minimal, moderate, heavy
  line_break_density: "high"          # low, medium, high
platform_overrides:
  linkedin:
    cta_style: "question_driven"
    emoji_usage: "minimal"
  instagram:
    emoji_usage: "moderate"
    hook_style: "visual_curiosity"
  twitter:
    cta_style: "direct_command"
    line_break_density: "medium"
  youtube:
    hook_style: "bold_statement"
```

### `config/feeds.yaml` — Radar Feed Sources

```yaml
niche: "AI automation for content creators"
keywords: ["AI content", "automation workflow", "creator economy", "viral video", "scriptwriting AI"]
rss_feeds:
  - name: "The Verge AI"
    url: "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"
    category: "tech_news"
  - name: "Creator Economy Newsletter"
    url: "https://creatoreconomy.so/rss/"
    category: "creator_business"
  - name: "Marketing AI Institute"
    url: "https://www.marketingaiinstitute.com/blog/rss.xml"
    category: "marketing_tech"
youtube_channels:
  - "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Example: Creator-focused channel ID
  - "UCJowOS1R0FnhipXVqEnYU1A"  # Example: AI tools channel
twitter_lists:
  - "1234567890123456789"  # List ID for "Top AI Creators"
google_trends_regions: ["BR", "US", "PT"]
scan_window_hours: 24
max_items_per_source: 10
materiality_threshold: 0.7  # 0-1, higher = stricter
```

---

## Procedure — Module 1: Raw-to-Ready Pipeline

### Input
- **Raw text** (transcript, voice note, meeting notes) — passed as file path or stdin
- **Tone profile** — slug from `tone_of_voice.yaml` (default: `b2b_corporate`)
- **Target platforms** — comma-separated subset of `instagram,tiktok,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter`

### Step 1: Clean & Structure Transcript
- Remove filler words ("né", "tipo assim", "é", "ah", pauses)
- Segment into logical topics using semantic boundaries
- Extract: **Core Thesis**, **Supporting Arguments**, **Data Points**, **Quotable Soundbites**, **Audience Pain Points**
- **Completion:** JSON object with labeled segments saved to workspace.

### Step 2: Apply Copywriting Frameworks
- Map each segment to **AIDA** (Attention → Interest → Desire → Action) or **PAS** (Problem → Agitation → Solution) or **Hook-Value-CTA** based on platform
- For each platform, select the framework that maximizes retention/conversion
- **Completion:** Framework-mapped outline per platform.

### Step 3: Generate 5 High-Impact Hooks (First 3 Seconds)
Produce 5 variations categorized by psychological trigger:
| Type | Description | Example |
|------|-------------|---------|
| **Curiosity** | Information gap | "The editing technique 99% of creators ignore..." |
| **Contrarian** | Counter-intuitive truth | "Stop posting daily — do this instead" |
| **Pain Point** | Visceral problem | "Why your Reels get 200 views and die" |
| **Social Proof** | Authority/results | "How [Client] 10x'd views with one script change" |
| **Bold Statement** | Provocative claim | "Your content calendar is a waste of time" |
- **Completion:** 5 hooks with type labels, ready for A/B testing.

### Step 4: Produce Video Script + Edit Guide (Markdown Table)
| Time | Voiceover (A-Roll) | B-Roll / Visual Cue | Text Overlay | SFX / Music Cue |
|------|-------------------|---------------------|--------------|-----------------|
| 0-3s | [Hook line] | Close-up face / screen record | **Hook text** | Whoosh / pop |
| 3-10s | [Context/Problem] | B-roll of struggle | "The Problem" | Tension riser |
| ... | ... | ... | ... | ... |
- **Completion:** Full script table with visual/audio direction.

### Step 5: Generate Platform-Specific Captions
| Platform | Format Rules |
|----------|--------------|
| **Instagram/TikTok** | Dynamic tone, strategic emojis, clean line breaks, engagement CTA ("Save this!", "Comment your biggest struggle"), 5-8 niche hashtags |
| **LinkedIn** | Professional narrative, "Lesson learned" framing, authority-building, ends with question for comments, 3-5 broad hashtags |
| **Twitter/X** | Thread format (1/n), hook tweet → value tweets → CTA tweet, highly shareable, 2-3 hashtags |
| **YouTube** | SEO-optimized description, timestamps (0:00 Hook, 0:45 Problem, ...), links/CTAs, 10-15 tags |
| **TikTok Enhanced** | Algorithm-optimized caption + text-on-screen overlay specs (position, style, animation per beat) + targeted sound/hashtag clusters (trending, niche, branded, community) + retention hooks |
| **Threads** | Multi-post thread structure (8-15 posts), conversational tone, reply prompts per post, organic hashtag usage, engagement hooks for replies |
| **Newsletter** | Subject line (A/B test 5 variants), preview text, curated takeaway (2-3 sentence TL;DR), Module 1 highlight + Module 2 radar section, primary/secondary CTAs, footer with unsubscribe |
- **Completion:** Ready-to-paste caption blocks in a single Markdown file (extended platforms return structured data: overlay specs, thread posts, newsletter sections).

### Step 6: Deliver Output
- Write `output/{timestamp}_pipeline_result.md` with all sections clearly separated
- Print summary to console with file path
- **Verification:** File exists, contains all 4 caption blocks, script table has ≥5 rows, 5 hooks present.

---

## Procedure — Module 2: Automated Trend Radar (Cron-Ready)

### Input (from config + runtime args)
- **Niche definition** — 1-2 sentence description + keywords
- **Feed sources** — `config/feeds.yaml`
- **Tone profile** — for post drafting
- **Webhook URL** — Slack (`incoming-webhook`) or Telegram (`bot_token` + `chat_id`)
- **Approval channel** — where cards are posted

### Step 1: Incremental Feed Collection
- For each RSS feed: fetch new items since last successful run (stored in `state/last_run.json`)
- For YouTube: call `search.list` with `order=viewCount`, `publishedAfter=last_run`, filter by channel IDs + keywords
- For Twitter/X: fetch list timeline, filter by engagement threshold (likes + RTs > 50) + keywords
- For Google Trends: fetch `daily_trends` for regions, filter by keyword overlap
- **Dedupe** by URL canonicalization + title similarity (Jaccard > 0.8)
- **Completion:** Raw candidate pool saved to `state/candidates_{timestamp}.json`.

### Step 2: Strategic Filtering & Scoring
For each candidate, compute **Relevance Score** (0-1):
- Keyword density in title/body (30%)
- Source authority tier (20%) — Tier 1: primary sources, Tier 2: trade pubs, Tier 3: aggregators
- Recency decay (20%) — exponential decay over `scan_window_hours`
- Engagement velocity (15%) — views/likes/comments per hour
- Cross-source corroboration (15%) — same topic appears in ≥2 sources
- **Threshold:** Keep only items with score ≥ `materiality_threshold` (default 0.7)
- **Completion:** Ranked shortlist (top 5) saved to `state/shortlist_{timestamp}.json`.

### Step 3: Executive Summary + Insight Generation
For each shortlisted item, produce:
```json
{
  "title": "Original headline",
  "source": "Publication / Channel @handle",
  "url": "https://...",
  "score": 0.87,
  "executive_summary": "3-sentence summary: what happened, why it matters for [niche], implied opportunity/threat.",
  "key_insight": "One-sentence strategic takeaway for the audience.",
  "suggested_angle": "Contrarian / Educational / Case Study / Prediction / Framework"
}
```
- **Completion:** Enriched shortlist with insights.

### Step 4: Draft Publication-Ready Post
Using the **tone profile** and **platform override** (default: primary channel from config, e.g., LinkedIn):
- Apply platform-specific structure (from Module 1 Step 5)
- Inject the `key_insight` as the core value
- Include **source attribution** ("Via @source")
- Add **CTA** per tone config (`question_driven` → "What's your take on this shift?")
- **Completion:** `draft_post` field added to each shortlist item.

### Step 5: Format Approval Card (Slack Block Kit / Telegram Inline Keyboard)
**Slack Payload:**
```json
{
  "blocks": [
    {"type": "header", "text": {"type": "plain_text", "text": "📰 [Title]"}},
    {"type": "section", "text": {"type": "mrkdwn", "text": "*Fonte:* [Source]\n*Por que importa:* [executive_summary]\n\n*✍️ Sugestão de Post:*\n[draft_post]"}},
    {"type": "actions", "elements": [
      {"type": "button", "text": {"type": "plain_text", "text": "✅ Aprovar"}, "style": "primary", "value": "approve_{item_id}"},
      {"type": "button", "text": {"type": "plain_text", "text": "✏️ Pedir Alteração"}, "value": "edit_{item_id}"},
      {"type": "button", "text": {"type": "plain_text", "text": "🗑️ Descartar"}, "style": "danger", "value": "discard_{item_id}"}
    ]}
  ]
}
```
**Telegram Payload:** InlineKeyboardMarkup with same three buttons, `callback_data` = action_itemId.

- **Completion:** Webhook POST delivered, response logged.

### Step 6: State Persistence & Silence on Empty
- Update `state/last_run.json` with current timestamp and processed item IDs
- If shortlist is empty → **no webhook sent** (silent tick) unless `force_report=true`
- **Verification:** State file updated; webhook delivery logged (success/4xx/5xx).

---

## Integration — Slack / Telegram Webhook Setup

### Slack (Incoming Webhook)
1. Create Slack App → Incoming Webhooks → Install to Workspace → Copy Webhook URL
2. Set env var: `export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."`
3. Test: `python scripts/test_webhook.py --url $SLACK_WEBHOOK_URL --sample`

### Telegram (Bot + Webhook)
1. Create bot via @BotFather → Get `BOT_TOKEN`
2. Get `CHAT_ID` (add bot to group, send message, call `getUpdates`)
3. Set env vars: `export TELEGRAM_BOT_TOKEN="..."`, `export TELEGRAM_CHAT_ID="-100..."`
4. Test: `python scripts/test_webhook.py --telegram --token $TELEGRAM_BOT_TOKEN --chat $TELEGRAM_CHAT_ID --sample`

### Cronjob Registration (Hermes)
```bash
# Every 4 hours during business hours (9am-9pm BRST)
cronjob action=create \
  schedule="0 9-21/4 * * *" \
  prompt="Load content-strategist-viral-scriptwriter skill and run Module 2 Radar for niche 'AI automation for content creators' with webhook $SLACK_WEBHOOK_URL" \
  skills=["content-strategist-viral-scriptwriter"] \
  name="content-radar-4h" \
  deliver="origin"
```

---

## Helper Scripts (in `scripts/`)

| Script | Purpose | Key Functions |
|--------|---------|---------------|
| `module1_pipeline.py` | CLI entry for Module 1 | `clean_transcript()`, `apply_frameworks()`, `generate_hooks()`, `build_script_table()`, `write_captions()` |
| `module2_radar.py` | CLI entry for Module 2 | `collect_feeds()`, `score_candidates()`, `generate_insights()`, `draft_posts()`, `send_webhook()` |
| `validate_tone.py` | Validates `tone_of_voice.yaml` schema | Pydantic model validation |
| `test_webhook.py` | Sends sample approval card | Slack Block Kit / Telegram InlineKeyboard |
| `utils/feeds.py` | RSS/YouTube/Twitter/Trends fetchers | `fetch_rss()`, `fetch_youtube()`, `fetch_twitter_list()`, `fetch_trends()` |
| `utils/scoring.py` | Relevance scoring logic | `compute_relevance()`, `dedupe_candidates()` |
| `utils/formatting.py` | Platform caption formatters | `format_instagram()`, `format_tiktok()`, `format_tiktok_enhanced()`, `format_linkedin()`, `format_twitter_thread()`, `format_threads()`, `format_youtube()`, `format_newsletter()` |
| `utils/llm_delegation.py` | LLM delegation builders | `build_hook_generation_task()`, `build_insight_generation_task()`, `build_draft_post_task()` |
| `hermes_entry.py` | Hermes LLM-enhanced entry points | `run_pipeline_llm()`, `run_radar_llm()` |
| `deploy_client.py` | Automated client onboarding | Creates config, validates keys, registers cron, tests webhook |
| `review_local.py` | Local CLI Review & Approval Sandbox | Interactive terminal dashboard for reviewing, editing, approving Module 1/2 content |

All scripts use `typer` for CLI, `pydantic` for config validation, `httpx` for async HTTP, `python-dotenv` for env loading.

---

## LLM-Enhanced Generation (Hermes `delegate_task`)

When running inside Hermes Agent, both modules support **structured LLM delegation** via the built-in `delegate_task` tool for higher-quality creative output:

| Module | Feature | Delegation Function | Output Schema |
|--------|---------|---------------------|---------------|
| **Module 1** | Hook Generation | `generate_hooks_llm()` | `HooksOutputSchema` (5 typed hooks) |
| **Module 2** | Insight Generation | `generate_insights_llm()` | `InsightSchema` (summary, insight, angle) |
| **Module 2** | Draft Post Generation | `draft_post_llm()` | `DraftPostSchema` (platform-optimized post) |

### How It Works

1. **Structured Prompts** — Each delegation uses a detailed prompt with tone profile, platform specs, and psychological trigger taxonomy
2. **JSON Schema Validation** — Output validated against Pydantic schemas (retry on failure)
3. **Fallback** — If `delegate_task` unavailable (CLI mode), falls back to template-based generation
4. **Tone Enforcement** — Forbidden words, preferred phrases, and platform overrides injected into prompts

### Hermes Usage

```python
# In Hermes chat with skill loaded:
from scripts.hermes_entry import run_pipeline_llm, run_radar_llm

# Module 1 with LLM hooks
result = await run_pipeline_llm(
    input_path="transcripts/meeting.txt",
    tone_id="b2b_corporate",
    platforms=["instagram", "linkedin", "twitter", "youtube"],
    delegate_task_fn=delegate_task  # Hermes built-in tool
)

# Module 2 with LLM insights + drafts
items = await run_radar_llm(
    feeds_config="config/feeds.yaml",
    tone_config="config/tone_of_voice.yaml",
    webhook_url=SLACK_WEBHOOK_URL,
    delegate_task_fn=delegate_task
)
```

See `scripts/hermes_entry.py` for full implementation.

---

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| Transcript cleaning removes speaker identity | Preserve `[Speaker 1]`/`[Speaker 2]` tags before cleaning; pass to script as context |
| Hooks feel generic / clickbaity | Enforce `tone.forbidden_words`; require each hook to reference a specific insight from Step 1 |
| Radar pulls irrelevant viral content | Tighten `keywords` + raise `materiality_threshold`; add negative keywords to `feeds.yaml` |
| Webhook buttons don't work (Slack) | Ensure Slack App has `commands` + `chat:write` scopes; interactivity endpoint configured for "edit" flow |
| Cron runs but no delivery visible | Check `state/last_run.json` timestamp; verify webhook URL env var exists in cron environment |
| Tone config ignored on LinkedIn | Confirm `platform_overrides.linkedin` exists in tone YAML; module merges base + override |
| YouTube API quota exhausted | Cache channel uploads; use `search.list` with `maxResults=5` per channel; implement exponential backoff |

---

## Verification Checklist

- [ ] `config/tone_of_voice.yaml` passes `validate_tone.py` without errors
- [ ] `config/feeds.yaml` contains at least 3 RSS feeds + 1 YouTube channel + 1 Twitter list
- [ ] Module 1: Given a 5-min transcript, produces Markdown with 5 hooks, script table (≥8 rows), 4 caption blocks
- [ ] Module 2: Single run returns ≤5 cards, each with executive_summary, draft_post, and working Slack/Telegram buttons
- [ ] Cronjob `content-radar-4h` appears in `cronjob(action="list")` and fires on schedule
- [ ] Webhook test delivers a sample card to target channel with three clickable buttons
- [ ] Outputs respect `tone.forbidden_words` (grep output for any forbidden term → zero hits)

---

## References

- `references/copywriting-frameworks.md` — AIDA, PAS, Hook-Value-CTA, StoryBrand cheat sheets with examples
- `references/hook-taxonomy.md` — 25 hook templates categorized by psychological trigger
- `references/platform-specs.md` — Character limits, hashtag best practices, algorithm signals per platform
- `references/webhook-schemas.md` — JSON Schema for Slack Block Kit and Telegram InlineKeyboard payloads

---

## Templates

- `templates/tone_of_voice.yaml` — Starter tone profiles (b2b_corporate, provocative_analyst, friendly_peer, formal_academic)
- `templates/feeds.yaml` — Example feed configs for "AI automation", "Creator economy", "B2B SaaS marketing"
- `templates/pipeline_output.md` — Annotated example of Module 1 final Markdown
- `templates/radar_card.json` — Example Slack/Telegram approval card payload

---

## Related Skills

- `la-vague-radar-curator` — Cultural trend hunting for editorial magazine (cinema/fashion/music)
- `movie_scriptwriting` — Hollywood screenplay format for narrative fiction
- `humanizer` — Strip AI-isms from generated copy
- `competitor-news-monitor` — Company-specific material event tracking
- `blogwatcher` — RSS/Atom feed ingestion (used by Module 2 feed collector)
- `cronjob` — Scheduling Module 2 recurring runs