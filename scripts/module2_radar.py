#!/usr/bin/env python3
"""
Module 2 Radar — Trend Monitoring & Approval Cards
Usage: python module2_radar.py --feeds config/feeds.yaml --webhook-url $SLACK_WEBHOOK_URL
"""

import argparse
import asyncio
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import yaml
from pydantic import BaseModel, Field

# Optional: LLM delegation (requires Hermes delegate_task tool)
try:
    from llm_delegation import (
        build_insight_generation_task,
        build_draft_post_task,
        InsightSchema,
        DraftPostSchema
    )
    LLM_DELEGATION_AVAILABLE = True
except ImportError:
    LLM_DELEGATION_AVAILABLE = False


# --- Pydantic Models ---

class FeedConfig(BaseModel):
    name: str
    url: str
    category: str


class YouTubeChannelConfig(BaseModel):
    channel_id: str
    name: str
    keywords: list[str] = []


class TwitterListConfig(BaseModel):
    list_id: str
    name: str
    description: str = ""


class FeedsConfig(BaseModel):
    niche: str
    keywords: list[str]
    rss_feeds: list[FeedConfig]
    youtube_channels: list[YouTubeChannelConfig]
    twitter_lists: list[TwitterListConfig]
    google_trends_regions: list[str]
    scan_window_hours: int = 24
    max_items_per_source: int = 10
    materiality_threshold: float = 0.7
    primary_platform: str = "linkedin"
    webhook_url_env: str = "SLACK_WEBHOOK_URL"


class ToneProfile(BaseModel):
    tone_id: str
    display_name: str
    language: str
    persona: dict
    structure_preferences: dict
    platform_overrides: dict = {}


@dataclass
class CandidateItem:
    source: str
    source_name: str
    title: str
    url: str
    published_at: str
    content_preview: str
    keywords_matched: list[str]
    engagement: dict | None = None


@dataclass
class EnrichedItem:
    item_id: str
    title: str
    source: str
    source_url: str
    published_at: str
    collected_at: str
    score: float
    score_breakdown: dict
    keywords_matched: list[str]
    executive_summary: str
    key_insight: str
    suggested_angle: str
    draft_post: str
    platform: str
    tone_id: str
    status: str = "pending_approval"
    approval_history: list = None


