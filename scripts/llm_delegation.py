#!/usr/bin/env python3
"""
LLM-Enhanced Creative Writing Subagents for Content Strategist Agent.

This module provides structured subagent delegation for:
- Hook generation (Module 1)
- Insight/Executive Summary generation (Module 2)
- Draft Post generation (Module 2)

Uses Hermes `delegate_task` with JSON Schema validation for reliable structured output.
"""

import json
from typing import Any, Optional
from pydantic import BaseModel, Field


# --- Output Schemas for Structured Delegation ---

class HookSchema(BaseModel):
    hook_type: str = Field(description="Psychological trigger type", pattern="^(curiosity|contrarian|pain_point|social_proof|bold_statement)$")
    text: str = Field(description="The hook text, max 160 chars", max_length=160)
    platform_fit: list[str] = Field(description="Platforms where this hook performs best", min_items=1)


class HooksOutputSchema(BaseModel):
    hooks: list[HookSchema] = Field(description="Exactly 5 hooks, one per type", min_length=5, max_length=5)


class InsightSchema(BaseModel):
    executive_summary: str = Field(description="3-sentence summary: what happened, why it matters for niche, implied opportunity/threat", max_length=500)
    key_insight: str = Field(description="One-sentence strategic takeaway for the audience", max_length=280)
    suggested_angle: str = Field(description="Content angle", pattern="^(Contrarian|Educational|Case Study|Prediction|Framework)$")


class DraftPostSchema(BaseModel):
    draft_post: str = Field(description="Platform-optimized draft post ready for approval card", max_length=3000)


# --- Subagent Prompts ---

HOOK_GENERATION_PROMPT = """You are a viral content strategist specializing in short-form video hooks (Reels, TikTok, Shorts).

TASK: Generate exactly 5 hooks for a video script based on the provided insights. Each hook must use a DIFFERENT psychological trigger type.

HOOK TYPES (use exactly one of each):
1. **curiosity** — Information gap: "The [specific thing] [authority] don't want you to know"
2. **contrarian** — Counter-intuitive truth: "Stop [universal advice]. Start [alternative] instead."
3. **pain_point** — Visceral problem: "Why your [output] [fails specific way] (and the fix)"
4. **social_proof** — Authority/results: "How [client] [result] in [timeframe] with [method]"
5. **bold_statement** — Provocative claim: "[Industry standard] is dead. [New paradigm] wins."

CONSTRAINTS:
- Each hook ≤ 160 characters (Twitter-safe)
- Reference SPECIFIC insights from the input (numbers, names, concrete outcomes)
- No generic clickbait — every hook must be grounded in the provided insights
- Apply the tone profile: {tone_description}
- Platform fit: indicate which platforms each hook suits best

INPUT INSIGHTS:
{insights}

TONE PROFILE:
- Archetype: {archetype}
- Traits: {traits}
- Forbidden words: {forbidden_words}
- Preferred phrases: {preferred_phrases}
- Hook style preference: {hook_style}

Return ONLY valid JSON matching the schema. Exactly 5 hooks, one per type."""


INSIGHT_GENERATION_PROMPT = """You are a B2B content strategist and trend analyst. Your job: extract strategic insights from raw trend data for a specific niche.

TASK: Analyze the trend item and produce an executive summary + key insight + suggested angle.

NICHE: {niche}
TONE: {tone_description}

TREND ITEM:
- Title: {title}
- Source: {source}
- Published: {published_at}
- Keywords matched: {keywords_matched}
- Content preview: {content_preview}
- Engagement: {engagement}

REQUIREMENTS:
1. **executive_summary** (3 sentences max):
   - Sentence 1: What happened (facts only)
   - Sentence 2: Why it matters for THIS niche (connect the dots)
   - Sentence 3: Implied opportunity or threat for the audience

2. **key_insight** (1 sentence, ≤280 chars):
   - The strategic "so what?" — not a summary, an implication
   - Example: "The category 'autonomous editing' just got validated by $180M VC — commoditization in 6-12 months."

3. **suggested_angle** (one of: Contrarian, Educational, Case Study, Prediction, Framework):
   - Contrarian: "Everyone thinks X, actually Y"
   - Educational: "Here's how to prepare for X"
   - Case Study: "How [company] navigated this"
   - Prediction: "In 12 months, X will be standard"
   - Framework: "Use this 3-step model to adapt"

TONE CONSTRAINTS:
- {tone_description}
- Forbidden words: {forbidden_words}
- Use preferred phrases where natural: {preferred_phrases}

Return ONLY valid JSON matching the schema."""


