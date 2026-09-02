"""
Utility modules for Content Strategist & Viral Scriptwriter Agent.
"""

from .feeds import fetch_rss, fetch_youtube, fetch_twitter_list, fetch_google_trends, collect_all_feeds, CandidateItem
from .scoring import compute_relevance, dedupe_candidates, rank_candidates, jaccard_similarity, SOURCE_AUTHORITY
from .formatting import (
    format_instagram,
    format_tiktok,
    format_tiktok_enhanced,
    format_linkedin,
    format_twitter_thread,
    format_threads,
    format_youtube,
    format_newsletter,
    format_for_platform,
    apply_tone_filters,
    get_platform_tone,
    ToneProfile,
    ScriptData,
    TikTokOverlaySpec,
    TikTokSoundCluster,
    ThreadsPost,
    NewsletterEmail,
    FORMATTERS
)
# llm_delegation is in parent scripts directory, not utils
try:
    import sys
    from pathlib import Path
    scripts_dir = Path(__file__).parent.parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from llm_delegation import (
        build_hook_generation_task,
        build_insight_generation_task,
        build_draft_post_task,
        HooksOutputSchema,
        InsightSchema,
        DraftPostSchema,
        LLM_DELEGATION_AVAILABLE
    )
except ImportError:
    # Fallback if not available
    build_hook_generation_task = None
    build_insight_generation_task = None
    build_draft_post_task = None
    HooksOutputSchema = None
    InsightSchema = None
    DraftPostSchema = None
    LLM_DELEGATION_AVAILABLE = False

__all__ = [
    # feeds
    "fetch_rss",
    "fetch_youtube",
    "fetch_twitter_list",
    "fetch_google_trends",
    "collect_all_feeds",
    "CandidateItem",
    # scoring
    "compute_relevance",
    "dedupe_candidates",
    "rank_candidates",
    "jaccard_similarity",
    "SOURCE_AUTHORITY",
    # formatting
    "format_instagram",
    "format_tiktok",
    "format_tiktok_enhanced",
    "format_linkedin",
    "format_twitter_thread",
    "format_threads",
    "format_youtube",
    "format_newsletter",
    "format_for_platform",
    "apply_tone_filters",
    "get_platform_tone",
    "ToneProfile",
    "ScriptData",
    "TikTokOverlaySpec",
    "TikTokSoundCluster",
    "ThreadsPost",
    "NewsletterEmail",
    "FORMATTERS",
    # llm_delegation
    "build_hook_generation_task",
    "build_insight_generation_task",
    "build_draft_post_task",
    "HooksOutputSchema",
    "InsightSchema",
    "DraftPostSchema",
    "LLM_DELEGATION_AVAILABLE",
]