class StateManager:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.last_run_file = self.state_dir / "last_run.json"

    def load_last_run(self) -> dict:
        if self.last_run_file.exists():
            with open(self.last_run_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "last_run_timestamp": None,
            "processed_item_ids": [],
            "source_checkpoints": {},
            "errors": []
        }

    def save_last_run(self, state: dict):
        with open(self.last_run_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

    def save_candidates(self, candidates: list[CandidateItem], timestamp: str):
        file = self.state_dir / f"candidates_{timestamp}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in candidates], f, ensure_ascii=False, indent=2)

    def save_shortlist(self, items: list[EnrichedItem], timestamp: str):
        file = self.state_dir / f"shortlist_{timestamp}.json"
        with open(file, "w", encoding="utf-8") as f:
            json.dump([asdict(i) for i in items], f, ensure_ascii=False, indent=2)


# --- Feed Collectors ---

async def fetch_rss(session: httpx.AsyncClient, feed: FeedConfig, since: datetime | None, max_items: int) -> list[CandidateItem]:
    """Fetch and parse RSS/Atom feed."""
    try:
        resp = await session.get(feed.url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        content = resp.text

        # Simple regex-based parsing (for production, use feedparser)
        items = []
        # Match <item> or <entry> blocks
        entry_pattern = r"<(?:item|entry)>(.*?)</(?:item|entry)>"
        entries = re.findall(entry_pattern, content, re.DOTALL)

        for entry in entries[:max_items]:
            title_match = re.search(r"<title[^>]*><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>", entry, re.DOTALL)
            link_match = re.search(r"<link[^>]*><!\[CDATA\[(.*?)\]\]></link>|<link[^>]*>(.*?)</link>|<link[^>]*href=['\"](.*?)['\"]", entry)
            pub_match = re.search(r"<pubDate[^>]*><!\[CDATA\[(.*?)\]\]></pubDate>|<pubDate[^>]*>(.*?)</pubDate>|<published[^>]*><!\[CDATA\[(.*?)\]\]></published>|<published[^>]*>(.*?)</published>", entry, re.DOTALL)
            desc_match = re.search(r"<description[^>]*><!\[CDATA\[(.*?)\]\]></description>|<description[^>]*>(.*?)</description>|<summary[^>]*><!\[CDATA\[(.*?)\]\]></summary>|<summary[^>]*>(.*?)</summary>", entry, re.DOTALL)

            title = (title_match.group(1) or title_match.group(2) or "").strip() if title_match else ""
            url = (link_match.group(1) or link_match.group(2) or link_match.group(3) or "").strip() if link_match else ""
            pub_str = (pub_match.group(1) or pub_match.group(2) or pub_match.group(3) or pub_match.group(4) or "").strip() if pub_match else ""
            preview = (desc_match.group(1) or desc_match.group(2) or desc_match.group(3) or desc_match.group(4) or "").strip() if desc_match else ""

            # Clean HTML from preview
            preview = re.sub(r"<[^>]+>", "", preview)
            preview = re.sub(r"\s+", " ", preview)[:500]

            # Parse date
            published_at = None
            if pub_str:
                try:
                    # Try multiple formats
                    for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]:
                        try:
                            published_at = datetime.strptime(pub_str, fmt)
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass

            # Filter by date
            if since and published_at and published_at < since:
                continue

            # Keyword matching
            text = f"{title} {preview}".lower()
            matched = [kw for kw in feed.keywords if kw.lower() in text] if hasattr(feed, 'keywords') else []
            # Use global keywords from config
            # (passed via closure or global)

            items.append(CandidateItem(
                source="rss",
                source_name=feed.name,
                title=title,
                url=url,
                published_at=published_at.isoformat() if published_at else datetime.now(timezone.utc).isoformat(),
                content_preview=preview,
                keywords_matched=matched
            ))

        return items
    except Exception as e:
        print(f"Error fetching RSS {feed.name}: {e}", file=sys.stderr)
        return []


async def fetch_youtube(session: httpx.AsyncClient, channel: YouTubeChannelConfig, api_key: str, since: datetime | None, max_items: int) -> list[CandidateItem]:
    """Fetch recent videos from YouTube channel."""
    if not api_key:
        return []

    try:
        # Get uploads playlist ID
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "contentDetails", "id": channel.channel_id, "key": api_key}
        resp = await session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("items"):
            return []

        uploads_playlist = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Fetch playlist items
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": uploads_playlist,
            "maxResults": max_items,
            "key": api_key
        }
        resp = await session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for item in data.get("items", []):
            snippet = item["snippet"]
            published_at = datetime.fromisoformat(snippet["publishedAt"].replace("Z", "+00:00"))

            if since and published_at < since:
                continue

            title = snippet["title"]
            video_id = snippet["resourceId"]["videoId"]
            url = f"https://www.youtube.com/watch?v={video_id}"
            preview = snippet.get("description", "")[:500]

            text = f"{title} {preview}".lower()
            matched = [kw for kw in channel.keywords if kw.lower() in text]

            items.append(CandidateItem(
                source="youtube",
                source_name=channel.name,
                title=title,
                url=url,
                published_at=published_at.isoformat(),
                content_preview=preview,
                keywords_matched=matched,
                engagement={"platform": "youtube", "video_id": video_id}
            ))

        return items
    except Exception as e:
        print(f"Error fetching YouTube {channel.name}: {e}", file=sys.stderr)
        return []


async def fetch_twitter_list(session: httpx.AsyncClient, twitter_list: TwitterListConfig, bearer_token: str, since: datetime | None, max_items: int) -> list[CandidateItem]:
    """Fetch tweets from Twitter List."""
    if not bearer_token:
        return []

    try:
        url = f"https://api.twitter.com/2/lists/{twitter_list.list_id}/tweets"
        headers = {"Authorization": f"Bearer {bearer_token}"}
        params = {
            "max_results": min(max_items, 100),
            "tweet.fields": "created_at,public_metrics,author_id",
            "expansions": "author_id"
        }
        resp = await session.get(url, headers=headers, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        items = []
        for tweet in data.get("data", []):
            created_at = datetime.fromisoformat(tweet["created_at"].replace("Z", "+00:00"))

            if since and created_at < since:
                continue

            text = tweet["text"]
            # Extract URL from tweet if present
            urls = re.findall(r"https?://\S+", text)
            url = urls[0] if urls else f"https://twitter.com/i/web/status/{tweet['id']}"

            metrics = tweet.get("public_metrics", {})
            engagement = {
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0)
            }

            items.append(CandidateItem(
                source="twitter",
                source_name=twitter_list.name,
                title=text[:100] + ("..." if len(text) > 100 else ""),
                url=url,
                published_at=created_at.isoformat(),
                content_preview=text[:500],
                keywords_matched=[],  # Will be filled by caller
                engagement=engagement
            ))

        return items
    except Exception as e:
        print(f"Error fetching Twitter list {twitter_list.name}: {e}", file=sys.stderr)
        return []


