#!/usr/bin/env python3
"""
Client Deployment Script for Content Strategist & Viral Scriptwriter Agent.

Automates client onboarding:
- Creates client config from templates
- Prompts for niche, keywords, tone preference
- Validates API keys (YouTube, Twitter, Slack/Telegram)
- Registers Hermes cronjob for Module 2
- Sends test webhook to verify delivery

Usage:
    python deploy_client.py --client-name "Acme Corp" --niche "B2B SaaS marketing"
    python deploy_client.py --interactive
    python deploy_client.py --config-file client_config.json
"""

import argparse
import json
import os
import re
import shutil
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml
import httpx
from pydantic import BaseModel, ValidationError, field_validator


# --- Configuration Models ---

class ClientConfig(BaseModel):
    """Client deployment configuration."""
    client_name: str
    client_slug: str
    niche: str
    description: str = ""
    keywords: list[str] = []
    tone_id: str = "b2b_corporate"
    tone_customizations: dict = {}
    feeds: dict = {}
    webhook: dict = {}
    cron: dict = {}
    created_at: str = ""
    
    @field_validator("client_slug", mode="before")
    @classmethod
    def generate_slug(cls, v: str, info) -> str:
        if v:
            return v
        # Generate from client_name
        name = info.data.get("client_name", "client")
        return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


class ToneCustomization(BaseModel):
    """Tone profile customization."""
    display_name: Optional[str] = None
    archetype: Optional[str] = None
    traits: Optional[list[str]] = None
    forbidden_words: Optional[list[str]] = None
    preferred_phrases: Optional[list[str]] = None
    hook_style: Optional[str] = None
    cta_style: Optional[str] = None
    emoji_usage: Optional[str] = None
    line_break_density: Optional[str] = None
    platform_overrides: Optional[dict] = None


# --- Default Templates ---

DEFAULT_KEYWORDS_BY_NICHE = {
    "ai_automation": [
        "AI content", "automation workflow", "creator economy", "viral video",
        "scriptwriting AI", "content marketing AI", "video editing AI"
    ],
    "b2b_saas": [
        "B2B SaaS", "product-led growth", "SaaS metrics", "customer acquisition",
        "churn reduction", "PLG", "SaaS marketing", "B2B content"
    ],
    "creator_economy": [
        "creator economy", "monetization", "audience building", "content strategy",
        "influencer marketing", "creator tools", "passive income"
    ],
    "video_marketing": [
        "video marketing", "short-form video", "Reels strategy", "TikTok marketing",
        "YouTube growth", "video retention", "viral hooks"
    ],
    "content_ai": [
        "AI writing", "content automation", "AI copywriting", "generative AI",
        "prompt engineering", "AI content tools", "LLM applications"
    ]
}

DEFAULT_RSS_FEEDS = {
    "ai_automation": [
        {"name": "The Verge AI", "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml", "category": "tech_news"},
        {"name": "TechCrunch AI", "url": "https://techcrunch.com/tag/artificial-intelligence/feed/", "category": "tech_news"},
        {"name": "Creator Economy Newsletter", "url": "https://creatoreconomy.so/rss/", "category": "creator_business"},
        {"name": "Marketing AI Institute", "url": "https://www.marketingaiinstitute.com/blog/rss.xml", "category": "marketing_tech"},
        {"name": "The Information AI", "url": "https://www.theinformation.com/feed/tag/artificial-intelligence", "category": "tech_business"},
        {"name": "a16z Consumer", "url": "https://a16z.com/consumer/feed/", "category": "vc_perspective"}
    ],
    "b2b_saas": [
        {"name": "SaaStr", "url": "https://www.saastr.com/feed/", "category": "saas_business"},
        {"name": "Lenny's Newsletter", "url": "https://www.lennysnewsletter.com/feed", "category": "product_growth"},
        {"name": "FirstRound Review", "url": "https://review.firstround.com/rss", "category": "startup_advice"},
        {"name": "Harvard Business Review", "url": "https://hbr.org/feed", "category": "business_strategy"},
        {"name": "TechCrunch SaaS", "url": "https://techcrunch.com/tag/saas/feed/", "category": "tech_news"}
    ],
    "creator_economy": [
        {"name": "Creator Economy Newsletter", "url": "https://creatoreconomy.so/rss/", "category": "creator_business"},
        {"name": "The Business of Creators", "url": "https://thebusinessofcreators.com/feed/", "category": "creator_business"},
        {"name": "Linktree Blog", "url": "https://linktr.ee/blog/rss/", "category": "creator_tools"},
        {"name": "Patreon Blog", "url": "https://blog.patreon.com/rss/", "category": "creator_platform"},
        {"name": "Substack Blog", "url": "https://blog.substack.com/feed/", "category": "newsletter_platform"}
    ]
}