DRAFT_POST_PROMPT = """You are a senior social media copywriter for B2B brands. Write a publication-ready post for the approval card.

TASK: Draft a platform-optimized post based on the trend insight.

CONTEXT:
- Niche: {niche}
- Platform: {platform}
- Tone: {tone_description}
- Key insight: {key_insight}
- Executive summary: {executive_summary}
- Source attribution: {source}
- Suggested angle: {suggested_angle}

PLATFORM SPECIFICATIONS ({platform}):
{platform_specs}

TONE CONSTRAINTS:
- Archetype: {archetype}
- Traits: {traits}
- Forbidden words: {forbidden_words} — DO NOT USE THESE
- Preferred phrases: {preferred_phrases} — incorporate naturally
- Hook style: {hook_style}
- CTA style: {cta_style}
- Emoji usage: {emoji_usage}
- Line break density: {line_break_density}

OUTPUT REQUIREMENTS:
- Ready to paste — no placeholders
- Includes source attribution ("Via @{source}" or similar)
- Ends with appropriate CTA per tone
- Hashtags per platform best practices
- Respects platform character limits

Return ONLY valid JSON with "draft_post" field."""


# --- Platform Specs for Prompt Injection ---

PLATFORM_SPECS = {
    "instagram": """- Caption limit: 2,200 chars (125 visible before 'more')
- Hashtags: 5-15 (mix niche/broad/branded)
- Line breaks: Critical — double breaks for readability
- Emojis: Moderate (3-8), bullet points, section dividers
- CTA: End of caption + first comment for hashtags
- Algorithm signals: Saves > Shares > Comments > Likes""",
    "tiktok": """- Caption limit: 2,200 chars (150 visible)
- Hashtags: 3-5 highly relevant (trending + niche)
- Line breaks: Single OK
- Emojis: Heavy encouraged (8-15)
- CTA: "Follow for more", "Comment [X]", "Stitch this"
- Algorithm: Completion rate > Re-watches > Shares > Comments""",
    "linkedin": """- Post limit: 3,000 chars (140 visible before 'see more')
- Hashtags: 3-5 broad professional, at end
- Line breaks: Double for paragraphs
- Emojis: Minimal (0-3), section markers only
- CTA: Question for comments ("What's your experience?")
- Algorithm: Dwell time > Comments > Shares > Reactions""",
    "twitter": """- Thread format: 5-15 tweets, each ≤280 chars
- Hashtags: 1-2 per thread (first or last tweet)
- Numbering: 1/10, 2/10, etc.
- Emojis: Moderate (1-3 per tweet)
- CTA: Last tweet — Follow, RT, Link, Question
- Algorithm: RTs > Replies > Likes > Profile clicks""",
    "youtube": """- Description: 5,000 chars (first 2 lines = search snippet)
- Timestamps required: 0:00 Hook, 0:45 Problem, etc.
- Hashtags: 3-5 above title (auto-extracted)
- Tags (backend): 10-15 specific + broad
- CTA: First 2 lines + pinned comment + end screen
- Algorithm: AVD > CTR > Engagement""",
}


def build_tone_description(tone: dict) -> str:
    """Build compact tone description for prompt injection."""
    persona = tone.get("persona", {})
    struct = tone.get("structure_preferences", {})
    return (
        f"Archetype: {persona.get('archetype', 'Expert Mentor')}. "
        f"Traits: {', '.join(persona.get('traits', ['authoritative', 'data-driven']))}. "
        f"Hook style: {struct.get('hook_style', 'contrarian_insight')}. "
        f"CTA style: {struct.get('cta_style', 'question_driven')}. "
        f"Emoji: {struct.get('emoji_usage', 'minimal')}. "
        f"Line breaks: {struct.get('line_break_density', 'high')}."
    )


# --- Delegate Task Builders ---

