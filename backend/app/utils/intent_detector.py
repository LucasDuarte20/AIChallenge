import re
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    STOCK = "stock"
    PRICE = "price"
    MATERIAL_SEARCH = "material_search"
    PENDING_STOCK = "pending_stock"
    BUY_LIST = "buy_list"
    TOTAL_COST = "total_cost"
    UNKNOWN = "unknown"


@dataclass
class DetectedIntent:
    intent: Intent
    material_code: str | None
    material_mlfb: str | None
    material_name: str | None
    confidence: float


# Patrones de extracción de entidades
_CODE_RE = re.compile(r'\b(\d{5,7})\b')
_MLFB_RE = re.compile(r'\b([A-Z0-9]{3,10}-[A-Z0-9]{1,10}(?:-[A-Z0-9]+)?)\b', re.IGNORECASE)

_STOCK_KW = ["stock", "hay", "existe", "tengo", "disponible", "cantidad", "cuanto", "cuánto", "unidades"]
_PRICE_KW = ["precio", "costo", "cuesta", "vale", "valor", "sale", "cuánto sale", "cuanto sale"]
_PENDING_KW = ["pendiente", "pendientes", "en viaje", "viaje", "en camino"]
_BUY_KW = ["comprar", "compra", "a comprar", "que falta", "qué falta", "necesito comprar"]
_TOTAL_KW = ["costo total", "total", "inversión", "inversion", "capital", "importe total"]
_SEARCH_KW = ["buscame", "búscame", "busca", "buscar", "encontrá", "encontra", "muestra"]


def detect_intent(text: str) -> DetectedIntent:
    t = text.lower().strip()

    code_match = _CODE_RE.search(text)
    mlfb_match = _MLFB_RE.search(text)

    material_code = code_match.group(1) if code_match else None
    material_mlfb = mlfb_match.group(1).upper() if mlfb_match else None

    # Intentar extraer nombre de material (todo lo que no sea código ni MLFB)
    material_name: str | None = None
    clean = re.sub(r'\b\d{5,7}\b', '', text)
    clean = _MLFB_RE.sub('', clean)
    clean = re.sub(r'\b(hay|stock|precio|costo|cuanto|cuánto|buscame|búscame|busca|material|del|de|el|la|me|un|una)\b', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[?¿!¡]', '', clean).strip()
    if len(clean) > 4:
        material_name = clean.strip()

    intent = Intent.UNKNOWN
    confidence = 0.5

    if any(kw in t for kw in _TOTAL_KW) and (material_code or material_mlfb):
        intent = Intent.TOTAL_COST
        confidence = 0.92
    elif any(kw in t for kw in _BUY_KW):
        intent = Intent.BUY_LIST
        confidence = 0.92
    elif any(kw in t for kw in _PENDING_KW):
        intent = Intent.PENDING_STOCK
        confidence = 0.90
    elif any(kw in t for kw in _PRICE_KW):
        intent = Intent.PRICE
        confidence = 0.90
    elif any(kw in t for kw in _STOCK_KW):
        intent = Intent.STOCK
        confidence = 0.88
    elif any(kw in t for kw in _SEARCH_KW) or material_code or material_mlfb:
        intent = Intent.MATERIAL_SEARCH
        confidence = 0.75

    return DetectedIntent(
        intent=intent,
        material_code=material_code,
        material_mlfb=material_mlfb,
        material_name=material_name,
        confidence=confidence,
    )
