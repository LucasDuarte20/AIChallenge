from fastapi import APIRouter

from app.api.routes import chat, health, import_excel, materials, stock, audio, clients, geocode, plans

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(import_excel.router)
api_router.include_router(clients.router)
api_router.include_router(geocode.router)
api_router.include_router(plans.router)
api_router.include_router(materials.router)
api_router.include_router(stock.router)
api_router.include_router(chat.router)
api_router.include_router(audio.router)
