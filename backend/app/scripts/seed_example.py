"""Inserta datos de ejemplo en la base de datos."""
import logging
from app.models.database import SessionLocal, engine
from app.models.tables import Base, MaterialStock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SEED_DATA = [
    {
        "material_raw": "786518 - Int Tmag 06kA C 2P 16A",
        "material_code": "786518",
        "material_name": "Int Tmag 06kA C 2P 16A",
        "material_mlfb": "5TJ6216-7",
        "stock_actual": 5947.0,
        "stock_en_viaje": 0.0,
        "stock_pendiente": 0.0,
        "stock_a_comprar": 0.0,
        "costo_estante_usd_unit": 4.08,
        "stock_actual_x_costo_usd": 24263.76,
        "source_file": "seed_example",
        "source_sheet": "Sheet1",
    },
    {
        "material_raw": "786520 - Int Tmag 06kA C 2P 20A",
        "material_code": "786520",
        "material_name": "Int Tmag 06kA C 2P 20A",
        "material_mlfb": "5TJ6220-7",
        "stock_actual": 1200.0,
        "stock_en_viaje": 200.0,
        "stock_pendiente": 100.0,
        "stock_a_comprar": 0.0,
        "costo_estante_usd_unit": 4.50,
        "stock_actual_x_costo_usd": 5400.0,
        "source_file": "seed_example",
        "source_sheet": "Sheet1",
    },
    {
        "material_raw": "790100 - Contactor 3P 9A 24VDC",
        "material_code": "790100",
        "material_name": "Contactor 3P 9A 24VDC",
        "material_mlfb": "3RT2016-2BB41",
        "stock_actual": 45.0,
        "stock_en_viaje": 0.0,
        "stock_pendiente": 20.0,
        "stock_a_comprar": 50.0,
        "costo_estante_usd_unit": 38.50,
        "stock_actual_x_costo_usd": 1732.5,
        "source_file": "seed_example",
        "source_sheet": "Sheet1",
    },
    {
        "material_raw": "790200 - Relé Térmico 6-9A",
        "material_code": "790200",
        "material_name": "Relé Térmico 6-9A",
        "material_mlfb": "3RU2116-1JB0",
        "stock_actual": 0.0,
        "stock_en_viaje": 0.0,
        "stock_pendiente": 0.0,
        "stock_a_comprar": 30.0,
        "costo_estante_usd_unit": None,
        "stock_actual_x_costo_usd": None,
        "source_file": "seed_example",
        "source_sheet": "Sheet1",
    },
    {
        "material_raw": "800015 - Cable H07V-K 1x1.5mm2 Azul",
        "material_code": "800015",
        "material_name": "Cable H07V-K 1x1.5mm2 Azul",
        "material_mlfb": "3G2.5-BL",
        "stock_actual": 850.0,
        "stock_en_viaje": 150.0,
        "stock_pendiente": 0.0,
        "stock_a_comprar": 0.0,
        "costo_estante_usd_unit": 0.95,
        "stock_actual_x_costo_usd": 807.5,
        "source_file": "seed_example",
        "source_sheet": "Sheet1",
    },
]


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        inserted = 0
        for data in SEED_DATA:
            existing = db.query(MaterialStock).filter(
                MaterialStock.material_code == data["material_code"]
            ).first()
            if not existing:
                db.add(MaterialStock(**data))
                inserted += 1
        db.commit()
        logger.info("Seed completado: %d materiales insertados.", inserted)
        print(f"Seed completado: {inserted} materiales insertados.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