async def fetch_google_trends(session: httpx.AsyncClient, region: str, since: datetime | None, max_items: int) -> list[CandidateItem]:
    """Fetch Google Trends daily trends (unofficial)."""
    try:
        # Use trends.google.com/trends/api/dailytrends (unofficial)
        url = f"https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-180&geo={region}"
        resp = await session.get(url, timeout=30)
        # Response starts with ")]}'\n" - skip it
        text = resp.text
        if text.startswith(")]}'"):
            text = text[5:]
        data = json.loads(text)

        items = []
        for trend_day in data.get("default", {}).get("trendingSearchesDays", []):
            for trend in trend_day.get("trendingSearches", [])[:max_items]:
                title = trend.get("title", {}).get("query", "")
                traffic = trend.get("formattedTraffic", "")
                url = f"https://trends.google.com/trends/explore?q={title}&geo={region}"

                items.append(CandidateItem(
                    source="google_trends",
                    source_name=f"Google Trends {region}",
                    title=title,
                    url=url,
                    published_at=datetime.now(timezone.utc).isoformat(),
                    content_preview=f"Trending in {region}: {traffic} searches",
                    keywords_matched=[],
                    engagement={"region": region, "traffic": traffic}
                ))

        return items
    except Exception as e:
        print(f"Error fetching Google Trends {region}: {e}", file=sys.stderr)
        return []


# --- Scoring & Filtering ---

def compute_relevance(candidate: CandidateItem, niche_keywords: list[str], source_authority: dict, now: datetime) -> float:
    """Compute relevance score 0-1."""
    score = 0.0
    text = f"{candidate.title} {candidate.content_preview}".lower()

    # Keyword density (30%)
    matches = sum(1 for kw in niche_keywords if kw.lower() in text)
    kw_score = min(matches / max(len(niche_keywords), 1), 1.0)
    score += 0.3 * kw_score

    # Source authority (20%)
    authority = source_authority.get(candidate.source_name, 0.5)
    score += 0.2 * authority

    # Recency decay (20%)
    try:
        pub_date = datetime.fromisoformat(candidate.published_at.replace("Z", "+00:00"))
        hours_ago = (now - pub_date).total_seconds() / 3600
        recency_score = max(0, 1 - hours_ago / 168)  # Decay over 1 week
    except Exception:
        recency_score = 0.5
    score += 0.2 * recency_score

    # Engagement velocity (15%)
    eng = candidate.engagement or {}
    if eng:
        total_eng = eng.get("likes", 0) + eng.get("retweets", 0) * 2 + eng.get("replies", 0) * 1.5
        # Normalize (log scale)
        import math
        eng_score = min(math.log10(total_eng + 1) / 4, 1.0)  # 10k = ~1.0
    else:
        eng_score = 0.3
    score += 0.15 * eng_score

    # Cross-source corroboration (15%) - simplified: bonus if same keywords appear in multiple sources
    # This would need cross-reference in production
    score += 0.15 * 0.5

    return min(score, 1.0)


def dedupe_candidates(candidates: list[CandidateItem]) -> list[CandidateItem]:
    """Deduplicate by URL and title similarity."""
    seen_urls = set()
    seen_titles = []
    unique = []

    for c in candidates:
        # Normalize URL
        norm_url = c.url.split("?")[0].rstrip("/")
        if norm_url in seen_urls:
            continue

        # Title similarity (Jaccard on words)
        title_words = set(c.title.lower().split())
        is_dup = False
        for seen_title in seen_titles:
            seen_words = set(seen_title.lower().split())
            if title_words and seen_words:
                intersection = len(title_words & seen_words)
                union = len(title_words | seen_words)
                if intersection / union > 0.8:
                    is_dup = True
                    break

        if not is_dup:
            seen_urls.add(norm_url)
            seen_titles.append(c.title)
            unique.append(c)

    return unique


