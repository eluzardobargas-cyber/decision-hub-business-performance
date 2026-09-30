# seed_pedidos.py

import sys
from datetime import date, datetime, timedelta
from sqlalchemy import text

from app_db import engine
from parametros import (
    PERMITIR_ENTREGAS_SABADO,
    PERMITIR_ENTREGAS_DOMINGO,
)


MAPA_DIAS = {
    0: "LUN",
    1: "MAR",
    2: "MIE",
    3: "JUE",
    4: "VIE",
    5: "SAB",
    6: "DOM",
}

INCLUIR_EXCEPCION_CAPACIDAD_DEMO = True

CANTIDAD_PEDIDOS_EXCEPCION_DEMO = 2
PESO_EXCEPCION_CAPACIDAD_KG = 4200

MARCA_EXCEPCION_CAPACIDAD = (
    "ESCENARIO_DEMO_EXCEPCION_CAPACIDAD"
)

def obtener_dia_operativo(fecha_entrega):
    return MAPA_DIAS[fecha_entrega.weekday()]


def siguiente_fecha_entrega(fecha_pedido):
    """
    Regla de preventa:
    - Pedido LUN-JUE -> entrega día siguiente.
    - Pedido VIE -> entrega SAB si hay reparto sábado; si no, LUN.
    - Pedido SAB -> entrega LUN.
    - Pedido DOM -> entrega LUN.
    """

    fecha_entrega = fecha_pedido + timedelta(days=1)

    if fecha_entrega.weekday() == 5 and not PERMITIR_ENTREGAS_SABADO:
        return fecha_entrega + timedelta(days=2)

    if fecha_entrega.weekday() == 6 and not PERMITIR_ENTREGAS_DOMINGO:
        return fecha_entrega + timedelta(days=1)

    if fecha_pedido.weekday() == 5:
        return fecha_pedido + timedelta(days=2)

    if fecha_pedido.weekday() == 6:
        return fecha_pedido + timedelta(days=1)

    return fecha_entrega


def resolver_fechas():
    """
    Uso:
    python seed_pedidos.py
        -> pedido hoy, entrega según regla preventa

    python seed_pedidos.py 2026-07-04
        -> simula fecha de pedido 2026-07-04 y calcula entrega

    python seed_pedidos.py 2026-07-04 entrega
        -> toma 2026-07-04 como fecha de entrega y fecha pedido = día anterior
    """

    if len(sys.argv) > 1:
        fecha = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

        if len(sys.argv) > 2 and sys.argv[2].lower() == "entrega":
            fecha_entrega = fecha
            fecha_pedido = fecha_entrega - timedelta(days=1)
        else:
            fecha_pedido = fecha
            fecha_entrega = siguiente_fecha_entrega(fecha_pedido)
    else:
        fecha_pedido = date.today()
        fecha_entrega = siguiente_fecha_entrega(fecha_pedido)

    return fecha_pedido, fecha_entrega


