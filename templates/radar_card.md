# Radar Approval Card Template — Module 2 Example

This is an example of the JSON payload sent to Slack/Telegram for each trend item.

---

## Slack Payload (Block Kit)

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
        "text": "*Fonte:* The Verge AI • 2h atrás\n*Por que importa:* Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.\n\n*✍️ Sugestão de Post:*\nO mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation"
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
        { "type": "mrkdwn", "text": "🤖 Content Strategist Agent • Item ID: trend_20260828_001 • Score: 0.87 • Angle: Contrarian" }
      ]
    }
  ],
  "text": "Nova tendência detectada: AI Video Editing Tools Surge in Q4 Funding — Aprovar, Editar ou Descartar"
}
```

---

## Telegram Payload (Bot API)

```json
{
  "chat_id": "-1001234567890",
  "text": "📰 *AI Video Editing Tools Surge in Q4 Funding*\n\n*Fonte:* The Verge AI • 2h atrás\n*Por que importa:* Três startups de edição de vídeo com IA levantaram $180M combinados. Sinal claro: o mercado está apostando em 'edição autônoma' como próxima categoria. Para criadores, significa ferramentas mais baratas e poderosas chegando em 6 meses.\n\n*✍️ Sugestão de Post:*\nO mercado de edição de vídeo com IA acabou de receber $180M em uma semana. 🎬\n\nNão é coincidência — é validação de categoria. As ferramentas que antes custavam $500/mês vão virar commodities.\n\nA pergunta não é 'se' você vai usar IA para editar. É 'quando' você vai migrar seu workflow.\n\nJá testou alguma? Qual seu gargalo hoje? 👇\n\n#IA #VideoEditing #CreatorEconomy #Automation",
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

---

## Internal Enriched Item (Module 2 State)

```json
{
  "item_id": "trend_20260828_001",
  "title": "AI Video Editing Tools Surge in Q4 Funding",
  "source": "The Verge AI",
  "source_url": "https://www.theverge.com/ai-artificial-intelligence/2026/8/28/ai-video-editing-funding",
  "published_at": "2026-08-28T14:30:00Z",
  "collected_at": "2026-08-28T16:00:00-03:00",
  "score": 0.87,
  "score_breakdown": {
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
  "status": "pending_approval",
  "approval_history": []
}
```

---

## Callback Handling Flow

### Slack Interactivity Endpoint

```
POST /slack/interactions
Content-Type: application/json

Payload: {
  "type": "block_actions",
  "user": { "id": "U123456", "username": "content_lead" },
  "actions": [{
    "action_id": "approve_trend_20260828_001",
    "value": "approve_trend_20260828_001",
    "type": "button"
  }],
  "message": { ...original message... },
  "trigger_id": "123456.789012.abcdef"
}
```

**Handler Logic:**
1. Parse `action_id` → extract `action` + `item_id`
2. Load item from `state/shortlist_{date}.json`
3. If `approve_*`:
   - Update item `status` = "approved"
   - Trigger publish workflow (Module 1 pipeline with this trend as input, or direct post via social API)
   - `chat.update` message: replace buttons with "✅ Aprovado! Publicando..."
4. If `edit_*`:
   - Update item `status` = "editing"
   - Open modal (views.open) with pre-filled draft in textarea
   - On modal submit: update draft, re-render card with new draft
5. If `discard_*`:
   - Update item `status` = "discarded"
   - `chat.update` message: replace buttons with "🗑️ Descartado."

---

### Telegram Callback Query

```json
{
  "callback_query": {
    "id": "123456789",
    "from": { "id": 123456789, "username": "content_lead" },
    "message": { "message_id": 42, "chat": { "id": -1001234567890 }, "text": "..." },
    "data": "approve_trend_20260828_001"
  }
}
```

**Handler Logic:**
1. Parse `data` → extract `action` + `item_id`
2. Load item from state
3. If `approve_*`:
   - Update status = "approved"
   - Trigger publish
   - `editMessageText`: "✅ Aprovado! Publicando..."
4. If `edit_*`:
   - Update status = "editing"
   - `editMessageText`: "✏️ Modo edição. Responda com o novo texto."
   - Set conversation state to capture next message from this user as edit
5. If `discard_*`:
   - Update status = "discarded"
   - `editMessageText`: "🗑️ Descartado."

---

## Approval States

| State | Description | Next Actions |
|-------|-------------|--------------|
| `pending_approval` | Card sent, awaiting action | approve / edit / discard |
| `editing` | User requested changes | capture edit → re-render card |
| `approved` | Ready to publish | trigger publish workflow |
| `published` | Successfully posted | archive |
| `discarded` | Rejected | log reason, archive |

---

## Publish Workflow (Post-Approval)

Upon `approve` action, the system can:
1. **Direct post** via platform APIs (LinkedIn UGC, Twitter v2, Instagram Graph, YouTube Data)
2. **Trigger Module 1** with the trend as input → generate full script + captions → human review → publish
3. **Queue in content calendar** (Airtable, Notion, Google Sheets) for scheduled publishing
4. **Send to team** via Asana/Trello/Linear task with draft attached

The skill is agnostic to the publish mechanism — implement the webhook handler to integrate with your stack.