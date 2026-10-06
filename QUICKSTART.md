# Metis — The Content Strategist & Viral Scriptwriter Agent

Quick start guide for the Metis Content Strategist Agent.

---

## 1️⃣ Install (2 minutes)

```bash
# 1. Unzip the package
unzip content-strategist-v1.0.zip
cd content-strategist

# 2. Run installer (creates venv + installs deps)
./install.sh

# 3. Activate environment
source .venv/bin/activate  # Windows: .venv\Scripts\activate

```

> **Tip**: Add the export to your `.bashrc` / `.zshrc` / PowerShell profile so it persists.

---

## 2️⃣ Configure Your Brand Voice (3 minutes)

```bash
# Copy templates to config
cp templates/tone_of_voice.yaml config/tone_of_voice.yaml
cp templates/feeds.yaml config/feeds.yaml

# Edit tone_of_voice.yaml with your brand personality
# Edit feeds.yaml with your niche keywords & RSS sources
```

### Tone Presets Included:
| Preset | Best For |
|--------|----------|
| `b2b_corporate` | LinkedIn, professional services, SaaS |
| `provocative_analyst` | Twitter, thought leadership, contrarian takes |
| `friendly_peer` | Instagram/TikTok, creator-to-creator |
| `formal_academic` | Whitepapers, research, technical content |

**Customize**: Edit `forbidden_words`, `preferred_phrases`, `emoji_usage` to match your voice.

---

## 3️⃣ Run Module 1 — Transcript → 7 Platforms (2 minutes)

```bash
# Put your transcript in a text file
# Format: raw transcript or structured with markers:
# Tese: your main thesis
# Argumento: supporting point
# Dado: data point
# Frase: quotable soundbite
# Dor: audience pain point

# Run pipeline
python scripts/module1_pipeline.py \
  --input transcripts/my_meeting.txt \
  --tone b2b_corporate \
  --platforms instagram,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter \
  --tone-config config/tone_of_voice.yaml \
  --output-dir output
```

**Output**: `output/TIMESTAMP_pipeline_result.md` with:
- ✅ 5 psychological hooks (curiosity, contrarian, pain, proof, bold)
- ✅ Video script + B-roll table (time, voiceover, visual, overlay, SFX)
- ✅ 7 platform captions (IG, LinkedIn, Twitter thread, YouTube, TikTok Enhanced, Threads, Newsletter)

---

## 4️⃣ Run Module 2 — Trend Radar (set & forget)

```bash
# Configure feeds.yaml with your niche
# Add API keys to .env:
# YOUTUBE_API_KEY=xxx
# TWITTER_BEARER_TOKEN=xxx

# One-off run
python scripts/module2_radar.py \
  --feeds config/feeds.yaml \
  --tone-config config/tone_of_voice.yaml \
  --webhook-url $SLACK_WEBHOOK_URL \
  --state-dir state
```

**Output**: Approval cards in Slack/Telegram with ✅ Approve / ✏️ Edit / 🗑️ Discard buttons.

**Or run locally** (no webhooks needed):
```bash
python scripts/review_local.py --state-dir state --approved-dir state/approved
```

---

## 5️⃣ Review & Approve (1 minute)

```bash
python scripts/review_local.py --state-dir state --approved-dir state/approved
```

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| `1` / `2` | Browse Module 1 / Module 2 |
| `↑/↓` | Navigate items |
| `Enter` | View details |
| `e` | Edit inline |
| `a` | Approve → `state/approved/` |
| `d` | Discard |
| `4` → `1` | Export all as JSON |
| `4` → `2` | Export all as Markdown |

---

## 6️⃣ Export & Schedule (1 minute)

```bash
# From review_local.py menu: 4 → 1
# Creates: export_all_TIMESTAMP.json

# Or export Markdown for Hootsuite/Buffer:
# 4 → 2 → creates export_md_TIMESTAMP/ folder
```

**Import into your scheduler:**
- **Notion**: Import JSON → database
- **Buffer/Hootsuite**: Upload Markdown files
- **Later/Planoly**: Copy-paste from Markdown

---

## 📁 Project Structure

```
content-strategist/
├── config/                 # Your configs (gitignored)
│   ├── tone_of_voice.yaml
│   └── feeds.yaml
├── templates/              # Starter templates
├── references/             # Cheat sheets
├── scripts/
│   ├── module1_pipeline.py     # Transcript → 7 platforms
│   ├── module2_radar.py        # Trend radar + approval cards
│   ├── review_local.py         # Local CLI review sandbox
│   ├── deploy_client.py        # Automated client onboarding
│   ├── validate_tone.py        # Tone config validator
│   ├── test_webhook.py         # Webhook tester
│   └── utils/                  # Shared formatters, scorers, feed fetchers
├── state/                    # Runtime state (auto-created)
│   ├── *_pipeline_result.md
│   ├── shortlist_*.json
│   └── approved/             # Approved content
├── output/                   # Module 1 outputs
├── templates/                # Starter configs
└── requirements.txt
```

---

## 🔧 Environment Variables

Create `.env` file:
```bash
# Required for Module 2
YOUTUBE_API_KEY=your_youtube_data_api_v3_key
TWITTER_BEARER_TOKEN=your_twitter_api_v2_bearer_token

# Webhooks (choose one)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
TELEGRAM_BOT_TOKEN=123456:abc...
TELEGRAM_CHAT_ID=-1001234567890

```

---

## 🆘 Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError` | `pip install -r requirements.txt` |
| Tone validation fails | Check `config/tone_of_voice.yaml` syntax |
| No trends found | Lower `materiality_threshold` in `feeds.yaml`, add more RSS feeds |
| Webhook 403/404 | Verify webhook URL, check Slack/Telegram bot permissions |
| YouTube quota exceeded | Reduce `max_items_per_source`, add caching |
*Content Strategist Agent v1.0 — Built for B2B creators who value speed & quality.*