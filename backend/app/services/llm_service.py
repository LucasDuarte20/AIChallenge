import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

import httpx

from app.core.config import settings
from app.utils.intent_detector import DetectedIntent, Intent

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    @abstractmethod
    async def enhance_intent(self, query: str, detected: DetectedIntent) -> DetectedIntent:
        ...

    @abstractmethod
    async def generate_response(self, prompt: str) -> str:
        ...


class MockLLMProvider(LLMProvider):
    async def enhance_intent(self, query: str, detected: DetectedIntent) -> DetectedIntent:
        return detected

    async def generate_response(self, prompt: str) -> str:
        return "[mock] Respuesta generada por reglas locales."


class OllamaLLMProvider(LLMProvider):
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def enhance_intent(self, query: str, detected: DetectedIntent) -> DetectedIntent:
        if detected.confidence >= 0.85:
            return detected

        prompt = (
            'Analizá la siguiente pregunta sobre stock de materiales industriales. '
            'Respondé SOLO con JSON, sin explicaciones.\n\n'
            f'Pregunta: "{query}"\n\n'
            'Intents posibles: stock, price, material_search, pending_stock, buy_list, total_cost, unknown\n\n'
            'Formato de respuesta:\n'
            '{"intent": "<intent>", "material_code": "<código numérico o null>", "material_mlfb": "<MLFB o null>"}'
        )
        try:
            raw = await self._call(prompt)
            data = json.loads(raw.strip())
            intent_str = data.get("intent", detected.intent.value)
            try:
                detected.intent = Intent(intent_str)
            except ValueError:
                pass
            detected.material_code = data.get("material_code") or detected.material_code
            detected.material_mlfb = data.get("material_mlfb") or detected.material_mlfb
            detected.confidence = 0.82
        except Exception as exc:
            logger.warning("Ollama enhance_intent falló: %s", exc)

        return detected

    async def generate_response(self, prompt: str) -> str:
        return await self._call(prompt)

    async def _call(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]


class OpenAILLMProvider(LLMProvider):
    """Placeholder para integración futura con OpenAI."""

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def enhance_intent(self, query: str, detected: DetectedIntent) -> DetectedIntent:
        # TODO: implementar con openai >= 1.0
        logger.info("OpenAI enhance_intent: pendiente de implementación")
        return detected

    async def generate_response(self, prompt: str) -> str:
        # TODO: implementar con openai >= 1.0
        return "[openai] Integración pendiente de configuración."


def get_llm_provider() -> LLMProvider:
    if settings.llm_provider == "ollama":
        return OllamaLLMProvider(settings.ollama_base_url, settings.ollama_model)
    if settings.llm_provider == "openai":
        return OpenAILLMProvider(settings.openai_api_key, settings.openai_model)
    return MockLLMProvider()
