# seed_clientes.py

from sqlalchemy import text
from app_db import engine


CLIENTES = [
    {
        "nombre": "Depósito Central",
        "direccion": "Paso de la Arena, Montevideo",
        "lat": -34.8569,
        "lon": -56.2731,
        "tipo": "base",
        "estado_cliente": "activo",
        "prioridad": "normal",
        "dias_asignados": "LUN,MAR,MIE,JUE,VIE",
        "demanda": 0,
        "demora": 0,
        "abre": 0,
        "cierra": 600,
        "es_deposito": True,
    },

    # Cadenas
    {"nombre": "Cadena1", "direccion": "Montevideo", "lat": -34.8812, "lon": -56.1654, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 900, "demora": 50, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Cadena2", "direccion": "Pocitos, Montevideo", "lat": -34.9142, "lon": -56.1485, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 800, "demora": 45, "abre": 30, "cierra": 300, "es_deposito": False},
    {"nombre": "Cadena3", "direccion": "Tres Cruces, Montevideo", "lat": -34.8943, "lon": -56.1658, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 700, "demora": 40, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Cadena4", "direccion": "Sayago, Montevideo", "lat": -34.8355, "lon": -56.2052, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 1000, "demora": 60, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Cadena5", "direccion": "Carrasco, Montevideo", "lat": -34.8890, "lon": -56.0610, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 650, "demora": 45, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Cadena6", "direccion": "Atlántida, Canelones", "lat": -34.7718, "lon": -55.7610, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 900, "demora": 60, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Cadena7", "direccion": "Las Piedras, Canelones", "lat": -34.7291, "lon": -56.2144, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 800, "demora": 50, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Cadena8", "direccion": "Lagomar, Ciudad de la Costa", "lat": -34.8325, "lon": -55.9782, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 600, "demora": 45, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cadena9", "direccion": "Pando, Canelones", "lat": -34.7172, "lon": -55.9584, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 750, "demora": 50, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Cadena10", "direccion": "Canelones, Uruguay", "lat": -34.5228, "lon": -56.2778, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 800, "demora": 60, "abre": 90, "cierra": 480, "es_deposito": False},

    # Comercios
    {"nombre": "Cliente1", "direccion": "Prado, Montevideo", "lat": -34.8694, "lon": -56.1952, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 250, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente2", "direccion": "Buceo, Montevideo", "lat": -34.8995, "lon": -56.1264, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 420, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente3", "direccion": "Parque Rodó, Montevideo", "lat": -34.9130, "lon": -56.1690, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 120, "demora": 10, "abre": 60, "cierra": 480, "es_deposito": False},
    {"nombre": "Cliente4", "direccion": "Cerro, Montevideo", "lat": -34.8912, "lon": -56.2541, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 480, "demora": 25, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Cliente5", "direccion": "Sayago, Montevideo", "lat": -34.8482, "lon": -56.1984, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 300, "demora": 20, "abre": 90, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente6", "direccion": "Colón, Montevideo", "lat": -34.8055, "lon": -56.2190, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 350, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente7", "direccion": "Malvín, Montevideo", "lat": -34.8920, "lon": -56.0980, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 180, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente8", "direccion": "Pocitos, Montevideo", "lat": -34.9101, "lon": -56.1420, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 220, "demora": 15, "abre": 60, "cierra": 240, "es_deposito": False},
    {"nombre": "Cliente9", "direccion": "Unión, Montevideo", "lat": -34.8818, "lon": -56.1285, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 390, "demora": 20, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente10", "direccion": "Cordón, Montevideo", "lat": -34.9012, "lon": -56.1782, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 310, "demora": 20, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Cliente11", "direccion": "Aguada, Montevideo", "lat": -34.8891, "lon": -56.1888, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 260, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente12", "direccion": "La Teja, Montevideo", "lat": -34.8605, "lon": -56.2324, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 450, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente13", "direccion": "Belvedere, Montevideo", "lat": -34.8528, "lon": -56.2205, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 280, "demora": 15, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente14", "direccion": "Villa Española, Montevideo", "lat": -34.8668, "lon": -56.1421, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 240, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente15", "direccion": "Centro, Montevideo", "lat": -34.9067, "lon": -56.1997, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 110, "demora": 10, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Cliente16", "direccion": "Punta Carretas, Montevideo", "lat": -34.9215, "lon": -56.1594, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 330, "demora": 20, "abre": 90, "cierra": 390, "es_deposito": False},

    # Costa / Canelones
    {"nombre": "Cliente17", "direccion": "Solymar, Ciudad de la Costa", "lat": -34.8230, "lon": -55.9453, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 520, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente18", "direccion": "Shangrilá, Ciudad de la Costa", "lat": -34.8510, "lon": -55.9981, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 300, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente19", "direccion": "El Pinar, Ciudad de la Costa", "lat": -34.7935, "lon": -55.9048, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 430, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente20", "direccion": "Pando, Canelones", "lat": -34.7212, "lon": -55.9596, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 270, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente21", "direccion": "Barros Blancos, Canelones", "lat": -34.7547, "lon": -56.0026, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 410, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente22", "direccion": "Sauce, Canelones", "lat": -34.6507, "lon": -56.0644, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 360, "demora": 25, "abre": 120, "cierra": 420, "es_deposito": False},

    # Nuevos / prioritarios
    {"nombre": "Cliente23", "direccion": "Carrasco Norte, Montevideo", "lat": -34.8725, "lon": -56.0551, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 260, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente24", "direccion": "La Blanqueada, Montevideo", "lat": -34.8878, "lon": -56.1518, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 320, "demora": 20, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente25", "direccion": "Malvín Norte, Montevideo", "lat": -34.8788, "lon": -56.1043, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 210, "demora": 15, "abre": 90, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente26", "direccion": "Cordón, Montevideo", "lat": -34.9010, "lon": -56.1740, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "JUE", "demanda": 600, "demora": 35, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Cliente27", "direccion": "Centro, Montevideo", "lat": -34.9055, "lon": -56.1942, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "LUN", "demanda": 500, "demora": 30, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Cliente28", "direccion": "Pocitos, Montevideo", "lat": -34.9098, "lon": -56.1450, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "MIE", "demanda": 450, "demora": 30, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Cliente29", "direccion": "Las Piedras, Canelones", "lat": -34.7305, "lon": -56.2158, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "MAR", "demanda": 700, "demora": 35, "abre": 60, "cierra": 300, "es_deposito": False},
]


with engine.begin() as conn:
    conn.execute(text("DELETE FROM logistica.rutas_generadas"))
    conn.execute(text("DELETE FROM logistica.pedidos"))
    conn.execute(text("DELETE FROM logistica.clientes"))

    for cliente in CLIENTES:
        conn.execute(
            text("""
                INSERT INTO logistica.clientes
                (
                    nombre,
                    direccion,
                    lat,
                    lon,
                    tipo,
                    estado_cliente,
                    prioridad,
                    dias_asignados,
                    demanda,
                    demora,
                    abre,
                    cierra,
                    es_deposito,
                    activo
                )
                VALUES
                (
                    :nombre,
                    :direccion,
                    :lat,
                    :lon,
                    :tipo,
                    :estado_cliente,
                    :prioridad,
                    :dias_asignados,
                    :demanda,
                    :demora,
                    :abre,
                    :cierra,
                    :es_deposito,
                    TRUE
                )
            """),
            cliente
        )


print("✅ Maestro de clientes cargado correctamente")