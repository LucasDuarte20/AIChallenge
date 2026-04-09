import logging
from abc import ABC, abstractmethod

from app.core.config import settings

logger = logging.getLogger(__name__)


class AudioTranscriber(ABC):
    @abstractmethod
    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        ...


class MockAudioTranscriber(AudioTranscriber):
    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        logger.info("MockAudioTranscriber: simulando transcripción de '%s' (%d bytes)", filename, len(audio_bytes))
        return "hay stock del material 786518"


class OpenAIWhisperTranscriber(AudioTranscriber):
    """Adaptador para Whisper via OpenAI API."""

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        # TODO: implementar con openai >= 1.0
        # client = AsyncOpenAI(api_key=settings.openai_api_key)
        # response = await client.audio.transcriptions.create(
        #     model="whisper-1",
        #     file=(filename, audio_bytes),
        # )
        # return response.text
        raise NotImplementedError("Configurá OPENAI_API_KEY para usar Whisper.")


class LocalWhisperTranscriber(AudioTranscriber):
    """Adaptador para whisper.cpp local o faster-whisper (futuro)."""

    async def transcribe(self, audio_bytes: bytes, filename: str) -> str:
        # TODO: conectar con servidor whisper local
        raise NotImplementedError("Whisper local no configurado.")


def get_transcriber() -> AudioTranscriber:
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return OpenAIWhisperTranscriber()
    return MockAudioTranscriber()