# --- Insight Generation & Drafting ---

ANGLES = ["Contrarian", "Educational", "Case Study", "Prediction", "Framework"]

def generate_insights(candidate: CandidateItem, niche: str, tone: ToneProfile) -> tuple[str, str, str]:
    """Generate executive summary, key insight, and suggested angle.
    
    Uses LLM delegation if available (Hermes delegate_task), falls back to templates.
    """
    # Try LLM delegation first (would need delegate_task_fn passed in)
    # For CLI usage, fall back to templates
    pass
    
    # Template fallback (current implementation)
    angle = "Contrarian"  # Default

    executive_summary = (
        f"{candidate.title}. "
        f"This signals a shift in {niche} that creators and businesses should monitor. "
        f"Early movers will capture disproportionate value."
    )

    key_insight = (
        f"The underlying trend in {candidate.source_name} reveals {niche} is approaching "
        f"an inflection point — adapt now or lose relevance."
    )

    return executive_summary, key_insight, angle


def generate_insights_llm(candidate: CandidateItem, niche: str, tone: ToneProfile, delegate_task_fn) -> tuple[str, str, str]:
    """Generate insights using LLM delegation (for use within Hermes)."""
    if not LLM_DELEGATION_AVAILABLE:
        return generate_insights(candidate, niche, tone)
    
    # Build delegation task
    tone_dict = tone.model_dump()
    trend_item = {
        "title": candidate.title,
        "source": candidate.source_name,
        "published_at": candidate.published_at,
        "keywords_matched": candidate.keywords_matched,
        "content_preview": candidate.content_preview,
        "engagement": candidate.engagement or {}
    }
    task = build_insight_generation_task(trend_item, niche, tone_dict)
    
    # Delegate to subagent
    result = delegate_task_fn(
        goal=task["goal"],
        context=task["context"],
        output_schema=task["output_schema"]
    )
    
    # Parse validated output
    validated = InsightSchema.model_validate_json(result)
    
    return validated.executive_summary, validated.key_insight, validated.suggested_angle


def draft_post(item: EnrichedItem, tone: ToneProfile, platform: str) -> str:
    """Generate platform-specific draft post.
    
    Uses LLM delegation if available (Hermes delegate_task), falls back to templates.
    """
    # Template fallback (current implementation)
    platform_override = tone.platform_overrides.get(platform, {})

    # Base draft from key insight
    base = f"{item.key_insight}\n\n{item.executive_summary}\n\nWhat's your take on this shift? 👇"

    # Apply platform formatting (simplified)
    if platform == "linkedin":
        return f"{item.title}\n\n{base}\n\n#AI #ContentStrategy #CreatorEconomy"
    elif platform in ["instagram", "tiktok"]:
        return f"{item.title} 🚀\n\n{base}\n\n#{item.keywords_matched[0].replace(' ', '') if item.keywords_matched else 'Trending'} #CreatorTools"
    elif platform == "twitter":
        return f"1/3 {item.title}\n\n2/3 {item.key_insight}\n\n3/3 {item.executive_summary}\n\nThoughts? 🧵"
    else:
        return base


def draft_post_llm(item: EnrichedItem, tone: ToneProfile, platform: str, delegate_task_fn) -> str:
    """Generate draft post using LLM delegation (for use within Hermes)."""
    if not LLM_DELEGATION_AVAILABLE:
        return draft_post(item, tone, platform)
    
    # Build delegation task
    tone_dict = tone.model_dump()
    item_dict = {
        "key_insight": item.key_insight,
        "executive_summary": item.executive_summary,
        "source": item.source,
        "suggested_angle": item.suggested_angle
    }
    task = build_draft_post_task(item_dict, item.niche if hasattr(item, 'niche') else "", platform, tone_dict)
    
    # Delegate to subagent
    result = delegate_task_fn(
        goal=task["goal"],
        context=task["context"],
        output_schema=task["output_schema"]
    )
    
    # Parse validated output
    validated = DraftPostSchema.model_validate_json(result)
    
    return validated.draft_post


# --- Webhook Delivery ---

