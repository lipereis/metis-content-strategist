#!/usr/bin/env python3
"""
Test webhook delivery for Module 2 approval cards.
Usage: python test_webhook.py --url $SLACK_WEBHOOK_URL --sample
       python test_webhook.py --telegram --token $BOT_TOKEN --chat $CHAT_ID --sample
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx


SAMPLE_ITEM = {
    "item_id": "trend_20260828_001",
    "title": "AI Video Editing Tools Surge in Q4 Funding",
    "source": "The Verge AI",
    "source_url": "https://www.theverge.com/ai-artificial-intelligence/2026/8/28/ai-video-editing-funding",
    "published_at": "2026-08-28T14:30:00Z",
    "collected_at": datetime.now(timezone.utc).isoformat(),
    "score": 0.87,
    "score_breakdown:": {
        "keyword_density": 0.9,
        "source_authority": 0.95,
        "recency": 0.98,
        "engagement_velocity": 0.7,
        "cross_source_corroboration": 0.8
    },
    "keywords_matched": ["AI video", "editing", "funding", "creator tools", "automation"],
    "executive_summary": "Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.",
    "key_insight": "A categoria 'edição autônoma' acabou de ser validada por $180M em capital de risco — commoditização em 6-12 meses.",
    "suggested_angle": "Contrarian",
    "draft_post": "O mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation",
    "platform": "linkedin",
    "tone_id": "b2b_corporate",
    "status": "pending_approval"
}


def format_relative_time(iso_string: str) -> str:
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


def build_slack_payload(item: dict) -> dict:
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"📰 {item['title']}", "emoji": True}
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Fonte:* {item['source']} • {format_relative_time(item['published_at'])}\n"
                            f"*Por que importa:* {item['executive_summary']}\n\n"
                            f"*✍️ Sugestão de Post:*\n{item['draft_post']}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {"type": "button", "text": {"type": "plain_text", "text": "✅ Aprovar", "emoji": True}, "style": "primary", "value": f"approve_{item['item_id']}", "action_id": f"approve_{item['item_id']}"},
                    {"type": "button", "text": {"type": "plain_text", "text": "✏️ Pedir Alteração", "emoji": True}, "value": f"edit_{item['item_id']}", "action_id": f"edit_{item['item_id']}"},
                    {"type": "button", "text": {"type": "plain_text", "text": "🗑️ Descartar", "emoji": True}, "style": "danger", "value": f"discard_{item['item_id']}", "action_id": f"discard_{item['item_id']}"}
                ]
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"🤖 Content Strategist Agent • Item ID: {item['item_id']} • Score: {item['score']:.2f} • Angle: {item['suggested_angle']}"}]
            }
        ],
        "text": f"Nova tendência detectada: {item['title']} — Aprovar, Editar ou Descartar"
    }


def build_telegram_payload(item: dict, chat_id: str) -> dict:
    return {
        "chat_id": chat_id,
        "text": f"📰 *{item['title']}*\n\n*Fonte:* {item['source']} • {format_relative_time(item['published_at'])}\n*Por que importa:* {item['executive_summary']}\n\n*✍️ Sugestão de Post:*\n{item['draft_post']}",
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "✅ Aprovar", "callback_data": f"approve_{item['item_id']}"},
                {"text": "✏️ Pedir Alteração", "callback_data": f"edit_{item['item_id']}"},
                {"text": "🗑️ Descartar", "callback_data": f"discard_{item['item_id']}"}
            ]]
        }
    }


async def send_slack_webhook(webhook_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(webhook_url, json=payload)
            resp.raise_for_status()
            print(f"✅ Slack webhook delivered successfully (status: {resp.status_code})")
            return True
    except httpx.HTTPStatusError as e:
        print(f"❌ Slack webhook failed: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Slack webhook error: {e}")
        return False


async def send_telegram_webhook(bot_token: str, payload: dict) -> bool:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("ok"):
                print(f"✅ Telegram message sent successfully (message_id: {data['result']['message_id']})")
                return True
            else:
                print(f"❌ Telegram API error: {data}")
                return False
    except httpx.HTTPStatusError as e:
        print(f"❌ Telegram webhook failed: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"❌ Telegram webhook error: {e}")
        return False


async def main():
    parser = argparse.ArgumentParser(description="Test webhook delivery for approval cards")
    parser.add_argument("--url", help="Slack incoming webhook URL")
    parser.add_argument("--telegram", action="store_true", help="Use Telegram Bot API instead of Slack")
    parser.add_argument("--token", help="Telegram bot token (required with --telegram)")
    parser.add_argument("--chat", help="Telegram chat ID (required with --telegram)")
    parser.add_argument("--sample", action="store_true", help="Send sample approval card")
    parser.add_argument("--payload", help="Path to JSON file with custom item payload")
    args = parser.parse_args()

    if not args.sample and not args.payload:
        print("Error: Must specify --sample or --payload", file=sys.stderr)
        sys.exit(1)

    # Load item
    if args.payload:
        with open(args.payload, "r", encoding="utf-8") as f:
            item = json.load(f)
    else:
        item = SAMPLE_ITEM

    if args.telegram:
        if not args.token:
            args.token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not args.chat:
            args.chat = os.getenv("TELEGRAM_CHAT_ID")
        if not args.token or not args.chat:
            print("Error: --token and --chat required for Telegram (or set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars)", file=sys.stderr)
            sys.exit(1)

        payload = build_telegram_payload(item, args.chat)
        success = await send_telegram_webhook(args.token, payload)
    else:
        webhook_url = args.url or os.getenv("SLACK_WEBHOOK_URL")
        if not webhook_url:
            print("Error: --url required for Slack (or set SLACK_WEBHOOK_URL env var)", file=sys.stderr)
            sys.exit(1)

        payload = build_slack_payload(item)
        success = await send_slack_webhook(webhook_url, payload)

    if success:
        print("🎉 Test delivery successful!")
        sys.exit(0)
    else:
        print("💥 Test delivery failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())