DEFAULT_YOUTUBE_CHANNELS = {
    "ai_automation": [
        {"channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "name": "Creator Education", "keywords": ["scriptwriting", "viral", "retention", "algorithm"]},
        {"channel_id": "UCJowOS1R0FnhipXVqEnYU1A", "name": "AI Tools Review", "keywords": ["AI tools", "automation", "content creation"]},
        {"channel_id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Marketing Strategy", "keywords": ["content strategy", "growth", "monetization"]}
    ],
    "b2b_saas": [
        {"channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "name": "SaaS Growth", "keywords": ["SaaS", "growth", "metrics", "PLG"]},
        {"channel_id": "UCJowOS1R0FnhipXVqEnYU1A", "name": "B2B Marketing", "keywords": ["B2B", "lead generation", "content marketing"]}
    ],
    "creator_economy": [
        {"channel_id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "name": "Creator Business", "keywords": ["monetization", "audience", "creator economy"]},
        {"channel_id": "UCJowOS1R0FnhipXVqEnYU1A", "name": "Content Strategy", "keywords": ["content strategy", "viral", "growth"]}
    ]
}

DEFAULT_TWITTER_LISTS = {
    "ai_automation": [
        {"list_id": "1234567890123456789", "name": "Top AI Creators", "description": "Curated AI-focused content creators"},
        {"list_id": "9876543210987654321", "name": "Creator Economy Leaders", "description": "Founders and operators in creator economy"}
    ],
    "b2b_saas": [
        {"list_id": "1234567890123456789", "name": "SaaS Founders", "description": "B2B SaaS founders and executives"},
        {"list_id": "9876543210987654321", "name": "Product Leaders", "description": "Product managers and growth leaders"}
    ],
    "creator_economy": [
        {"list_id": "1234567890123456789", "name": "Top Creators", "description": "Leading content creators across platforms"},
        {"list_id": "9876543210987654321", "name": "Creator Tools", "description": "Founders building creator tools"}
    ]
}

TONE_PRESETS = {
    "b2b_corporate": {
        "display_name": "B2B Corporativo",
        "archetype": "Expert Mentor",
        "traits": ["authoritative", "data-driven", "actionable", "concise"],
        "forbidden_words": ["vibes", "game-changer", "unlock", "skyrocket", "masterclass", "hack", "secret", "insane", "crazy"],
        "preferred_phrases": ["In practice,", "The data shows", "Key takeaway:", "Action item:", "Bottom line:", "Pro tip:"],
        "hook_style": "contrarian_insight",
        "cta_style": "question_driven",
        "emoji_usage": "minimal",
        "line_break_density": "high"
    },
    "provocative_analyst": {
        "display_name": "Analista Provocativo",
        "archetype": "Contrarian Truth-Teller",
        "traits": ["sharp", "evidence-based", "unfiltered", "intellectually honest"],
        "forbidden_words": ["amazing", "incredible", "fantastic", "best", "top", "ultimate", "complete guide"],
        "preferred_phrases": ["Here's the uncomfortable truth:", "The data contradicts:", "Everyone gets this wrong:", "Reality check:"],
        "hook_style": "contrarian",
        "cta_style": "challenge",
        "emoji_usage": "none",
        "line_break_density": "medium"
    },
    "friendly_peer": {
        "display_name": "Parceiro Criador",
        "archetype": "Experienced Peer",
        "traits": ["relatable", "encouraging", "practical", "transparent"],
        "forbidden_words": ["guaranteed", "proven", "expert", "guru", "master", "dominate", "crush it"],
        "preferred_phrases": ["I learned the hard way:", "What worked for me:", "Here's what actually happened:", "Real talk:"],
        "hook_style": "pain_point",
        "cta_style": "question_driven",
        "emoji_usage": "moderate",
        "line_break_density": "high"
    },
    "formal_academic": {
        "display_name": "Formal Acadêmico",
        "archetype": "Research Authority",
        "traits": ["rigorous", "cited", "nuanced", "objective"],
        "forbidden_words": ["hack", "trick", "shortcut", "easy", "simple", "viral", "explode", "blow up"],
        "preferred_phrases": ["Research indicates:", "Evidence suggests:", "Studies demonstrate:", "The literature shows:"],
        "hook_style": "curiosity",
        "cta_style": "resource_link",
        "emoji_usage": "none",
        "line_break_density": "low"
    }
}


# --- Deployment Class ---

class ClientDeployer:
    def __init__(self, skill_root: Path):
        self.skill_root = skill_root
        self.templates_dir = skill_root / "templates"
        self.scripts_dir = skill_root / "scripts"
        self.config_dir = skill_root / "config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def slugify(self, text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    
    def prompt_with_default(self, prompt: str, default: str = "") -> str:
        if default:
            user_input = input(f"{prompt} [{default}]: ").strip()
            return user_input if user_input else default
        else:
            while True:
                user_input = input(f"{prompt}: ").strip()
                if user_input:
                    return user_input
                print("  This field is required.")
    
    def prompt_yes_no(self, prompt: str, default: bool = True) -> bool:
        default_str = "Y/n" if default else "y/N"
        user_input = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not user_input:
            return default
        return user_input in ("y", "yes", "sim", "s")
    
    def prompt_choice(self, prompt: str, choices: list[str], default: str = "") -> str:
        print(f"{prompt}")
        for i, choice in enumerate(choices, 1):
            marker = " (default)" if choice == default else ""
            print(f"  {i}. {choice}{marker}")
        while True:
            user_input = input(f"Choice [1-{len(choices)}]: ").strip()
            if not user_input and default:
                return default
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(choices):
                    return choices[idx]
            except ValueError:
                pass
            print(f"  Please enter a number between 1 and {len(choices)}.")
    
    def prompt_list(self, prompt: str, default: list[str] = None) -> list[str]:
        if default:
            print(f"{prompt} (comma-separated) [{', '.join(default)}]: ")
        else:
            print(f"{prompt} (comma-separated): ")
        user_input = input("> ").strip()
        if not user_input and default:
            return default
        return [item.strip() for item in user_input.split(",") if item.strip()]
    
    def collect_client_info_interactive(self) -> ClientConfig:
        """Interactive client information collection."""
        print("\n" + "="*60)
        print("  CONTENT STRATEGIST AGENT — CLIENT DEPLOYMENT")
        print("="*60 + "\n")
        
        # Basic info
        print("📋 BASIC INFORMATION")
        client_name = self.prompt_with_default("Client name", "Acme Corp")
        client_slug = self.prompt_with_default("Client slug (for directories)", self.slugify(client_name))
        niche = self.prompt_with_default("Niche/industry (e.g., 'AI automation for creators')", "AI automation for content creators")
        description = self.prompt_with_default("Brief description", "")
        
        # Keywords
        print("\n🔑 KEYWORDS")
        print("Select a preset or enter custom keywords:")
        niche_presets = list(DEFAULT_KEYWORDS_BY_NICHE.keys()) + ["custom"]
        preset_choice = self.prompt_choice("Keyword preset", niche_presets, "ai_automation")
        
        if preset_choice != "custom":
            keywords = DEFAULT_KEYWORDS_BY_NICHE[preset_choice].copy()
            print(f"  Using preset '{preset_choice}': {', '.join(keywords)}")
            if self.prompt_yes_no("Add/modify keywords?", False):
                extra = self.prompt_list("Additional keywords")
                keywords.extend(extra)
        else:
            keywords = self.prompt_list("Keywords (comma-separated)", DEFAULT_KEYWORDS_BY_NICHE["ai_automation"])
        
        # Tone
        print("\n🎭 TONE OF VOICE")
        tone_choices = list(TONE_PRESETS.keys())
        tone_id = self.prompt_choice("Select tone preset", tone_choices, "b2b_corporate")
        tone_preset = TONE_PRESETS[tone_id].copy()
        
        tone_customizations = {}
        if self.prompt_yes_no(f"Customize '{tone_preset['display_name']}' tone?", False):
            tone_customizations["display_name"] = self.prompt_with_default("Display name", tone_preset["display_name"])
            tone_customizations["archetype"] = self.prompt_with_default("Archetype", tone_preset["archetype"])
            tone_customizations["traits"] = self.prompt_list("Traits (comma-separated)", tone_preset["traits"])
            tone_customizations["forbidden_words"] = self.prompt_list("Forbidden words", tone_preset["forbidden_words"])
            tone_customizations["preferred_phrases"] = self.prompt_list("Preferred phrases", tone_preset["preferred_phrases"])
            tone_customizations["hook_style"] = self.prompt_with_default("Hook style", tone_preset["hook_style"])
            tone_customizations["cta_style"] = self.prompt_with_default("CTA style", tone_preset["cta_style"])
            tone_customizations["emoji_usage"] = self.prompt_with_default("Emoji usage", tone_preset["emoji_usage"])
            tone_customizations["line_break_density"] = self.prompt_with_default("Line break density", tone_preset["line_break_density"])
        
        # Feeds
        print("\n📡 FEED SOURCES")
        feed_preset = self.prompt_choice("Feed preset", list(DEFAULT_RSS_FEEDS.keys()) + ["custom"], "ai_automation")
        
        if feed_preset != "custom":
            rss_feeds = DEFAULT_RSS_FEEDS[feed_preset]
            youtube_channels = DEFAULT_YOUTUBE_CHANNELS.get(feed_preset, [])
            twitter_lists = DEFAULT_TWITTER_LISTS.get(feed_preset, [])
            print(f"  Using preset '{feed_preset}': {len(rss_feeds)} RSS, {len(youtube_channels)} YouTube, {len(twitter_lists)} Twitter lists")
        else:
            rss_feeds = []
            print("  Enter RSS feeds (empty name to stop):")
            while True:
                name = self.prompt_with_default("  Feed name", "")
                if not name:
                    break
                url = self.prompt_with_default("  Feed URL", "")
                category = self.prompt_with_default("  Category", "general")
                rss_feeds.append({"name": name, "url": url, "category": category})
            
            youtube_channels = []
            print("  Enter YouTube channels (empty ID to stop):")
            while True:
                channel_id = self.prompt_with_default("  Channel ID", "")
                if not channel_id:
                    break
                name = self.prompt_with_default("  Channel name", "")
                keywords = self.prompt_list("  Keywords")
                youtube_channels.append({"channel_id": channel_id, "name": name, "keywords": keywords})
            
            twitter_lists = []
            print("  Enter Twitter lists (empty ID to stop):")
            while True:
                list_id = self.prompt_with_default("  List ID", "")
                if not list_id:
                    break
                name = self.prompt_with_default("  List name", "")
                description = self.prompt_with_default("  Description", "")
                twitter_lists.append({"list_id": list_id, "name": name, "description": description})
        
        google_trends_regions = self.prompt_list("Google Trends regions", ["BR", "US", "PT"])
        scan_window_hours = int(self.prompt_with_default("Scan window (hours)", "24"))
        max_items_per_source = int(self.prompt_with_default("Max items per source", "10"))
        materiality_threshold = float(self.prompt_with_default("Materiality threshold (0-1)", "0.7"))
        primary_platform = self.prompt_choice("Primary platform", ["linkedin", "instagram", "twitter", "youtube"], "linkedin")
        
        # Webhook
        print("\n🔗 WEBHOOK CONFIGURATION")
        webhook_type = self.prompt_choice("Webhook type", ["slack", "telegram"], "slack")
        
        webhook = {"type": webhook_type}
        if webhook_type == "slack":
            webhook["url"] = self.prompt_with_default("Slack webhook URL", "")
            webhook["env_var"] = "SLACK_WEBHOOK_URL"
        else:
            webhook["bot_token"] = self.prompt_with_default("Telegram bot token", "")
            webhook["chat_id"] = self.prompt_with_default("Telegram chat ID", "")
            webhook["env_var_bot"] = "TELEGRAM_BOT_TOKEN"
            webhook["env_var_chat"] = "TELEGRAM_CHAT_ID"
        
        # Cron
        print("\n⏰ CRONJOB SCHEDULE")
        cron_preset = self.prompt_choice("Schedule preset", [
            "every_4h_business", "every_6h", "daily_9am", "twice_daily", "custom"
        ], "every_4h_business")
        
        cron_schedules = {
            "every_4h_business": "0 9-21/4 * * *",
            "every_6h": "0 */6 * * *",
            "daily_9am": "0 9 * * *",
            "twice_daily": "0 9,21 * * *"
        }
        
        if cron_preset == "custom":
            cron_schedule = self.prompt_with_default("Cron expression", "0 9-21/4 * * *")
        else:
            cron_schedule = cron_schedules[cron_preset]
        
        cron_name = self.prompt_with_default("Cronjob name", f"content-radar-{client_slug}")
        
        # Build config
        config = ClientConfig(
            client_name=client_name,
            client_slug=client_slug,
            niche=niche,
            description=description,
            keywords=keywords,
            tone_id=tone_id,
            tone_customizations=tone_customizations,
            feeds={
                "rss_feeds": rss_feeds,
                "youtube_channels": youtube_channels,
                "twitter_lists": twitter_lists,
                "google_trends_regions": google_trends_regions,
                "scan_window_hours": scan_window_hours,
                "max_items_per_source": max_items_per_source,
                "materiality_threshold": materiality_threshold,
                "primary_platform": primary_platform
            },
            webhook=webhook,
            cron={
                "schedule": cron_schedule,
                "name": cron_name
            },
            created_at=datetime.now().isoformat()
        )
        
        return config
    
    def load_config_from_file(self, filepath: Path) -> ClientConfig:
        """Load client config from JSON file."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ClientConfig(**data)
    
    def apply_tone_customizations(self, base_tone: dict, customizations: dict) -> dict:
        """Apply customizations to base tone preset."""
        result = base_tone.copy()
        for key, value in customizations.items():
            if value is not None:
                result[key] = value
        return result
    
    def generate_tone_yaml(self, config: ClientConfig) -> str:
        """Generate tone_of_voice.yaml content."""
        base_tone = TONE_PRESETS[config.tone_id].copy()
        customized = self.apply_tone_customizations(base_tone, config.tone_customizations)
        
        # Build platform overrides
        platform_overrides = {
            "linkedin": {
                "cta_style": "question_driven",
                "emoji_usage": "minimal",
                "hook_style": "contrarian_insight"
            },
            "instagram": {
                "emoji_usage": "moderate",
                "hook_style": "visual_curiosity",
                "line_break_density": "high"
            },
            "twitter": {
                "cta_style": "direct_command",
                "line_break_density": "medium",
                "hook_style": "bold_statement"
            },
            "youtube": {
                "hook_style": "bold_statement",
                "emoji_usage": "minimal"
            }
        }
        
        # Override primary platform
        primary = config.feeds.get("primary_platform", "linkedin")
        if primary in platform_overrides:
            platform_overrides[primary]["hook_style"] = customized.get("hook_style", "contrarian_insight")
        
        tone_yaml = {
            "tone_id": config.tone_id,
            "display_name": customized.get("display_name", base_tone["display_name"]),
            "language": "pt-BR",
            "persona": {
                "archetype": customized.get("archetype", base_tone["archetype"]),
                "traits": customized.get("traits", base_tone["traits"]),
                "forbidden_words": customized.get("forbidden_words", base_tone["forbidden_words"]),
                "preferred_phrases": customized.get("preferred_phrases", base_tone["preferred_phrases"])
            },
            "structure_preferences": {
                "hook_style": customized.get("hook_style", base_tone["hook_style"]),
                "cta_style": customized.get("cta_style", base_tone["cta_style"]),
                "emoji_usage": customized.get("emoji_usage", base_tone["emoji_usage"]),
                "line_break_density": customized.get("line_break_density", base_tone["line_break_density"])
            },
            "platform_overrides": platform_overrides
        }
        
        return yaml.dump(tone_yaml, allow_unicode=True, sort_keys=False)
    
    def generate_feeds_yaml(self, config: ClientConfig) -> str:
        """Generate feeds.yaml content."""
        feeds_yaml = {
            "niche": config.niche,
            "keywords": config.keywords,
            "rss_feeds": config.feeds.get("rss_feeds", []),
            "youtube_channels": config.feeds.get("youtube_channels", []),
            "twitter_lists": config.feeds.get("twitter_lists", []),
            "google_trends_regions": config.feeds.get("google_trends_regions", ["BR", "US"]),
            "scan_window_hours": config.feeds.get("scan_window_hours", 24),
            "max_items_per_source": config.feeds.get("max_items_per_source", 10),
            "materiality_threshold": config.feeds.get("materiality_threshold", 0.7),
            "primary_platform": config.feeds.get("primary_platform", "linkedin"),
            "webhook_url_env": config.webhook.get("env_var", "SLACK_WEBHOOK_URL")
        }
        
        return yaml.dump(feeds_yaml, allow_unicode=True, sort_keys=False)
    
    def write_config_files(self, config: ClientConfig) -> dict[str, Path]:
        """Write all config files for the client."""
        client_config_dir = self.config_dir / config.client_slug
        client_config_dir.mkdir(parents=True, exist_ok=True)
        
        files = {}
        
        # tone_of_voice.yaml
        tone_path = client_config_dir / "tone_of_voice.yaml"
        tone_path.write_text(self.generate_tone_yaml(config), encoding="utf-8")
        files["tone"] = tone_path
        
        # feeds.yaml
        feeds_path = client_config_dir / "feeds.yaml"
        feeds_path.write_text(self.generate_feeds_yaml(config), encoding="utf-8")
        files["feeds"] = feeds_path
        
        # client_config.json (for reference)
        config_path = client_config_dir / "client_config.json"
        config_data = config.model_dump()
        config_path.write_text(json.dumps(config_data, ensure_ascii=False, indent=2), encoding="utf-8")
        files["config"] = config_path
        
        # .env template
        env_path = client_config_dir / ".env.template"
        env_lines = [
            f"# {config.client_name} - Environment Variables",
            f"# Generated: {datetime.now().isoformat()}",
            "",
            "# Required for Module 2 (Radar)",
            "YOUTUBE_API_KEY=your_youtube_data_api_v3_key",
            "TWITTER_BEARER_TOKEN=your_twitter_api_v2_bearer_token",
            ""
        ]
        
        if config.webhook.get("type") == "slack":
            env_lines.append(f"SLACK_WEBHOOK_URL={config.webhook.get('url', 'your_slack_webhook_url')}")
        else:
            env_lines.append(f"TELEGRAM_BOT_TOKEN={config.webhook.get('bot_token', 'your_telegram_bot_token')}")
            env_lines.append(f"TELEGRAM_CHAT_ID={config.webhook.get('chat_id', 'your_telegram_chat_id')}")
        
        env_path.write_text("\n".join(env_lines), encoding="utf-8")
        files["env"] = env_path
        
        # README for client
        readme_path = client_config_dir / "README.md"
        readme_content = f"""# {config.client_name} — Content Strategist Agent Config

Generated: {config.created_at}
Client slug: `{config.client_slug}`

## Files

| File | Purpose |
|------|---------|
| `tone_of_voice.yaml` | Brand voice configuration |
| `feeds.yaml` | Trend monitoring feed sources |
| `.env.template` | Environment variables template (copy to `.env` and fill in) |
| `client_config.json` | Full deployment config (reference) |

## Quick Start

```bash
# 1. Copy env template and fill in your API keys
cp .env.template .env
# Edit .env with your actual keys

# 2. Validate tone config
python ../../scripts/validate_tone.py tone_of_voice.yaml

# 3. Test Module 1 (pipeline)
python ../../scripts/module1_pipeline.py --input transcript.txt --tone {config.tone_id} --platforms instagram,linkedin,twitter,youtube --tone-config tone_of_voice.yaml

# 4. Test Module 2 (radar) once
python ../../scripts/module2_radar.py --feeds feeds.yaml --tone-config tone_of_voice.yaml --webhook-url $SLACK_WEBHOOK_URL

# 5. In Hermes: Register cronjob
# cronjob action=create schedule="{config.cron['schedule']}" prompt="Load content-strategist-viral-scriptwriter and run Module 2 Radar for niche '{config.niche}' with webhook $SLACK_WEBHOOK_URL" skills=["content-strategist-viral-scriptwriter"] name="{config.cron['name']}"
```

## Configuration Summary

- **Niche**: {config.niche}
- **Keywords**: {', '.join(config.keywords[:10])}{'...' if len(config.keywords) > 10 else ''}
- **Tone**: {config.tone_id} ({TONE_PRESETS[config.tone_id]['display_name']})
- **Primary Platform**: {config.feeds.get('primary_platform', 'linkedin')}
- **Webhook**: {config.webhook.get('type', 'slack').upper()}
- **Cron Schedule**: {config.cron['schedule']}
- **Cron Name**: {config.cron['name']}

## Feed Sources

- RSS Feeds: {len(config.feeds.get('rss_feeds', []))}
- YouTube Channels: {len(config.feeds.get('youtube_channels', []))}
- Twitter Lists: {len(config.feeds.get('twitter_lists', []))}
- Google Trends Regions: {', '.join(config.feeds.get('google_trends_regions', []))}

## Next Steps

1. Fill in `.env` with real API keys
2. Test webhook delivery: `python ../../scripts/test_webhook.py --url $SLACK_WEBHOOK_URL --sample`
3. Register cronjob in Hermes
4. Run first radar cycle manually to verify
"""
        readme_path.write_text(readme_content, encoding="utf-8")
        files["readme"] = readme_path
        
        return files
    
    def validate_api_keys(self, config: ClientConfig) -> dict[str, bool]:
        """Validate API keys by making test requests."""
        results = {}
        
        # YouTube API
        youtube_key = os.getenv("YOUTUBE_API_KEY")
        if youtube_key:
            try:
                resp = httpx.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    params={"part": "id", "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "key": youtube_key},
                    timeout=10
                )
                results["youtube"] = resp.status_code == 200
            except Exception:
                results["youtube"] = False
        else:
            results["youtube"] = False
        
        # Twitter API
        twitter_token = os.getenv("TWITTER_BEARER_TOKEN")
        if twitter_token:
            try:
                resp = httpx.get(
                    "https://api.twitter.com/2/users/me",
                    headers={"Authorization": f"Bearer {twitter_token}"},
                    timeout=10
                )
                results["twitter"] = resp.status_code == 200
            except Exception:
                results["twitter"] = False
        else:
            results["twitter"] = False
        
        # Slack webhook
        if config.webhook.get("type") == "slack":
            slack_url = config.webhook.get("url") or os.getenv("SLACK_WEBHOOK_URL")
            if slack_url:
                try:
                    resp = httpx.post(slack_url, json={"text": "🧪 Test from Content Strategist Agent deploy"}, timeout=10)
                    results["slack"] = resp.status_code == 200
                except Exception:
                    results["slack"] = False
            else:
                results["slack"] = False
        else:
            results["slack"] = None  # Not applicable
        
        # Telegram
        if config.webhook.get("type") == "telegram":
            bot_token = config.webhook.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = config.webhook.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID")
            if bot_token and chat_id:
                try:
                    resp = httpx.post(
                        f"https://api.telegram.org/bot{bot_token}/sendMessage",
                        json={"chat_id": chat_id, "text": "🧪 Test from Content Strategist Agent deploy"},
                        timeout=10
                    )
                    results["telegram"] = resp.status_code == 200 and resp.json().get("ok")
                except Exception:
                    results["telegram"] = False
            else:
                results["telegram"] = False
        else:
            results["telegram"] = None  # Not applicable
        
        return results
    
    def register_cronjob(self, config: ClientConfig) -> bool:
        """Register cronjob via Hermes CLI."""
        try:
            # Escape prompt for shell
            prompt = (
                f"Load content-strategist-viral-scriptwriter and run Module 2 Radar "
                f"for niche '{config.niche}' with webhook $SLACK_WEBHOOK_URL"
            )
            
            cmd = [
                "hermes", "cronjob", "create",
                "--schedule", config.cron["schedule"],
                "--prompt", prompt,
                "--skills", "content-strategist-viral-scriptwriter",
                "--name", config.cron["name"],
                "--deliver", "origin"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ Cronjob registered: {config.cron['name']}")
                return True
            else:
                print(f"  ❌ Cronjob registration failed: {result.stderr}")
                return False
        except FileNotFoundError:
            print("  ⚠️  Hermes CLI not found. Skipping cronjob registration.")
            print("     Run manually in Hermes:")
            print(f"     cronjob action=create schedule=\"{config.cron['schedule']}\" prompt=\"Load content-strategist-viral-scriptwriter and run Module 2 Radar for niche '{config.niche}' with webhook $SLACK_WEBHOOK_URL\" skills=[\"content-strategist-viral-scriptwriter\"] name=\"{config.cron['name']}\"")
            return False
        except Exception as e:
            print(f"  ❌ Cronjob registration error: {e}")
            return False
    
    def send_test_webhook(self, config: ClientConfig) -> bool:
        """Send test webhook to verify delivery."""
        try:
            from scripts.test_webhook import build_slack_payload, build_telegram_payload, send_slack_webhook, send_telegram_webhook
            import asyncio
            
            # Create sample item
            sample_item = {
                "item_id": "trend_test_001",
                "title": "Test Trend from Deployment",
                "source": "Deployment Test",
                "source_url": "https://example.com",
                "published_at": datetime.now().isoformat(),
                "collected_at": datetime.now().isoformat(),
                "score": 0.95,
                "score_breakdown": {},
                "keywords_matched": config.keywords[:3],
                "executive_summary": "This is a test trend from the client deployment script. If you see this, webhook delivery is working correctly.",
                "key_insight": "Webhook integration verified successfully.",
                "suggested_angle": "Educational",
                "draft_post": "🧪 **Test Post**\n\nWebhook integration verified! The Content Strategist Agent is ready for deployment.\n\n#Test #Deployment #ContentStrategist",
                "platform": config.feeds.get("primary_platform", "linkedin"),
                "tone_id": config.tone_id,
                "status": "pending_approval"
            }
            
            if config.webhook.get("type") == "slack":
                webhook_url = config.webhook.get("url") or os.getenv("SLACK_WEBHOOK_URL")
                if not webhook_url:
                    print("  ⚠️  No Slack webhook URL configured")
                    return False
                payload = build_slack_payload(sample_item)
                return asyncio.run(send_slack_webhook(webhook_url, payload))
            else:
                bot_token = config.webhook.get("bot_token") or os.getenv("TELEGRAM_BOT_TOKEN")
                chat_id = config.webhook.get("chat_id") or os.getenv("TELEGRAM_CHAT_ID")
                if not bot_token or not chat_id:
                    print("  ⚠️  No Telegram bot token/chat ID configured")
                    return False
                payload = build_telegram_payload(sample_item, chat_id)
                return asyncio.run(send_telegram_webhook(bot_token, payload))
        except ImportError:
            print("  ⚠️  Test webhook module not available")
            return False
        except Exception as e:
            print(f"  ❌ Test webhook error: {e}")
            return False
    
    def deploy(self, config: ClientConfig, validate_keys: bool = True, register_cron: bool = True, test_webhook: bool = True) -> dict:
        """Execute full deployment."""
        print(f"\n🚀 DEPLOYING: {config.client_name} ({config.client_slug})")
        print("-" * 50)
        
        results = {
            "config_files": {},
            "api_keys": {},
            "cronjob": False,
            "test_webhook": False
        }
        
        # 1. Write config files
        print("\n📝 Writing config files...")
        results["config_files"] = {k: str(v) for k, v in self.write_config_files(config).items()}
        for name, path in results["config_files"].items():
            print(f"  ✅ {name}: {path}")
        
        # 2. Validate API keys
        if validate_keys:
            print("\n🔐 Validating API keys...")
            results["api_keys"] = self.validate_api_keys(config)
            for service, status in results["api_keys"].items():
                if status is None:
                    print(f"  ⏭️  {service}: not configured")
                elif status:
                    print(f"  ✅ {service}: valid")
                else:
                    print(f"  ❌ {service}: invalid or missing")
        
        # 3. Register cronjob
        if register_cron:
            print("\n⏰ Registering cronjob...")
            results["cronjob"] = self.register_cronjob(config)
        
        # 4. Test webhook
        if test_webhook:
            print("\n🔗 Sending test webhook...")
            results["test_webhook"] = self.send_test_webhook(config)
            if results["test_webhook"]:
                print("  ✅ Test webhook delivered")
            else:
                print("  ❌ Test webhook failed")
        
        # Summary
        print("\n" + "="*50)
        print("📋 DEPLOYMENT SUMMARY")
        print("="*50)
        print(f"Client: {config.client_name} ({config.client_slug})")
        print(f"Config dir: {self.config_dir / config.client_slug}")
        print(f"Niche: {config.niche}")
        print(f"Tone: {config.tone_id}")
        print(f"Primary platform: {config.feeds.get('primary_platform', 'linkedin')}")
        print(f"Cron: {config.cron['name']} ({config.cron['schedule']})")
        print(f"Webhook: {config.webhook.get('type', 'slack').upper()}")
        
        if validate_keys:
            print("\nAPI Keys:")
            for service, status in results["api_keys"].items():
                if status is not None:
                    print(f"  {service}: {'✅' if status else '❌'}")
        
        print(f"\nCronjob: {'✅' if results['cronjob'] else '❌'}")
        print(f"Test Webhook: {'✅' if results['test_webhook'] else '❌'}")
        
        print(f"\n📁 All files in: {self.config_dir / config.client_slug}")
        print(f"📖 See README.md there for next steps")
        
        return results


# --- Main Entry ---

def main():
    parser = argparse.ArgumentParser(description="Deploy Content Strategist Agent for a client")
    parser.add_argument("--client-name", help="Client name")
    parser.add_argument("--client-slug", help="Client slug (directory name)")
    parser.add_argument("--niche", help="Niche/industry description")
    parser.add_argument("--tone", choices=list(TONE_PRESETS.keys()), default="b2b_corporate", help="Tone preset")
    parser.add_argument("--webhook-type", choices=["slack", "telegram"], default="slack")
    parser.add_argument("--webhook-url", help="Slack webhook URL")
    parser.add_argument("--telegram-token", help="Telegram bot token")
    parser.add_argument("--telegram-chat", help="Telegram chat ID")
    parser.add_argument("--schedule", default="0 9-21/4 * * *", help="Cron schedule")
    parser.add_argument("--config-file", help="Load config from JSON file")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--no-validate-keys", action="store_true", help="Skip API key validation")
    parser.add_argument("--no-cron", action="store_true", help="Skip cronjob registration")
    parser.add_argument("--no-test-webhook", action="store_true", help="Skip test webhook")
    parser.add_argument("--skill-root", help="Skill root directory", default=".")
    
    args = parser.parse_args()
    
    skill_root = Path(args.skill_root).resolve()
    deployer = ClientDeployer(skill_root)
    
    # Load or collect config
    if args.config_file:
        config = deployer.load_config_from_file(Path(args.config_file))
    elif args.interactive or not args.client_name:
        config = deployer.collect_client_info_interactive()
    else:
        # Build from CLI args
        client_slug = args.client_slug or deployer.slugify(args.client_name)
        
        # Build feeds from presets
        feed_preset = "ai_automation"  # default
        rss_feeds = DEFAULT_RSS_FEEDS.get(feed_preset, [])
        youtube_channels = DEFAULT_YOUTUBE_CHANNELS.get(feed_preset, [])
        twitter_lists = DEFAULT_TWITTER_LISTS.get(feed_preset, [])
        
        webhook = {"type": args.webhook_type}
        if args.webhook_type == "slack":
            webhook["url"] = args.webhook_url or ""
            webhook["env_var"] = "SLACK_WEBHOOK_URL"
        else:
            webhook["bot_token"] = args.telegram_token or ""
            webhook["chat_id"] = args.telegram_chat or ""
            webhook["env_var_bot"] = "TELEGRAM_BOT_TOKEN"
            webhook["env_var_chat"] = "TELEGRAM_CHAT_ID"
        
        config = ClientConfig(
            client_name=args.client_name,
            client_slug=client_slug,
            niche=args.niche or "AI automation for content creators",
            keywords=DEFAULT_KEYWORDS_BY_NICHE[feed_preset],
            tone_id=args.tone,
            feeds={
                "rss_feeds": rss_feeds,
                "youtube_channels": youtube_channels,
                "twitter_lists": twitter_lists,
                "google_trends_regions": ["BR", "US"],
                "scan_window_hours": 24,
                "max_items_per_source": 10,
                "materiality_threshold": 0.7,
                "primary_platform": "linkedin"
            },
            webhook=webhook,
            cron={
                "schedule": args.schedule,
                "name": f"content-radar-{client_slug}"
            }
        )
    
    # Deploy
    try:
        results = deployer.deploy(
            config,
            validate_keys=not args.no_validate_keys,
            register_cron=not args.no_cron,
            test_webhook=not args.no_test_webhook
        )
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()