def build_slack_payload(item: EnrichedItem) -> dict:
    """Build Slack Block Kit payload."""
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📰 {item.title}", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fonte:* {item.source} • {format_relative_time(item.published_at)}\n"
                            f"*Por que importa:* {item.executive_summary}\n\n"
                            f"*✍️ Sugestão de Post:*\n{item.draft_post}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ Aprovar", "emoji": True}, "style": "primary", "value": f"approve_{item.item_id}", "action_id": f"approve_{item.item_id}"},
                    {"type": "button", "text": {"type": "plain_text", "text": "✏️ Pedir Alteração", "emoji": True}, "value": f"edit_{item.item_id}", "action_id": f"edit_{item.item_id}"},
                    {"type": "button", "text": {"type": "plain_text", "text": "🗑️ Descartar", "emoji": True}, "style": "danger", "value": f"discard_{item.item_id}", "action_id": f"discard_{item.item_id}"}
                ]
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"🤖 Content Strategist Agent • Item ID: {item.item_id} • Score: {item.score:.2f} • Angle: {item.suggested_angle}"}]
            }
        ],
        "text": f"Nova tendência detectada: {item.title} — Aprovar, Editar ou Descartar"
    }


def build_telegram_payload(item: EnrichedItem, chat_id: str) -> dict:
    """Build Telegram Bot API payload."""
    return {
        "chat_id": chat_id,
        "text": f"📰 *{item.title}*\n\n*Fonte:* {item.source} • {format_relative_time(item.published_at)}\n*Por que importa:* {item.executive_summary}\n\n*✍️ Sugestão de Post:*\n{item.draft_post}",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Aprovar", "callback_data": f"approve_{item.item_id}"},
                {"text": "✏️ Pedir Alteração", "callback_data": f"edit_{item.item_id}"},
                {"text": "🗑️ Descartar", "callback_data": f"discard_{item.item_id}"}
            ]]
        }
    }


def format_relative_time(iso_string: str) -> str:
    """Format ISO timestamp as relative time in Portuguese."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - dt
        hours = diff.total_seconds() / 3600
        if hours < 1:
            mins = int(diff.total_seconds() / 60)
            return f"{mins}min atrás"
        elif hours < 24:
            return f"{int(hours)}h atrás"
        else:
            days = int(hours / 24)
            return f"{days}d atrás"
    except Exception:
        return "recentemente"


async def send_webhook(webhook_url: str, payload: dict, is_telegram: bool = False, chat_id: str = "") -> bool:
    """Send webhook payload."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if is_telegram:
                # Telegram uses bot token in URL: https://api.telegram.org/bot{token}/sendMessage
                resp = await client.post(webhook_url, json=payload)
            else:
                # Slack incoming webhook
                resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            return True
    except Exception as e:
        print(f"Webhook delivery failed: {e}", file=sys.stderr)
        return False


# --- Main Radar Logic ---

