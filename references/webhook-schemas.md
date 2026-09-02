# Webhook Payload Schemas

JSON Schemas for Module 2 approval cards (Slack Block Kit + Telegram Inline Keyboard).

---

## Slack Block Kit — Approval Card

### Full Payload Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SlackApprovalCard",
  "type": "object",
  "required": ["blocks"],
  "properties": {
    "blocks": {
      "type": "array",
      "minItems": 3,
      "maxItems": 5,
      "items": {
        "anyOf": [
          { "$ref": "#/definitions/HeaderBlock" },
          { "$ref": "#/definitions/SectionBlock" },
          { "$ref": "#/definitions/ActionsBlock" },
          { "$ref": "#/definitions/DividerBlock" },
          { "$ref": "#/definitions/ContextBlock" }
        ]
      }
    },
    "text": { "type": "string", "description": "Fallback plain text for notifications" }
  },
  "definitions": {
    "HeaderBlock": {
      "type": "object",
      "required": ["type", "text"],
      "properties": {
        "type": { "const": "header" },
        "text": {
          "type": "object",
          "required": ["type", "text"],
          "properties": {
            "type": { "const": "plain_text" },
            "text": { "type": "string", "maxLength": 150 },
            "emoji": { "type": "boolean", "default": true }
          }
        }
      }
    },
    "SectionBlock": {
      "type": "object",
      "required": ["type", "text"],
      "properties": {
        "type": { "const": "section" },
        "text": {
          "type": "object",
          "required": ["type", "text"],
          "properties": {
            "type": { "const": "mrkdwn" },
            "text": { "type": "string", "maxLength": 3000 }
          }
        }
      }
    },
    "ActionsBlock": {
      "type": "object",
      "required": ["type", "elements"],
      "properties": {
        "type": { "const": "actions" },
        "elements": {
          "type": "array",
          "minItems": 3,
          "maxItems": 3,
          "items": { "$ref": "#/definitions/ButtonElement" }
        }
      }
    },
    "ButtonElement": {
      "type": "object",
      "required": ["type", "text", "value", "action_id"],
      "properties": {
        "type": { "const": "button" },
        "text": {
          "type": "object",
          "required": ["type", "text"],
          "properties": {
            "type": { "const": "plain_text" },
            "text": { "type": "string", "maxLength": 75 },
            "emoji": { "type": "boolean", "default": true }
          }
        },
        "style": { "type": "string", "enum": ["primary", "danger", "default"], "default": "default" },
        "value": { "type": "string", "pattern": "^(approve|edit|discard)_[a-z0-9_-]+$" },
        "action_id": { "type": "string", "pattern": "^(approve|edit|discard)_[a-z0-9_-]+$" }
      }
    },
    "DividerBlock": {
      "type": "object",
      "required": ["type"],
      "properties": { "type": { "const": "divider" } }
    },
    "ContextBlock": {
      "type": "object",
      "required": ["type", "elements"],
      "properties": {
        "type": { "const": "context" },
        "elements": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["type", "text"],
            "properties": {
              "type": { "const": "mrkdwn" },
              "text": { "type": "string" }
            }
          }
        }
      }
    }
  }
}
```

### Example Rendered Payload

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "📰 AI Video Editing Tools Surge in Q4 Funding",
        "emoji": true
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Fonte:* TechCrunch • 2h atrás\n*Por que importa:* Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.\n\n*✍️ Sugestão de Post:*\nO mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "✅ Aprovar", "emoji": true },
          "style": "primary",
          "value": "approve_trend_20260828_001",
          "action_id": "approve_trend_20260828_001"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "✏️ Pedir Alteração", "emoji": true },
          "value": "edit_trend_20260828_001",
          "action_id": "edit_trend_20260828_001"
        },
        {
          "type": "button",
          "text": { "type": "plain_text", "text": "🗑️ Descartar", "emoji": true },
          "style": "danger",
          "value": "discard_trend_20260828_001",
          "action_id": "discard_trend_20260828_001"
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        { "type": "mrkdwn", "text": "🤖 Content Strategist Agent • Item ID: trend_20260828_001 • Score: 0.87" }
      ]
    }
  ],
  "text": "Nova tendência detectada: AI Video Editing Tools Surge in Q4 Funding — Aprovar, Editar ou Descartar"
}
```

### Button Value Convention

```
{action}_{item_id}
```

