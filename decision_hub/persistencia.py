# persistencia.py

from sqlalchemy import inspect, text

from app_db import engine


def _columnas_tabla(nombre_tabla):
    inspector = inspect(engine)
    return {
        columna["name"]
        for columna in inspector.get_columns(nombre_tabla, schema="logistica")
    }


def limpiar_rutas(fecha_entrega, id_ejecucion=None):
    columnas = _columnas_tabla("rutas_generadas")

    campo_fecha = (
        "fecha_entrega"
        if "fecha_entrega" in columnas
        else "fecha_operativa"
    )

    filtros = [f"{campo_fecha} = :fecha_entrega"]
    params = {"fecha_entrega": fecha_entrega}

    if id_ejecucion is not None and "id_ejecucion" in columnas:
        filtros.append("id_ejecucion = :id_ejecucion")
        params["id_ejecucion"] = id_ejecucion

    with engine.begin() as conn:
        conn.execute(
            text(
                "DELETE FROM logistica.rutas_generadas "
                f"WHERE {' AND '.join(filtros)}"
            ),
            params,
        )


def _insertar_ruta(conn, columnas_tabla, datos):
    datos = {
        columna: valor
        for columna, valor in datos.items()
        if columna in columnas_tabla
    }

    if not datos:
        raise RuntimeError("No hay columnas compatibles para guardar rutas.")

    columnas = ", ".join(datos.keys())
    valores = ", ".join(f":{columna}" for columna in datos.keys())

    conn.execute(
        text(
            "INSERT INTO logistica.rutas_generadas "
            f"({columnas}) VALUES ({valores})"
        ),
        datos,
    )


def guardar_rutas(
    fecha_entrega,
    dia_operativa,
    rutas,
    id_ejecucion=None,
):
    """
    Guarda la planificación automática de una ejecución.

    Antes de insertar las rutas, elimina únicamente los registros
    correspondientes a la misma fecha y ejecución.
    """

    limpiar_rutas(
        fecha_entrega,
        id_ejecucion=id_ejecucion,
    )

    columnas_tabla = _columnas_tabla(
        "rutas_generadas"
    )

    secuencia_visible_por_salida = {}

    with engine.begin() as conn:

        for r in rutas:

            camion = r["camion"]

            numero_salida = int(
                r.get("numero_salida") or 1
            )

            clave_salida = (
                camion,
                numero_salida,
            )

            secuencia_visible_por_salida[clave_salida] = (
                secuencia_visible_por_salida.get(
                    clave_salida,
                    0,
                )
                + 1
            )

            datos = {
                "id_ejecucion": id_ejecucion,
                "fecha_operativa": fecha_entrega,
                "fecha_entrega": fecha_entrega,
                "dia_operativa": dia_operativa,
                "dia_operativo": dia_operativa,

                "vehiculo_id": r.get("vehiculo_id"),
                "id_camion": r.get("id_camion"),
                "camion": camion,
                "perfil_camion": r.get("perfil_camion"),

                "numero_salida": numero_salida,
                "tipo_salida": (
                    r.get("tipo_salida")
                    or "PLANIFICADA"
                ),
                "autorizacion_manual": bool(
                    r.get(
                        "autorizacion_manual",
                        False,
                    )
                ),
                "minutos_extension": int(
                    r.get("minutos_extension") or 0
                ),
                "motivo_autorizacion": r.get(
                    "motivo_autorizacion"
                ),

                "secuencia":
                    secuencia_visible_por_salida[
                        clave_salida
                    ],

                "id_pedido": r.get("id_pedido"),
                "id_cliente": r.get("id_cliente"),
                "cliente": r.get("cliente"),
                "direccion": r.get(
                    "direccion",
                    "",
                ),
                "barrio": r.get(
                    "barrio",
                    "",
                ),

                "hora_estimada": r.get(
                    "hora_llegada"
                ),
                "hora_llegada": r.get(
                    "hora_llegada"
                ),
                "hora_salida": r.get(
                    "hora_salida"
                ),

                "carga_kg": r.get("carga_kg"),
                "capacidad_camion_kg": r.get(
                    "capacidad_camion_kg"
                ),
                "capacidad_restante": r.get(
                    "capacidad_restante"
                ),

                "lat": r.get("lat"),
                "lon": r.get("lon"),

                "tiempo_viaje_min": r.get(
                    "tiempo_viaje_min"
                ),
                "tiempo_servicio_min": r.get(
                    "tiempo_servicio_min"
                ),
                "tiempo_total_camion_min": r.get(
                    "tiempo_total_camion_min"
                ),

                "distancia_km": r.get(
                    "distancia_km"
                ),
                "distancia_total_camion_km": r.get(
                    "distancia_total_camion_km"
                ),

                "tipo_cliente": r.get(
                    "tipo_cliente"
                ),
                "estado_cliente": r.get(
                    "estado_cliente"
                ),
                "estado_planificacion": r.get(
                    "estado_planificacion"
                ),
                "grupo_logistico": r.get(
                    "grupo_logistico",
                    "",
                ),
                "prioridad": r.get("prioridad"),

                "costo_estimado": r.get(
                    "costo_estimado_camion"
                ),
                "costo_estimado_camion": r.get(
                    "costo_estimado_camion"
                ),

                "estado_asignacion": r.get(
                    "estado_asignacion"
                ),
            }

            _insertar_ruta(
                conn,
                columnas_tabla,
                datos,
            )

    print(
        f"Rutas guardadas correctamente: {len(rutas)}"
    )
