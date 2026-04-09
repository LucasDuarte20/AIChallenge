import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.schemas.chat import ChatResponse
from app.services.audio_service import get_transcriber
from app.services.chat_service import process_chat

router = APIRouter(prefix="/transcribe-audio", tags=["audio"])
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"audio/webm", "audio/ogg", "audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav"}


@router.post("", response_model=ChatResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Recibe un archivo de audio, lo transcribe y procesa como consulta de chat.
    En modo mock retorna una transcripción de ejemplo.
    """
    content_type = audio.content_type or ""
    if content_type and content_type not in ALLOWED_TYPES:
        logger.warning("Tipo de audio no soportado oficialmente: %s", content_type)

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Archivo de audio vacío")

    transcriber = get_transcriber()
    try:
        transcribed_text = await transcriber.transcribe(audio_bytes, audio.filename or "audio.webm")
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc))
    except Exception as exc:
        logger.error("Error en transcripción: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error en transcripción: {exc}")

    logger.info("Transcripción: '%s'", transcribed_text)
    response = await process_chat(transcribed_text, db)
    response.response = f"[Audio transcripto: *{transcribed_text}*]\n\n{response.response}"
    return response
