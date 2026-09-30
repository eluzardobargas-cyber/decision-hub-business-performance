# repositorio.py

import pandas as pd
from app_db import engine


def cargar_clientes():
    sql = """
    SELECT *
    FROM logistica.clientes
    WHERE activo = TRUE
    """
    return pd.read_sql(sql, engine)


def cargar_flota():
    sql = """
    SELECT *
    FROM logistica.flota
    ORDER BY id_camion
    """
    return pd.read_sql(sql, engine)


def cargar_pedidos_planificables(fecha_entrega):
    """
    Recupera el conjunto completo que debe entrar en la planificación:

    1. Pedidos normales previstos para la fecha.
    2. Pedidos pendientes de reintento por una incidencia abierta de reparto.

    Si un pedido aparece en ambos conjuntos, se conserva una sola vez y
    prevalece su condición de reintento urgente.
    """

    sql = """
    WITH candidatos AS (

        -- Pedidos normales de la fecha
        SELECT
            p.id_pedido,
            p.id_cliente,
            p.fecha_pedido,
            p.fecha_entrega,
            p.peso_kg,
            p.volumen_m3,
            p.prioridad AS prioridad_pedido,
            p.estado_planificacion,

            c.nombre,
            c.direccion,
            '' AS barrio,
            c.lat,
            c.lon,
            c.tipo,
            c.estado_cliente,
            c.dias_asignados,
            c.demora,
            c.abre,
            c.cierra,
            c.es_deposito,

            0 AS es_reintento

        FROM logistica.pedidos p

        JOIN logistica.clientes c
            ON p.id_cliente = c.id_cliente

        WHERE p.fecha_entrega = %(fecha_entrega)s
          AND p.estado_pedido = 'VALIDADO'
          AND p.estado_planificacion IN (
              'PROGRAMADO',
              'EXTRAORDINARIO'
          )


        UNION ALL


        -- Pedidos recuperados desde incidencias abiertas de reparto
        SELECT
            p.id_pedido,
            p.id_cliente,
            p.fecha_pedido,
            i.fecha_reintento AS fecha_entrega,
            p.peso_kg,
            p.volumen_m3,
            'URGENTE' AS prioridad_pedido,
            'EXTRAORDINARIO' AS estado_planificacion,

            c.nombre,
            c.direccion,
            '' AS barrio,
            c.lat,
            c.lon,
            c.tipo,
            c.estado_cliente,
            c.dias_asignados,
            c.demora,
            c.abre,
            c.cierra,
            c.es_deposito,

            1 AS es_reintento

        FROM logistica.incidencias_planificacion i

        JOIN logistica.pedidos p
            ON i.id_pedido = p.id_pedido

        JOIN logistica.clientes c
            ON p.id_cliente = c.id_cliente

        WHERE i.fecha_reintento = %(fecha_entrega)s
          AND i.origen = 'REPARTO'
          AND i.estado_incidencia = 'ABIERTA'
          AND p.estado_pedido <> 'ENTREGADO'
    ),

    candidatos_unicos AS (
        SELECT
            *,
            ROW_NUMBER() OVER (
                PARTITION BY id_pedido
                ORDER BY es_reintento DESC
            ) AS numero_fila
        FROM candidatos
    )

    SELECT
        id_pedido,
        id_cliente,
        fecha_pedido,
        fecha_entrega,
        peso_kg,
        volumen_m3,
        prioridad_pedido,
        estado_planificacion,
        nombre,
        direccion,
        barrio,
        lat,
        lon,
        tipo,
        estado_cliente,
        dias_asignados,
        demora,
        abre,
        cierra,
        es_deposito

    FROM candidatos_unicos

    WHERE numero_fila = 1

    ORDER BY
        CASE
            WHEN prioridad_pedido = 'URGENTE' THEN 0
            ELSE 1
        END,
        tipo,
        nombre
    """

    return pd.read_sql(
        sql,
        engine,
        params={"fecha_entrega": fecha_entrega},
    )


def cargar_deposito():
    sql = """
    SELECT *
    FROM logistica.clientes
    WHERE es_deposito = TRUE
    LIMIT 1
    """
    return pd.read_sql(sql, engine)