async def run_radar(feeds_config: FeedsConfig, tone: ToneProfile, webhook_url: str, state: StateManager, force_report: bool = False):
    """Execute one radar cycle."""
    now = datetime.now(timezone.utc)
    last_run = state.load_last_run()
    since = None
    if last_run.get("last_run_timestamp"):
        try:
            since = datetime.fromisoformat(last_run["last_run_timestamp"])
        except Exception:
            pass

    print(f"🔍 Starting radar scan for niche: {feeds_config.niche}")
    print(f"   Since: {since.isoformat() if since else 'beginning of time'}")
    print(f"   Window: {feeds_config.scan_window_hours}h")

    # Collect candidates from all sources
    all_candidates = []

    async with httpx.AsyncClient() as session:
        # RSS feeds
        for feed in feeds_config.rss_feeds:
            print(f"  📡 Fetching RSS: {feed.name}")
            candidates = await fetch_rss(session, feed, since, feeds_config.max_items_per_source)
            # Add global keyword matching
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)

        # YouTube
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        for channel in feeds_config.youtube_channels:
            print(f"  ▶️ Fetching YouTube: {channel.name}")
            candidates = await fetch_youtube(session, channel, youtube_api_key, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)

        # Twitter
        twitter_bearer = os.getenv("TWITTER_BEARER_TOKEN")
        for tw_list in feeds_config.twitter_lists:
            print(f"  🐦 Fetching Twitter List: {tw_list.name}")
            candidates = await fetch_twitter_list(session, tw_list, twitter_bearer, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)

        # Google Trends
        for region in feeds_config.google_trends_regions:
            print(f"  📈 Fetching Google Trends: {region}")
            candidates = await fetch_google_trends(session, region, since, feeds_config.max_items_per_source)
            for c in candidates:
                text = f"{c.title} {c.content_preview}".lower()
                c.keywords_matched = [kw for kw in feeds_config.keywords if kw.lower() in text]
            all_candidates.extend(candidates)

    print(f"  📊 Raw candidates: {len(all_candidates)}")

    # Deduplicate
    unique_candidates = dedupe_candidates(all_candidates)
    print(f"  🔄 After dedupe: {len(unique_candidates)}")

    # Save raw candidates
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
    top_candidates = scored[:5]  # Top 5

    print(f"  ✅ Shortlisted: {len(top_candidates)} (threshold: {feeds_config.materiality_threshold})")

    # Enrich and generate drafts
    enriched_items = []
    for i, (score, candidate) in enumerate(top_candidates):
        item_id = f"trend_{now.strftime('%Y%m%d')}_{i+1:03d}"
        exec_summary, key_insight, angle = generate_insights(candidate, feeds_config.niche, tone)

        enriched = EnrichedItem(
            item_id=item_id,
            title=candidate.title,
            source=candidate.source_name,
            source_url=candidate.url,
            published_at=candidate.published_at,
            collected_at=now.isoformat(),
            score=score,
            score_breakdown={},  # Could add detailed breakdown
            keywords_matched=candidate.keywords_matched,
            executive_summary=exec_summary,
            key_insight=key_insight,
            suggested_angle=angle,
            draft_post="",  # Will fill below
            platform=feeds_config.primary_platform,
            tone_id=tone.tone_id
        )
        # Add niche for LLM delegation context
        enriched.niche = feeds_config.niche
        enriched.draft_post = draft_post(enriched, tone, feeds_config.primary_platform)
        enriched_items.append(enriched)

    # Save shortlist
    state.save_shortlist(enriched_items, timestamp)

    # Send webhooks
    if enriched_items or force_report:
        print(f"  📤 Sending {len(enriched_items)} approval cards...")
        for item in enriched_items:
            if "slack.com" in webhook_url or "hooks.slack.com" in webhook_url:
                payload = build_slack_payload(item)
                success = await send_webhook(webhook_url, payload)
            else:
                # Assume Telegram
                chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
                payload = build_telegram_payload(item, chat_id)
                success = await send_webhook(webhook_url, payload, is_telegram=True, chat_id=chat_id)

            if success:
                print(f"    ✅ Sent: {item.title[:50]}...")
            else:
                print(f"    ❌ Failed: {item.title[:50]}...")
    else:
        print("  🔇 No material trends — silent tick")

    # Update last run state
    last_run["last_run_timestamp"] = now.isoformat()
    last_run["processed_item_ids"] = [item.item_id for item in enriched_items]
    last_run["source_checkpoints"]["radar"] = now.isoformat()
    state.save_last_run(last_run)

    print("✅ Radar cycle complete")


def load_tone_profile(tone_path: Path) -> ToneProfile:
    with open(tone_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ToneProfile(**data)


def main():
    parser = argparse.ArgumentParser(description="Module 2: Trend Radar → Approval Cards")
    parser.add_argument("--feeds", required=True, help="Path to feeds.yaml config")
    parser.add_argument("--tone-config", default="config/tone_of_voice.yaml", help="Path to tone config YAML")
    parser.add_argument("--webhook-url", help="Webhook URL (Slack or Telegram). Can also use env var from feeds config.")
    parser.add_argument("--state-dir", default="state", help="State directory")
    parser.add_argument("--force-report", action="store_true", help="Send report even if no trends")
    args = parser.parse_args()

    # Load configs
    feeds_path = Path(args.feeds)
    with open(feeds_path, "r", encoding="utf-8") as f:
        feeds_data = yaml.safe_load(f)
    feeds_config = FeedsConfig(**feeds_data)

    tone_path = Path(args.tone_config)
    if not tone_path.exists():
        tone_path = Path(__file__).parent.parent / "templates" / "tone_of_voice.yaml"
    tone = load_tone_profile(tone_path)

    # Determine webhook URL
    webhook_url = args.webhook_url or os.getenv(feeds_config.webhook_url_env)
    if not webhook_url:
        print("Error: No webhook URL provided. Use --webhook-url or set env var.", file=sys.stderr)
        sys.exit(1)

    # Run radar
    state = StateManager(Path(args.state_dir))
    asyncio.run(run_radar(feeds_config, tone, webhook_url, state, args.force_report))


if __name__ == "__main__":
    main()