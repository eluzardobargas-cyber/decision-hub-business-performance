# app.py

import urllib.parse
import folium
from streamlit_folium import st_folium
import sys
import subprocess
import streamlit as st
import pandas as pd
from sqlalchemy import text
from pathlib import Path

from app_db import engine
from gestion_incidencias import registrar_incidencia_reparto
from optimizador import generar_ruta_para_excepcion
from persistencia import guardar_salida_adicional
from datetime import timedelta

from parametros import (
    PERMITIR_ENTREGAS_SABADO,
    PERMITIR_ENTREGAS_DOMINGO,
    TIEMPO_PREPARACION_NUEVA_SALIDA_MIN,
)

# Directorio base del módulo para resolver scripts independientemente
# de la carpeta desde la que se ejecute Streamlit.
BASE_DIR = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Decision Hub | Operations",
    layout="wide"
)

st.title("Decision Hub | Operations")


def ejecutar_script(script, *args):
    import os

    script_path = BASE_DIR / script
    comando = [sys.executable, str(script_path), *args]

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"

    resultado = subprocess.run(
        comando,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        cwd=BASE_DIR,   #hace que los procesos secundarios se ejecuten con decision_hub como directorio de trabajo.
    )

    return resultado

def ejecutar_planificacion_operativa(fecha_pedido, generar_demo=False):
    pasos = []

    if generar_demo:
        pasos.append(("seed_pedidos.py", fecha_pedido))

    pasos.extend(
        [
            ("validacion_pedidos.py", fecha_pedido),
            ("optimizador.py", fecha_pedido),
        ]
    )

    salidas = []

    for script, fecha in pasos:
        resultado = ejecutar_script(script, fecha)

        if resultado.returncode != 0:
            return {
                "ok": False,
                "script": script,
                "salida": resultado.stdout,
                "error": resultado.stderr,
            }

        salidas.append(resultado.stdout)

    return {
        "ok": True,
        "salida": "\n".join(salidas),
        "error": "",
    }

def cargar_fechas():
    return pd.read_sql("""
        SELECT DISTINCT fecha_operativa
        FROM logistica.rutas_generadas
        ORDER BY fecha_operativa DESC
    """, engine)


def cargar_rutas(fecha):
    return pd.read_sql(
        """
        SELECT *
        FROM logistica.rutas_generadas
        WHERE fecha_operativa = %(fecha)s
          AND id_ejecucion = (
              SELECT id_ejecucion
              FROM logistica.rutas_generadas
              WHERE fecha_operativa = %(fecha)s
                AND id_ejecucion IS NOT NULL
              ORDER BY fecha_registro DESC
              LIMIT 1
          )
        ORDER BY
            camion,
            COALESCE(numero_salida, 1),
            secuencia
        """,
        engine,
        params={"fecha": fecha},
    )


def cargar_incidencias(fecha):
    return pd.read_sql("""
        SELECT *
        FROM logistica.incidencias_planificacion
        WHERE fecha_entrega = %(fecha)s
        ORDER BY fecha_registro DESC
    """, engine, params={"fecha": fecha})

def cargar_excepciones_planificacion(fecha):
    return pd.read_sql(
        """
        SELECT
            i.id_incidencia,
            i.id_pedido,
            i.fecha_entrega,
            i.cliente,
            i.tipo_incidencia,
            i.gravedad,
            i.motivo,
            i.accion_sugerida,
            i.estado_incidencia,
            i.observacion,

            p.id_cliente,
            p.peso_kg,
            p.volumen_m3,
            p.prioridad,
            p.estado_pedido,
            p.estado_planificacion

        FROM logistica.incidencias_planificacion i

        LEFT JOIN logistica.pedidos p
            ON p.id_pedido = i.id_pedido

        WHERE i.fecha_entrega = %(fecha)s
          AND i.origen = 'PLANIFICACION'
          AND i.estado_incidencia = 'ABIERTA'
          AND i.tipo_incidencia = 'APROBACION_MANUAL'

        ORDER BY i.fecha_registro ASC
        """,
        engine,
        params={"fecha": fecha},
    )


def cargar_resumen_camiones(fecha):
    return pd.read_sql(
        """
        WITH ultima_ejecucion AS (
            SELECT MAX(id_ejecucion) AS id_ejecucion
            FROM logistica.rutas_generadas
            WHERE fecha_operativa = %(fecha)s
        ),

        rutas_ultima_ejecucion AS (
            SELECT rg.*
            FROM logistica.rutas_generadas rg

            INNER JOIN ultima_ejecucion ue
                ON rg.id_ejecucion = ue.id_ejecucion

            WHERE rg.fecha_operativa = %(fecha)s
        ),

        resumen_por_salida AS (
            SELECT
                camion,
                numero_salida,

                COALESCE(
                    SUM(carga_kg),
                    0
                ) AS carga_salida,

                COALESCE(
                    SUM(
                        COALESCE(tiempo_viaje_min, 0)
                        + COALESCE(tiempo_servicio_min, 0)
                    ),
                    0
                ) AS tiempo_salida_min

            FROM rutas_ultima_ejecucion

            GROUP BY
                camion,
                numero_salida
        ),

        resumen_diario AS (
            SELECT
                camion,
                COALESCE(SUM(tiempo_salida_min), 0)
                    AS tiempo_total_min,
                COALESCE(MAX(numero_salida), 0)
                    AS ultima_salida

            FROM resumen_por_salida

            GROUP BY camion
        ),

        ultima_salida_camion AS (
            SELECT DISTINCT ON (camion)
                camion,
                numero_salida,
                carga_salida,
                tiempo_salida_min

            FROM resumen_por_salida

            ORDER BY
                camion,
                numero_salida DESC
        )

        SELECT
            f.descripcion AS camion,
            f.capacidad_kg,
            f.jornada_max_min,

            COALESCE(
                usc.carga_salida,
                0
            ) AS carga_salida_actual,

            f.capacidad_kg
                - COALESCE(usc.carga_salida, 0)
                AS capacidad_disponible_salida_actual,

            COALESCE(
                rd.tiempo_total_min,
                0
            ) AS tiempo_total_min,

            f.jornada_max_min
                - COALESCE(rd.tiempo_total_min, 0)
                AS minutos_disponibles,

            COALESCE(
                rd.ultima_salida,
                0
            ) AS ultima_salida,

            COALESCE(
                usc.tiempo_salida_min,
                0
            ) AS tiempo_ultima_salida_min

        FROM logistica.flota f

        LEFT JOIN resumen_diario rd
            ON rd.camion = f.descripcion

        LEFT JOIN ultima_salida_camion usc
            ON usc.camion = f.descripcion

        ORDER BY f.descripcion
        """,
        engine,
        params={"fecha": fecha},
    )

