# gestion_incidencias.py

from sqlalchemy import inspect, text

from app_db import engine


def _columnas_tabla(nombre_tabla):
    inspector = inspect(engine)
    return {
        columna["name"]
        for columna in inspector.get_columns(nombre_tabla, schema="logistica")
    }


def limpiar_incidencias(fecha_entrega, id_ejecucion=None):
    """
    Elimina únicamente incidencias generadas por la planificación.

    Las incidencias abiertas de reparto deben conservarse porque actúan
    como cola de pedidos pendientes de reintento.
    """
    columnas = _columnas_tabla("incidencias_planificacion")

    filtros = ["fecha_entrega = :fecha_entrega"]
    params = {"fecha_entrega": fecha_entrega}

    if "origen" in columnas:
        filtros.append(
            "(origen IS NULL OR origen = 'PLANIFICACION')"
        )

    if id_ejecucion is not None and "id_ejecucion" in columnas:
        filtros.append("id_ejecucion = :id_ejecucion")
        params["id_ejecucion"] = id_ejecucion

    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM logistica.incidencias_planificacion "
                f"WHERE {' AND '.join(filtros)}"
            ),
            params,
        )


def registrar_incidencia(
    id_pedido,
    fecha_entrega,
    cliente,
    tipo,
    gravedad,
    accion,
    id_ejecucion=None,
    motivo=None,
):
    columnas_tabla = _columnas_tabla("incidencias_planificacion")

    datos = {
        "id_ejecucion": id_ejecucion,
        "id_pedido": id_pedido,
        "fecha_entrega": fecha_entrega,
        "cliente": cliente,
        "tipo_incidencia": tipo,
        "gravedad": gravedad,
        "motivo": motivo,
        "accion_sugerida": accion,
        "origen": "PLANIFICACION",
        "estado_incidencia": "ABIERTA",
        }

    datos = {
        columna: valor
        for columna, valor in datos.items()
        if columna in columnas_tabla
    }

    if not datos:
        raise RuntimeError("No hay columnas compatibles para guardar incidencias.")

    columnas = ", ".join(datos.keys())
    valores = ", ".join(f":{columna}" for columna in datos.keys())

    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO logistica.incidencias_planificacion "
                f"({columnas}) VALUES ({valores})"
            ),
            datos,
        )
def cerrar_incidencias_planificacion_asignadas(
    fecha_entrega,
    ids_asignados,
):
    """
    Cierra las incidencias abiertas de planificación cuando
    el pedido ya aparece asignado en la planificación vigente.
    """

    if not ids_asignados:
        return

    with engine.begin() as conn:

        for id_pedido in ids_asignados:

            conn.execute(
                text("""
                    UPDATE logistica.incidencias_planificacion
                    SET
                        resuelta = TRUE,
                        estado_incidencia = 'CERRADA',
                        observacion = CASE
                            WHEN observacion IS NULL
                                 OR TRIM(observacion) = ''
                            THEN
                                'Cerrada automáticamente: '
                                'el pedido fue asignado a una ruta.'
                            ELSE
                                observacion
                                || ' | Cerrada automáticamente: '
                                'el pedido fue asignado a una ruta.'
                        END
                    WHERE id_pedido = :id_pedido
                      AND fecha_entrega = :fecha_entrega
                      AND origen = 'PLANIFICACION'
                      AND estado_incidencia = 'ABIERTA'
                """),
                {
                    "id_pedido": int(id_pedido),
                    "fecha_entrega": fecha_entrega,
                },
            )
from datetime import timedelta


def siguiente_dia_operativo(fecha):

    siguiente = fecha + timedelta(days=1)

    while True:

        # Domingo
        if siguiente.weekday() == 6:
            siguiente += timedelta(days=1)
            continue

        return siguiente


def registrar_incidencia_reparto(
    id_pedido,
    fecha_entrega,
    cliente,
    estado,
    motivo,
    observacion,
):
    fecha_reintento = siguiente_dia_operativo(fecha_entrega)

    with engine.begin() as conn:
        # Evita duplicar la incidencia si se pulsa Guardar varias veces
        # durante el mismo intento de entrega.
        incidencia_mismo_intento = conn.execute(
            text("""
                SELECT id_incidencia
                FROM logistica.incidencias_planificacion
                WHERE id_pedido = :id_pedido
                  AND fecha_entrega = :fecha_entrega
                  AND origen = 'REPARTO'
                  AND estado_incidencia = 'ABIERTA'
                ORDER BY id_incidencia DESC
                LIMIT 1
            """),
            {
                "id_pedido": int(id_pedido),
                "fecha_entrega": fecha_entrega,
            },
        ).first()

        if incidencia_mismo_intento:
            conn.execute(
                text("""
                    UPDATE logistica.incidencias_planificacion
                    SET
                        tipo_incidencia = :tipo,
                        motivo = :motivo,
                        observacion = :observacion,
                        fecha_reintento = :fecha_reintento,
                        accion_sugerida =
                            'Reintentar entrega automáticamente.'
                    WHERE id_incidencia = :id_incidencia
                """),
                {
                    "tipo": estado,
                    "motivo": motivo,
                    "observacion": observacion,
                    "fecha_reintento": fecha_reintento,
                    "id_incidencia": incidencia_mismo_intento.id_incidencia,
                },
            )
            return

        # Si este es un nuevo intento fallido, la incidencia anterior
        # ya fue atendida y queda guardada como parte del histórico.
        conn.execute(
            text("""
                UPDATE logistica.incidencias_planificacion
                SET
                    resuelta = TRUE,
                    estado_incidencia = 'REINTENTADA'
                WHERE id_pedido = :id_pedido
                  AND origen = 'REPARTO'
                  AND estado_incidencia = 'ABIERTA'
                  AND fecha_reintento = :fecha_entrega
            """),
            {
                "id_pedido": int(id_pedido),
                "fecha_entrega": fecha_entrega,
            },
        )

        # Registra el resultado del nuevo intento como una incidencia nueva.
        conn.execute(
            text("""
                INSERT INTO logistica.incidencias_planificacion
                (
                    id_pedido,
                    fecha_entrega,
                    fecha_reintento,
                    cliente,
                    tipo_incidencia,
                    gravedad,
                    motivo,
                    observacion,
                    accion_sugerida,
                    origen,
                    estado_incidencia,
                    resuelta
                )
                VALUES
                (
                    :id_pedido,
                    :fecha_entrega,
                    :fecha_reintento,
                    :cliente,
                    :tipo,
                    'MEDIA',
                    :motivo,
                    :observacion,
                    'Reintentar entrega automáticamente.',
                    'REPARTO',
                    'ABIERTA',
                    FALSE
                )
            """),
            {
                "id_pedido": int(id_pedido),
                "fecha_entrega": fecha_entrega,
                "fecha_reintento": fecha_reintento,
                "cliente": cliente,
                "tipo": estado,
                "motivo": motivo,
                "observacion": observacion,
            },
        )