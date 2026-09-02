#!/usr/bin/env python3
"""
Hermes Agent Entry Point for Content Strategist & Viral Scriptwriter.

This module demonstrates how to use the LLM delegation features
when running inside Hermes Agent (where `delegate_task` is available).

Usage in Hermes:
    # Load the skill
    skill_view(name="content-strategist-viral-scriptwriter")
    
    # Then call the pipeline with LLM-enhanced generation
    from scripts.hermes_entry import run_pipeline_llm, run_radar_llm
    
    # Module 1 with LLM hooks
    result = run_pipeline_llm(
        input_path="transcript.txt",
        tone_id="b2b_corporate",
        platforms=["instagram", "linkedin", "twitter", "youtube"]
    )
    
    # Module 2 with LLM insights + drafts
    result = run_radar_llm(
        feeds_config="config/feeds.yaml",
        tone_config="config/tone_of_voice.yaml",
        webhook_url=SLACK_WEBHOOK_URL
    )
"""

import json
from pathlib import Path
from typing import Any

# These imports work when running inside Hermes with the skill loaded
from scripts.module1_pipeline import (
    run_pipeline,
    generate_hooks_llm,
    load_tone_profile,
    PipelineOutput,
    ToneProfile
)
from scripts.module2_radar import (
    run_radar,
    generate_insights_llm,
    draft_post_llm,
    load_tone_profile as load_tone_profile_radar,
    FeedsConfig,
    StateManager,
    EnrichedItem
)
from scripts.utils.llm_delegation import LLM_DELEGATION_AVAILABLE


# --- Hermes delegate_task wrapper ---

async def hermes_delegate_task(goal: str, context: str, output_schema: dict) -> str:
    """
    Wrapper for Hermes delegate_task tool.
    
    In actual Hermes usage, this would be replaced by the built-in delegate_task tool.
    This is a placeholder showing the expected interface.
    """
    # This is a stub — in Hermes, you'd use the actual delegate_task tool
    # which is available in the agent's toolset when the skill is loaded
    raise NotImplementedError(
        "This function should be replaced by Hermes' built-in delegate_task tool. "
        "When running inside Hermes with this skill loaded, use the delegate_task tool directly."
    )


# --- Module 1: LLM-Enhanced Pipeline ---

async def run_pipeline_llm(
    input_path: str,
    tone_id: str = "b2b_corporate",
    platforms: list[str] | None = None,
    tone_config: str = "config/tone_of_voice.yaml",
    delegate_task_fn = None
) -> PipelineOutput:
    """
    Run Module 1 pipeline with LLM-enhanced hook generation.
    
    Args:
        input_path: Path to transcript file
        tone_id: Tone profile ID
        platforms: Target platforms
        tone_config: Path to tone config YAML
        delegate_task_fn: Hermes delegate_task function (pass the tool reference)
    
    Returns:
        PipelineOutput with LLM-generated hooks
    """
    if platforms is None:
        platforms = ["instagram", "linkedin", "twitter", "youtube"]
    
    # Load tone
    tone_path = Path(tone_config)
    if not tone_path.exists():
        tone_path = Path(__file__).parent.parent / "templates" / "tone_of_voice.yaml"
    tone = load_tone_profile(tone_path)
    
    # Read input
    with open(Path(input_path), "r", encoding="utf-8") as f:
        raw_text = f.read()
    
    # Import pipeline internals
    from scripts.module1_pipeline import clean_transcript, extract_insights, select_framework, build_script_table, format_caption, write_output
    
    # Step 1: Clean & segment
    cleaned_text, segments = clean_transcript(raw_text)
    
    # Step 2: Extract insights
    insights = extract_insights(segments)
    
    # Step 3: Framework map
    framework_map = {p: select_framework(p) for p in platforms}
    
    # Step 4: Generate hooks (LLM-enhanced)
    if delegate_task_fn and LLM_DELEGATION_AVAILABLE:
        hooks = await generate_hooks_llm(insights, tone, delegate_task_fn)
    else:
        from scripts.module1_pipeline import generate_hooks
        hooks = generate_hooks(insights, tone)
    
    # Step 5: Build script table
    script_table = build_script_table(insights, hooks)
    
    # Step 6: Generate captions
    captions = [format_caption(p, insights, hooks, script_table, tone) for p in platforms]
    
    # Assemble output
    from datetime import datetime
    output = PipelineOutput(
        metadata={
            "input_file": str(input_path),
            "tone_id": tone.tone_id,
            "platforms": platforms,
            "generated_at": datetime.now().isoformat(),
            "raw_char_count": len(raw_text),
            "cleaned_char_count": len(cleaned_text),
            "hooks_generated_by": "llm" if delegate_task_fn else "template"
        },
        cleaned_segments=segments,
        framework_map=framework_map,
        hooks=hooks,
        script_table=script_table,
        captions=captions
    )
    
    # Write output
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = write_output(output, output_dir)
    
    print(f"✅ Pipeline complete. Output: {output_file}")
    print(f"   Hooks: {len(output.hooks)} (via {'LLM' if delegate_task_fn else 'template'})")
    
    return output