Where:
- `action` ∈ {`approve`, `edit`, `discard`}
- `item_id` = `trend_{YYYYMMDD}_{NNN}` (zero-padded sequence per day)

**Interactivity endpoint** must handle:
- `approve_*` → Mark approved, optionally trigger publish workflow
- `edit_*` → Open modal with pre-filled draft for modification
- `discard_*` → Mark rejected, log reason (optional follow-up modal)

---

## Telegram Bot API — Inline Keyboard

### Payload Structure (sendMessage)

```json
{
  "chat_id": "-1001234567890",
  "text": "📰 *AI Video Editing Tools Surge in Q4 Funding*\n\n*Fonte:* TechCrunch • 2h atrás\n*Por que importa:* Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.\n\n*✍️ Sugestão de Post:*\nO mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation",
  "parse_mode": "Markdown",
  "reply_markup": {
    "inline_keyboard": [
      [
        { "text": "✅ Aprovar", "callback_data": "approve_trend_20260828_001" },
        { "text": "✏️ Pedir Alteração", "callback_data": "edit_trend_20260828_001" },
        { "text": "🗑️ Descartar", "callback_data": "discard_trend_20260828_001" }
      ]
    ]
  }
}
```

### Callback Data Convention

Same as Slack: `{action}_{item_id}`

**Webhook handler** receives `CallbackQuery` with:
- `data`: callback_data string
- `message`: original message (for editing/deleting)
- `from`: user who clicked

**Response actions:**
- `approve_*` → `editMessageText` with "✅ Aprovado! Publicando..." + trigger publish
- `edit_*` → `editMessageText` with "✏️ Modo edição ativado. Responda com as alterações..." + set conversation state
- `discard_*` → `editMessageText` with "🗑️ Descartado." + log

---

## Shared Item ID Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "TrendItemId",
  "type": "string",
  "pattern": "^trend_\\d{8}_\\d{3}$",
  "examples": ["trend_20260828_001", "trend_20260828_042"]
}
```

---

## Module 2 Internal State (for reference)

### `state/last_run.json`

```json
{
  "last_run_timestamp": "2026-08-28T13:00:00-03:00",
  "processed_item_ids": ["trend_20260828_001", "trend_20260828_002"],
  "source_checkpoints": {
    "rss_the_verge_ai": "2026-08-28T12:45:00Z",
    "youtube_UC_x5XG1OV2P6uZZ5FSM9Ttw": "2026-08-28T12:50:00Z",
    "twitter_list_1234567890123456789": "2026-08-28T12:55:00Z",
    "google_trends_BR": "2026-08-28T12:58:00Z"
  },
  "errors": []
}
```

### `state/candidates_{timestamp}.json` (raw pool)

```json
[
  {
    "source": "rss",
    "source_name": "The Verge AI",
    "title": "AI video editing startups raise $180M",
    "url": "https://www.theverge.com/...",
    "published_at": "2026-08-28T14:30:00Z",
    "content_preview": "Three startups...",
    "keywords_matched": ["AI video", "editing", "funding"],
    "engagement": null
  }
]
```

### `state/shortlist_{timestamp}.json` (enriched, ranked)

```json
[
  {
    "item_id": "trend_20260828_001",
    "title": "AI Video Editing Tools Surge in Q4 Funding",
    "source": "The Verge AI",
    "url": "https://www.theverge.com/...",
    "score": 0.87,
    "executive_summary": "Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.",
    "key_insight": "A categoria 'edição autônoma' acabou de ser validada por $180M em capital de risco — commoditização em 6-12 meses.",
    "suggested_angle": "Contrarian",
    "draft_post": "O mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation"
  }
]
```

---

## Validation Checklist for Webhook Delivery

- [ ] Slack: `blocks` array validates against schema above
- [ ] Slack: `text` fallback present (plain text summary)
- [ ] Slack: Three buttons with correct `action_id`/`value` pattern
- [ ] Telegram: `reply_markup.inline_keyboard` has exactly 1 row × 3 buttons
- [ ] Telegram: `callback_data` matches `{action}_{item_id}` pattern
- [ ] Both: `item_id` matches `trend_YYYYMMDD_NNN` format
- [ ] Both: Message text ≤ platform limits (Slack 40k, Telegram 4096)
- [ ] Both: Markdown/MarkdownV2 escaping correct (no raw `_`, `*`, `[` unescaped)