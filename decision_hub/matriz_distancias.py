# matriz_distancias.py

import math

import numpy as np

from parametros import VELOCIDAD_MEDIA_KMH


def haversine_km(lat1, lon1, lat2, lon2):
    """Calcula distancia aproximada entre dos coordenadas en kilometros."""

    radio_tierra_km = 6371

    lat1_rad = math.radians(float(lat1))
    lon1_rad = math.radians(float(lon1))
    lat2_rad = math.radians(float(lat2))
    lon2_rad = math.radians(float(lon2))

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return radio_tierra_km * c


def crear_matriz_distancias(clientes):
    """Crea matriz de distancias en kilometros."""

    n = len(clientes)
    matriz = np.zeros((n, n), dtype=float)

    for i in range(n):
        for j in range(n):
            if i == j:
                matriz[i][j] = 0
            else:
                matriz[i][j] = haversine_km(
                    clientes.iloc[i]["lat"],
                    clientes.iloc[i]["lon"],
                    clientes.iloc[j]["lat"],
                    clientes.iloc[j]["lon"],
                )

    return matriz


def crear_matriz_tiempos_min(clientes):
    """Convierte distancias aproximadas en minutos."""

    matriz_distancias = crear_matriz_distancias(clientes)
    matriz_tiempos = matriz_distancias / VELOCIDAD_MEDIA_KMH * 60

    return np.ceil(matriz_tiempos).astype(int)