def diagnosticar_excepcion(pedido, resumen_camiones):
    """
    Realiza un diagnóstico preliminar de las alternativas disponibles
    para un pedido que quedó fuera de ruta.

    La validación definitiva se realizará al calcular la nueva salida
    o al incorporar el pedido a una ruta.
    """

    peso_valor = pedido.get("peso_kg")

    peso_pedido = (
        0.0
        if pd.isna(peso_valor)
        else float(peso_valor)
    )

    diagnosticos = []

    for _, camion in resumen_camiones.iterrows():

        def valor_numerico(columna):
            valor = camion.get(columna)

            if pd.isna(valor):
                return 0.0

            return float(valor)

        capacidad_total = valor_numerico(
            "capacidad_kg"
        )

        carga_salida_actual = valor_numerico(
            "carga_salida_actual"
        )

        capacidad_disponible_actual = valor_numerico(
            "capacidad_disponible_salida_actual"
        )

        jornada_maxima = valor_numerico(
            "jornada_max_min"
        )

        tiempo_total = valor_numerico(
            "tiempo_total_min"
        )

        minutos_disponibles = valor_numerico(
            "minutos_disponibles"
        )

        ultima_salida = int(
            valor_numerico("ultima_salida")
        )

        cabe_en_salida_actual = (
            capacidad_disponible_actual >= peso_pedido
        )

        cabe_en_nueva_salida = (
            capacidad_total >= peso_pedido
        )

        existe_tiempo_disponible = (
            minutos_disponibles > 0
        )

        if not cabe_en_nueva_salida:

            situacion = "SIN_VEHICULO_COMPATIBLE"

            accion_sugerida = (
                "Evaluar otro vehículo o mover a otra fecha"
            )

        elif ultima_salida == 0 and existe_tiempo_disponible:

            situacion = "VEHICULO_SIN_SALIDA"

            accion_sugerida = (
                "Crear una salida estándar"
            )

        elif cabe_en_salida_actual and existe_tiempo_disponible:

            situacion = "POSIBLE_SALIDA_ACTUAL"

            accion_sugerida = (
                "Evaluar incorporación a la salida actual"
            )

        elif (
            not cabe_en_salida_actual
            and existe_tiempo_disponible
        ):

            situacion = "CAPACIDAD"

            accion_sugerida = (
                "Crear una nueva salida estándar"
            )

        elif (
            cabe_en_salida_actual
            and not existe_tiempo_disponible
        ):

            situacion = "JORNADA"

            accion_sugerida = (
                "Autorizar extensión de jornada "
                "o mover a otra fecha"
            )

        else:

            situacion = "CAPACIDAD_Y_JORNADA"

            accion_sugerida = (
                "Crear una salida extraordinaria "
                "o mover a otra fecha"
            )

        diagnosticos.append(
            {
                "camion": camion["camion"],
                "capacidad_kg": capacidad_total,
                "carga_salida_actual": carga_salida_actual,
                "capacidad_disponible_salida_actual":
                    capacidad_disponible_actual,
                "peso_pedido": peso_pedido,
                "jornada_max_min": jornada_maxima,
                "tiempo_total_min": tiempo_total,
                "minutos_disponibles": minutos_disponibles,
                "ultima_salida": ultima_salida,
                "cabe_en_salida_actual":
                    cabe_en_salida_actual,
                "cabe_en_nueva_salida":
                    cabe_en_nueva_salida,
                "situacion": situacion,
                "accion_sugerida": accion_sugerida,
            }
        )

    return pd.DataFrame(diagnosticos)

def mover_excepcion_a_otra_fecha(
    id_incidencia,
    id_pedido,
    fecha_operativa,
    nueva_fecha,
    observacion,
):
    """
    Reprograma un pedido pendiente de aprobación manual.

    El pedido se incorpora a la nueva fecha como urgente y
    extraordinario. La incidencia original queda cerrada y
    la decisión administrativa se conserva en el histórico.
    """

    if nueva_fecha <= fecha_operativa:
        raise ValueError(
            "La nueva fecha debe ser posterior a la fecha operativa."
        )

    if nueva_fecha.weekday() == 6:
        raise ValueError(
            "No se puede reprogramar una entrega para domingo."
        )

    observacion_limpia = (
        observacion.strip()
        if observacion
        else "Pedido reprogramado por decisión administrativa."
    )

    with engine.begin() as conn:

        # Incorporar el pedido a la nueva fecha.
        conn.execute(
            text(
                """
                UPDATE logistica.pedidos
                SET
                    fecha_entrega = :nueva_fecha,
                    prioridad = 'URGENTE',
                    estado_planificacion = 'EXTRAORDINARIO'
                WHERE id_pedido = :id_pedido
                """
            ),
            {
                "id_pedido": int(id_pedido),
                "nueva_fecha": nueva_fecha,
            },
        )

        # Cerrar la incidencia de planificación.
        conn.execute(
            text(
                """
                UPDATE logistica.incidencias_planificacion
                SET
                    resuelta = TRUE,
                    estado_incidencia = 'CERRADA',
                    fecha_reintento = :nueva_fecha,
                    observacion = :observacion
                WHERE id_incidencia = :id_incidencia
                  AND id_pedido = :id_pedido
                  AND estado_incidencia = 'ABIERTA'
                """
            ),
            {
                "id_incidencia": int(id_incidencia),
                "id_pedido": int(id_pedido),
                "nueva_fecha": nueva_fecha,
                "observacion": observacion_limpia,
            },
        )

        # Guardar la decisión administrativa.
        conn.execute(
            text(
                """
                INSERT INTO logistica.decisiones_excepciones
                (
                    id_pedido,
                    id_incidencia,
                    fecha_operativa,
                    tipo_restriccion,
                    decision_tomada,
                    nueva_fecha,
                    motivo,
                    observacion,
                    usuario_decision,
                    estado
                )
                VALUES
                (
                    :id_pedido,
                    :id_incidencia,
                    :fecha_operativa,
                    'PENDIENTE_ANALISIS',
                    'MOVER_A_OTRA_FECHA',
                    :nueva_fecha,
                    'Pedido excluido de la planificación automática.',
                    :observacion,
                    'Administrador',
                    'APLICADA'
                )
                """
            ),
            {
                "id_pedido": int(id_pedido),
                "id_incidencia": int(id_incidencia),
                "fecha_operativa": fecha_operativa,
                "nueva_fecha": nueva_fecha,
                "observacion": observacion_limpia,
            },
        )

def cargar_contexto_nueva_salida(
    fecha_operativa,
    camion,
):
    """
    Recupera la ejecución vigente, el tiempo acumulado
    del vehículo y el siguiente número de salida.

    El tiempo utilizado se calcula sumando los tiempos
    de viaje y servicio guardados en cada parada.
    """

    return pd.read_sql(
        """
        WITH ultima_ejecucion AS (
            SELECT id_ejecucion
            FROM logistica.rutas_generadas
            WHERE fecha_operativa = %(fecha)s
              AND id_ejecucion IS NOT NULL
            ORDER BY fecha_registro DESC
            LIMIT 1
        ),

        tiempos_por_salida AS (
            SELECT
                COALESCE(
                    rg.numero_salida,
                    1
                ) AS numero_salida,

                SUM(
                    COALESCE(
                        rg.tiempo_viaje_min,
                        0
                    )
                    +
                    COALESCE(
                        rg.tiempo_servicio_min,
                        0
                    )
                ) AS minutos_salida

            FROM logistica.rutas_generadas rg

            INNER JOIN ultima_ejecucion ue
                ON ue.id_ejecucion = rg.id_ejecucion

            WHERE rg.fecha_operativa = %(fecha)s
              AND rg.camion = %(camion)s

            GROUP BY
                COALESCE(
                    rg.numero_salida,
                    1
                )
        ),

        resumen_camion AS (
            SELECT
                COALESCE(
                    SUM(minutos_salida),
                    0
                ) AS minutos_utilizados,

                COALESCE(
                    MAX(numero_salida),
                    0
                ) + 1 AS numero_salida

            FROM tiempos_por_salida
        )

        SELECT
            ue.id_ejecucion,

            f.descripcion AS camion,
            f.capacidad_kg,
            f.jornada_max_min,

            rc.minutos_utilizados,
            rc.numero_salida

        FROM ultima_ejecucion ue

        INNER JOIN logistica.flota f
            ON f.descripcion = %(camion)s

        CROSS JOIN resumen_camion rc
        """,
        engine,
        params={
            "fecha": fecha_operativa,
            "camion": camion,
        },
    )


