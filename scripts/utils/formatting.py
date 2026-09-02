#!/usr/bin/env python3
"""
Platform-specific caption formatters for Module 1 Pipeline.

Supports: Instagram, TikTok (enhanced), LinkedIn, Twitter/X, YouTube, Threads, Email Newsletter
"""

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToneProfile:
    tone_id: str
    display_name: str
    language: str
    persona: dict
    structure_preferences: dict
    platform_overrides: dict


@dataclass
class ScriptData:
    thesis: str
    hooks: list[dict]
    script_rows: list[dict]
    insights: dict


@dataclass
class TikTokOverlaySpec:
    """TikTok text-on-screen overlay specification."""
    timestamp: str          # e.g., "0-3s"
    text: str               # Overlay text
    position: str           # "top", "center", "bottom", "lower_third"
    style: str              # "bold", "highlight", "typewriter", "handwritten"
    animation: str          # "fade_in", "slide_up", "pop", "typewriter"
    duration: float         # seconds
    font_size: int          # 12-72
    color: str              # hex or named color
    background: Optional[str] = None  # optional background box


@dataclass
class TikTokSoundCluster:
    """TikTok targeted sound/hashtag cluster."""
    sound_id: str           # TikTok sound ID or "original"
    sound_name: str         # Human-readable name
    hashtags: list[str]     # Associated hashtag cluster
    trend_status: str       # "rising", "peak", "evergreen", "niche"
    niche_relevance: float  # 0-1


@dataclass
class ThreadsPost:
    """Single Threads post in a thread."""
    text: str
    reply_to: Optional[int] = None  # index of parent post
    media_hint: Optional[str] = None  # "image", "carousel", "video"


@dataclass
class NewsletterEmail:
    """Email newsletter structure."""
    subject_line: str
    preview_text: str
    preheader: str
    headline: str
    curated_takeaway: str
    main_content: str
    module1_highlight: Optional[str] = None
    module2_highlight: Optional[str] = None
    cta_primary: str = ""
    cta_secondary: Optional[str] = None
    footer: str = ""
    tags: list[str] = field(default_factory=list)


def get_platform_tone(tone: ToneProfile, platform: str) -> dict:
    """Merge base tone preferences with platform overrides."""
    base = tone.structure_preferences.copy()
    override = tone.platform_overrides.get(platform, {})
    base.update(override)
    return base


def apply_tone_filters(text: str, tone: ToneProfile, platform: str) -> str:
    """Apply tone-specific filters: forbidden words, emoji density, line breaks."""
    platform_tone = get_platform_tone(tone, platform)

    # Remove forbidden words
    for forbidden in tone.persona.get("forbidden_words", []):
        pattern = re.compile(re.escape(forbidden), re.IGNORECASE)
        text = pattern.sub("[filtered]", text)

    # Adjust emoji usage
    emoji_level = platform_tone.get("emoji_usage", "moderate")
    if emoji_level == "none":
        text = re.sub(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF]", "", text)
    elif emoji_level == "minimal":
        emojis = re.findall(r"[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002700-\U000027BF\U0001F900-\U0001F9FF]", text)
        if len(emojis) > 3:
            for emoji in emojis[3:]:
                text = text.replace(emoji, "", 1)

    # Adjust line break density
    line_break_density = platform_tone.get("line_break_density", "medium")
    if line_break_density == "high":
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"([.!?])\s+([A-Z])", r"\1\n\n\2", text)
    elif line_break_density == "low":
        text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


# =============================================================================
# EXISTING PLATFORMS (Instagram, TikTok basic, LinkedIn, Twitter, YouTube)
# =============================================================================

def format_instagram(script_data: ScriptData, tone: ToneProfile) -> str:
    platform_tone = get_platform_tone(tone, "instagram")
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["visual_curiosity", "curiosity", "bold_statement"]), script_data.hooks[0])

    lines = [
        hook["text"],
        "",
        f"We encoded {', '.join(['AIDA', 'PAS', 'Hook-Value-CTA', 'StoryBrand'])} into an agent that:",
        "✅ Generates 5 psychologically-distinct hooks",
        "✅ Builds your B-roll table automatically",
        "✅ Outputs 4 platform captions from one source",
        "",
        "Beta results: 47/50 creators saw 2x retention in week 1.",
        "3 hours → 12 minutes. 200 views → 15k average.",
        "",
        "Your next viral script is 12 minutes away. 🎬",
        "",
        "First script free. Link in bio. 👇",
        "",
        "#AIcontent #Scriptwriting #ViralVideo #CreatorTools #ContentAutomation #VideoMarketing #AIFilmaking"
    ]
    return apply_tone_filters("\n".join(lines), tone, "instagram")


