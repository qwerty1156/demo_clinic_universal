from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from settings import Settings
from config.clinic import clinic_context

logger = logging.getLogger(__name__)


class GeminiAI:
    """Small async REST client for Gemini generateContent."""

    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self.url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.model}:generateContent"
        )

    async def answer_customer(self, question: str) -> str | None:
        if not self.api_key:
            return None

        system = (
            "Ты AI-консультант клиники. Отвечай коротко, дружелюбно и профессионально. "
            "Используй только факты из данных клиники ниже. Никогда не придумывай услуги, цены, врачей, адрес, расписание, гарантии или диагнозы. "
            "Не ставь диагнозы и не назначай лечение. Если вопрос требует осмотра, скажи, что точный ответ возможен после консультации врача. "
            "Обычно отвечай в 1–3 предложениях. После полезного ответа мягко предложи записаться, если это уместно.\n\n"
            f"ДАННЫЕ КЛИНИКИ:\n{clinic_context()}\n\n"
            f"ВОПРОС КЛИЕНТА:\n{question}"
        )

        payload: dict[str, Any] = {
            "contents": [{"parts": [{"text": system}]}],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.9,
                "maxOutputTokens": 300,
            },
        }

        timeout = aiohttp.ClientTimeout(total=45)
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }

        for attempt in range(3):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(self.url, json=payload, headers=headers) as response:
                        if response.status in {429, 500, 502, 503, 504} and attempt < 2:
                            await asyncio.sleep(2**attempt)
                            continue
                        if response.status >= 400:
                            logger.error("Gemini HTTP %s", response.status)
                            return None
                        data = await response.json()

                candidates = data.get("candidates") or []
                if not candidates:
                    return None
                parts = (candidates[0].get("content") or {}).get("parts") or []
                for part in parts:
                    if isinstance(part, dict) and part.get("text"):
                        return str(part["text"]).strip()
                return None
            except asyncio.TimeoutError:
                logger.warning("Gemini timeout, attempt=%s", attempt + 1)
            except aiohttp.ClientError as exc:
                logger.warning("Gemini network error: %s", exc)
            except Exception:
                logger.exception("Unexpected Gemini error")

        return None
