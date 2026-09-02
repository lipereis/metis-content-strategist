#!/usr/bin/env python3
"""
Relevance scoring and deduplication utilities for Module 2 Radar.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


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


SOURCE_AUTHORITY = {
    # Tier 1: Primary sources
    "The Verge AI": 0.95,
    "TechCrunch AI": 0.95,
    "The Information AI": 0.90,
    "a16z Consumer": 0.90,

    # Tier 2: Trade publications
    "Creator Economy Newsletter": 0.80,
    "Marketing AI Institute": 0.85,
    "Example Creator Education": 0.70,
    "Example AI Tools Review": 0.70,
    "Example Marketing Strategy": 0.70,

    # Tier 3: Social / aggregated
    "Top AI Creators": 0.80,
    "Creator Economy Leaders": 0.80,

    # Algorithmic
    "Google Trends BR": 0.60,
    "Google Trends US": 0.60,
    "Google Trends PT": 0.50,
    "Google Trends GB": 0.50,
}


def compute_relevance(
    candidate: CandidateItem,
    niche_keywords: list[str],
    source_authority: dict[str, float] | None = None,
    now: datetime | None = None
) -> float:
    """
    Compute relevance score 0-1 based on weighted factors:
    - Keyword density (30%)
    - Source authority (20%)
    - Recency decay (20%)
    - Engagement velocity (15%)
    - Cross-source corroboration (15%)
    """
    if source_authority is None:
        source_authority = SOURCE_AUTHORITY
    if now is None:
        now = datetime.now(timezone.utc)

    score = 0.0
    text = f"{candidate.title} {candidate.content_preview}".lower()

    # 1. Keyword density (30%)
    matches = sum(1 for kw in niche_keywords if kw.lower() in text)
    kw_score = min(matches / max(len(niche_keywords), 1), 1.0)
    score += 0.30 * kw_score

    # 2. Source authority (20%)
    authority = source_authority.get(candidate.source_name, 0.5)
    score += 0.20 * authority

    # 3. Recency decay (20%) - exponential decay over scan window (default 168h = 1 week)
    try:
        pub_date = datetime.fromisoformat(candidate.published_at.replace("Z", "+00:00"))
        hours_ago = (now - pub_date).total_seconds() / 3600
        recency_score = max(0.0, 1.0 - hours_ago / 168.0)
    except Exception:
        recency_score = 0.5
    score += 0.20 * recency_score

    # 4. Engagement velocity (15%)
    eng = candidate.engagement or {}
    if eng:
        total_eng = (
            eng.get("likes", 0) +
            eng.get("retweets", 0) * 2 +
            eng.get("replies", 0) * 1.5 +
            eng.get("quotes", 0) * 1.5
        )
        # Log scale normalization: 10k engagements ≈ 1.0
        eng_score = min(math.log10(total_eng + 1) / 4.0, 1.0)
    else:
        eng_score = 0.3  # Neutral for sources without engagement data
    score += 0.15 * eng_score

    # 5. Cross-source corroboration (15%)
    # In production, this would check if same topic appears in multiple sources
    # For now, give a modest bonus for items with multiple keyword matches
    cross_score = min(len(candidate.keywords_matched) / 3.0, 1.0) * 0.5 + 0.5
    score += 0.15 * cross_score

    return min(score, 1.0)


def jaccard_similarity(set1: set[str], set2: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union > 0 else 0.0


def dedupe_candidates(candidates: list[CandidateItem], title_threshold: float = 0.8) -> list[CandidateItem]:
    """
    Deduplicate candidates by URL canonicalization and title similarity.
    """
    seen_urls = set()
    seen_titles: list[set[str]] = []
    unique = []

    for c in candidates:
        # Normalize URL: remove query params, fragments, trailing slashes
        norm_url = c.url.split("?")[0].split("#")[0].rstrip("/")
        if norm_url in seen_urls:
            continue

        # Title similarity using Jaccard on word sets
        title_words = set(c.title.lower().split())
        is_duplicate = False
        for seen_title_words in seen_titles:
            if jaccard_similarity(title_words, seen_title_words) > title_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_urls.add(norm_url)
            seen_titles.append(title_words)
            unique.append(c)

    return unique


def rank_candidates(candidates: list[CandidateItem], niche_keywords: list[str], top_k: int = 5) -> list[tuple[float, CandidateItem]]:
    """Score and rank candidates, return top-k."""
    scored = []
    for c in candidates:
        score = compute_relevance(c, niche_keywords)
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:top_k]