def format_tiktok(script_data: ScriptData, tone: ToneProfile) -> str:
    """Basic TikTok caption formatter (legacy). Use format_tiktok_enhanced for full specs."""
    platform_tone = get_platform_tone(tone, "tiktok")
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["bold_statement", "contrarian", "visual_curiosity"]), script_data.hooks[0])

    lines = [
        f"{hook['text']} ⚡",
        "",
        "AIDA + PAS + Hook-Value-CTA + StoryBrand = automated viral scripts",
        "✅ 5 hook types • Auto A/B test",
        "✅ B-roll table • Zero editor guesswork",
        "✅ 1 source → 4 platforms",
        "",
        "47/50 beta creators: 2x retention week 1",
        "3h → 12min | 200 → 15k views avg",
        "",
        "Next viral script: 12 min away 🎬",
        "First free. Link in bio 👇",
        "",
        "#AIcontent #Scriptwriting #ViralVideo #CreatorTools #FYP #Viral"
    ]
    return apply_tone_filters("\n".join(lines), tone, "tiktok")


def format_linkedin(script_data: ScriptData, tone: ToneProfile) -> str:
    platform_tone = get_platform_tone(tone, "linkedin")
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["contrarian_insight", "contrarian", "pain_point"]), script_data.hooks[0])

    lines = [
        hook["text"],
        "",
        "Most creators spend 3+ hours writing scripts that the algorithm buries in the first 3 seconds. The problem isn't your ideas — it's your structure.",
        "",
        "We built an AI agent that applies proven frameworks automatically:",
        "",
        "→ 5 hook variations per script (curiosity, contrarian, pain point, social proof, bold statement)",
        "→ B-roll table for your editor (zero guesswork)",
        "→ 4 platform-optimized captions from one input",
        "",
        "Beta data: 50 creators. 47 saw ≥2x retention in 7 days.",
        "Average production time: 3 hours → 12 minutes.",
        "Average views: 200 → 15,000.",
        "",
        "The uncomfortable truth: Manual scriptwriting doesn't scale. Dynamic systems do.",
        "",
        "What's the biggest friction in your current script workflow?",
        "",
        "#ContentStrategy #AITools #CreatorEconomy #VideoMarketing #ContentAutomation"
    ]
    return apply_tone_filters("\n".join(lines), tone, "linkedin")


def format_twitter_thread(script_data: ScriptData, tone: ToneProfile) -> list[str]:
    platform_tone = get_platform_tone(tone, "twitter")
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["bold_statement", "contrarian", "curiosity"]), script_data.hooks[0])

    tweets = [
        f"1/10 {hook['text']} 🧵",
        "2/10 The problem: Creators spend 3h writing scripts that get 200 views. The algorithm kills you in the first 3 seconds.",
        "3/10 The fix: We encoded 4 viral frameworks into an agent:\n• AIDA (retention)\n• PAS (pain-point conversion)\n• Hook-Value-CTA (short-form)\n• StoryBrand (narrative clarity)",
        "4/10 Per script, it generates 5 hook types:\n1. Curiosity gap\n2. Contrarian truth\n3. Pain point\n4. Social proof\n5. Bold statement\n= Built-in A/B testing.",
        "5/10 It also builds a B-roll table:\nTime | Voiceover | Visual | Text Overlay | SFX\nYour editor drags & drops. Zero guesswork.",
        "6/10 One source → 4 captions:\nIG/TikTok (dynamic, emojis)\nLinkedIn (narrative, authority)\nTwitter (thread, viral)\nYouTube (SEO, timestamps)",
        "7/10 Beta: 50 creators. 47 doubled retention in week 1.\nTime: 3h → 12min. Views: 200 → 15k avg.",
        "8/10 The uncomfortable truth: Content calendars are traps. Dynamic systems win.",
        "9/10 Your next viral script is 12 minutes away. First one free.",
        "10/10 Link in bio. Try it and report back your retention numbers. 📊\n\n#AI #ContentCreation #CreatorEconomy"
    ]
    return [apply_tone_filters(t, tone, "twitter") for t in tweets]


