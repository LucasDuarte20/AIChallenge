from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, func

from app.models.database import Base


class MaterialStock(Base):
    __tablename__ = "materials_stock"

    id = Column(Integer, primary_key=True, index=True)
    material_raw = Column(Text, nullable=False)
    material_code = Column(String(100), nullable=True, index=True)
    material_name = Column(Text, nullable=True)
    material_mlfb = Column(String(100), nullable=True, index=True)
    stock_actual = Column(Float, nullable=True)
    stock_en_viaje = Column(Float, nullable=True)
    stock_pendiente = Column(Float, nullable=True)
    stock_a_comprar = Column(Float, nullable=True)
    costo_estante_usd_unit = Column(Float, nullable=True)
    stock_actual_x_costo_usd = Column(Float, nullable=True)
    source_file = Column(String(255), nullable=True)
    source_sheet = Column(String(100), nullable=True)
    last_stock_date = Column(DateTime(timezone=True), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    sheet_name = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default="started")
    rows_total = Column(Integer, nullable=True)
    rows_inserted = Column(Integer, nullable=True)
    rows_failed = Column(Integer, nullable=True)
    error_details = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text, nullable=False)
    detected_intent = Column(String(50), nullable=True)
    extracted_material_code = Column(String(100), nullable=True)
    extracted_material_name = Column(Text, nullable=True)
    matched_material_id = Column(Integer, nullable=True)
    response_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_number = Column(String(50), nullable=True, index=True)  # N. Cli.
    name = Column(Text, nullable=False, index=True)  # 1. Nombre
    address_raw = Column(Text, nullable=True)
    phone = Column(String(100), nullable=True)
    office = Column(String(50), nullable=True)  # Oficina
    executive_code = Column(String(50), nullable=True, index=True)  # Vendedor
    sector = Column(String(100), nullable=True)  # Sector

    # Campos para agenda (pueden venir del Excel futuro o editarse)
    client_size = Column(String(20), nullable=True)  # chico|mediano|grande
    potential = Column(String(20), nullable=True)  # bajo|medio|alto

    # Geo / routing
    department = Column(String(80), nullable=True, index=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    geocode_status = Column(String(30), nullable=True)  # ok|approx|failed
    geocode_provider = Column(String(30), nullable=True)  # nominatim

    source_file = Column(String(255), nullable=True)
    source_sheet = Column(String(100), nullable=True)
    imported_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PlanJob(Base):
    __tablename__ = "plan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    scope_executive_code = Column(String(50), nullable=True)  # null = todos
    status = Column(String(20), nullable=False, default="started")
    customers_total = Column(Integer, nullable=True)
    visits_planned = Column(Integer, nullable=True)
    error_details = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)


class VisitPlan(Base):
    __tablename__ = "visit_plan"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    executive_code = Column(String(50), nullable=False, index=True)
    customer_id = Column(Integer, nullable=False, index=True)

    visit_date = Column(DateTime(timezone=True), nullable=False, index=True)
    day_order = Column(Integer, nullable=True)  # orden dentro del día

    # Snapshot útil para export
    customer_name = Column(Text, nullable=True)
    customer_address = Column(Text, nullable=True)
    department = Column(String(80), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
