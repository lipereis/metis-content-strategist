# Metis — The Content Strategist & Viral Scriptwriter Agent — Distribution Package

**Version 1.0** | Zero-cost infrastructure, paid usage model

---

## 📦 What's Included

```
metis-content-strategist-v1.0/
├── QUICKSTART.md              # 10-min setup guide
├── LICENSE_GIST_TEMPLATE.json # License server template
├── install.sh / install.bat   # One-click installer
├── Dockerfile                 # Container deployment
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── scripts/
│   ├── license.py             # Zero-cost license validator (GitHub Gist)
│   ├── review_local.py        # Interactive CLI review sandbox
│   ├── module1_pipeline.py    # Transcript → 7 platforms
│   ├── module2_radar.py       # Trend radar + approval cards
│   ├── deploy_client.py       # Automated client onboarding
│   ├── validate_tone.py       # Tone config validator
│   ├── test_webhook.py        # Webhook tester
│   ├── stripe_webhook_handler.py # Stripe → GitHub Gist sync
│   └── utils/                 # Shared formatters, scorers, fetchers
├── templates/
│   ├── tone_of_voice.yaml     # 4 brand voice presets
│   └── feeds.yaml             # Example feed configs for 3 niches
├── references/                # Copywriting cheat sheets
├── .github/workflows/
│   ├── test.yml               # CI/CD pipeline
│   └── license-sync.yml       # Stripe → Gist automation
└── .github/workflows/license-sync.yml
```

---

## 🚀 Quick Start for Customers

```bash
# 1. Unzip & install
unzip metis-content-strategist-v1.0.zip && cd metis-content-strategist
./install.sh          # Linux/macOS
# or install.bat      # Windows

# 2. Configure
cp templates/tone_of_voice.yaml config/
cp templates/feeds.yaml config/
# Edit config/tone_of_voice.yaml with brand voice
# Edit config/feeds.yaml with niche keywords

# 3. Add license key
export METIS_LICENSE="YOUR_KEY"
# Windows: $env:METIS_LICENSE="YOUR_KEY"

# 4. Run Module 1 — Transcript → 7 platforms
python scripts/module1_pipeline.py \
  --input transcripts/meeting.txt \
  --platforms instagram,linkedin,twitter,youtube,tiktok_enhanced,threads,newsletter

# 5. Review & approve locally (no webhooks!)
python scripts/review_local.py --state-dir state --approved-dir state/approved

# 6. Export for schedulers
# Menu option 4 → 1 (JSON for Notion/Buffer) or 4 → 2 (Markdown for Hootsuite)
```

---

## 🔐 License System (Zero-Cost)

**How it works:**
1. You create a **secret GitHub Gist** with license database (template: `LICENSE_GIST_TEMPLATE.json`)
2. Customer sets `METIS_LICENSE` env var
3. Script validates against Gist (24h local cache, zero server cost)
3. You update Gist to add/revoke keys instantly

**Gist Structure:**
```json
{
  "licenses": {
    "METIS-PRO-CLIENT-001": {"email": "client@co.com", "plan": "pro", "expires": "2025-12-31", "max_runs": 1000}
  },
  "revoked": []
}
```

---

## 💰 Pricing Tiers (Suggested)

| Tier | Price | Max Runs | Best For |
|------|-------|----------|----------|
| **Pro** | $97/mo or $997/yr | 1,000/mo | Solo creators, small teams |
| **Agency** | $297/mo or $2,997/yr | Unlimited | Marketing agencies |
| **Enterprise** | Custom | Unlimited | Large orgs, custom models |

**Payment**: Stripe Payment Links (2.9% + 30¢), PayPal.me, Wise, or bank transfer — no monthly platform fees.

---

## 🤝 Sales Assets Included

| Asset | File | Purpose |
|-------|------|---------|
| **Quick Start Guide** | `QUICKSTART.md` | Customer onboarding |
| **License Template** | `LICENSE_GIST_TEMPLATE.json` | Copy-paste to Gist |
| **Installer** | `install.sh` / `install.bat` | One-click setup |
| **Dockerfile** | `Dockerfile` | Container deployment |
| **Demo Transcript** | `sample_transcript.txt` | Test input |

---

## 🔧 Technical Specs

| Component | Tech |
|-----------|------|
| **Core** | Python 3.10+ |
| **License** | JWT-style via GitHub Gist (zero server) |
| **APIs** | YouTube Data v3, Twitter API v2, RSS/Atom |
| **Webhooks** | Slack Block Kit, Telegram Bot API |
| **Export** | JSON (Notion/Buffer API) + Markdown (Hootsuite) |
| **CI/CD** | GitHub Actions (test, license sync) |

---

## 📋 Deployment Options

| Method | Command | Best For |
|---------|---------|----------|
| **Local CLI** | `python scripts/review_local.py` | Solo creators, agencies |
| **Docker** | `docker run -v ./data:/app/data -e KEY metis-content-strategist` | Servers, CI/CD |
| **Hermes Agent** | `hermes skills install metis-content-strategist` | Hermes users |
| **Scheduled** | `cronjob action=create schedule="0 9-21/4 * * *"` | Automated radar |

---

## 📞 Support & Updates

- **Issues**: GitHub Issues (private repo access granted on purchase)
- **Updates**: Download new release from GitHub Releases
- **License**: Validates automatically on each run
- **Customization**: Edit `templates/tone_of_voice.yaml` for brand voice

---

## 📄 License

**Commercial License** — Purchaser may:
- ✅ Use internally for unlimited projects
- ✅ Use for client work (agency tier)
- ✅ Modify source code for internal use
- ❌ Resell or redistribute source code
- ❌ Remove license validation

---

**Built for B2B creators who value speed, quality, and ownership.** 🚀

*Metis — The Content Strategist & Viral Scriptwriter Agent v1.0 — Zero infrastructure, pure profit.*