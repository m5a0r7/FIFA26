from __future__ import annotations

from typing import Any

import httpx

from backend.app.agents import WorldCupAgent
from backend.app.config import Settings


class TelegramWebhookHandler:
    def __init__(self, settings: Settings, agent: WorldCupAgent | None = None) -> None:
        self.settings = settings
        self.agent = agent or WorldCupAgent()

    async def handle_update(self, update: dict[str, Any]) -> dict[str, Any]:
        message = update.get("message") or update.get("edited_message") or {}
        text = message.get("text")
        chat = message.get("chat") or {}
        chat_id = chat.get("id")

        if not text or chat_id is None:
            return {"ok": True, "detail": "ignored_non_text_update"}

        response = await self.agent.answer(text, session_id=f"telegram:{chat_id}")
        await self._send_message(chat_id, response.answer)
        return {"ok": True, "detail": "accepted", "mode": response.mode}

    async def _send_message(self, chat_id: int | str, text: str) -> None:
        if not self.settings.telegram_bot_token:
            return

        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text[:4096],
            "disable_web_page_preview": True,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=payload)
