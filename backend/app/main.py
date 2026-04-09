import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.models.database import engine
from app.models.tables import Base

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Chatbot API",
    description="API para consulta de stock de materiales por lenguaje natural",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)
    logger.info("Base de datos lista.")


app.include_router(api_router)
