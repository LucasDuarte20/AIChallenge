"""
Bot gratis por Telegram.
Reenvía mensajes al backend /chat y devuelve la respuesta.
"""

import logging

import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Hola. Enviame tu consulta de stock/precio en lenguaje natural.\n"
        "Ej: 'hay stock del material 786518?' o 'cuanto sale el 5TJ6216-7?'"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
    await update.message.reply_text(
        "Comandos:\n"
        "/start\n"
        "/help\n\n"
        "Ejemplos:\n"
        "- hay stock del material 786518?\n"
        "- cuanto sale el 5TJ6216-7?\n"
        "- que tengo que comprar?\n"
        "- materiales con stock pendiente"
    )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    text = update.message.text.strip()
    if not text:
        return

    backend_url = settings.bot_backend_url.rstrip("/")
    payload = {"message": text}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{backend_url}/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("Error llamando backend /chat: %s", exc)
        await update.message.reply_text("No pude consultar el sistema en este momento. Probá de nuevo en unos segundos.")
        return

    await update.message.reply_text(data.get("response", "No hubo respuesta."))


def main() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en .env")

    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Telegram bot iniciado.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