def guardar_salida_adicional(
    fecha_entrega,
    dia_operativa,
    rutas,
    id_ejecucion,
    numero_salida,
    tipo_salida="ADICIONAL",
    minutos_extension=0,
    motivo_autorizacion=None,
):
    """
    Añade una salida manual a una ejecución existente.

    No elimina ni modifica las rutas ya guardadas.
    """

    if not rutas:
        raise ValueError(
            "No existen rutas para guardar en la salida adicional."
        )

    if id_ejecucion is None:
        raise ValueError(
            "La salida adicional debe asociarse "
            "a una ejecución existente."
        )

    if int(numero_salida) < 1:
        raise ValueError(
            "El número de salida debe ser mayor que cero."
        )

    tipos_permitidos = {
        "ADICIONAL",
        "EXTRAORDINARIA",
    }

    tipo_salida = str(
        tipo_salida
    ).strip().upper()

    if tipo_salida not in tipos_permitidos:
        raise ValueError(
            "El tipo de salida debe ser "
            "ADICIONAL o EXTRAORDINARIA."
        )

    columnas_tabla = _columnas_tabla(
        "rutas_generadas"
    )

    secuencia_visible_por_camion = {}

    with engine.begin() as conn:

        for r in rutas:

            camion = r["camion"]

            secuencia_visible_por_camion[camion] = (
                secuencia_visible_por_camion.get(
                    camion,
                    0,
                )
                + 1
            )

            datos = {
                "id_ejecucion": id_ejecucion,
                "fecha_operativa": fecha_entrega,
                "fecha_entrega": fecha_entrega,
                "dia_operativa": dia_operativa,
                "dia_operativo": dia_operativa,

                "vehiculo_id": r.get("vehiculo_id"),
                "id_camion": r.get("id_camion"),
                "camion": camion,
                "perfil_camion": r.get(
                    "perfil_camion"
                ),

                "numero_salida": int(
                    numero_salida
                ),
                "tipo_salida": tipo_salida,
                "autorizacion_manual": True,
                "minutos_extension": max(
                    0,
                    int(minutos_extension or 0),
                ),
                "motivo_autorizacion":
                    motivo_autorizacion,

                "secuencia":
                    secuencia_visible_por_camion[
                        camion
                    ],

                "id_pedido": r.get("id_pedido"),
                "id_cliente": r.get("id_cliente"),
                "cliente": r.get("cliente"),
                "direccion": r.get(
                    "direccion",
                    "",
                ),
                "barrio": r.get(
                    "barrio",
                    "",
                ),

                "hora_estimada": r.get(
                    "hora_llegada"
                ),
                "hora_llegada": r.get(
                    "hora_llegada"
                ),
                "hora_salida": r.get(
                    "hora_salida"
                ),

                "carga_kg": r.get("carga_kg"),
                "capacidad_camion_kg": r.get(
                    "capacidad_camion_kg"
                ),
                "capacidad_restante": r.get(
                    "capacidad_restante"
                ),

                "lat": r.get("lat"),
                "lon": r.get("lon"),

                "tiempo_viaje_min": r.get(
                    "tiempo_viaje_min"
                ),
                "tiempo_servicio_min": r.get(
                    "tiempo_servicio_min"
                ),
                "tiempo_total_camion_min": r.get(
                    "tiempo_total_camion_min"
                ),

                "distancia_km": r.get(
                    "distancia_km"
                ),
                "distancia_total_camion_km": r.get(
                    "distancia_total_camion_km"
                ),

                "tipo_cliente": r.get(
                    "tipo_cliente"
                ),
                "estado_cliente": r.get(
                    "estado_cliente"
                ),
                "estado_planificacion": r.get(
                    "estado_planificacion"
                ),
                "grupo_logistico": r.get(
                    "grupo_logistico",
                    "",
                ),
                "prioridad": r.get("prioridad"),

                "costo_estimado": r.get(
                    "costo_estimado_camion"
                ),
                "costo_estimado_camion": r.get(
                    "costo_estimado_camion"
                ),

                "estado_asignacion": (
                    r.get("estado_asignacion")
                    or "ASIGNACION_MANUAL"
                ),
            }

            _insertar_ruta(
                conn,
                columnas_tabla,
                datos,
            )

    print(
        "Salida adicional guardada: "
        f"número {numero_salida}, "
        f"{len(rutas)} parada(s)."
    )
