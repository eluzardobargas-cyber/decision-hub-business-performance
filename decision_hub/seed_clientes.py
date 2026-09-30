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
    {"nombre": "Tienda Inglesa Central", "direccion": "Montevideo", "lat": -34.8812, "lon": -56.1654, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 900, "demora": 50, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Devoto Pocitos", "direccion": "Pocitos, Montevideo", "lat": -34.9142, "lon": -56.1485, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 800, "demora": 45, "abre": 30, "cierra": 300, "es_deposito": False},
    {"nombre": "Disco Tres Cruces", "direccion": "Tres Cruces, Montevideo", "lat": -34.8943, "lon": -56.1658, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 700, "demora": 40, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Macro Mercado Sayago", "direccion": "Sayago, Montevideo", "lat": -34.8355, "lon": -56.2052, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 1000, "demora": 60, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Supermercado Carrasco", "direccion": "Carrasco, Montevideo", "lat": -34.8890, "lon": -56.0610, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 650, "demora": 45, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Supermercado Atlántida", "direccion": "Atlántida, Canelones", "lat": -34.7718, "lon": -55.7610, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 900, "demora": 60, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Mayorista Las Piedras", "direccion": "Las Piedras, Canelones", "lat": -34.7291, "lon": -56.2144, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 800, "demora": 50, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Super Lagomar", "direccion": "Lagomar, Ciudad de la Costa", "lat": -34.8325, "lon": -55.9782, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 600, "demora": 45, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Distribuidor Pando", "direccion": "Pando, Canelones", "lat": -34.7172, "lon": -55.9584, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR,JUE", "demanda": 750, "demora": 50, "abre": 60, "cierra": 420, "es_deposito": False},
    {"nombre": "Super Canelones Centro", "direccion": "Canelones, Uruguay", "lat": -34.5228, "lon": -56.2778, "tipo": "cadena", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN,MIE,VIE", "demanda": 800, "demora": 60, "abre": 90, "cierra": 480, "es_deposito": False},

    # Comercios
    {"nombre": "Almacén Don Pedro", "direccion": "Prado, Montevideo", "lat": -34.8694, "lon": -56.1952, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 250, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Autoservicio Buceo", "direccion": "Buceo, Montevideo", "lat": -34.8995, "lon": -56.1264, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 420, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Kiosco Parque Rodó", "direccion": "Parque Rodó, Montevideo", "lat": -34.9130, "lon": -56.1690, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 120, "demora": 10, "abre": 60, "cierra": 480, "es_deposito": False},
    {"nombre": "Provisión Cerro", "direccion": "Cerro, Montevideo", "lat": -34.8912, "lon": -56.2541, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 480, "demora": 25, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Mini Tala Sayago", "direccion": "Sayago, Montevideo", "lat": -34.8482, "lon": -56.1984, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 300, "demora": 20, "abre": 90, "cierra": 360, "es_deposito": False},
    {"nombre": "Almacén Colón", "direccion": "Colón, Montevideo", "lat": -34.8055, "lon": -56.2190, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 350, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Almacén Malvín", "direccion": "Malvín, Montevideo", "lat": -34.8920, "lon": -56.0980, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 180, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Fiambrería Pocitos", "direccion": "Pocitos, Montevideo", "lat": -34.9101, "lon": -56.1420, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 220, "demora": 15, "abre": 60, "cierra": 240, "es_deposito": False},
    {"nombre": "Autoservicio Unión", "direccion": "Unión, Montevideo", "lat": -34.8818, "lon": -56.1285, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 390, "demora": 20, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Provisión Cordón", "direccion": "Cordón, Montevideo", "lat": -34.9012, "lon": -56.1782, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 310, "demora": 20, "abre": 0, "cierra": 300, "es_deposito": False},
    {"nombre": "Mercadito Aguada", "direccion": "Aguada, Montevideo", "lat": -34.8891, "lon": -56.1888, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 260, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Autoservicio La Teja", "direccion": "La Teja, Montevideo", "lat": -34.8605, "lon": -56.2324, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 450, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Despensa Belvedere", "direccion": "Belvedere, Montevideo", "lat": -34.8528, "lon": -56.2205, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 280, "demora": 15, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Almacén Villa Española", "direccion": "Villa Española, Montevideo", "lat": -34.8668, "lon": -56.1421, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 240, "demora": 15, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Kiosco Centro", "direccion": "Centro, Montevideo", "lat": -34.9067, "lon": -56.1997, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "LUN", "demanda": 110, "demora": 10, "abre": 0, "cierra": 240, "es_deposito": False},
    {"nombre": "Minimarket Punta Carretas", "direccion": "Punta Carretas, Montevideo", "lat": -34.9215, "lon": -56.1594, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 330, "demora": 20, "abre": 90, "cierra": 390, "es_deposito": False},

    # Costa / Canelones
    {"nombre": "Autoservicio Solymar", "direccion": "Solymar, Ciudad de la Costa", "lat": -34.8230, "lon": -55.9453, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 520, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Almacén Shangrilá", "direccion": "Shangrilá, Ciudad de la Costa", "lat": -34.8510, "lon": -55.9981, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 300, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Mercado El Pinar", "direccion": "El Pinar, Ciudad de la Costa", "lat": -34.7935, "lon": -55.9048, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 430, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Almacén Pando Centro", "direccion": "Pando, Canelones", "lat": -34.7212, "lon": -55.9596, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 270, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Autoservicio Barros Blancos", "direccion": "Barros Blancos, Canelones", "lat": -34.7547, "lon": -56.0026, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MAR", "demanda": 410, "demora": 25, "abre": 90, "cierra": 420, "es_deposito": False},
    {"nombre": "Minimarket Sauce", "direccion": "Sauce, Canelones", "lat": -34.6507, "lon": -56.0644, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 360, "demora": 25, "abre": 120, "cierra": 420, "es_deposito": False},

    # Nuevos / prioritarios
    {"nombre": "Cliente Carrasco Norte", "direccion": "Carrasco Norte, Montevideo", "lat": -34.8725, "lon": -56.0551, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "MIE", "demanda": 260, "demora": 20, "abre": 120, "cierra": 420, "es_deposito": False},
    {"nombre": "Cliente La Blanqueada", "direccion": "La Blanqueada, Montevideo", "lat": -34.8878, "lon": -56.1518, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "JUE", "demanda": 320, "demora": 20, "abre": 60, "cierra": 360, "es_deposito": False},
    {"nombre": "Cliente Malvín Norte", "direccion": "Malvín Norte, Montevideo", "lat": -34.8788, "lon": -56.1043, "tipo": "comercio", "estado_cliente": "nuevo", "prioridad": "normal", "dias_asignados": "VIE", "demanda": 210, "demora": 15, "abre": 90, "cierra": 360, "es_deposito": False},
    {"nombre": "Cordón Prioritario", "direccion": "Cordón, Montevideo", "lat": -34.9010, "lon": -56.1740, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "JUE", "demanda": 600, "demora": 35, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Centro Prioritario", "direccion": "Centro, Montevideo", "lat": -34.9055, "lon": -56.1942, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "LUN", "demanda": 500, "demora": 30, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Pocitos Prioritario", "direccion": "Pocitos, Montevideo", "lat": -34.9098, "lon": -56.1450, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "MIE", "demanda": 450, "demora": 30, "abre": 0, "cierra": 180, "es_deposito": False},
    {"nombre": "Las Piedras Prioritario", "direccion": "Las Piedras, Canelones", "lat": -34.7305, "lon": -56.2158, "tipo": "comercio", "estado_cliente": "activo", "prioridad": "urgente", "dias_asignados": "MAR", "demanda": 700, "demora": 35, "abre": 60, "cierra": 300, "es_deposito": False},
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