def format_youtube(script_data: ScriptData, tone: ToneProfile) -> str:
    platform_tone = get_platform_tone(tone, "youtube")
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["bold_statement", "curiosity", "social_proof"]), script_data.hooks[0])

    lines = [
        f"{hook['text']} 🎬",
        "",
        "In this video, we break down the AI agent that encodes AIDA, PAS, Hook-Value-CTA, and StoryBrand frameworks into an automated scriptwriting pipeline — from raw notes to multi-platform captions in 12 minutes.",
        "",
        "TIMESTAMPS:",
        "0:00 The Problem: 3 Hours for 200 Views",
        "1:15 The Solution: 4 Frameworks Automated",
        "2:30 Hook Generation: 5 Types, Built-in A/B Testing",
        "3:45 B-Roll Table: Zero Editor Guesswork",
        "5:00 One Source → 4 Platform Captions",
        "6:15 Beta Results: 47/50 Creators 2x Retention",
        "7:30 The Uncomfortable Truth About Content Calendars",
        "8:45 Live Demo: Raw Notes → Viral Script",
        "10:00 Your Next Steps (First Script Free)",
        "",
        "KEY INSIGHTS:",
        "• Framework automation beats manual study every time",
        "• Hook variety = algorithm resilience",
        "• Visual planning in script = 50% faster editing",
        "• Multi-platform adaptation = maximum distribution per unit effort",
        "",
        "GET YOUR FIRST SCRIPT FREE:",
        "🔗 [AFFILIATE/LINK]",
        "",
        "CONNECT:",
        "📸 Instagram: @handle",
        "💼 LinkedIn: @handle",
        "🐦 Twitter: @handle",
        "📧 Newsletter: [link]",
        "",
        "CHAPTERS:",
        "0:00 Hook",
        "1:15 Problem",
        "2:30 Framework Automation",
        "3:45 Hook Generation",
        "5:00 B-Roll Table",
        "6:15 Multi-Platform Output",
        "7:30 Beta Results",
        "8:45 Live Demo",
        "10:00 CTA",
        "",
        "#AIContent #Scriptwriting #ViralVideo #CreatorTools #ContentAutomation #VideoMarketing #AIFilmmaking #YouTubeGrowth"
    ]
    return apply_tone_filters("\n".join(lines), tone, "youtube")


# =============================================================================
# NEW PLATFORMS: TikTok Enhanced, Threads, Email Newsletter
# =============================================================================

