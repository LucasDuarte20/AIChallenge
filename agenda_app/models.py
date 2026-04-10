from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass
class ClientRow:
    """Fila de cliente alineada al Excel de industria."""

    row_index: int  # 1-based en la hoja
    customer_number: str | None
    name: str
    department: str | None
    address_raw: str | None
    client_size: str | None
    potential: str | None
    phone: str | None
    office: str | None
    executive_code: str | None
    sector: str | None
    last_visit: date | None
    next_visit: date | None
    lat: float | None = None
    lon: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)