def calcular_duracion_salida(rutas):
    """
    Obtiene la duración total calculada por OR-Tools.

    Si el motor devuelve el total del camión en cada parada,
    se utiliza el valor máximo para evitar duplicarlo.
    """

    duraciones = []

    for ruta in rutas:
        valor = ruta.get(
            "tiempo_total_camion_min"
        )

        if (
            valor is not None
            and not pd.isna(valor)
        ):
            duraciones.append(
                float(valor)
            )

    if duraciones:
        return max(duraciones)

    return sum(
        float(
            ruta.get("tiempo_viaje_min")
            or 0
        )
        +
        float(
            ruta.get("tiempo_servicio_min")
            or 0
        )
        for ruta in rutas
    )


def desplazar_hora_ruta(
    valor_hora,
    minutos_desplazamiento,
):
    """
    Desplaza una hora calculada por OR-Tools.

    Se utiliza para situar la nueva salida después del
    tiempo consumido por las salidas anteriores y del
    tiempo de preparación en el depósito.
    """

    if (
        valor_hora is None
        or pd.isna(valor_hora)
    ):
        return None

    hora = pd.to_datetime(
        str(valor_hora),
        errors="coerce",
    )

    if pd.isna(hora):
        return valor_hora

    hora_desplazada = (
        hora
        + pd.Timedelta(
            minutes=int(
                minutos_desplazamiento
            )
        )
    )

    return hora_desplazada.strftime(
        "%H:%M"
    )


def hora_a_minutos(valor_hora):
    """
    Convierte una hora a minutos desde medianoche
    para poder comparar llegada y cierre del cliente.
    """

    if (
        valor_hora is None
        or pd.isna(valor_hora)
    ):
        return None

    hora = pd.to_datetime(
        str(valor_hora),
        errors="coerce",
    )

    if pd.isna(hora):
        return None

    return int(
        hora.hour * 60
        + hora.minute
    )