def format_tiktok_enhanced(script_data: ScriptData, tone: ToneProfile) -> dict:
    """
    Enhanced TikTok formatter returning full production spec:
    - caption (optimized for algorithm)
    - overlay_specs (text-on-screen for each beat)
    - sound_clusters (targeted sound/hashtag groups)
    - hashtag_strategy (tiered hashtag selection)
    """
    platform_tone = get_platform_tone(tone, "tiktok")
    
    # Select hook optimized for TikTok (visual + retention)
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["bold_statement", "visual_curiosity", "contrarian"]), script_data.hooks[0])
    
    # Build caption (algorithm-optimized)
    caption_lines = [
        f"{hook['text']} 🎯",
        "",
        "Stop guessing what works. This agent writes viral scripts in 12 min using 4 proven frameworks.",
        "",
        "✅ AIDA + PAS + HVC + StoryBrand",
        "✅ 5 hook types = built-in A/B test",
        "✅ B-roll table = editor knows exactly what to cut",
        "✅ 1 input → 4 platform outputs",
        "",
        "47/50 creators: 2x retention week 1",
        "3h → 12min | 200 → 15k avg views",
        "",
        "👇 Link in bio for first free script",
        "",
        "#scriptwriting #contentcreation #aitools #viralvideo #creatortools #fyp #viral #contentstrategy"
    ]
    caption = apply_tone_filters("\n".join(caption_lines), tone, "tiktok")
    
    # Build overlay specs from script_rows
    overlay_specs = []
    for i, row in enumerate(script_data.script_rows[:8]):  # First 8 beats for 60s video
        time_match = re.match(r"(\d+)-(\d+)s?", row["time_range"])
        if time_match:
            start, end = int(time_match.group(1)), int(time_match.group(2))
            duration = end - start
        else:
            start, end, duration = i * 7, (i + 1) * 7, 7
        
        overlay_text = row["text_overlay"]
        if len(overlay_text) > 32:  # TikTok overlay char limit ~32
            overlay_text = overlay_text[:29] + "..."
        
        overlay_specs.append(TikTokOverlaySpec(
            timestamp=f"{start}-{end}s",
            text=overlay_text,
            position=_get_overlay_position(i),
            style=_get_overlay_style(i),
            animation=_get_overlay_animation(i),
            duration=duration,
            font_size=_get_font_size(i),
            color="#FFFFFF",
            background="#000000AA" if i % 2 == 0 else None
        ))
    
    # Sound/hashtag clusters for niche targeting
    sound_clusters = _build_tiktok_sound_clusters(script_data.insights.get("niche", "AI automation"))
    
    # Tiered hashtag strategy
    hashtag_strategy = {
        "trending": ["fyp", "viral", "foryou", "trending"],
        "niche": ["scriptwriting", "contentcreation", "aitools", "viralvideo", "creatortools"],
        "branded": ["contentstrategist"],
        "community": ["creatorlife", "contentcreator", "videomarketing", "aiart"]
    }
    
    return {
        "caption": caption,
        "overlay_specs": [vars(o) for o in overlay_specs],
        "sound_clusters": [vars(s) for s in sound_clusters],
        "hashtag_strategy": hashtag_strategy,
        "video_duration_target": "60s",
        "beat_count": len(overlay_specs),
        "retention_hooks": _extract_retention_hooks(script_data.script_rows)
    }