# --- Module 2: LLM-Enhanced Radar ---

async def run_radar_llm(
    feeds_config_path: str,
    tone_config: str = "config/tone_of_voice.yaml",
    webhook_url: str | None = None,
    state_dir: str = "state",
    force_report: bool = False,
    delegate_task_fn = None
):
    """
    Run Module 2 radar with LLM-enhanced insight generation and draft posts.
    
    Args:
        feeds_config_path: Path to feeds.yaml
        tone_config: Path to tone config YAML
        webhook_url: Slack/Telegram webhook URL
        state_dir: State directory
        force_report: Send report even if no trends
        delegate_task_fn: Hermes delegate_task function
    """
    # Load configs
    with open(feeds_config_path, "r", encoding="utf-8") as f:
        feeds_data = json.load(f) if feeds_config_path.endswith(".json") else __import__("yaml").safe_load(f)
    
    # Handle YAML loading
    import yaml
    with open(feeds_config_path, "r", encoding="utf-8") as f:
        feeds_data = yaml.safe_load(f)
    
    feeds_config = FeedsConfig(**feeds_data)
    
    tone_path = Path(tone_config)
    if not tone_path.exists():
        tone_path = Path(__file__).parent.parent / "templates" / "tone_of_voice.yaml"
    tone = load_tone_profile_radar(tone_path)
    
    # Determine webhook URL
    import os
    if webhook_url is None:
        webhook_url = os.getenv(feeds_config.webhook_url_env)
    if not webhook_url:
        raise ValueError("No webhook URL provided")
    
    # Run radar with LLM-enhanced functions
    # We need to monkey-patch the generate_insights and draft_post calls
    # For simplicity, we'll recreate the run_radar logic here with LLM calls
    
    from scripts.module2_radar import (
        fetch_rss, fetch_youtube, fetch_twitter_list, fetch_google_trends,
        dedupe_candidates, compute_relevance, send_webhook,
        build_slack_payload, build_telegram_payload, format_relative_time
    )
    from datetime import datetime, timezone
    
    now = datetime.now(timezone.utc)
    state = StateManager(Path(state_dir))
    last_run = state.load_last_run()
    
    since = None
    if last_run.get("last_run_timestamp"):
        try:
            since = datetime.fromisoformat(last_run["last_run_timestamp"])
        except Exception:
            pass
    
    print(f"🔍 Starting LLM-enhanced radar scan for niche: {feeds_config.niche}")
    
    # Collect candidates (same as original)
    all_candidates = []
    
    import httpx
    async with httpx.AsyncClient() as session:
        for feed in feeds_config.rss_feeds:
            print(f"  📡 Fetching RSS: {feed.name}")
            candidates = await fetch_rss(session, feed, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)
        
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        for channel in feeds_config.youtube_channels:
            print(f"  ▶️ Fetching YouTube: {channel.name}")
            candidates = await fetch_youtube(session, channel, youtube_api_key, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)
        
        twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
        for tw_list in feeds_config.twitter_lists:
            print(f"  🐦 Fetching Twitter List: {tw_list.name}")
            candidates = await fetch_twitter_list(session, tw_list, twitter_bearer, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)
        
        for region in feeds_config.google_trends_regions:
            print(f"  📈 Fetching Google Trends: {region}")
            candidates = await fetch_google_trends(session, region, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)
    
    print(f"  📊 Raw candidates: {len(all_candidates)}")
    unique_candidates = dedupe_candidates(all_candidates)
    print(f"  🔄 After dedupe: {len(unique_candidates)}")
    
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    state.save_candidates(unique_candidates, timestamp)
    
    # Score and filter
    source_authority = {
        "The Verge AI": 0.95, "TechCrunch AI": 0.95, "The Information AI": 0.9,
        "Creator Economy Newsletter": 0.8, "Marketing AI Institute": 0.85,
        "a16z Consumer": 0.9, "Example Creator Education": 0.7,
        "Example AI Tools Review": 0.7, "Example Marketing Strategy": 0.7,
        "Top AI Creators": 0.8, "Creator Economy Leaders": 0.8,
        "Google Trends BR": 0.6, "Google Trends US": 0.6, "Google Trends PT": 0.5, "Google Trends GB": 0.5
    }
    
    scored = []
    for c in unique_candidates:
        score = compute_relevance(c, feeds_config.keywords, source_authority, now)
        if score >= feeds_config.materiality_threshold:
            scored.append((score, c))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    top_candidates = scored[:5]
    
    print(f"  ✅ Shortlisted: {len(top_candidates)} (threshold: {feeds_config.materiality_threshold})")
    
    # Enrich with LLM-enhanced generation
    enriched_items = []
    for i, (score, candidate) in enumerate(top_candidates):
        item_id = f"trend_{now.strftime('%Y%m%d')}_{i+1:03d}"
        
        # LLM-enhanced insights
        if delegate_task_fn and LLM_DELEGATION_AVAILABLE:
            exec_summary, key_insight, angle = await generate_insights_llm(candidate, feeds_config.niche, tone, delegate_task_fn)
        else:
            from scripts.module2_radar import generate_insights
            exec_summary, key_insight, angle = generate_insights(candidate, feeds_config.niche, tone)
        
        enriched = EnrichedItem(
            item_id=item_id,
            title=candidate.title,
            source=candidate.source_name,
            source_url=candidate.url,
            published_at=candidate.published_at,
            collected_at=now.isoformat(),
            score=score,
            score_breakdown={},
            keywords_matched=candidate.keywords_matched,
            executive_summary=exec_summary,
            key_insight=key_insight,
            suggested_angle=angle,
            draft_post="",
            platform=feeds_config.primary_platform,
            tone_id=tone.tone_id
        )
        enriched.niche = feeds_config.niche
        
        # LLM-enhanced draft post
        if delegate_task_fn and LLM_DELEGATION_AVAILABLE:
            enriched.draft_post = await draft_post_llm(enriched, tone, feeds_config.primary_platform, delegate_task_fn)
        else:
            from scripts.module2_radar import draft_post
            enriched.draft_post = draft_post(enriched, tone, feeds_config.primary_platform)
        
        enriched_items.append(enriched)
    
    state.save_shortlist(enriched_items, timestamp)
    
    # Send webhooks
    if enriched_items or force_report:
        print(f"  📤 Sending {len(enriched_items)} approval cards...")
        for item in enriched_items:
            if "slack.com" in webhook_url or "hooks.slack.com" in webhook_url:
                payload = build_slack_payload(item)
                success = await send_webhook(webhook_url, payload)
            else:
                chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
                payload = build_telegram_payload(item, chat_id)
                success = await send_webhook(webhook_url, payload, is_telegram=True, chat_id=chat_id)
            
            if success:
                print(f"    ✅ Sent: {item.title[:50]}...")
            else:
                print(f"    ❌ Failed: {item.title[:50]}...")
    else:
        print("  🔇 No material trends — silent tick")
    
    # Update state
    last_run["last_run_timestamp"] = now.isoformat()
    last_run["processed_item_ids"] = [item.item_id for item in enriched_items]
    last_run["source_checkpoints"]["radar"] = now.isoformat()
    state.save_last_run(last_run)
    
    print("✅ LLM-enhanced radar cycle complete")
    return enriched_items


# --- Example Hermes Skill Usage ---

HERMES_USAGE_EXAMPLE = '''
# In Hermes chat, after loading the skill:

# 1. Module 1 with LLM hooks
from scripts.hermes_entry import run_pipeline_llm

# Pass the delegate_task tool as a function
result = await run_pipeline_llm(
    input_path="transcripts/meeting.txt",
    tone_id="b2b_corporate",
    platforms=["instagram", "linkedin", "twitter", "youtube"],
    delegate_task_fn=delegate_task  # Hermes built-in tool
)

# 2. Module 2 with LLM insights + drafts
from scripts.hermes_entry import run_radar_llm

items = await run_radar_llm(
    feeds_config="config/feeds.yaml",
    tone_config="config/tone_of_voice.yaml",
    webhook_url=SLACK_WEBHOOK_URL,
    delegate_task_fn=delegate_task
)

# The delegate_task tool is automatically available in Hermes when this skill is loaded.
# Just pass it as the delegate_task_fn parameter.
'''

if __name__ == "__main__":
    print("This module is designed to be imported in Hermes Agent context.")
    print("See HERMES_USAGE_EXAMPLE for usage pattern.")
    print(f"\nLLM Delegation Available: {LLM_DELEGATION_AVAILABLE}")