def crear_nueva_salida_desde_excepcion(
    id_incidencia,
    id_pedido,
    fecha_operativa,
    camion,
    observacion,
):
    """
    Crea una salida adicional estándar para resolver
    un pedido pendiente de aprobación manual.

    La operación:

    - conserva las salidas existentes;
    - calcula la nueva ruta mediante OR-Tools;
    - añade el tiempo de preparación definido;
    - comprueba la jornada máxima;
    - comprueba el cierre del cliente;
    - guarda la nueva salida;
    - cierra la incidencia;
    - registra la decisión administrativa.

    Si la jornada máxima se supera, la salida estándar
    no se crea y deberá utilizarse otra alternativa.
    """

    contexto_df = cargar_contexto_nueva_salida(
        fecha_operativa=fecha_operativa,
        camion=camion,
    )

    if contexto_df.empty:
        raise ValueError(
            "No se encontró una planificación vigente "
            "para la fecha y el camión seleccionados."
        )

    contexto = contexto_df.iloc[0]

    id_ejecucion = contexto[
        "id_ejecucion"
    ]

    numero_salida = int(
        contexto["numero_salida"]
    )

    minutos_utilizados = (
        0.0
        if pd.isna(
            contexto["minutos_utilizados"]
        )
        else float(
            contexto["minutos_utilizados"]
        )
    )

    jornada_maxima = (
        0.0
        if pd.isna(
            contexto["jornada_max_min"]
        )
        else float(
            contexto["jornada_max_min"]
        )
    )

    if jornada_maxima <= 0:
        raise ValueError(
            "El camión seleccionado no tiene una "
            "jornada máxima válida."
        )

    rutas = generar_ruta_para_excepcion(
        fecha_entrega=fecha_operativa,
        id_pedido=int(id_pedido),
        camion=camion,
    )

    if not rutas:
        raise ValueError(
            "El motor no generó una ruta para "
            "el pedido seleccionado."
        )

    duracion_nueva_salida = (
        calcular_duracion_salida(
            rutas
        )
    )

    minutos_preparacion = int(
        TIEMPO_PREPARACION_NUEVA_SALIDA_MIN
    )

    minutos_totales_estimados = (
        minutos_utilizados
        + minutos_preparacion
        + duracion_nueva_salida
    )

    minutos_extension = max(
        0,
        int(
            minutos_totales_estimados
            - jornada_maxima
        ),
    )

    if minutos_extension > 0:
        raise ValueError(
            "La nueva salida excedería la jornada "
            f"máxima en {minutos_extension} minutos. "
            "Utiliza «Crear salida extraordinaria», "
            "autoriza una extensión de jornada o mueve "
            "el pedido a otra fecha."
        )

    desplazamiento_horario = int(
        minutos_utilizados
        + minutos_preparacion
    )

    observacion_limpia = (
        observacion.strip()
        if observacion
        else (
            "Nueva salida creada desde "
            "Gestión de Excepciones."
        )
    )

    rutas_ajustadas = []

    for ruta_original in rutas:
        ruta = dict(
            ruta_original
        )

        ruta["hora_llegada"] = (
            desplazar_hora_ruta(
                ruta.get(
                    "hora_llegada"
                ),
                desplazamiento_horario,
            )
        )

        ruta["hora_salida"] = (
            desplazar_hora_ruta(
                ruta.get(
                    "hora_salida"
                ),
                desplazamiento_horario,
            )
        )

        ruta["hora_estimada"] = (
            ruta["hora_llegada"]
        )

        ruta["numero_salida"] = (
            numero_salida
        )

        ruta["tipo_salida"] = (
            "ADICIONAL"
        )

        ruta["autorizacion_manual"] = (
            True
        )

        ruta["minutos_extension"] = 0

        ruta["motivo_autorizacion"] = (
            observacion_limpia
        )

        cierre_cliente = hora_a_minutos(
            ruta.get(
                "ventana_cierre"
            )
        )

        llegada_estimada = hora_a_minutos(
            ruta.get(
                "hora_llegada"
            )
        )

        if (
            cierre_cliente is not None
            and llegada_estimada is not None
            and llegada_estimada
            > cierre_cliente
        ):
            raise ValueError(
                "La hora estimada de llegada "
                f"({ruta.get('hora_llegada')}) "
                "supera la hora de cierre del cliente."
            )

        rutas_ajustadas.append(
            ruta
        )

    mapa_dias = [
        "LUN",
        "MAR",
        "MIE",
        "JUE",
        "VIE",
        "SAB",
        "DOM",
    ]

    dia_operativa = mapa_dias[
        fecha_operativa.weekday()
    ]

    guardar_salida_adicional(
        fecha_entrega=fecha_operativa,
        dia_operativa=dia_operativa,
        rutas=rutas_ajustadas,
        id_ejecucion=id_ejecucion,
        numero_salida=numero_salida,
        tipo_salida="ADICIONAL",
        minutos_extension=0,
        motivo_autorizacion=(
            observacion_limpia
        ),
    )

    try:
        with engine.begin() as conn:

            resultado_incidencia = (
                conn.execute(
                    text(
                        """
                        UPDATE logistica.incidencias_planificacion
                        SET
                            resuelta = TRUE,
                            estado_incidencia = 'CERRADA',
                            observacion = :observacion
                        WHERE id_incidencia = :id_incidencia
                          AND id_pedido = :id_pedido
                          AND estado_incidencia = 'ABIERTA'
                        """
                    ),
                    {
                        "id_incidencia": int(
                            id_incidencia
                        ),
                        "id_pedido": int(
                            id_pedido
                        ),
                        "observacion": (
                            observacion_limpia
                        ),
                    },
                )
            )

            if resultado_incidencia.rowcount == 0:
                raise ValueError(
                    "La incidencia ya no está abierta "
                    "o no corresponde al pedido."
                )

            conn.execute(
                text(
                    """
                    INSERT INTO logistica.decisiones_excepciones
                    (
                        id_pedido,
                        id_incidencia,
                        fecha_operativa,
                        tipo_restriccion,
                        decision_tomada,
                        camion_destino,
                        numero_salida,
                        minutos_extension,
                        motivo,
                        observacion,
                        usuario_decision,
                        estado
                    )
                    VALUES
                    (
                        :id_pedido,
                        :id_incidencia,
                        :fecha_operativa,
                        'CAPACIDAD',
                        'NUEVA_SALIDA_ESTANDAR',
                        :camion,
                        :numero_salida,
                        0,
                        :motivo,
                        :observacion,
                        'Administrador',
                        'APLICADA'
                    )
                    """
                ),
                {
                    "id_pedido": int(
                        id_pedido
                    ),
                    "id_incidencia": int(
                        id_incidencia
                    ),
                    "fecha_operativa": (
                        fecha_operativa
                    ),
                    "camion": camion,
                    "numero_salida": (
                        numero_salida
                    ),
                    "motivo": (
                        "Pedido excluido de la "
                        "planificación automática "
                        "por restricciones operativas."
                    ),
                    "observacion": (
                        observacion_limpia
                    ),
                },
            )

    except Exception:
        # Si falla el registro de la decisión o el cierre
        # de la incidencia, se elimina la salida añadida
        # para evitar una planificación inconsistente.
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    DELETE FROM logistica.rutas_generadas
                    WHERE fecha_operativa = :fecha
                      AND id_ejecucion = :id_ejecucion
                      AND camion = :camion
                      AND numero_salida = :numero_salida
                    """
                ),
                {
                    "fecha": fecha_operativa,
                    "id_ejecucion": id_ejecucion,
                    "camion": camion,
                    "numero_salida": (
                        numero_salida
                    ),
                },
            )

        raise

    costo_estimado = max(
        [
            float(
                ruta.get(
                    "costo_estimado_camion"
                )
                or 0
            )
            for ruta in rutas_ajustadas
        ],
        default=0,
    )

    hora_final_estimada = max(
        [
            ruta.get("hora_salida")
            for ruta in rutas_ajustadas
            if ruta.get("hora_salida")
        ],
        default=None,
    )

    return {
        "camion": camion,
        "numero_salida": numero_salida,
        "duracion_min": (
            duracion_nueva_salida
        ),
        "minutos_preparacion": (
            minutos_preparacion
        ),
        "hora_final_estimada": (
            hora_final_estimada
        ),
        "costo_estimado": (
            costo_estimado
        ),
    }

def cargar_salidas(fecha):
    return pd.read_sql(
        """
        SELECT DISTINCT
            camion,

            CAST(
                COALESCE(numero_salida, 1)
                AS INTEGER
            ) AS numero_salida,

            COALESCE(
                tipo_salida,
                'PLANIFICADA'
            ) AS tipo_salida

        FROM logistica.rutas_generadas

        WHERE fecha_operativa = %(fecha)s

          AND id_ejecucion = (
              SELECT id_ejecucion
              FROM logistica.rutas_generadas
              WHERE fecha_operativa = %(fecha)s
                AND id_ejecucion IS NOT NULL
              ORDER BY fecha_registro DESC
              LIMIT 1
          )

        ORDER BY
            camion,
            numero_salida
        """,
        engine,
        params={"fecha": fecha},
    )


def cargar_ruta_repartidor(
    fecha,
    camion,
    numero_salida,
):
    return pd.read_sql(
        """
        SELECT
            rg.id_pedido,
            rg.numero_salida,
            rg.tipo_salida,
            rg.secuencia,
            rg.cliente,
            rg.direccion,
            rg.lat,
            rg.lon,
            rg.hora_llegada,
            rg.hora_salida,
            rg.carga_kg,
            rg.prioridad,

            CASE
                WHEN i.id_incidencia IS NOT NULL
                    AND i.estado_incidencia = 'ABIERTA'
                    AND i.fecha_reintento = rg.fecha_operativa
                THEN 'VALIDADO'
                ELSE p.estado_pedido
            END AS estado_pedido,

            CASE
                WHEN i.id_incidencia IS NOT NULL
                    AND i.estado_incidencia = 'ABIERTA'
                    AND i.fecha_reintento = rg.fecha_operativa
                THEN ''
                ELSE COALESCE(
                    p.observacion_entrega,
                    ''
                )
            END AS observacion_entrega

        FROM logistica.rutas_generadas rg

        LEFT JOIN logistica.pedidos p
            ON rg.id_pedido = p.id_pedido

        LEFT JOIN logistica.incidencias_planificacion i
            ON i.id_pedido = rg.id_pedido
          AND i.origen = 'REPARTO'
          AND i.estado_incidencia = 'ABIERTA'
          AND i.fecha_reintento = rg.fecha_operativa

        WHERE rg.fecha_operativa = %(fecha)s
          AND rg.camion = %(camion)s

          AND COALESCE(
              rg.numero_salida,
              1
          ) = %(numero_salida)s

          AND rg.id_ejecucion = (
              SELECT id_ejecucion
              FROM logistica.rutas_generadas
              WHERE fecha_operativa = %(fecha)s
                AND id_ejecucion IS NOT NULL
              ORDER BY fecha_registro DESC
              LIMIT 1
          )

        ORDER BY rg.secuencia
        """,
        engine,
        params={
            "fecha": fecha,
            "camion": camion,
            "numero_salida": int(numero_salida),
        },
    )

def crear_url_navegacion(lat, lon):
    return (
        "https://www.google.com/maps/dir/?api=1"
        f"&destination={lat},{lon}"
        "&travelmode=driving"
    )


def crear_mensaje_whatsapp(
    camion,
    numero_salida,
    fecha,
):
    camion_url = urllib.parse.quote(
        camion
    )

    url_app = (
        "http://192.168.1.24:8501"
        f"?vista=repartidor"
        f"&fecha={fecha}"
        f"&camion={camion_url}"
        f"&salida={int(numero_salida)}"
    )

    mensaje = (
        "🚚 Decision Hub | Operations\n\n"
        f"Camión asignado: {camion}\n"
        f"Salida: {int(numero_salida)}\n"
        f"Fecha: {fecha}\n\n"
        f"Abrir ruta:\n{url_app}"
    )

    return (
        "https://wa.me/?text="
        + urllib.parse.quote(mensaje)
    )


def mostrar_mapa_ruta(ruta):
    if ruta.empty:
        return

    centro = [ruta["lat"].mean(), ruta["lon"].mean()]

    mapa = folium.Map(location=centro, zoom_start=11)

    puntos = []

    for _, fila in ruta.iterrows():
        punto = [fila["lat"], fila["lon"]]
        puntos.append(punto)

        folium.Marker(
            location=punto,
            popup=f"{fila['secuencia']}. {fila['cliente']}<br>{fila['direccion']}",
            tooltip=f"{fila['secuencia']}. {fila['cliente']}",
        ).add_to(mapa)

    if len(puntos) > 1:
        folium.PolyLine(puntos, weight=4).add_to(mapa)

    st_folium(mapa, width=None, height=500)

def actualizar_estado(id_pedido, estado, observacion, motivo_no_entrega=None):
    requiere_revision = estado in [
        "NO_ENTREGADO",
        "RECHAZADO",
        "REPROGRAMAR",
    ]
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE logistica.pedidos
                SET
                    estado_pedido = :estado,
                    observacion_entrega = :observacion,
                    motivo_no_entrega = :motivo_no_entrega,
                    requiere_revision = :requiere_revision,
                    fecha_actualizacion_estado = NOW()
                WHERE id_pedido = :id_pedido
            """),
            {
                "estado": estado,
                "observacion": observacion,
                "motivo_no_entrega": motivo_no_entrega,
                "requiere_revision": requiere_revision,
                "id_pedido": int(id_pedido),
            }
        )
        if estado == "ENTREGADO":
            conn.execute(
                text("""
                    UPDATE logistica.incidencias_planificacion
                    SET
                        resuelta = TRUE,
                        estado_incidencia = 'CERRADA'
                    WHERE id_pedido = :id_pedido
                      AND origen = 'REPARTO'
                      AND estado_incidencia = 'ABIERTA'
                """),
                {
                    "id_pedido": int(id_pedido),
                },
            )