def format_threads(script_data: ScriptData, tone: ToneProfile) -> dict:
    """
    Threads formatter returning multi-post thread structure:
    - posts: list of ThreadsPost objects
    - thread_length: total posts
    - engagement_hooks: reply prompts per post
    """
    platform_tone = get_platform_tone(tone, "threads")
    
    # Select hook for Threads (text-first, conversational)
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["curiosity", "pain_point", "contrarian_insight"]), script_data.hooks[0])
    
    # Build thread posts
    posts = []
    
    # Post 1: Hook
    posts.append(ThreadsPost(
        text=f"{hook['text']}\n\n🧵 Thread: How to automate viral scriptwriting in 12 minutes"
    ))
    
    # Post 2: Problem
    posts.append(ThreadsPost(
        text="The problem: Most creators spend 3+ hours writing scripts that get 200 views.\n\nThe algorithm buries you in the first 3 seconds because your structure doesn't match retention signals.\n\nI analyzed 10,000 viral Reels/TikToks. The top 1% share 4 structural traits.",
        reply_to=0
    ))
    
    # Post 3: Framework 1
    posts.append(ThreadsPost(
        text="Framework 1: AIDA (Attention → Interest → Desire → Action)\n\nUsed for: YouTube intros, long-form retention.\n\nThe agent auto-applies this to your raw notes — no manual study needed.",
        reply_to=1
    ))
    
    # Post 4: Framework 2
    posts.append(ThreadsPost(
        text="Framework 2: PAS (Problem → Agitation → Solution)\n\nUsed for: LinkedIn, educational content.\n\nIdentifies audience pain, twists the knife, presents your method as the relief.",
        reply_to=2
    ))
    
    # Post 5: Framework 3
    posts.append(ThreadsPost(
        text="Framework 3: Hook-Value-CTA (Short-form optimized)\n\nUsed for: Reels, TikTok, Shorts (<60s).\n\nHook (0-3s) → Dense value (3-30s) → Frictionless CTA (last 3s).\n\nGenerates 5 hook types per script = built-in A/B testing.",
        reply_to=3
    ))
    
    # Post 6: Framework 4
    posts.append(ThreadsPost(
        text="Framework 4: StoryBrand (Narrative clarity)\n\nUsed for: YouTube descriptions, email sequences.\n\nCharacter → Problem → Guide → Plan → CTA → Success/Failure.\n\nTurns your content into a story the audience sees themselves in.",
        reply_to=4
    ))
    
    # Post 7: Visual planning (B-roll table)
    posts.append(ThreadsPost(
        text="The game-changer: Auto-generated B-roll table.\n\nTime | Voiceover | Visual | Text Overlay | SFX\n\nYour editor drags & drops. Zero guesswork. Cuts editing time 50%.\n\nMost creators skip this. That's why their retention curves flatline.",
        reply_to=5
    ))
    
    # Post 8: Multi-platform output
    posts.append(ThreadsPost(
        text="One raw input → 4 platform outputs:\n\n📱 Instagram/TikTok: Dynamic, emojis, retention hooks\n💼 LinkedIn: Narrative, authority, question CTA\n🐦 Twitter/X: Thread format, viral mechanics\n📺 YouTube: SEO, timestamps, chapters\n\nMaximum distribution per unit effort.",
        reply_to=6
    ))
    
    # Post 9: Proof
    posts.append(ThreadsPost(
        text="Beta results (50 creators, 7 days):\n• 47/50 saw ≥2x retention\n• Avg production: 3h → 12min\n• Avg views: 200 → 15,000\n• Platform split: 40% Reels, 30% TikTok, 20% Shorts, 10% LinkedIn Video\n\nThe data doesn't lie. Structure beats effort.",
        reply_to=7
    ))
    
    # Post 10: CTA + engagement hook
    posts.append(ThreadsPost(
        text="The uncomfortable truth: Content calendars are traps. Dynamic systems win.\n\nYour next viral script is 12 minutes away. First one free — link in bio.\n\n👇 What's the #1 friction in your script workflow? (I read every reply)",
        reply_to=8
    ))
    
    # Engagement hooks for replies
    engagement_hooks = [
        "What's your current script process?",
        "Which framework would you try first?",
        "How long does your scripting take?",
        "What's your biggest retention killer?",
        "AIDA or PAS for your niche?",
        "Do you plan B-rolls before filming?",
        "Which platform drives most revenue?",
        "Manual or AI-assisted?",
        "What would you do with 3 extra hours?",
        "Ready to test the agent?"
    ]
    
    return {
        "posts": [vars(p) for p in posts],
        "thread_length": len(posts),
        "engagement_hooks": engagement_hooks,
        "estimated_read_time": f"{len(posts) * 45}s",
        "character_counts": [len(p.text) for p in posts],
        "hashtag_strategy": {
            "broad": ["ContentStrategy", "AITools", "CreatorEconomy"],
            "niche": ["Scriptwriting", "ViralVideo", "ContentAutomation"],
            "branded": ["ContentStrategist"]
        }
    }


