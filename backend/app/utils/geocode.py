import logging
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class GeocodeResult:
    lat: float | None
    lon: float | None
    department: str | None
    status: str  # ok|approx|failed
    provider: str


async def geocode_uy_address(address: str) -> GeocodeResult:
    """
    MVP: usa Nominatim (OpenStreetMap). Gratis, sin API key.
    Nota: respetar rate limits (este MVP hace cache en DB por cliente).
    """
    q = (address or "").strip()
    if not q:
        return GeocodeResult(None, None, None, "failed", "nominatim")

    # Forzar Uruguay para mejorar precisión
    query = f"{q}, Uruguay"
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": query, "format": "jsonv2", "addressdetails": 1, "limit": 1}
    headers = {"User-Agent": "aichallenge-visit-planner/0.1 (local-mvp)"}

    try:
        async with httpx.AsyncClient(timeout=20.0, headers=headers) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data: list[dict[str, Any]] = resp.json()
    except Exception as exc:
        logger.warning("Geocode falló para '%s': %s", q, exc)
        return GeocodeResult(None, None, None, "failed", "nominatim")

    if not data:
        return GeocodeResult(None, None, None, "failed", "nominatim")

    item = data[0]
    lat = float(item.get("lat")) if item.get("lat") else None
    lon = float(item.get("lon")) if item.get("lon") else None

    addr = item.get("address") or {}
    # Uruguay: suele venir como "state" o "county" o "city"
    dept = (
        addr.get("state")
        or addr.get("county")
        or addr.get("region")
        or addr.get("city")
        or addr.get("town")
    )
    if isinstance(dept, str):
        dept = dept.replace("Departamento de", "").strip()

    return GeocodeResult(lat, lon, dept, "ok" if lat and lon else "failed", "nominatim")