def generar_pedidos_demo():

    fecha_pedido, fecha_entrega = resolver_fechas()
    dia_operativo = obtener_dia_operativo(fecha_entrega)

    pedidos_creados = 0
    pedidos_extraordinarios = 0

    clientes_excepcion = []
    ids_clientes_excepcion = set()
    orden_clientes_excepcion = {}

    with engine.begin() as conn:

        # Eliminar los pedidos demo anteriores de la fecha.
        # Se mantienen los pedidos que tengan incidencias asociadas.
                # Limpiar decisiones asociadas a excepciones sintéticas
        # de planificación para la fecha que se va a regenerar.
        conn.execute(
            text("""
                DELETE FROM logistica.decisiones_excepciones d
                USING
                    logistica.incidencias_planificacion i,
                    logistica.pedidos p
                WHERE d.id_incidencia = i.id_incidencia
                  AND i.id_pedido = p.id_pedido
                  AND p.fecha_entrega = :fecha_entrega
                  AND p.origen_pedido = 'DEMO'
                  AND i.origen = 'PLANIFICACION'
            """),
            {
                "fecha_entrega": fecha_entrega,
            },
        )

        # Eliminar las incidencias de planificación creadas por
        # ejecuciones sintéticas anteriores de la misma fecha.
        # No se eliminan incidencias originadas durante el reparto.
        conn.execute(
            text("""
                DELETE FROM logistica.incidencias_planificacion i
                USING logistica.pedidos p
                WHERE i.id_pedido = p.id_pedido
                  AND p.fecha_entrega = :fecha_entrega
                  AND p.origen_pedido = 'DEMO'
                  AND i.origen = 'PLANIFICACION'
            """),
            {
                "fecha_entrega": fecha_entrega,
            },
        )

        # Eliminar los pedidos demo anteriores, salvo aquellos
        # vinculados a una incidencia real de reparto.
        conn.execute(
            text("""
                DELETE FROM logistica.pedidos p
                WHERE p.fecha_entrega = :fecha_entrega
                  AND p.origen_pedido = 'DEMO'
                  AND NOT EXISTS (
                      SELECT 1
                      FROM logistica.incidencias_planificacion i
                      WHERE i.id_pedido = p.id_pedido
                        AND i.origen = 'REPARTO'
                  )
            """),
            {
                "fecha_entrega": fecha_entrega,
            },
        )

        clientes = conn.execute(
            text("""
                SELECT
                    id_cliente,
                    nombre,
                    dias_asignados,
                    demanda,
                    prioridad,
                    tipo
                FROM logistica.clientes
                WHERE activo = TRUE
                  AND es_deposito = FALSE
                ORDER BY id_cliente
            """)
        ).mappings().all()

        # Clientes que ya tienen un pedido conservado para esa fecha,
        # por ejemplo, pedidos trasladados desde una incidencia anterior.
        ids_clientes_con_pedido_existente = {
            int(id_cliente)
            for id_cliente in conn.execute(
                text("""
                    SELECT DISTINCT id_cliente
                    FROM logistica.pedidos
                    WHERE fecha_entrega = :fecha_entrega
                """),
                {
                    "fecha_entrega": fecha_entrega,
                },
            ).scalars().all()
        }

        # Seleccionar clientes diferentes para el escenario.
        # Se excluyen los clientes que ya tienen un pedido conservado
        # para la fecha y se priorizan los que no son cadenas.
        if INCLUIR_EXCEPCION_CAPACIDAD_DEMO and clientes:

            candidatos = [
                cliente
                for cliente in clientes
                if int(cliente["id_cliente"])
                not in ids_clientes_con_pedido_existente
            ]

            candidatos = sorted(
                candidatos,
                key=lambda cliente: (
                    str(cliente["tipo"] or "")
                    .strip()
                    .upper()
                    == "CADENA",
                    int(cliente["id_cliente"]),
                ),
            )

            clientes_excepcion = candidatos[
                :CANTIDAD_PEDIDOS_EXCEPCION_DEMO
            ]

            ids_clientes_excepcion = {
                int(cliente["id_cliente"])
                for cliente in clientes_excepcion
            }

            orden_clientes_excepcion = {
                int(cliente["id_cliente"]): numero
                for numero, cliente in enumerate(
                    clientes_excepcion,
                    start=1,
                )
            }

        for cliente in clientes:

            id_cliente = int(cliente["id_cliente"])
            # No generar otro pedido si el cliente ya tiene uno
            # conservado para la misma fecha.
            if id_cliente in ids_clientes_con_pedido_existente:
                continue

            dias_asignados = str(
                cliente["dias_asignados"] or ""
            )

            dias_cliente = [
                dia.strip().upper()
                for dia in dias_asignados.split(",")
                if dia.strip()
            ]

            corresponde_dia = (
                dia_operativo in dias_cliente
            )

            prioridad_cliente = str(
                cliente["prioridad"] or "NORMAL"
            ).strip().upper()

            es_excepcion_capacidad = (
                INCLUIR_EXCEPCION_CAPACIDAD_DEMO
                and id_cliente in ids_clientes_excepcion
            )

            # Los pedidos especiales se incorporan siempre
            # como extraordinarios, aunque el cliente no tenga
            # asignado el día de reparto.
            if es_excepcion_capacidad:

                estado_planificacion = "EXTRAORDINARIO"
                pedidos_extraordinarios += 1

            elif corresponde_dia:

                estado_planificacion = "PROGRAMADO"

            elif prioridad_cliente == "URGENTE":

                estado_planificacion = "EXTRAORDINARIO"
                pedidos_extraordinarios += 1

            else:

                continue

            if es_excepcion_capacidad:

                numero_excepcion = (
                    orden_clientes_excepcion[id_cliente]
                )

                peso_pedido = float(
                    PESO_EXCEPCION_CAPACIDAD_KG
                )

                prioridad_pedido = "NORMAL"

                observacion_pedido = (
                    f"{MARCA_EXCEPCION_CAPACIDAD}_"
                    f"{numero_excepcion}"
                    " | Pedido preparado para demostrar "
                    "la gestión administrativa de una "
                    "salida adicional."
                )

            else:

                peso_pedido = float(
                    cliente["demanda"] or 0
                )

                prioridad_pedido = prioridad_cliente

                observacion_pedido = (
                    "Pedido generado para día habitual"
                    if estado_planificacion == "PROGRAMADO"
                    else
                    "Pedido extraordinario incluido "
                    "para evaluación"
                )

            conn.execute(
                text("""
                    INSERT INTO logistica.pedidos
                    (
                        id_cliente,
                        fecha_pedido,
                        fecha_entrega,
                        cantidad_bultos,
                        peso_kg,
                        volumen_m3,
                        prioridad,
                        estado_pedido,
                        estado_planificacion,
                        observaciones,
                        origen_pedido
                    )
                    VALUES
                    (
                        :id_cliente,
                        :fecha_pedido,
                        :fecha_entrega,
                        :cantidad_bultos,
                        :peso_kg,
                        :volumen_m3,
                        :prioridad,
                        :estado_pedido,
                        :estado_planificacion,
                        :observaciones,
                        :origen_pedido
                    )
                """),
                {
                    "id_cliente": id_cliente,
                    "fecha_pedido": fecha_pedido,
                    "fecha_entrega": fecha_entrega,
                    "cantidad_bultos": max(
                        1,
                        int(peso_pedido / 50),
                    ),
                    "peso_kg": peso_pedido,
                    "volumen_m3": round(
                        peso_pedido / 350,
                        2,
                    ),
                    "prioridad": prioridad_pedido,
                    "estado_pedido": "VALIDADO",
                    "estado_planificacion":
                        estado_planificacion,
                    "observaciones":
                        observacion_pedido,
                    "origen_pedido": "DEMO",
                },
            )

            pedidos_creados += 1

    print("✅ Pedidos demo generados correctamente")
    print(f"Fecha pedido: {fecha_pedido}")
    print(f"Fecha entrega: {fecha_entrega}")
    print(f"Día operativo: {dia_operativo}")
    print(f"Pedidos creados: {pedidos_creados}")
    print(f"Extraordinarios: {pedidos_extraordinarios}")

    if clientes_excepcion:

        print(
            "⚠️ Escenario de capacidad incluido: "
            f"{len(clientes_excepcion)} pedidos de "
            f"{PESO_EXCEPCION_CAPACIDAD_KG} kg"
        )

        for numero, cliente in enumerate(
            clientes_excepcion,
            start=1,
        ):
            print(
                f"   {numero}. "
                f"{cliente['nombre']} — "
                f"{PESO_EXCEPCION_CAPACIDAD_KG} kg"
            )

    elif INCLUIR_EXCEPCION_CAPACIDAD_DEMO:

        print(
            "⚠️ No fue posible seleccionar clientes "
            "para el escenario de excepción."
        )

if __name__ == "__main__":
    generar_pedidos_demo()