def format_newsletter(script_data: ScriptData, tone: ToneProfile, 
                       module2_items: list[dict] = None) -> dict:
    """
    Email newsletter formatter returning broadcast-ready structure:
    - subject_line, preview_text, preheader
    - headline, curated_takeaway
    - main_content (Module 1 highlight)
    - module1_highlight, module2_highlight
    - cta_primary, cta_secondary
    - footer, tags
    """
    platform_tone = get_platform_tone(tone, "newsletter")
    
    # Select hook for email (curiosity + value promise)
    hook = next((h for h in script_data.hooks if h["hook_type"] in ["curiosity", "social_proof", "contrarian_insight"]), script_data.hooks[0])
    
    # Subject lines (A/B test variants)
    subject_lines = [
        f"{hook['text']}",
        f"🎬 3h → 12min: The scriptwriting shortcut top creators use",
        f"Your video script is costing you 90% retention (here's the fix)",
        f"How 47/50 creators doubled retention in 7 days",
        f"The 4 frameworks behind every viral video (automated)"
    ]
    subject_line = subject_lines[0]
    preview_text = "AIDA + PAS + Hook-Value-CTA + StoryBrand → automated in 12 minutes. First script free."
    
    # Curated takeaway (the "TL;DR" for busy readers)
    curated_takeaway = (
        "Manual scriptwriting doesn't scale. We encoded 4 viral frameworks (AIDA, PAS, "
        "Hook-Value-CTA, StoryBrand) into an agent that generates retention-optimized scripts "
        "in 12 minutes — complete with B-roll tables, 5 hook variations for A/B testing, "
        "and multi-platform captions. Beta: 47/50 creators saw 2x retention."
    )
    
    # Main content (Module 1 highlight)
    module1_highlight = f"""
## 🎬 This Week's Deep Dive: The 12-Minute Viral Script Pipeline

Most creators spend **3+ hours** writing scripts that the algorithm buries in the first 3 seconds. 
The problem isn't your ideas — it's your structure.

We built an AI agent that applies proven copywriting frameworks automatically:

**The 4 Frameworks:**
1. **AIDA** (Attention → Interest → Desire → Action) — YouTube intros, long-form retention
2. **PAS** (Problem → Agitation → Solution) — LinkedIn, educational content  
3. **Hook-Value-CTA** — Reels/TikTok/Shorts (<60s), retention-optimized
4. **StoryBrand** (Character → Problem → Guide → Plan → CTA) — Narrative clarity

**What the agent generates per script:**
- ✅ 5 hook variations (curiosity, contrarian, pain point, social proof, bold statement) = built-in A/B testing
- ✅ B-roll table with timestamps, visual cues, text overlays, SFX = zero editor guesswork
- ✅ 4 platform-optimized captions from one input (IG, LinkedIn, Twitter, YouTube)

**Beta Results (50 creators, 7 days):**
- 47/50 saw ≥2x retention
- Avg production time: 3 hours → 12 minutes
- Avg views: 200 → 15,000
"""
    
    # Module 2 highlight (trend radar)
    module2_highlight = ""
    if module2_items:
        module2_highlight = "## 📈 Trend Radar: This Week's Signal\n\n"
        for i, item in enumerate(module2_items[:3], 1):
            module2_highlight += f"""
**{i}. {item.get('title', 'Trending Topic')}**  
*Source: {item.get('source', 'Industry')} | Score: {item.get('score', 0):.0%}*

{item.get('executive_summary', 'Strategic insight available in dashboard.')}

💡 **Key Insight:** {item.get('key_insight', 'Monitor for strategic implications.')}

[View Approval Card →]({item.get('approval_url', '#')})
"""
    else:
        module2_highlight = """
## 📈 Trend Radar: This Week's Signal

*Radar running on 4-hour cycles. Next digest includes:*
- AI video editing funding surge ($180M+ Q4)
- Autonomous editing category validation
- Creator tool commoditization timeline

*Enable Module 2 in your dashboard to receive approval cards in Slack/Telegram.*
"""
    
    # CTAs
    cta_primary = "🎬 Generate Your First Free Script →"
    cta_secondary = "📊 View Trend Radar Dashboard"
    
    # Footer
    footer = """
---
**Content Strategist & Viral Scriptwriter Agent**  
Transforming raw ideas into retention-optimized content at scale.

[Dashboard] • [Module 1 Pipeline] • [Module 2 Radar] • [Settings] • [Unsubscribe]

*You're receiving this because you subscribed to Content Strategist insights.  
Reply to this email — I read every response.*
"""
    
    newsletter = NewsletterEmail(
        subject_line=subject_line,
        preview_text=preview_text,
        preheader="The 4 frameworks behind every viral video — now automated.",
        headline=f"🎬 {hook['text']}",
        curated_takeaway=curated_takeaway,
        main_content=module1_highlight + module2_highlight,
        module1_highlight=module1_highlight,
        module2_highlight=module2_highlight,
        cta_primary=cta_primary,
        cta_secondary=cta_secondary,
        footer=footer,
        tags=["content-strategy", "viral-scripts", "ai-automation", "creator-tools"]
    )
    
    return vars(newsletter)


# =============================================================================
# HELPER FUNCTIONS FOR TIKTOK ENHANCED
# =============================================================================

def _get_overlay_position(beat_index: int) -> str:
    positions = ["center", "lower_third", "top", "center", "lower_third", "center", "top", "center"]
    return positions[beat_index % len(positions)]


def _get_overlay_style(beat_index: int) -> str:
    styles = ["bold", "highlight", "typewriter", "bold", "handwritten", "highlight", "bold", "typewriter"]
    return styles[beat_index % len(styles)]


def _get_overlay_animation(beat_index: int) -> str:
    animations = ["pop", "slide_up", "typewriter", "fade_in", "pop", "slide_up", "fade_in", "pop"]
    return animations[beat_index % len(animations)]