def build_hook_generation_task(insights: dict, tone: dict) -> dict:
    """Build delegate_task call for hook generation."""
    tone_desc = build_tone_description(tone)
    persona = tone.get("persona", {})
    struct = tone.get("structure_preferences", {})

    prompt = HOOK_GENERATION_PROMPT.format(
        insights=json.dumps(insights, ensure_ascii=False, indent=2),
        tone_description=tone_desc,
        archetype=persona.get("archetype", "Expert Mentor"),
        traits=", ".join(persona.get("traits", ["authoritative", "data-driven"])),
        forbidden_words=", ".join(persona.get("forbidden_words", [])),
        preferred_phrases=", ".join(persona.get("preferred_phrases", [])),
        hook_style=struct.get("hook_style", "contrarian_insight"),
    )

    return {
        "goal": "Generate 5 viral video hooks (one per psychological type) from transcript insights",
        "context": prompt,
        "output_schema": HooksOutputSchema.model_json_schema(),
        "role": "leaf"
    }


def build_insight_generation_task(trend_item: dict, niche: str, tone: dict) -> dict:
    """Build delegate_task call for insight generation."""
    tone_desc = build_tone_description(tone)
    persona = tone.get("persona", {})

    prompt = INSIGHT_GENERATION_PROMPT.format(
        niche=niche,
        tone_description=tone_desc,
        title=trend_item.get("title", ""),
        source=trend_item.get("source", ""),
        published_at=trend_item.get("published_at", ""),
        keywords_matched=", ".join(trend_item.get("keywords_matched", [])),
        content_preview=trend_item.get("content_preview", ""),
        engagement=json.dumps(trend_item.get("engagement", {})),
        forbidden_words=", ".join(persona.get("forbidden_words", [])),
        preferred_phrases=", ".join(persona.get("preferred_phrases", [])),
    )

    return {
        "goal": "Generate executive summary, key insight, and content angle for a trend item",
        "context": prompt,
        "output_schema": InsightSchema.model_json_schema(),
        "role": "leaf"
    }


def build_draft_post_task(item: dict, niche: str, platform: str, tone: dict) -> dict:
    """Build delegate_task call for draft post generation."""
    tone_desc = build_tone_description(tone)
    persona = tone.get("persona", {})
    struct = tone.get("structure_preferences", {})
    platform_override = tone.get("platform_overrides", {}).get(platform, {})

    # Merge base + platform override
    hook_style = platform_override.get("hook_style", struct.get("hook_style", "contrarian_insight"))
    cta_style = platform_override.get("cta_style", struct.get("cta_style", "question_driven"))
    emoji_usage = platform_override.get("emoji_usage", struct.get("emoji_usage", "moderate"))
    line_breaks = platform_override.get("line_break_density", struct.get("line_break_density", "high"))

    prompt = DRAFT_POST_PROMPT.format(
        niche=niche,
        platform=platform,
        tone_description=tone_desc,
        key_insight=item.get("key_insight", ""),
        executive_summary=item.get("executive_summary", ""),
        source=item.get("source", ""),
        suggested_angle=item.get("suggested_angle", "Educational"),
        platform_specs=PLATFORM_SPECS.get(platform, PLATFORM_SPECS["linkedin"]),
        archetype=persona.get("archetype", "Expert Mentor"),
        traits=", ".join(persona.get("traits", ["authoritative", "data-driven"])),
        forbidden_words=", ".join(persona.get("forbidden_words", [])),
        preferred_phrases=", ".join(persona.get("preferred_phrases", [])),
        hook_style=hook_style,
        cta_style=cta_style,
        emoji_usage=emoji_usage,
        line_break_density=line_breaks,
    )

    return {
        "goal": f"Write a {platform}-optimized draft post for approval card",
        "context": prompt,
        "output_schema": DraftPostSchema.model_json_schema(),
        "role": "leaf"
    }


# --- Batch Helpers ---

def build_batch_hook_generation(insights_list: list[dict], tone: dict) -> list[dict]:
    """Build batch tasks for multiple transcript inputs."""
    return [build_hook_generation_task(insights, tone) for insights in insights_list]


def build_batch_insight_generation(trend_items: list[dict], niche: str, tone: dict) -> list[dict]:
    """Build batch tasks for multiple trend items."""
    return [build_insight_generation_task(item, niche, tone) for item in trend_items]


def build_batch_draft_posts(items: list[dict], niche: str, platform: str, tone: dict) -> list[dict]:
    """Build batch tasks for draft posts."""
    return [build_draft_post_task(item, niche, platform, tone) for item in items]