import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.tables import MaterialStock
from app.repositories import materials_repo, query_logs_repo
from app.schemas.chat import ChatResponse
from app.services import llm_service, search_service
from app.utils.intent_detector import Intent, detect_intent

logger = logging.getLogger(__name__)


def _fmt_num(val: Optional[float], decimals: int = 0) -> str:
    if val is None:
        return "-"
    if decimals == 0:
        return f"{val:,.0f}"
    return f"{val:,.{decimals}f}"


def _material_summary(m: MaterialStock) -> dict:
    return {
        "id": m.id,
        "material_raw": m.material_raw,
        "material_code": m.material_code,
        "material_mlfb": m.material_mlfb,
        "stock_actual": m.stock_actual,
        "stock_en_viaje": m.stock_en_viaje,
        "stock_pendiente": m.stock_pendiente,
        "stock_a_comprar": m.stock_a_comprar,
        "costo_estante_usd_unit": m.costo_estante_usd_unit,
        "stock_actual_x_costo_usd": m.stock_actual_x_costo_usd,
    }


def _build_stock_response(m: MaterialStock) -> str:
    lines = [f"**{m.material_raw}**"]
    if m.material_mlfb:
        lines.append(f"MLFB: {m.material_mlfb}")
    lines.append(f"• Stock actual: **{_fmt_num(m.stock_actual)} un.**")
    if m.stock_en_viaje:
        lines.append(f"• En viaje: {_fmt_num(m.stock_en_viaje)} un.")
    if m.stock_pendiente:
        lines.append(f"• Pendiente: {_fmt_num(m.stock_pendiente)} un.")
    if m.stock_a_comprar:
        lines.append(f"• A comprar: {_fmt_num(m.stock_a_comprar)} un.")
    return "\n".join(lines)


def _build_price_response(m: MaterialStock) -> str:
    lines = [f"**{m.material_raw}**"]
    if m.material_mlfb:
        lines.append(f"MLFB: {m.material_mlfb}")
    lines.append(f"• Costo unitario: **USD {_fmt_num(m.costo_estante_usd_unit, 2)}**")
    lines.append(f"• Stock actual x costo: **USD {_fmt_num(m.stock_actual_x_costo_usd, 2)}**")
    return "\n".join(lines)


def _build_total_cost_response(m: MaterialStock) -> str:
    lines = [f"**{m.material_raw}**"]
    if m.material_mlfb:
        lines.append(f"MLFB: {m.material_mlfb}")
    lines.append(f"• Stock actual: {_fmt_num(m.stock_actual)} un.")
    lines.append(f"• Costo unitario: USD {_fmt_num(m.costo_estante_usd_unit, 2)}")
    lines.append(f"• **Total en estante: USD {_fmt_num(m.stock_actual_x_costo_usd, 2)}**")
    return "\n".join(lines)


def _build_list_response(materials: list[MaterialStock], field: str, title: str) -> tuple[str, list[dict]]:
    if not materials:
        return f"No hay materiales con {title} en este momento.", []

    lines = [f"Materiales con {title} ({len(materials)} encontrados):\n"]
    for m in materials[:15]:
        val = getattr(m, field, None)
        lines.append(f"• {m.material_raw} — {_fmt_num(val)} un.")
    if len(materials) > 15:
        lines.append(f"... y {len(materials) - 15} más.")
    data = [_material_summary(m) for m in materials]
    return "\n".join(lines), data


async def process_chat(message: str, db: Session) -> ChatResponse:
    detected = detect_intent(message)
    logger.info("Intent detectado: %s (%.2f) | code=%s mlfb=%s", detected.intent, detected.confidence, detected.material_code, detected.material_mlfb)

    provider = llm_service.get_llm_provider()
    detected = await provider.enhance_intent(message, detected)

    response_text = ""
    data: Any = None
    matched_id: Optional[int] = None

    if detected.intent in (Intent.STOCK, Intent.PRICE, Intent.TOTAL_COST, Intent.MATERIAL_SEARCH):
        material = search_service.find_material(
            db,
            code=detected.material_code,
            mlfb=detected.material_mlfb,
            name_query=detected.material_name,
            fuzzy=True,
        )

        if material is None:
            response_text = (
                "No encontré ese material en el sistema. "
                "Podés buscar por código (ej: 786518), MLFB (ej: 5TJ6216-7) o nombre parcial."
            )
        else:
            matched_id = material.id
            data = _material_summary(material)
            if detected.intent == Intent.STOCK:
                response_text = _build_stock_response(material)
            elif detected.intent == Intent.PRICE:
                response_text = _build_price_response(material)
            elif detected.intent == Intent.TOTAL_COST:
                response_text = _build_total_cost_response(material)
            else:
                response_text = _build_stock_response(material)

    elif detected.intent == Intent.PENDING_STOCK:
        materials = materials_repo.get_with_pending_stock(db)
        response_text, data = _build_list_response(materials, "stock_pendiente", "stock pendiente")

    elif detected.intent == Intent.BUY_LIST:
        materials = materials_repo.get_buy_list(db)
        response_text, data = _build_list_response(materials, "stock_a_comprar", "stock a comprar")

    else:
        ejemplos = [
            "hay stock del material 786518?",
            "cuanto sale el 5TJ6216-7?",
            "que tengo que comprar?",
            "materiales con stock pendiente",
            "costo total del material 786518",
        ]
        response_text = "No entendi bien tu consulta. Podes preguntarme:\n" + "\n".join(
            f'  - "{e}"' for e in ejemplos
        )

    query_logs_repo.create(
        db,
        user_query=message,
        detected_intent=detected.intent.value,
        response_text=response_text,
        extracted_material_code=detected.material_code,
        extracted_material_name=detected.material_name,
        matched_material_id=matched_id,
    )

    return ChatResponse(
        response=response_text,
        intent=detected.intent.value,
        material_code=detected.material_code,
        material_mlfb=detected.material_mlfb,
        data=data,
        confidence=detected.confidence,
    )
