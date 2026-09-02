#!/usr/bin/env python3
"""
Feed fetching utilities for Module 2 Radar.
"""

import asyncio
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx


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


async def fetch_rss(session: httpx.AsyncClient, name: str, url: str, since: datetime | None, max_items: int, keywords: list[str]) -> list[CandidateItem]:
    """Fetch and parse RSS/Atom feed."""
    try:
        resp = await session.get(url, timeout=30, follow_redirects=True)
        resp.raise_for_status()
        content = resp.text

        items = []
        entry_pattern = r"<(?:item|entry)>(.*?)</(?:item|entry)>"
        entries = re.findall(entry_pattern, content, re.DOTALL)

        for entry in entries[:max_items]:
            title_match = re.search(r"<title[^>]*><!\[CDATA\[(.*?)\]\]></title>|<title[^>]*>(.*?)</title>", entry, re.DOTALL)
            link_match = re.search(r"<link[^>]*><!\[CDATA\[(.*?)\]\]></link>|<link[^>]*>(.*?)</link>|<link[^>]*href=['\"](.*?)['\"]", entry)
            pub_match = re.search(r"<pubDate[^>]*><!\[CDATA\[(.*?)\]\]></pubDate>|<pubDate[^>]*>(.*?)</pubDate>|<published[^>]*><!\[CDATA\[(.*?)\]\]></published>|<published[^>]*>(.*?)</published>", entry, re.DOTALL)
            desc_match = re.search(r"<description[^>]*><!\[CDATA\[(.*?)\]\]></description>|<description[^>]*>(.*?)</description>|<summary[^>]*><!\[CDATA\[(.*?)\]\]></summary>|<summary[^>]*>(.*?)</summary>", entry, re.DOTALL)

            title = (title_match.group(1) or title_match.group(2) or "").strip() if title_match else ""
            url_match = (link_match.group(1) or link_match.group(2) or link_match.group(3) or "").strip() if link_match else ""
            pub_str = (pub_match.group(1) or pub_match.group(2) or pub_match.group(3) or pub_match.group(4) or "").strip() if pub_match else ""
            preview = (desc_match.group(1) or desc_match.group(2) or desc_match.group(3) or desc_match.group(4) or "").strip() if desc_match else ""

            preview = re.sub(r"<[^>]+>", "", preview)
            preview = re.sub(r"\s+", " ", preview)[:500]

            published_at = None
            if pub_str:
                for fmt in ["%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        published_at = datetime.strptime(pub_str, fmt)
                        break
                    except ValueError:
                        continue

            if since and published_at and published_at < since:
                continue

            text = f"{title} {preview}".lower()
            matched = [kw for kw in keywords if kw.lower() in text]

            items.append(CandidateItem(
                source="rss",
                source_name=name,
                title=title,
                url=url_match,
                published_at=published_at.isoformat() if published_at else datetime.now(timezone.utc).isoformat(),
                content_preview=preview,
                keywords_matched=matched
            ))

        return items
    except Exception as e:
        print(f"Error fetching RSS {name}: {e}")
        return []


async def fetch_youtube(session: httpx.AsyncClient, channel_id: str, name: str, api_key: str, channel_keywords: list[str], since: datetime | None, max_items: int, global_keywords: list[str]) -> list[CandidateItem]:
    """Fetch recent videos from YouTube channel."""
    if not api_key:
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "contentDetails", "id": channel_id, "key": api_key}
        resp = await session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("items"):
            return []

        uploads_playlist = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

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
            matched = [kw for kw in (channel_keywords + global_keywords) if kw.lower() in text]

            items.append(CandidateItem(
                source="youtube",
                source_name=name,
                title=title,
                url=url,
                published_at=published_at.isoformat(),
                content_preview=preview,
                keywords_matched=matched,
                engagement={"platform": "youtube", "video_id": video_id}
            ))

        return items
    except Exception as e:
        print(f"Error fetching YouTube {name}: {e}")
        return []


async def fetch_twitter_list(session: httpx.AsyncClient, list_id: str, name: str, bearer_token: str, since: datetime | None, max_items: int, global_keywords: list[str]) -> list[CandidateItem]:
    """Fetch tweets from Twitter List."""
    if not bearer_token:
        return []

    try:
        url = f"https://api.twitter.com/2/lists/{list_id}/tweets"
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
            urls = re.findall(r"https?://\S+", text)
            url = urls[0] if urls else f"https://twitter.com/i/web/status/{tweet['id']}"

            metrics = tweet.get("public_metrics", {})
            engagement = {
                "likes": metrics.get("like_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "replies": metrics.get("reply_count", 0),
                "quotes": metrics.get("quote_count", 0)
            }

            text_lower = text.lower()
            matched = [kw for kw in global_keywords if kw.lower() in text_lower]

            items.append(CandidateItem(
                source="twitter",
                source_name=name,
                title=text[:100] + ("..." if len(text) > 100 else ""),
                url=url,
                published_at=created_at.isoformat(),
                content_preview=text[:500],
                keywords_matched=matched,
                engagement=engagement
            ))

        return items
    except Exception as e:
        print(f"Error fetching Twitter list {name}: {e}")
        return []


async def fetch_google_trends(session: httpx.AsyncClient, region: str, since: datetime | None, max_items: int) -> list[CandidateItem]:
    """Fetch Google Trends daily trends (unofficial)."""
    try:
        url = f"https://trends.google.com/trends/api/dailytrends?hl=en-US&tz=-180&geo={region}"
        resp = await session.get(url, timeout=30)
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
        print(f"Error fetching Google Trends {region}: {e}")
        return []


async def collect_all_feeds(feeds_config: dict, since: datetime | None, max_items: int, global_keywords: list[str]) -> list[CandidateItem]:
    """Collect candidates from all configured feed sources."""
    all_candidates = []

    async with httpx.AsyncClient() as session:
        # RSS feeds
        for feed in feeds_config.get("rss_feeds", []):
            candidates = await fetch_rss(
                session,
                feed["name"],
                feed["url"],
                since,
                max_items,
                global_keywords
            )
            all_candidates.extend(candidates)

        # YouTube
        youtube_api_key = feeds_config.get("youtube_api_key") or None
        for channel in feeds_config.get("youtube_channels", []):
            candidates = await fetch_youtube(
                session,
                channel["channel_id"],
                channel["name"],
                youtube_api_key,
                channel.get("keywords", []),
                since,
                max_items,
                global_keywords
            )
            all_candidates.extend(candidates)

        # Twitter
        twitter_bearer = feeds_config.get("twitter_bearer_token") or None
        for tw_list in feeds_config.get("twitter_lists", []):
            candidates = await fetch_twitter_list(
                session,
                tw_list["list_id"],
                tw_list["name"],
                twitter_bearer,
                since,
                max_items,
                global_keywords
            )
            all_candidates.extend(candidates)

        # Google Trends
        for region in feeds_config.get("google_trends_regions", []):
            candidates = await fetch_google_trends(session, region, since, max_items)
            all_candidates.extend(candidates)

    return all_candidates