def _get_font_size(beat_index: int) -> int:
    # Hook beats get larger text
    if beat_index in [0, 1]:
        return 56
    elif beat_index in [2, 3]:
        return 48
    return 42


def _build_tiktok_sound_clusters(niche: str) -> list[TikTokSoundCluster]:
    """Build niche-targeted sound/hashtag clusters."""
    base_clusters = [
        TikTokSoundCluster(
            sound_id="original",
            sound_name="Original Audio / Voiceover",
            hashtags=["originalsound", "voiceover", "educational"],
            trend_status="evergreen",
            niche_relevance=1.0
        ),
        TikTokSoundCluster(
            sound_id="trending_upbeat",
            sound_name="Upbeat Educational Background",
            hashtags=["learnontiktok", "edutok", "productivityhacks"],
            trend_status="rising",
            niche_relevance=0.9
        ),
        TikTokSoundCluster(
            sound_id="minimal_lofi",
            sound_name="Minimal Lo-fi Focus",
            hashtags=["deepwork", "focusmode", "studywithme"],
            trend_status="peak",
            niche_relevance=0.7
        )
    ]
    
    # Add niche-specific clusters
    if "ai" in niche.lower() or "automation" in niche.lower():
        base_clusters.append(TikTokSoundCluster(
            sound_id="ai_futuristic",
            sound_name="Futuristic AI Transition",
            hashtags=["ai", "artificialintelligence", "automation", "futuretech"],
            trend_status="rising",
            niche_relevance=0.95
        ))
    
    if "creator" in niche.lower() or "content" in niche.lower():
            base_clusters.append(TikTokSoundCluster(
                sound_id="creator_economy",
                sound_name="Creator Economy Anthem",
                hashtags=["creatoreconomy", "contentcreator", "buildinpublic", "indiehackers"],
                trend_status="rising",
                niche_relevance=0.9
            ))
    
    return base_clusters


def _extract_retention_hooks(script_rows: list[dict]) -> list[dict]:
    """Extract key retention moments from script."""
    hooks = []
    for i, row in enumerate(script_rows):
        if i == 0:
            hooks.append({"type": "hook", "timestamp": row["time_range"], "technique": "pattern_interrupt", "text": row["text_overlay"]})
        elif i == 1:
            hooks.append({"type": "value_promise", "timestamp": row["time_range"], "technique": "transformation", "text": row["text_overlay"]})
        elif "B-ROLL" in row["text_overlay"] or "ZERO GUESSWORK" in row["text_overlay"]:
            hooks.append({"type": "authority", "timestamp": row["time_range"], "technique": "proof", "text": row["text_overlay"]})
        elif "RETENTION" in row["text_overlay"] or "2X" in row["text_overlay"]:
            hooks.append({"type": "social_proof", "timestamp": row["time_range"], "technique": "data", "text": row["text_overlay"]})
        elif "FREE" in row["text_overlay"] or "LINK IN BIO" in row["text_overlay"]:
            hooks.append({"type": "cta", "timestamp": row["time_range"], "technique": "direct", "text": row["text_overlay"]})
    return hooks


# =============================================================================
# PLATFORM FORMATTER REGISTRY
# =============================================================================

FORMATTERS = {
    "instagram": format_instagram,
    "tiktok": format_tiktok,
    "tiktok_enhanced": format_tiktok_enhanced,
    "linkedin": format_linkedin,
    "twitter": format_twitter_thread,
    "threads": format_threads,
    "youtube": format_youtube,
    "newsletter": format_newsletter,
}


def format_for_platform(platform: str, script_data: ScriptData, tone: ToneProfile, **kwargs) -> Any:
    """Dispatch to platform-specific formatter."""
    formatter = FORMATTERS.get(platform.lower())
    if not formatter:
        raise ValueError(f"No formatter for platform: {platform}. Available: {list(FORMATTERS.keys())}")
    
    # Pass extra kwargs for formatters that need them (e.g., newsletter needs module2_items)
    if platform.lower() == "newsletter" and "module2_items" in kwargs:
        return formatter(script_data, tone, module2_items=kwargs["module2_items"])
    
    return formatter(script_data, tone)