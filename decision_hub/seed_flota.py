# seed_flota.py

from sqlalchemy import text
from app_db import engine
from parametros import (
    CAPACIDAD_GRANDE,
    CAPACIDAD_MEDIANA,
    CAPACIDAD_URBANA,
    JORNADA_MAX_MIN
)


FLOTA = [
    {
        "id_camion": 1,
        "descripcion": "Camión 1 - Grande Cadenas",
        "capacidad_kg": CAPACIDAD_GRANDE,
        "jornada_max_min": JORNADA_MAX_MIN,
    },
    {
        "id_camion": 2,
        "descripcion": "Camión 2 - Grande Cadenas",
        "capacidad_kg": CAPACIDAD_GRANDE,
        "jornada_max_min": JORNADA_MAX_MIN,
    },
    {
        "id_camion": 3,
        "descripcion": "Camión 3 - Mediano Mixto",
        "capacidad_kg": CAPACIDAD_MEDIANA,
        "jornada_max_min": JORNADA_MAX_MIN,
    },
    {
        "id_camion": 4,
        "descripcion": "Camión 4 - Urbano Comercios",
        "capacidad_kg": CAPACIDAD_URBANA,
        "jornada_max_min": JORNADA_MAX_MIN,
    },
    {
        "id_camion": 5,
        "descripcion": "Camión 5 - Urbano Comercios",
        "capacidad_kg": CAPACIDAD_URBANA,
        "jornada_max_min": JORNADA_MAX_MIN,
    },
]


with engine.begin() as conn:
    conn.execute(text("DELETE FROM logistica.flota"))

    for camion in FLOTA:
        conn.execute(
            text("""
                INSERT INTO logistica.flota
                (
                    id_camion,
                    descripcion,
                    capacidad_kg,
                    jornada_max_min
                )
                VALUES
                (
                    :id_camion,
                    :descripcion,
                    :capacidad_kg,
                    :jornada_max_min
                )
            """),
            camion
        )


print("✅ Flota cargada correctamente")