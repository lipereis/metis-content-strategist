# Metis — The Content Strategist & Viral Scriptwriter Agent

End-to-end B2B content production agent with two operational modules:

1. **Module 1: Raw-to-Ready Pipeline** — Transforms raw audio/transcripts into polished, multi-platform scripts and captions using proven copywriting frameworks
2. **Module 2: Automated Trend Radar** — Monitors RSS/YouTube/Twitter feeds for niche-relevant trends, produces executive summaries and publication-ready posts, delivers approval-ready payloads to Slack/Telegram via webhook

---

## How it runs

Rule-based steps run locally. The writing steps call an LLM through any OpenAI-compatible endpoint (Google's Gemini endpoint by default, which has a free tier), and every reply is validated against a Pydantic schema, with one retry that shows the model its validation error.

| Step | How |
|------|-----|
| Transcript cleaning and segmenting (thesis, arguments, data points, soundbites, pain points) | Rules for transcripts with `Tese:` / `Argumento:` / `Dado:` style markers; the LLM structures transcripts without markers |
| Framework map per platform | Rules |
| Five hooks (one per type), video script table, one caption per platform | LLM, prompted with the transcript's own content and told not to invent facts or numbers |
| Feed fetching (RSS, YouTube, X), relevance scoring, dedupe, state between runs | Local code |
| Executive summary, key insight, angle and draft post for each shortlisted trend | LLM |
| Approval cards to Slack or Telegram by webhook, local review sandbox | Local code |

```bash
export METIS_LLM_API_KEY=...        # free Gemini key: https://aistudio.google.com/apikey
# optional: METIS_LLM_BASE_URL, METIS_LLM_MODEL (default gemini-flash-latest)

python scripts/module1_pipeline.py --input sample_transcript.txt --tone-config templates/tone_of_voice.yaml
python scripts/module2_radar.py --feeds templates/feeds.yaml --tone-config templates/tone_of_voice.yaml --dry-run
```

Without a key, both commands stop with an error instead of producing canned text. `--offline` runs only the rule-based steps: Module 1 writes the segments and framework map with no hooks, script or captions; Module 2 shortlists trends and shows each feed's own preview with no draft. `--dry-run` on Module 2 prints the approval cards instead of sending them, so no webhook is needed to try it.

Tests fake the LLM, so they run without a key: `pytest tests`.

### Limits

- Metis started as a skill for the Hermes agent. `scripts/hermes_entry.py`, `scripts/llm_delegation.py`, `deploy_client.py` and the cron examples below belong to that integration and have not been re-tested since the standalone LLM path was added.
- The model is instructed to stay within the source material, but nothing checks its output against the transcript. A person should review before publishing; Module 2 is built around that approval step.
- Google Trends fetching currently fails (the endpoint no longer returns JSON), and YouTube and X need their own API keys. RSS is the source that works out of the box.
- `sample_transcript.txt` and the numbers in it are made-up input for trying the pipeline. They are not measured results.

---

## Installation

### 1. Install Dependencies
```bash
git clone https://github.com/lipereis/metis-content-strategist.git
cd metis-content-strategist
pip install -r requirements.txt
```

### 2. Configure Tone of Voice
```bash
cp templates/tone_of_voice.yaml config/tone_of_voice.yaml
# Edit config/tone_of_voice.yaml to match your brand voice
python scripts/validate_tone.py config/tone_of_voice.yaml
```

### 3. Configure Feed Sources (Module 2)
```bash
cp templates/feeds.yaml config/feeds.yaml
# Edit config/feeds.yaml with your niche, keywords, and feed sources
# Add API keys as environment variables:
# YOUTUBE_API_KEY, TWITTER_BEARER_TOKEN
```

### 4. Configure Webhooks
```bash
# Slack: Create incoming webhook, set SLACK_WEBHOOK_URL
# Telegram: Create bot, set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

---

## Usage

### Module 1: Pipeline (One-off)
```bash
# From transcript file
python scripts/module1_pipeline.py \
  --input transcripts/my_meeting.txt \
  --tone b2b_corporate \
  --platforms instagram,linkedin,twitter,youtube \
  --tone-config config/tone_of_voice.yaml \
  --output-dir output

# Output: output/20260828_101503_pipeline_result.md
```

### Module 2: Radar (One-off)
```bash
python scripts/module2_radar.py \
  --feeds config/feeds.yaml \
  --tone-config config/tone_of_voice.yaml \
  --webhook-url $SLACK_WEBHOOK_URL \
  --state-dir state
```

### Module 2: Radar (Scheduled via Cronjob)
```bash
# In Hermes chat:
cronjob action=create \
  schedule="0 9-21/4 * * *" \
  prompt="Load content-strategist-viral-scriptwriter skill and run Module 2 Radar for niche 'AI automation for content creators' with webhook $SLACK_WEBHOOK_URL" \
  skills=["content-strategist-viral-scriptwriter"] \
  name="content-radar-4h" \
  deliver="origin"
```

### Test Webhook
```bash
# Slack
python scripts/test_webhook.py --url $SLACK_WEBHOOK_URL --sample

# Telegram
python scripts/test_webhook.py --telegram --token $TELEGRAM_BOT_TOKEN --chat $TELEGRAM_CHAT_ID --sample
```

### Automated Client Deployment
```bash
# Interactive mode (recommended for new clients)
python scripts/deploy_client.py --interactive

# From CLI args
python scripts/deploy_client.py --client-name "Acme Corp" --niche "B2B SaaS marketing" --webhook-url $SLACK_WEBHOOK_URL

# From config file
python scripts/deploy_client.py --config-file client_config.json

# Skip certain steps
python scripts/deploy_client.py --interactive --no-validate-keys --no-cron
```

The deploy script will:
1. Create client config directory with `tone_of_voice.yaml`, `feeds.yaml`, `.env.template`
2. Validate API keys (YouTube, Twitter, Slack/Telegram)
3. Register Hermes cronjob for Module 2
4. Send test webhook to verify delivery
5. Generate client-specific README with next steps

---

## Project Structure

```
content-strategist-viral-scriptwriter/
├── SKILL.md                    # Main skill definition
├── requirements.txt            # Python dependencies
├── config/
│   ├── tone_of_voice.yaml      # Brand voice configuration
│   └── feeds.yaml              # Feed sources for radar
├── templates/
│   ├── tone_of_voice.yaml      # Starter tone profiles
│   ├── feeds.yaml              # Example feed configs
│   ├── pipeline_output.md      # Example Module 1 output
│   └── radar_card.md           # Example Module 2 approval card
├── references/
│   ├── copywriting-frameworks.md   # AIDA, PAS, HVC, StoryBrand
│   ├── hook-taxonomy.md            # 25 hook templates by type
│   ├── platform-specs.md           # Platform specs & limits
│   └── webhook-schemas.md          # Slack/Telegram payload schemas
├── scripts/
│   ├── module1_pipeline.py       # Module 1 CLI entry
│   ├── module2_radar.py          # Module 2 CLI entry
│   ├── deploy_client.py          # Automated client onboarding
│   ├── validate_tone.py          # Tone config validator
│   ├── test_webhook.py           # Webhook test utility
│   └── utils/
│       ├── __init__.py
│       ├── feeds.py              # RSS/YouTube/Twitter/Trends fetchers
│       ├── scoring.py            # Relevance scoring & dedupe
│       ├── formatting.py         # Platform caption formatters
│       └── llm_delegation.py     # LLM delegation builders + schemas
└── state/                        # Runtime state (auto-created)
    ├── last_run.json
    ├── candidates_*.json
    └── shortlist_*.json
```

---

## Configuration Details

### Tone of Voice (`config/tone_of_voice.yaml`)

Defines the agent's personality and output style:

```yaml
tone_id: "b2b_corporate"
display_name: "B2B Corporativo"
language: "pt-BR"
persona:
  archetype: "Expert Mentor"
  traits: ["authoritative", "data-driven", "actionable", "concise"]
  forbidden_words: ["vibes", "game-changer", "unlock", "skyrocket", "masterclass"]
  preferred_phrases: ["In practice,", "The data shows", "Key takeaway:"]
structure_preferences:
  hook_style: "contrarian_insight"
  cta_style: "question_driven"
  emoji_usage: "minimal"
  line_break_density: "high"
platform_overrides:
  linkedin:
    emoji_usage: "minimal"
  instagram:
    emoji_usage: "moderate"
```

### Feeds (`config/feeds.yaml`)

Defines what the radar monitors:

```yaml
niche: "AI automation for content creators"
keywords: ["AI content", "automation workflow", "creator economy", "viral video"]
rss_feeds:
  - name: "The Verge AI"
    url: "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"
    category: "tech_news"
youtube_channels:
  - channel_id: "UC_x5XG1OV2P6uZZ5FSM9Ttw"
    name: "Creator Education"
    keywords: ["scriptwriting", "viral", "retention"]
twitter_lists:
  - list_id: "1234567890123456789"
    name: "Top AI Creators"
google_trends_regions: ["BR", "US"]
scan_window_hours: 24
materiality_threshold: 0.7
primary_platform: "linkedin"
webhook_url_env: "SLACK_WEBHOOK_URL"
```

---

## Module 1 Output Format

The pipeline produces a Markdown file with:

1. **Cleaned Transcript Segments** — Thesis, arguments, data points, soundbites, pain points
2. **Framework Map** — Which copywriting framework per platform
3. **5 Hooks** — One per psychological type (Curiosity, Contrarian, Pain Point, Social Proof, Bold Statement)
4. **Script + Edit Guide** — Table with Time | Voiceover | B-Roll | Text Overlay | SFX
5. **4 Platform Captions** — Instagram/TikTok, LinkedIn, Twitter Thread, YouTube Description
6. **Quality Checklist** — Auto-verified

---

## Module 2 Output Format

Each radar cycle delivers approval cards to Slack/Telegram:

**Slack (Block Kit):**
- Header: Trend title
- Section: Source, executive summary, draft post
- Actions: [✅ Aprovar] [✏️ Pedir Alteração] [🗑️ Descartar]
- Context: Item ID, score, angle

**Telegram (Inline Keyboard):**
- Formatted message with Markdown
- 3-button inline keyboard with callback_data

Buttons trigger your webhook handler for approve/edit/discard workflows.

---

## Environment Variables

| Variable | Required For | Description |
|----------|--------------|-------------|
| `YOUTUBE_API_KEY` | Module 2 | YouTube Data API v3 key |
| `TWITTER_BEARER_TOKEN` | Module 2 | Twitter API v2 Bearer token |
| `SLACK_WEBHOOK_URL` | Module 2 | Slack incoming webhook URL |
| `TELEGRAM_BOT_TOKEN` | Module 2 | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Module 2 | Target chat/channel ID |

---

## Extending the Agent

### Add Custom Hook Templates
Edit `references/hook-taxonomy.md` and update `scripts/utils/formatting.py`

### Add New Platforms
1. Add formatter in `scripts/utils/formatting.py`
2. Register in `FORMATTERS` dict
3. Add platform specs in `references/platform-specs.md`
4. Add platform override support in `templates/tone_of_voice.yaml`

### Custom Scoring Weights
Modify `scripts/utils/scoring.py` `compute_relevance()` weights

### Custom Publish Workflow
Implement webhook handler for Slack `actions` / Telegram `callback_query`:
- `approve_*` → Publish via platform API or trigger Module 1
- `edit_*` → Open modal, capture edit, re-render card
- `discard_*` → Log, archive

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Tone validation fails | Check `config/tone_of_voice.yaml` against schema |
| No trends found | Lower `materiality_threshold`, add more feeds/keywords |
| Webhook 403/404 | Verify webhook URL, check Slack/Telegram bot permissions |
| YouTube quota exceeded | Reduce `max_items_per_source`, add caching |
| Cronjob not firing | Check `cronjob action=list`, verify schedule syntax |

---

## Related Skills

- `la-vague-radar-curator` — Cultural trend hunting for editorial magazine
- `movie_scriptwriting` — Hollywood screenplay format
- `humanizer` — Strip AI-isms from generated copy
- `competitor-news-monitor` — Company-specific material event tracking
- `blogwatcher` — RSS/Atom feed ingestion
- `cronjob` — Scheduling recurring runs

---

## License

MIT.