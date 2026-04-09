from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class MaterialStockBase(BaseModel):
    material_raw: str
    material_code: Optional[str] = None
    material_name: Optional[str] = None
    material_mlfb: Optional[str] = None
    stock_actual: Optional[float] = None
    stock_en_viaje: Optional[float] = None
    stock_pendiente: Optional[float] = None
    stock_a_comprar: Optional[float] = None
    costo_estante_usd_unit: Optional[float] = None
    stock_actual_x_costo_usd: Optional[float] = None
    source_file: Optional[str] = None
    source_sheet: Optional[str] = None


class MaterialStockRead(MaterialStockBase):
    id: int
    imported_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class MaterialStockSearchResult(BaseModel):
    items: list[MaterialStockRead]
    total: int
    query: str
