#!/usr/bin/env python3
"""
Module 1 Pipeline — Raw Transcript to Multi-Platform Content
Usage: python module1_pipeline.py --input transcript.txt --tone b2b_corporate --platforms instagram,linkedin,twitter,youtube
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator

# Optional: LLM delegation (requires Hermes delegate_task tool)
try:
    from llm_delegation import build_hook_generation_task, HooksOutputSchema
    LLM_DELEGATION_AVAILABLE = True
except ImportError:
    LLM_DELEGATION_AVAILABLE = False

# Standalone LLM client (OpenAI-compatible endpoint, Gemini by default)
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))
from llm_client import LLMError, MISSING_KEY_HELP, Transport, complete_json, llm_configured

# Import formatters from utils
try:
    import sys
    from pathlib import Path
    scripts_dir = Path(__file__).parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from utils import (
        format_tiktok_enhanced,
        format_threads,
        format_newsletter,
        format_for_platform,
        ToneProfile,
        ScriptData,
        FORMATTERS
    )
    EXTENDED_FORMATTERS_AVAILABLE = True
except ImportError:
    EXTENDED_FORMATTERS_AVAILABLE = False


# --- Pydantic Models ---

class ToneProfile(BaseModel):
    tone_id: str
    display_name: str
    language: str
    persona: dict
    structure_preferences: dict
    platform_overrides: dict = {}


class TranscriptSegment(BaseModel):
    segment_type: str  # thesis, argument, data_point, soundbite, pain_point
    content: str
    source_lines: list[int]


class Hook(BaseModel):
    hook_type: str  # curiosity, contrarian, pain_point, social_proof, bold_statement
    text: str
    platform_fit: list[str]


class ScriptRow(BaseModel):
    time_range: str
    voiceover: str
    broll: str
    text_overlay: str
    sfx: str


class CaptionBlock(BaseModel):
    platform: str
    content: str
    char_count: int
    hashtags: list[str]


class PipelineOutput(BaseModel):
    metadata: dict
    cleaned_segments: list[TranscriptSegment]
    framework_map: dict[str, str]
    hooks: list[Hook]
    script_table: list[ScriptRow]
    captions: list[CaptionBlock]


# --- Utility Functions ---

FILLER_WORDS_PT = {
    "né", "tipo assim", "é", "ah", "hum", "então", "daí", "pois é",
    "sabe", "tipo", "basicamente", "na verdade", "enfim", "por assim dizer"
}


def load_tone_profile(tone_path: Path) -> ToneProfile:
    with open(tone_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ToneProfile(**data)


def clean_transcript(text: str) -> tuple[str, list[TranscriptSegment]]:
    """Remove filler words, segment into logical topics."""
    lines = text.split("\n")
    cleaned_lines = []
    segments = []
    current_segment = None
    segment_start = 0

    for i, line in enumerate(lines):
        # Remove filler words
        words = line.split()
        filtered = [w for w in words if w.lower().strip(".,!?") not in FILLER_WORDS_PT]
        cleaned = " ".join(filtered)
        if cleaned.strip():
            cleaned_lines.append(cleaned)

        # Simple segmentation by topic markers (could be enhanced with NLP)
        if any(marker in line.lower() for marker in ["tese:", "thesis:", "argumento:", "argument:", "dado:", "data:", "frase:", "quote:", "dor:", "pain:"]):
            if current_segment:
                segments.append(current_segment)
            seg_type = "thesis" if "tese" in line.lower() or "thesis" in line.lower() else \
                       "argument" if "argumento" in line.lower() or "argument" in line.lower() else \
                       "data_point" if "dado" in line.lower() or "data" in line.lower() else \
                       "soundbite" if "frase" in line.lower() or "quote" in line.lower() else \
                       "pain_point"
            current_segment = TranscriptSegment(segment_type=seg_type, content=cleaned, source_lines=[i])
            segment_start = i
        elif current_segment:
            current_segment.content += " " + cleaned
            current_segment.source_lines.append(i)

    if current_segment:
        segments.append(current_segment)

    # If no explicit markers, create one big segment
    if not segments and cleaned_lines:
        segments.append(TranscriptSegment(
            segment_type="thesis",
            content=" ".join(cleaned_lines),
            source_lines=list(range(len(lines)))
        ))

    return "\n".join(cleaned_lines), segments


def extract_insights(segments: list[TranscriptSegment]) -> dict[str, Any]:
    """Extract structured insights from segments."""
    insights = {
        "core_thesis": "",
        "arguments": [],
        "data_points": [],
        "soundbites": [],
        "pain_points": []
    }
    for seg in segments:
        if seg.segment_type == "thesis" and not insights["core_thesis"]:
            insights["core_thesis"] = seg.content
        elif seg.segment_type == "argument":
            insights["arguments"].append(seg.content)
        elif seg.segment_type == "data_point":
            insights["data_points"].append(seg.content)
        elif seg.segment_type == "soundbite":
            insights["soundbites"].append(seg.content)
        elif seg.segment_type == "pain_point":
            insights["pain_points"].append(seg.content)
    return insights


def select_framework(platform: str) -> str:
    framework_map = {
        "instagram": "Hook-Value-CTA",
        "tiktok": "Hook-Value-CTA",
        "linkedin": "PAS → StoryBrand",
        "twitter": "Hook-Value-CTA (Thread)",
        "youtube": "AIDA → StoryBrand"
    }
    return framework_map.get(platform.lower(), "Hook-Value-CTA")


HOOK_TYPES = ["curiosity", "contrarian", "pain_point", "social_proof", "bold_statement"]


class HooksPlan(BaseModel):
    hooks: list[Hook]

    @model_validator(mode="after")
    def one_hook_per_type(self):
        types = sorted(h.hook_type for h in self.hooks)
        if types != sorted(HOOK_TYPES):
            raise ValueError(f"need exactly one hook of each type {HOOK_TYPES}, got {types}")
        return self


class InsightsPlan(BaseModel):
    core_thesis: str
    arguments: list[str] = []
    data_points: list[str] = []
    soundbites: list[str] = []
    pain_points: list[str] = []


class ScriptPlan(BaseModel):
    rows: list[ScriptRow] = Field(min_length=5, max_length=12)


class CaptionPlan(BaseModel):
    content: str = Field(min_length=20)


def _tone_brief(tone: ToneProfile) -> str:
    persona = tone.persona
    prefs = tone.structure_preferences
    return (f"Tone: {tone.display_name}. Write in {tone.language}. "
            f"Persona: {persona.get('archetype', '')}; traits: {', '.join(persona.get('traits', []))}. "
            f"Emoji usage: {prefs.get('emoji_usage', 'minimal')}; call to action style: {prefs.get('cta_style', '')}. "
            f"Never use these words: {', '.join(persona.get('forbidden_words', [])) or 'none'}.")


GROUNDING_RULE = ("Use only facts, numbers and claims that appear in the source material below. "
                  "Do not invent statistics, results, customers or quotes. If the source has no number, use none.")


def _source_block(insights: dict) -> str:
    return json.dumps(insights, ensure_ascii=False, indent=2)


def extract_insights_llm(cleaned_text: str, *, transport: Transport | None = None) -> dict[str, Any]:
    """Structure an unmarked transcript into thesis, arguments, data points, soundbites and pain points."""
    plan = complete_json(
        "You structure raw transcripts for a content team. " + GROUNDING_RULE,
        "Extract the core thesis, supporting arguments, data points, quotable soundbites and audience pain "
        f"points from this transcript. Leave a list empty if the transcript has nothing for it.\n\n{cleaned_text}",
        InsightsPlan, transport=transport)
    return plan.model_dump()


def generate_hooks(insights: dict, tone: ToneProfile, *, transport: Transport | None = None) -> list[Hook]:
    """Generate 5 hooks from the transcript insights, one per psychological type."""
    plan = complete_json(
        f"You write opening hooks for short-form video. {_tone_brief(tone)} {GROUNDING_RULE}",
        f"Write exactly five hooks, one for each type: {', '.join(HOOK_TYPES)}. Each hook is at most 160 "
        "characters. For platform_fit, list the platforms (instagram, tiktok, linkedin, twitter, youtube) "
        f"where that hook fits best.\n\nSource material:\n{_source_block(insights)}",
        HooksPlan, transport=transport)
    return plan.hooks


def generate_hooks_llm(insights: dict, tone: ToneProfile, delegate_task_fn) -> list[Hook]:
    """Generate hooks using LLM delegation (for use within Hermes).
    
    Args:
        insights: Extracted insights from transcript
        tone: ToneProfile configuration
        delegate_task_fn: Hermes delegate_task function reference
    
    Returns:
        List of Hook objects
    """
    if not LLM_DELEGATION_AVAILABLE:
        return generate_hooks(insights, tone)
    
    # Build delegation task
    tone_dict = tone.model_dump()
    task = build_hook_generation_task(insights, tone_dict)
    
    # Delegate to subagent
    result = delegate_task_fn(
        goal=task["goal"],
        context=task["context"],
        output_schema=task["output_schema"]
    )
    
    # Parse validated output
    validated = HooksOutputSchema.model_validate_json(result)
    
    # Convert to Hook objects
    hooks = []
    for h in validated.hooks:
        hooks.append(Hook(
            hook_type=h.hook_type,
            text=h.text,
            platform_fit=h.platform_fit
        ))
    
    return hooks


def build_script_table(insights: dict, hooks: list[Hook], tone: ToneProfile | None = None, *,
                       transport: Transport | None = None) -> list[ScriptRow]:
    """Build the video script + edit guide table (30-60s vertical video) from the insights."""
    opener = hooks[0].text if hooks else ""
    plan = complete_json(
        f"You script 30-60 second vertical videos for editors. {_tone_brief(tone) if tone else ''} {GROUNDING_RULE}",
        "Write the script as 5 to 12 rows covering the whole video in order. Each row has: time_range "
        "(like '0-3s'), voiceover (what is said), broll (what the editor shows), text_overlay (short "
        f"on-screen text) and sfx (sound or music cue). Open with this hook: {opener!r}. End with a call to "
        f"action.\n\nSource material:\n{_source_block(insights)}",
        ScriptPlan, transport=transport)
    return plan.rows


PLATFORM_BRIEFS = {
    "instagram": "Instagram Reels caption: hook on the first line, short lines, up to 2,200 characters, 5-8 hashtags at the end.",
    "tiktok": "TikTok caption: one or two punchy lines, under 300 characters, 3-5 hashtags.",
    "linkedin": "LinkedIn post: narrative and professional, short paragraphs, ends with a question, 3-5 hashtags, under 3,000 characters.",
    "twitter": "X/Twitter thread: 5 to 10 numbered posts (1/n, 2/n, ...), each under 280 characters, at most 3 hashtags in the last post.",
    "youtube": "YouTube description: one-line summary, a paragraph on what the video covers, key points as bullets, hashtags at the end. Do not invent timestamps or links.",
}


def format_caption(platform: str, insights: dict, hooks: list[Hook], script_rows: list[ScriptRow], tone: ToneProfile, *,
                   transport: Transport | None = None) -> CaptionBlock:
    """Generate platform-specific caption."""
    # Use extended formatters if available for new platforms
    if EXTENDED_FORMATTERS_AVAILABLE and platform.lower() in ["tiktok_enhanced", "threads", "newsletter"]:
        # Build script_data for extended formatters
        script_data = ScriptData(
            thesis=insights.get("core_thesis", ""),
            hooks=[{"hook_type": h.hook_type, "text": h.text, "platform_fit": h.platform_fit} for h in hooks],
            script_rows=[{"time_range": r.time_range, "voiceover": r.voiceover, "broll": r.broll, "text_overlay": r.text_overlay, "sfx": r.sfx} for r in script_rows],
            insights=insights
        )
        
        try:
            if platform.lower() == "tiktok_enhanced":
                result = format_tiktok_enhanced(script_data, tone)
                content = result["caption"]
            elif platform.lower() == "threads":
                result = format_threads(script_data, tone)
                # Join thread posts into single string for CaptionBlock
                content = "\n\n---\n\n".join([p["text"] for p in result["posts"]])
            elif platform.lower() == "newsletter":
                result = format_newsletter(script_data, tone, module2_items=[])
                content = result["main_content"]
            else:
                raise ValueError("Unknown extended platform")
        except Exception:
            # Fallback to template
            pass
        else:
            hashtags = re.findall(r"#(\w+)", content)
            return CaptionBlock(platform=platform, content=content, char_count=len(content), hashtags=hashtags)
    
    brief = PLATFORM_BRIEFS.get(platform.lower(), f"Caption for {platform}.")
    override = tone.platform_overrides.get(platform.lower(), {})
    script_text = "\n".join(f"{r.time_range}: {r.voiceover}" for r in script_rows)
    plan = complete_json(
        f"You write social captions. {_tone_brief(tone)} {GROUNDING_RULE}",
        f"{brief} Platform-specific tone settings: {json.dumps(override, ensure_ascii=False)}.\n\n"
        f"Hooks available: {json.dumps([h.text for h in hooks], ensure_ascii=False)}\n\n"
        f"Video script:\n{script_text}\n\nSource material:\n{_source_block(insights)}",
        CaptionPlan, transport=transport)
    content = plan.content
    hashtags = re.findall(r"#(\w+)", content)

    return CaptionBlock(platform=platform, content=content, char_count=len(content), hashtags=hashtags)


def run_pipeline(input_path: Path, tone: ToneProfile, platforms: list[str], *, offline: bool = False,
                 transport: Transport | None = None) -> PipelineOutput:
    """Execute the full Module 1 pipeline.

    offline=True runs only the rule-based steps (cleaning, segmentation, framework map) and
    leaves hooks, script and captions empty instead of inventing them.
    """
    with open(input_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Step 1: Clean & segment
    cleaned_text, segments = clean_transcript(raw_text)

    # Step 2: Extract insights. Transcripts without explicit markers come back as one
    # lump, so let the model structure them.
    insights = extract_insights(segments)
    unmarked = len(segments) == 1 and not any(insights[k] for k in ("arguments", "data_points", "soundbites", "pain_points"))
    if unmarked and not offline:
        insights = extract_insights_llm(cleaned_text, transport=transport)

    # Step 3: Framework map
    framework_map = {p: select_framework(p) for p in platforms}

    if offline:
        hooks, script_table, captions = [], [], []
    else:
        # Steps 4-6: hooks, script table, captions
        hooks = generate_hooks(insights, tone, transport=transport)
        script_table = build_script_table(insights, hooks, tone, transport=transport)
        captions = [format_caption(p, insights, hooks, script_table, tone, transport=transport) for p in platforms]

    return PipelineOutput(
        metadata={
            "input_file": str(input_path),
            "tone_id": tone.tone_id,
            "platforms": platforms,
            "generated_at": datetime.now().isoformat(),
            "raw_char_count": len(raw_text),
            "cleaned_char_count": len(cleaned_text),
            "mode": "offline" if offline else "llm",
        },
        cleaned_segments=segments,
        framework_map=framework_map,
        hooks=hooks,
        script_table=script_table,
        captions=captions
    )


def write_output(output: PipelineOutput, output_dir: Path) -> Path:
    """Write pipeline output to Markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{timestamp}_pipeline_result.md"

    md_parts = [
        f"# Pipeline Output — {output.metadata['generated_at']}\n",
        f"**Input:** `{output.metadata['input_file']}`  ",
        f"**Tone:** `{output.metadata['tone_id']}`  ",
        f"**Platforms:** `{', '.join(output.metadata['platforms'])}`  ",
        f"**Mode:** `{output.metadata.get('mode', 'llm')}`"
        + ("  \n_Offline run: hooks, script and captions were not generated._\n" if output.metadata.get("mode") == "offline" else "\n"),
        "## 1. CLEANED TRANSCRIPT SEGMENTS\n"
    ]

    for seg in output.cleaned_segments:
        md_parts.append(f"### {seg.segment_type.replace('_', ' ').title()}\n```\n{seg.content}\n```\n")

    md_parts.append("## 2. COPYWRITING FRAMEWORK MAP\n")
    md_parts.append("| Platform | Primary Framework |\n|----------|-------------------|")
    for platform, framework in output.framework_map.items():
        md_parts.append(f"| {platform} | {framework} |")
    md_parts.append("")

    md_parts.append("## 3. FIVE HIGH-IMPACT HOOKS\n")
    md_parts.append("| Type | Hook | Platform Fit |\n|------|------|--------------|")
    for hook in output.hooks:
        md_parts.append(f"| **{hook.hook_type.title()}** | {hook.text} | {', '.join(hook.platform_fit)} |")
    md_parts.append("")

    md_parts.append("## 4. VIDEO SCRIPT + EDIT GUIDE\n")
    md_parts.append("| Time | Voiceover (A-Roll) | B-Roll / Visual Cue | Text Overlay | SFX / Music Cue |")
    md_parts.append("|------|-------------------|---------------------|--------------|-----------------|")
    for row in output.script_table:
        md_parts.append(f"| {row.time_range} | {row.voiceover} | {row.broll} | {row.text_overlay} | {row.sfx} |")
    md_parts.append("")

    md_parts.append("## 5. PLATFORM CAPTIONS\n")
    for caption in output.captions:
        md_parts.append(f"### {caption.platform.title()} / Reels / TikTok\n")
        md_parts.append(f"```\n{caption.content}\n```\n")
        md_parts.append(f"*Chars: {caption.char_count} | Hashtags: {len(caption.hashtags)}*\n")

    md_parts.append("## 6. QUALITY CHECKLIST\n")
    checks = [
        ("5 hooks generated, one per type", len(output.hooks) == 5),
        ("Script table ≥5 rows", len(output.script_table) >= 5),
        ("One caption block per requested platform", len(output.captions) == len(output.metadata["platforms"])),
    ]
    for desc, passed in checks:
        md_parts.append(f"- [{'x' if passed else ' '}] {desc}")

    output_file.write_text("\n".join(md_parts), encoding="utf-8")
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Module 1: Raw Transcript → Multi-Platform Content")
    parser.add_argument("--input", required=True, help="Path to transcript file")
    parser.add_argument("--tone", default="b2b_corporate", help="Tone profile ID (from config/tone_of_voice.yaml)")
    parser.add_argument("--platforms", default="instagram,linkedin,twitter,youtube", help="Comma-separated platforms")
    parser.add_argument("--tone-config", default="config/tone_of_voice.yaml", help="Path to tone config YAML")
    parser.add_argument("--output-dir", default="output", help="Output directory")
    parser.add_argument("--offline", action="store_true",
                        help="Run only the rule-based steps; skip hooks, script and captions (no API key needed)")
    args = parser.parse_args()

    # Load tone profile
    tone_path = Path(args.tone_config)
    if not tone_path.exists():
        # Try templates directory
        tone_path = Path(__file__).parent.parent / "templates" / "tone_of_voice.yaml"
    tone = load_tone_profile(tone_path)

    if tone.tone_id != args.tone:
        print(f"Warning: Requested tone '{args.tone}' but config has '{tone.tone_id}'. Using config tone.")

    platforms = [p.strip() for p in args.platforms.split(",")]

    if not args.offline and not llm_configured():
        print(f"Error: {MISSING_KEY_HELP}", file=sys.stderr)
        sys.exit(2)

    # Run pipeline
    try:
        output = run_pipeline(Path(args.input), tone, platforms, offline=args.offline)
    except LLMError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Write output
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = write_output(output, output_dir)

    print(f"✅ Pipeline complete. Output written to: {output_file}")
    print(f"   Hooks: {len(output.hooks)} | Script rows: {len(output.script_table)} | Captions: {len(output.captions)}")


if __name__ == "__main__":
    main()