def calcular_siguiente_fecha_operativa(fecha_actual):
    """
    Devuelve el siguiente día habilitado para entregas.

    Lunes a viernes: habilitados.
    Sábado: según PERMITIR_ENTREGAS_SABADO.
    Domingo: según PERMITIR_ENTREGAS_DOMINGO.
    """
    siguiente_fecha = fecha_actual + timedelta(days=1)

    while True:
        dia_semana = siguiente_fecha.weekday()

        es_sabado = dia_semana == 5
        es_domingo = dia_semana == 6

        if es_sabado and not PERMITIR_ENTREGAS_SABADO:
            siguiente_fecha += timedelta(days=1)
            continue

        if es_domingo and not PERMITIR_ENTREGAS_DOMINGO:
            siguiente_fecha += timedelta(days=1)
            continue

        return siguiente_fecha


def reprogramar_pedido_no_entregado(id_pedido, fecha_entrega_original):
    """
    Conserva el pedido original con su estado final y crea un nuevo pedido
    urgente para el siguiente día operativo.

    Si ya existe una reprogramación de ese pedido para esa fecha,
    no vuelve a crearla.
    """
    nueva_fecha_entrega = calcular_siguiente_fecha_operativa(
        fecha_entrega_original
    )

    with engine.begin() as conn:
        ya_existe = conn.execute(
            text("""
                SELECT 1
                FROM logistica.pedidos
                WHERE id_pedido_origen = :id_pedido_origen
                  AND fecha_entrega = :fecha_entrega
                LIMIT 1
            """),
            {
                "id_pedido_origen": int(id_pedido),
                "fecha_entrega": nueva_fecha_entrega,
            },
        ).first()

        if ya_existe:
            return nueva_fecha_entrega, False

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
                    id_pedido_origen
                )
                SELECT
                    id_cliente,
                    CURRENT_DATE,
                    :nueva_fecha_entrega,
                    cantidad_bultos,
                    peso_kg,
                    volumen_m3,
                    'URGENTE',
                    'VALIDADO',
                    'EXTRAORDINARIO',
                    :observacion,
                    id_pedido
                FROM logistica.pedidos
                WHERE id_pedido = :id_pedido
            """),
            {
                "nueva_fecha_entrega": nueva_fecha_entrega,
                "observacion": (
                    f"Reprogramado automáticamente desde el pedido "
                    f"{id_pedido} por entrega no completada."
                ),
                "id_pedido": int(id_pedido),
            },
        )

    return nueva_fecha_entrega, True

params = st.query_params

vista_url = params.get("vista", None)

if vista_url == "repartidor":
    menu_default = "Repartidor"
else:
    menu_default = "Planificación"
params = st.query_params

vista_url = params.get("vista")

opciones_menu = [
    "Planificación",
    "Gestión de Excepciones",
    "Administración",
    "Repartidor",
]

if vista_url in ["planificacion", "administracion", "repartidor"]:
    menu = vista_url.capitalize()
else:
    menu = st.sidebar.radio(
        "Menú",
        opciones_menu,
    )


if menu == "Planificación":
    st.header("Ejecutar planificación")

    fecha_pedido = st.date_input("Fecha de pedido")

    generar_demo = st.checkbox(
    "Generar pedidos de demostración",
    value=True,
    help=(
        "Crea pedidos sintéticos para la fecha seleccionada. "
        "En una operación real, los pedidos vendrían del sistema comercial."
    ),
)
    
    if st.button("Ejecutar planificación"):
        with st.spinner("Ejecutando planificación..."):
            resultado = ejecutar_planificacion_operativa(
                fecha_pedido.strftime("%Y-%m-%d"),
                generar_demo=generar_demo,
            )

        if resultado["ok"]:
            st.success("Planificación ejecutada correctamente.")
        else:
            st.error(
                f"Error durante la planificación en "
                f"{resultado['script']}."
            )
            st.code(resultado["error"])


elif menu == "Administración":
    st.header("Panel administrativo")

    fechas = cargar_fechas()

    if fechas.empty:
        st.warning("No hay rutas generadas.")
        st.stop()

    fecha = st.selectbox(
        "Fecha operativa",
        fechas["fecha_operativa"].tolist()
    )

    rutas = cargar_rutas(fecha)
    incidencias = cargar_incidencias(fecha)

    rutas["numero_salida"] = (
        pd.to_numeric(
            rutas["numero_salida"],
            errors="coerce",
        )
        .fillna(1)
        .astype(int)
    )

    rutas["tipo_salida"] = (
        rutas["tipo_salida"]
        .fillna("PLANIFICADA")
    )

    km_total = (
        rutas["distancia_km"]
        .fillna(0)
        .sum()
    )

    tiempo_rutas_min = (
        rutas["tiempo_viaje_min"]
        .fillna(0)
        .sum()
        +
        rutas["tiempo_servicio_min"]
        .fillna(0)
        .sum()
    )

    salidas_adicionales = (
        rutas.loc[
            rutas["numero_salida"] > 1,
            [
                "camion",
                "numero_salida",
            ],
        ]
        .drop_duplicates()
    )

    tiempo_preparacion_total = (
        len(salidas_adicionales)
        * TIEMPO_PREPARACION_NUEVA_SALIDA_MIN
    )

    tiempo_total_min = (
        tiempo_rutas_min
        + tiempo_preparacion_total
    )

    COSTO_KM = 35
    COSTO_HORA = 500

    coste_total = (
        km_total * COSTO_KM
        + (tiempo_total_min / 60) * COSTO_HORA
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Pedidos planificados", len(rutas))
    c2.metric("Pendientes aprobación", len(incidencias))
    c3.metric("Km estimados", round(km_total, 2))
    c4.metric("Horas reparto", round(tiempo_total_min / 60, 2))
    c5.metric("Coste estimado", f"$ {round(coste_total, 2)}")

    st.divider()

    st.subheader("Resumen por camión")

    resumen = (
        rutas.groupby(
            [
                "camion",
                "numero_salida",
                "tipo_salida",
            ],
            dropna=False,
        )
        .agg(
            paradas=("cliente", "count"),
            carga_total=("carga_kg", "sum"),
            km_total=("distancia_km", "sum"),
            tiempo_viaje=("tiempo_viaje_min", "sum"),
            tiempo_servicio=("tiempo_servicio_min", "sum"),
        )
        .reset_index()
    )

    resumen["tiempo_ruta_min"] = (
        resumen["tiempo_viaje"].fillna(0)
        + resumen["tiempo_servicio"].fillna(0)
    )

    resumen["tiempo_preparacion_min"] = (
        resumen["numero_salida"].apply(
            lambda numero:
                0
                if int(numero) == 1
                else TIEMPO_PREPARACION_NUEVA_SALIDA_MIN
        )
    )

    resumen["tiempo_salida_total_min"] = (
        resumen["tiempo_ruta_min"]
        + resumen["tiempo_preparacion_min"]
    )

    flota = pd.read_sql(
        """
        SELECT
            descripcion,
            capacidad_kg,
            jornada_max_min
        FROM logistica.flota
        ORDER BY descripcion
        """,
        engine,
    )

    resumen = resumen.merge(
        flota[
            [
                "descripcion",
                "capacidad_kg",
                "jornada_max_min",
            ]
        ],
        left_on="camion",
        right_on="descripcion",
        how="left",
    )

    resumen.drop(
        columns="descripcion",
        inplace=True,
    )

    resumen["capacidad_disponible"] = (
        resumen["capacidad_kg"]
        - resumen["carga_total"]
    )

    resumen = resumen.sort_values(
        [
            "camion",
            "numero_salida",
        ]
    )

    resumen["tiempo_acumulado_dia"] = (
        resumen.groupby("camion")[
            "tiempo_salida_total_min"
        ]
        .cumsum()
    )

    resumen["minutos_disponibles"] = (
        resumen["jornada_max_min"]
        - resumen["tiempo_acumulado_dia"]
    )

    resumen_vista = resumen[
        [
            "camion",
            "numero_salida",
            "tipo_salida",
            "paradas",
            "carga_total",
            "capacidad_kg",
            "capacidad_disponible",
            "km_total",
            "tiempo_ruta_min",
            "tiempo_preparacion_min",
            "tiempo_salida_total_min",
            "tiempo_acumulado_dia",
            "jornada_max_min",
            "minutos_disponibles",
        ]
    ].copy()

    resumen_vista = resumen_vista.rename(
        columns={
            "camion": "Camión",
            "numero_salida": "Salida",
            "tipo_salida": "Tipo de salida",
            "paradas": "Paradas",
            "carga_total": "Carga total",
            "capacidad_kg": "Capacidad",
            "capacidad_disponible": "Capacidad disponible",
            "km_total": "Km",
            "tiempo_ruta_min": "Tiempo de ruta",
            "tiempo_preparacion_min": "Preparación",
            "tiempo_salida_total_min": "Tiempo de salida",
            "tiempo_acumulado_dia": "Tiempo acumulado",
            "jornada_max_min": "Jornada máxima",
            "minutos_disponibles": "Minutos disponibles",
        }
    )

    st.dataframe(
        resumen_vista,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Rutas generadas")

    columnas_rutas = [
        "camion",
        "numero_salida",
        "tipo_salida",
        "secuencia",
        "cliente",
        "direccion",
        "hora_llegada",
        "hora_salida",
        "carga_kg",
        "prioridad",
        "tipo_cliente",
        "grupo_logistico",
    ]

    columnas_disponibles = [
        columna
        for columna in columnas_rutas
        if columna in rutas.columns
    ]

    rutas_vista = rutas[columnas_disponibles].copy()

    rutas_vista = rutas_vista.rename(
    columns={
        "camion": "Camión",
        "numero_salida": "Salida",
        "tipo_salida": "Tipo de salida",
        "secuencia": "Secuencia",
        "cliente": "Cliente",
        "direccion": "Dirección",
        "hora_llegada": "Hora llegada",
        "hora_salida": "Hora salida",
        "carga_kg": "Carga kg",
        "prioridad": "Prioridad",
        "tipo_cliente": "Tipo de cliente",
        "grupo_logistico": "Grupo logístico",
        }
    )

    st.dataframe(
        rutas_vista,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Incidencias operativas")
    st.dataframe(incidencias, use_container_width=True)

elif menu == "Gestión de Excepciones":

    st.title("Gestión de Excepciones")

    st.caption(
        "Resolución de pedidos que no pudieron incorporarse "
        "automáticamente a una ruta."
    )

    fecha_excepciones = st.date_input(
        "Fecha operativa",
        value=pd.Timestamp.today().date(),
        key="fecha_gestion_excepciones",
    )

    excepciones = cargar_excepciones_planificacion(
        fecha_excepciones
    )

    resumen_camiones = cargar_resumen_camiones(
        fecha_excepciones
    )

    if excepciones.empty:

        st.success(
            "No existen pedidos pendientes de intervención "
            "administrativa para la fecha seleccionada."
        )

    else:

        st.warning(
            f"Existen {len(excepciones)} pedido(s) "
            "pendiente(s) de resolución."
        )

        opciones_pedidos = {}

        for indice, fila in excepciones.iterrows():

            peso = (
                0.0
                if pd.isna(fila["peso_kg"])
                else float(fila["peso_kg"])
            )

            cliente = (
                fila["cliente"]
                if pd.notna(fila["cliente"])
                else "Cliente no identificado"
            )

            etiqueta = (
                f"Pedido {int(fila['id_pedido'])} — "
                f"{cliente} — "
                f"{peso:,.0f} kg"
            )

            opciones_pedidos[etiqueta] = indice

        pedido_seleccionado_texto = st.selectbox(
            "Selecciona el pedido pendiente",
            options=list(opciones_pedidos.keys()),
            key="pedido_excepcion_seleccionado",
        )

        indice_pedido = opciones_pedidos[
            pedido_seleccionado_texto
        ]

        pedido = excepciones.loc[indice_pedido]

        peso_pedido = (
            0.0
            if pd.isna(pedido["peso_kg"])
            else float(pedido["peso_kg"])
        )

        prioridad_pedido = (
            pedido["prioridad"]
            if pd.notna(pedido["prioridad"])
            else "NORMAL"
        )

        st.subheader("Pedido pendiente")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Pedido",
            int(pedido["id_pedido"]),
        )

        col2.metric(
            "Cliente",
            pedido["cliente"],
        )

        col3.metric(
            "Peso",
            f"{peso_pedido:,.0f} kg",
        )

        col4.metric(
            "Prioridad",
            prioridad_pedido,
        )

        with st.expander(
            "Motivo registrado por el optimizador",
            expanded=True,
        ):

            motivo = (
                pedido["motivo"]
                if pd.notna(pedido["motivo"])
                else "No se registró un motivo detallado."
            )

            accion_original = (
                pedido["accion_sugerida"]
                if pd.notna(pedido["accion_sugerida"])
                else "Sin definir"
            )

            st.write(motivo)

            st.write(
                "**Acción sugerida originalmente:** "
                f"{accion_original}"
            )

        st.subheader("Diagnóstico de la flota")

        if resumen_camiones.empty:

            st.error(
                "No se encontró información de flota o rutas "
                "para la fecha seleccionada."
            )

        else:

            diagnostico = diagnosticar_excepcion(
                pedido,
                resumen_camiones,
            )

            diagnostico_visible = diagnostico[
                [
                    "camion",
                    "carga_salida_actual",
                    "capacidad_kg",
                    "capacidad_disponible_salida_actual",
                    "tiempo_total_min",
                    "jornada_max_min",
                    "minutos_disponibles",
                    "ultima_salida",
                    "situacion",
                    "accion_sugerida",
                ]
            ].copy()

            diagnostico_visible.columns = [
                "Camión",
                "Carga salida actual",
                "Capacidad total",
                "Capacidad disponible",
                "Tiempo utilizado",
                "Jornada máxima",
                "Minutos disponibles",
                "Última salida",
                "Diagnóstico",
                "Acción sugerida",
            ]

            st.dataframe(
                diagnostico_visible,
                use_container_width=True,
                hide_index=True,
            )

            st.info(
                "Este diagnóstico compara el peso del pedido con "
                "la capacidad y el tiempo disponibles. La viabilidad "
                "definitiva se comprobará al calcular la salida."
            )

            st.subheader("Decisión administrativa")

            accion = st.radio(
                "Selecciona una acción",
                [
                    "Crear nueva salida",
                    "Autorizar extensión de jornada",
                    "Crear salida extraordinaria",
                    "Mover a otra fecha",
                ],
                key=f"accion_excepcion_{int(pedido['id_pedido'])}",
            )

            st.write(
                f"**Acción seleccionada:** {accion}"
            )

            if accion == "Crear nueva salida":

                camiones_compatibles = diagnostico[
                    diagnostico["cabe_en_nueva_salida"] == True
                ].copy()

                if camiones_compatibles.empty:

                    st.error(
                        "Ningún vehículo tiene capacidad total "
                        "suficiente para transportar el pedido."
                    )

                else:

                    camion_nueva_salida = st.selectbox(
                        "Camión para la nueva salida",
                        options=camiones_compatibles[
                            "camion"
                        ].tolist(),
                        key=(
                            "camion_nueva_salida_"
                            f"{int(pedido['id_pedido'])}"
                        ),
                    )

                    datos_camion = (
                        camiones_compatibles[
                            camiones_compatibles["camion"]
                            == camion_nueva_salida
                        ]
                        .iloc[0]
                    )

                    col_a, col_b, col_c = st.columns(3)

                    col_a.metric(
                        "Capacidad total",
                        f"{datos_camion['capacidad_kg']:,.0f} kg",
                    )

                    col_b.metric(
                        "Tiempo utilizado",
                        f"{datos_camion['tiempo_total_min']:,.0f} min",
                    )

                    col_c.metric(
                        "Tiempo disponible",
                        f"{datos_camion['minutos_disponibles']:,.0f} min",
                    )

                    st.caption(
                        "La comprobación definitiva incluirá "
                        f"{TIEMPO_PREPARACION_NUEVA_SALIDA_MIN} minutos "
                        "de preparación de la nueva salida."
                    )

                    observacion_salida = st.text_area(
                        "Motivo u observación",
                        value=(
                            "Se autoriza una nueva salida por falta "
                            "de capacidad en la salida inicial."
                        ),
                        key=(
                            "observacion_nueva_salida_"
                            f"{int(pedido['id_pedido'])}"
                        ),
                    )

                    if st.button(
                        "Confirmar nueva salida",
                        type="primary",
                        key=(
                            "confirmar_nueva_salida_"
                            f"{int(pedido['id_pedido'])}"
                        ),
                    ):
                        try:

                            resultado = (
                                crear_nueva_salida_desde_excepcion(
                                    id_incidencia=pedido[
                                        "id_incidencia"
                                    ],
                                    id_pedido=pedido[
                                        "id_pedido"
                                    ],
                                    fecha_operativa=fecha_excepciones,
                                    camion=camion_nueva_salida,
                                    observacion=observacion_salida,
                                )
                            )

                            st.success(
                                "Nueva salida creada correctamente: "
                                f"{resultado['camion']} — "
                                f"Salida {resultado['numero_salida']}."
                            )

                            st.info(
                                "Duración estimada de la ruta: "
                                f"{resultado['duracion_min']:.0f} minutos. "
                                "Preparación de la salida: "
                                f"{resultado['minutos_preparacion']} minutos. "
                                "Hora final estimada: "
                                f"{resultado['hora_final_estimada']}."
                            )

                            if resultado["costo_estimado"] > 0:
                                st.info(
                                    "Coste estimado de la salida: "
                                    f"$ {resultado['costo_estimado']:,.2f}"
                                )

                            st.rerun()

                        except ValueError as error:
                            st.error(str(error))

                        except Exception as error:
                            st.error(
                                "No fue posible crear la nueva salida."
                            )
                            st.exception(error)


            elif accion == "Mover a otra fecha":

                nueva_fecha = st.date_input(
                    "Nueva fecha de entrega",
                    value=fecha_excepciones + timedelta(days=1),
                    min_value=fecha_excepciones + timedelta(days=1),
                    key=(
                        "nueva_fecha_"
                        f"{int(pedido['id_pedido'])}"
                    ),
                )

                observacion_decision = st.text_area(
                    "Motivo u observación de la reprogramación",
                    placeholder=(
                        "Ejemplo: se reprograma por falta de capacidad "
                        "operativa en la fecha seleccionada."
                    ),
                    key=(
                        "observacion_reprogramacion_"
                        f"{int(pedido['id_pedido'])}"
                    ),
                )

                if nueva_fecha.weekday() == 6:
                    st.warning(
                        "La fecha seleccionada es domingo. "
                        "Selecciona otro día operativo."
                    )

                if st.button(
                    "Confirmar nueva fecha",
                    type="primary",
                    key=(
                        "confirmar_reprogramacion_"
                        f"{int(pedido['id_pedido'])}"
                    ),
                ):
                    try:

                        mover_excepcion_a_otra_fecha(
                            id_incidencia=pedido[
                                "id_incidencia"
                            ],
                            id_pedido=pedido[
                                "id_pedido"
                            ],
                            fecha_operativa=fecha_excepciones,
                            nueva_fecha=nueva_fecha,
                            observacion=observacion_decision,
                        )

                        st.success(
                            f"El pedido {int(pedido['id_pedido'])} "
                            f"fue reprogramado para el "
                            f"{nueva_fecha.strftime('%d/%m/%Y')}."
                        )

                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

                    except Exception as error:
                        st.error(
                            "No fue posible aplicar la reprogramación."
                        )
                        st.exception(error)


            elif accion == "Autorizar extensión de jornada":

                st.info(
                    "Esta alternativa se conectará después de validar "
                    "la creación de una salida estándar."
                )


            elif accion == "Crear salida extraordinaria":

                st.info(
                    "Esta alternativa se conectará después de validar "
                    "la creación de una salida estándar."
                )

elif menu == "Repartidor":
    st.header("Validación de entregas")

    fechas = cargar_fechas()

    if fechas.empty:
        st.warning("No hay rutas generadas.")
        st.stop()

    fecha_param = params.get("fecha", None)

    if fecha_param:
        fecha = pd.to_datetime(fecha_param).date()
    else:
        fecha = st.selectbox(
            "Fecha operativa",
            fechas["fecha_operativa"].tolist()
        )

    salidas = cargar_salidas(fecha)

    if salidas.empty:
        st.warning(
            "No existen salidas para la fecha seleccionada."
        )
        st.stop()

    camion_param = params.get(
        "camion",
        None,
    )

    salida_param = params.get(
        "salida",
        None,
    )

    if camion_param:

        camion = camion_param

        try:
            numero_salida = int(
                salida_param or 1
            )
        except (TypeError, ValueError):
            numero_salida = 1

        salida_encontrada = salidas[
            (salidas["camion"] == camion)
            &
            (
                salidas["numero_salida"]
                == numero_salida
            )
        ]

        if salida_encontrada.empty:
            st.error(
                "La salida indicada no existe "
                "en la planificación vigente."
            )
            st.stop()

        tipo_salida = (
            salida_encontrada
            .iloc[0]["tipo_salida"]
        )

        st.info(
            f"Camión asignado: {camion} — "
            f"Salida {numero_salida} — "
            f"{tipo_salida}"
        )

    else:

        salidas = salidas.copy()

        salidas["etiqueta"] = salidas.apply(
            lambda fila: (
                f"{fila['camion']} — "
                f"Salida "
                f"{int(fila['numero_salida'])} — "
                f"{fila['tipo_salida']}"
            ),
            axis=1,
        )

        etiqueta_salida = st.selectbox(
            "Camión y salida",
            salidas["etiqueta"].tolist(),
        )

        salida_seleccionada = (
            salidas[
                salidas["etiqueta"]
                == etiqueta_salida
            ]
            .iloc[0]
        )

        camion = salida_seleccionada[
            "camion"
        ]

        numero_salida = int(
            salida_seleccionada[
                "numero_salida"
            ]
        )

        tipo_salida = salida_seleccionada[
            "tipo_salida"
        ]

    ruta = cargar_ruta_repartidor(
        fecha=fecha,
        camion=camion,
        numero_salida=numero_salida,
    )

    if ruta.empty:
        st.warning(
            "La salida seleccionada no contiene paradas."
        )
        st.stop()

    st.subheader(
        f"Ruta asignada — {camion} — "
        f"Salida {numero_salida}"
    )

    st.caption(
        f"Tipo de salida: {tipo_salida}"
    )

    mostrar_mapa_ruta(ruta)

    # El botón solo se muestra cuando la ruta se abre
    # desde la aplicación administrativa.
    if not camion_param:

        url_whatsapp = crear_mensaje_whatsapp(
            camion=camion,
            numero_salida=numero_salida,
            fecha=fecha,
        )

        st.link_button(
            "📲 Enviar ruta por WhatsApp",
            url_whatsapp,
        )
    for _, fila in ruta.iterrows():
        with st.container(border=True):
            st.markdown(
                f"### {fila['secuencia']}. {fila['cliente']}"
            )
            st.markdown(
                f"**📍 Dirección:** {fila['direccion']}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(
                    f"**Llegada:** {fila['hora_llegada']}"
                )
                st.write(
                    f"**Salida:** {fila['hora_salida']}"
                )

            with col2:
                st.write(
                    f"**Carga kg:** {fila['carga_kg']}"
                )
                st.write(
                    f"**Prioridad:** {fila['prioridad']}"
                )

            with col3:
                estado_actual = str(
                    fila["estado_pedido"] or "VALIDADO"
                ).upper()

                st.write(
                    f"**Estado actual:** {estado_actual}"
                )

            estados_disponibles = [
                "VALIDADO",
                "ENTREGADO",
                "NO_ENTREGADO",
                "RECHAZADO",
                "REPROGRAMAR",
            ]

            if estado_actual in estados_disponibles:
                indice_estado = estados_disponibles.index(
                    estado_actual
                )
            else:
                indice_estado = 0

            estado = st.selectbox(
                "Actualizar estado",
                estados_disponibles,
                index=indice_estado,
                key=f"estado_{fila['id_pedido']}",
            )

            motivo_no_entrega = None

            if estado in [
                "NO_ENTREGADO",
                "RECHAZADO",
                "REPROGRAMAR",
            ]:
                motivo_no_entrega = st.selectbox(
                    "Motivo",
                    [
                        "Cliente cerrado",
                        "Cliente rechaza pedido",
                        "No se encontró responsable",
                        "Dirección incorrecta",
                        "Sin tiempo suficiente",
                        "Falta mercadería",
                        "Otro",
                    ],
                    key=f"motivo_{fila['id_pedido']}",
                )

            observacion = st.text_area(
                "Observación",
                value=fila["observacion_entrega"] or "",
                key=f"obs_{fila['id_pedido']}",
            )

            if st.button(
                "💾 Guardar estado",
                key=f"btn_{fila['id_pedido']}",
                type="primary",
            ):
                actualizar_estado(
                    id_pedido=fila["id_pedido"],
                    estado=estado,
                    observacion=observacion,
                    motivo_no_entrega=motivo_no_entrega,
                )

                if estado in [
                    "NO_ENTREGADO",
                    "RECHAZADO",
                    "REPROGRAMAR",
                ]:
                    registrar_incidencia_reparto(
                        id_pedido=fila["id_pedido"],
                        fecha_entrega=fecha,
                        cliente=fila["cliente"],
                        estado=estado,
                        motivo=motivo_no_entrega,
                        observacion=observacion,
                    )
 
                st.success(
                    f"Estado actualizado a {estado}."
                )
                st.rerun()