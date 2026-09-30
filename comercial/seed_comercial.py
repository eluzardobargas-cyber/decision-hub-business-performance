# seed_comercial.py

from __future__ import annotations

import argparse
import random
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from sqlalchemy.engine import Engine

from pathlib import Path
import sys


# ============================================================
# RUTA RAÍZ DEL PROYECTO
# ============================================================

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]

if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))


from decision_hub.app_db import engine


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

SEMILLA = 42

CANTIDAD_PRODUCTOS = 100

FECHA_FIN = date.today()
FECHA_INICIO = FECHA_FIN - relativedelta(months=6)

CATEGORIAS = [
    "Categoría 1",
    "Categoría 2",
    "Categoría 3",
    "Categoría 4",
    "Categoría 5",
]

SUBCATEGORIAS = [
    "Subcategoría 1",
    "Subcategoría 2",
    "Subcategoría 3",
    "Subcategoría 4",
]

MARCAS = [
    "Marca 1",
    "Marca 2",
    "Marca 3",
    "Marca 4",
    "Marca 5",
    "Marca 6",
]

CANALES = [
    "Comercial",
    "Teléfono",
    "WhatsApp",
    "Web",
]

FORMAS_PAGO = [
    "Contado",
    "Crédito 15 días",
    "Crédito 30 días",
    "Crédito 45 días",
]

PRIORIDADES = [
    "Normal",
    "Alta",
    "Urgente",
]


# ============================================================
# UTILIDADES
# ============================================================

def inicializar_semilla() -> None:
    """
    Inicializa las semillas aleatorias para que la generación
    sea reproducible.
    """
    random.seed(SEMILLA)
    np.random.seed(SEMILLA)


def redondear(valor: float, decimales: int = 2) -> float:
    return round(float(valor), decimales)


def fecha_entrega_desde_pedido(fecha_pedido: date) -> date:
    """
    Genera una fecha de entrega entre 1 y 4 días posteriores.
    Evita que la entrega caiga en domingo.
    """
    dias_entrega = random.choices(
        population=[1, 2, 3, 4],
        weights=[40, 35, 20, 5],
        k=1,
    )[0]

    fecha_entrega = fecha_pedido + timedelta(days=dias_entrega)

    if fecha_entrega.weekday() == 6:
        fecha_entrega += timedelta(days=1)

    return fecha_entrega


def determinar_estado(
    fecha_pedido: date,
    fecha_entrega: date,
    fecha_actual: date,
) -> str:
    """
    Determina el estado considerando la antigüedad del pedido.
    Los pedidos recientes tienen mayor probabilidad de estar pendientes.
    """
    antiguedad = (fecha_actual - fecha_pedido).days

    if fecha_entrega > fecha_actual:
        return "Pendiente"

    if antiguedad <= 3:
        return random.choices(
            population=[
                "Entregado",
                "Pendiente",
                "Reprogramado",
                "Cancelado",
            ],
            weights=[48, 37, 11, 4],
            k=1,
        )[0]

    return random.choices(
        population=[
            "Entregado",
            "Reprogramado",
            "Cancelado",
            "Rechazado",
        ],
        weights=[89, 6, 3, 2],
        k=1,
    )[0]

def sumar_dias_sin_domingo(
    fecha_base: date,
    dias: int,
) -> date:
    """
    Suma días naturales y, si el resultado cae en domingo,
    desplaza la fecha al lunes.
    """
    fecha_resultado = fecha_base + timedelta(days=dias)

    if fecha_resultado.weekday() == 6:
        fecha_resultado += timedelta(days=1)

    return fecha_resultado


def generar_ciclo_operativo(
    fecha_pedido: date,
    fecha_entrega_solicitada: date,
    fecha_actual: date,
) -> dict[str, Any]:
    """
    Genera un ciclo operativo coherente para un pedido sintético.

    Devuelve:
    - estado final;
    - fechas operativas;
    - información de intentos;
    - indicadores OTIF;
    - incidencia opcional.
    """
    antiguedad = (fecha_actual - fecha_pedido).days

    # Pedido cuya fecha de entrega todavía no ha llegado.
    if fecha_entrega_solicitada > fecha_actual:
        return {
            "estado_pedido": "Pendiente",
            "fecha_primer_intento": None,
            "fecha_nuevo_intento": None,
            "fecha_entrega": None,
            "fecha_cancelacion": None,
            "numero_intentos": 0,
            "resultado_primer_intento": "Pendiente",
            "motivo_no_entrega": None,
            "tiene_incidencia": False,
            "es_entregado": False,
            "es_cancelado": False,
            "es_reprogramado": False,
            "es_evaluable_otif": False,
            "es_on_time": False,
            "es_in_full": False,
            "es_otif": False,
            "incidencia": None,
        }

    # Los pedidos recientes mantienen más pendientes
    # e incidencias abiertas.
    if antiguedad <= 3:
        escenario = random.choices(
            population=[
                "entregado_primero",
                "entregado_reprogramado",
                "pendiente_reintento",
                "cancelado_previo",
                "rechazado",
            ],
            weights=[48, 18, 22, 7, 5],
            k=1,
        )[0]
    else:
        escenario = random.choices(
            population=[
                "entregado_primero",
                "entregado_reprogramado",
                "cancelado_previo",
                "cancelado_reintento",
                "rechazado",
            ],
            weights=[78, 12, 4, 3, 3],
            k=1,
        )[0]

    fecha_primer_intento = fecha_entrega_solicitada

    # ========================================================
    # ENTREGADO EN PRIMER INTENTO
    # ========================================================
    if escenario == "entregado_primero":
        variacion_dias = random.choices(
            population=[-1, 0, 1, 2],
            weights=[12, 68, 15, 5],
            k=1,
        )[0]

        fecha_entrega = sumar_dias_sin_domingo(
            fecha_entrega_solicitada,
            variacion_dias,
        )

        es_on_time = (
            fecha_entrega <= fecha_entrega_solicitada
        )

        return {
            "estado_pedido": "Entregado",
            "fecha_primer_intento": fecha_primer_intento,
            "fecha_nuevo_intento": None,
            "fecha_entrega": fecha_entrega,
            "fecha_cancelacion": None,
            "numero_intentos": 1,
            "resultado_primer_intento": "Entregado",
            "motivo_no_entrega": None,
            "tiene_incidencia": False,
            "es_entregado": True,
            "es_cancelado": False,
            "es_reprogramado": False,
            "es_evaluable_otif": True,
            "es_on_time": es_on_time,
            "es_in_full": True,
            "es_otif": es_on_time,
            "incidencia": None,
        }

    # ========================================================
    # ENTREGADO DESPUÉS DE REINTENTO
    # ========================================================
    if escenario == "entregado_reprogramado":
        motivo = random.choice(
            [
                "Cliente ausente",
                "Restricción horaria",
                "Acceso restringido",
                "Dirección incompleta",
                "Problema operativo",
            ]
        )

        fecha_nuevo_intento = sumar_dias_sin_domingo(
            fecha_primer_intento,
            random.randint(1, 3),
        )

        fecha_entrega = fecha_nuevo_intento

        return {
            "estado_pedido": "Entregado",
            "fecha_primer_intento": fecha_primer_intento,
            "fecha_nuevo_intento": fecha_nuevo_intento,
            "fecha_entrega": fecha_entrega,
            "fecha_cancelacion": None,
            "numero_intentos": 2,
            "resultado_primer_intento": "No entregado",
            "motivo_no_entrega": motivo,
            "tiene_incidencia": True,
            "es_entregado": True,
            "es_cancelado": False,
            "es_reprogramado": True,
            "es_evaluable_otif": True,
            "es_on_time": False,
            "es_in_full": True,
            "es_otif": False,
            "incidencia": {
                "tipo_incidencia": "ENTREGA_FALLIDA",
                "gravedad": "MEDIA",
                "accion_sugerida": "Reprogramar entrega",
                "resuelta": True,
                "estado_incidencia": "CERRADA",
                "observacion": (
                    "Pedido entregado correctamente "
                    "en un segundo intento."
                ),
                "motivo": motivo,
                "fecha_reintento": fecha_nuevo_intento,
            },
        }

    # ========================================================
    # PENDIENTE DE REINTENTO
    # ========================================================
    if escenario == "pendiente_reintento":
        motivo = random.choice(
            [
                "Cliente ausente",
                "Acceso restringido",
                "Reprogramación solicitada por cliente",
                "Dirección incompleta",
            ]
        )

        fecha_nuevo_intento = sumar_dias_sin_domingo(
            fecha_primer_intento,
            random.randint(1, 4),
        )

        return {
            "estado_pedido": "Reprogramado",
            "fecha_primer_intento": fecha_primer_intento,
            "fecha_nuevo_intento": fecha_nuevo_intento,
            "fecha_entrega": None,
            "fecha_cancelacion": None,
            "numero_intentos": 1,
            "resultado_primer_intento": "No entregado",
            "motivo_no_entrega": motivo,
            "tiene_incidencia": True,
            "es_entregado": False,
            "es_cancelado": False,
            "es_reprogramado": True,
            "es_evaluable_otif": False,
            "es_on_time": False,
            "es_in_full": False,
            "es_otif": False,
            "incidencia": {
                "tipo_incidencia": "ENTREGA_FALLIDA",
                "gravedad": "MEDIA",
                "accion_sugerida": "Realizar nuevo intento",
                "resuelta": False,
                "estado_incidencia": "ABIERTA",
                "observacion": (
                    "Pedido pendiente de una nueva visita."
                ),
                "motivo": motivo,
                "fecha_reintento": fecha_nuevo_intento,
            },
        }

    # ========================================================
    # CANCELADO ANTES DEL INTENTO
    # ========================================================
    if escenario == "cancelado_previo":
        fecha_cancelacion = fecha_entrega_solicitada - timedelta(
            days=random.randint(0, 2)
        )

        return {
            "estado_pedido": "Cancelado",
            "fecha_primer_intento": None,
            "fecha_nuevo_intento": None,
            "fecha_entrega": None,
            "fecha_cancelacion": fecha_cancelacion,
            "numero_intentos": 0,
            "resultado_primer_intento": "No aplica",
            "motivo_no_entrega": "Cancelado antes de planificación",
            "tiene_incidencia": False,
            "es_entregado": False,
            "es_cancelado": True,
            "es_reprogramado": False,
            "es_evaluable_otif": False,
            "es_on_time": False,
            "es_in_full": False,
            "es_otif": False,
            "incidencia": None,
        }

    # ========================================================
    # CANCELADO DESPUÉS DE REINTENTO
    # ========================================================
    if escenario == "cancelado_reintento":
        motivo = random.choice(
            [
                "Cliente no disponible",
                "Dirección no localizada",
                "Pedido rechazado tras reprogramación",
            ]
        )

        fecha_nuevo_intento = sumar_dias_sin_domingo(
            fecha_primer_intento,
            random.randint(1, 3),
        )

        return {
            "estado_pedido": "Cancelado",
            "fecha_primer_intento": fecha_primer_intento,
            "fecha_nuevo_intento": fecha_nuevo_intento,
            "fecha_entrega": None,
            "fecha_cancelacion": fecha_nuevo_intento,
            "numero_intentos": 2,
            "resultado_primer_intento": "No entregado",
            "motivo_no_entrega": motivo,
            "tiene_incidencia": True,
            "es_entregado": False,
            "es_cancelado": True,
            "es_reprogramado": True,
            "es_evaluable_otif": False,
            "es_on_time": False,
            "es_in_full": False,
            "es_otif": False,
            "incidencia": {
                "tipo_incidencia": "CANCELACION_POSTERIOR",
                "gravedad": "ALTA",
                "accion_sugerida": "Revisar con el área comercial",
                "resuelta": True,
                "estado_incidencia": "CERRADA",
                "observacion": (
                    "Pedido cancelado después de un "
                    "intento de reprogramación."
                ),
                "motivo": motivo,
                "fecha_reintento": fecha_nuevo_intento,
            },
        }

    # ========================================================
    # RECHAZADO POR EL CLIENTE
    # ========================================================
    motivo = "Cliente rechazó la mercadería"

    return {
        "estado_pedido": "Rechazado",
        "fecha_primer_intento": fecha_primer_intento,
        "fecha_nuevo_intento": None,
        "fecha_entrega": None,
        "fecha_cancelacion": None,
        "numero_intentos": 1,
        "resultado_primer_intento": "Rechazado",
        "motivo_no_entrega": motivo,
        "tiene_incidencia": True,
        "es_entregado": False,
        "es_cancelado": False,
        "es_reprogramado": False,
        "es_evaluable_otif": False,
        "es_on_time": False,
        "es_in_full": False,
        "es_otif": False,
        "incidencia": {
            "tipo_incidencia": "PEDIDO_RECHAZADO",
            "gravedad": "ALTA",
            "accion_sugerida": "Contactar al cliente",
            "resuelta": True,
            "estado_incidencia": "CERRADA",
            "observacion": (
                "El cliente rechazó el pedido "
                "durante el intento de entrega."
            ),
            "motivo": motivo,
            "fecha_reintento": None,
        },
    }

def seleccionar_fecha_registro(fecha_pedido: date) -> datetime:
    """
    Genera una hora de registro dentro de un horario comercial.
    """
    hora = random.randint(8, 18)
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)

    return datetime.combine(
        fecha_pedido,
        datetime.min.time(),
    ).replace(
        hour=hora,
        minute=minuto,
        second=segundo,
    )


def ajustar_dia_habil(fecha: date) -> date:
    """
    Desplaza una fecha que caiga en domingo al lunes siguiente.
    """
    if fecha.weekday() == 6:
        return fecha + timedelta(days=1)
    return fecha


def normalizar_estado_logistico(estado: Any) -> str:
    """
    Homologa estados técnicos de logística a los estados usados
    por el dashboard.
    """
    if estado is None or pd.isna(estado):
        return "Pendiente"

    valor = str(estado).strip().upper()

    mapa = {
        "PLANIFICADO": "Pendiente",
        "PENDIENTE": "Pendiente",
        "ASIGNADO": "Pendiente",
        "EN RUTA": "Pendiente",
        "EN_RUTA": "Pendiente",
        "REPROGRAMADO": "Reprogramado",
        "REINTENTO": "Reprogramado",
        "PENDIENTE DE REINTENTO": "Reprogramado",
        "ENTREGADO": "Entregado",
        "COMPLETADO": "Entregado",
        "CANCELADO": "Cancelado",
        "ANULADO": "Cancelado",
        "RECHAZADO": "Rechazado",
    }

    return mapa.get(valor, str(estado).strip().title())


def _primera_columna_disponible(
    columnas: set[str],
    candidatas: list[str],
) -> str | None:
    for candidata in candidatas:
        if candidata in columnas:
            return candidata
    return None


def _columnas_tabla(
    db_engine: Engine,
    esquema: str,
    tabla: str,
) -> set[str]:
    consulta = text(
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :esquema
          AND table_name = :tabla
        """
    )

    datos = pd.read_sql(
        consulta,
        db_engine,
        params={"esquema": esquema, "tabla": tabla},
    )

    return set(datos["column_name"].astype(str))


def cargar_operacion_logistica(
    db_engine: Engine,
) -> pd.DataFrame:
    """
    Obtiene una fila consolidada por pedido desde logistica.pedidos
    y, cuando existe, complementa la fecha real desde
    logistica.entregas.

    La función detecta nombres de columnas habituales para no acoplar
    el generador a una única versión del esquema.
    """
    columnas_pedidos = _columnas_tabla(
        db_engine,
        "logistica",
        "pedidos",
    )

    if not columnas_pedidos:
        print(
            "Aviso: no se encontró logistica.pedidos. "
            "Todos los ciclos operativos serán sintéticos."
        )
        return pd.DataFrame()

    id_col = _primera_columna_disponible(
        columnas_pedidos,
        ["id_pedido", "pedido_id"],
    )

    if id_col is None:
        print(
            "Aviso: logistica.pedidos no contiene una columna "
            "identificadora compatible. Se omite la integración real."
        )
        return pd.DataFrame()

    mapeo_pedidos = {
        "estado_logistico_real": _primera_columna_disponible(
            columnas_pedidos,
            ["estado", "estado_pedido", "estado_logistico"],
        ),
        "fecha_planificada_real": _primera_columna_disponible(
            columnas_pedidos,
            [
                "fecha_planificada",
                "fecha_entrega_solicitada",
                "fecha_comprometida",
                "fecha_programada",
            ],
        ),
        "fecha_primer_intento_real": _primera_columna_disponible(
            columnas_pedidos,
            [
                "fecha_primer_intento",
                "primer_intento",
                "fecha_intento",
            ],
        ),
        "fecha_nuevo_intento_real": _primera_columna_disponible(
            columnas_pedidos,
            [
                "fecha_nuevo_intento",
                "fecha_reintento",
                "fecha_reprogramada",
                "nueva_fecha_entrega",
            ],
        ),
        "fecha_entrega_real": _primera_columna_disponible(
            columnas_pedidos,
            [
                "fecha_entrega_real",
                "fecha_entrega",
                "entregado_en",
            ],
        ),
        "fecha_cancelacion_real": _primera_columna_disponible(
            columnas_pedidos,
            ["fecha_cancelacion", "cancelado_en"],
        ),
        "numero_intentos_real": _primera_columna_disponible(
            columnas_pedidos,
            ["numero_intentos", "cantidad_intentos", "intentos"],
        ),
        "resultado_primer_intento_real": _primera_columna_disponible(
            columnas_pedidos,
            ["resultado_primer_intento", "resultado_intento"],
        ),
        "motivo_no_entrega_real": _primera_columna_disponible(
            columnas_pedidos,
            [
                "motivo_no_entrega",
                "motivo_reprogramacion",
                "motivo_cancelacion",
            ],
        ),
    }

    select_partes = [
        f'CAST("{id_col}" AS TEXT) AS id_pedido'
    ]

    for alias, columna in mapeo_pedidos.items():
        if columna is not None:
            select_partes.append(f'"{columna}" AS "{alias}"')
        else:
            select_partes.append(f'NULL AS "{alias}"')

    consulta_pedidos = text(
        "SELECT " + ", ".join(select_partes)
        + ' FROM logistica.pedidos'
    )

    reales = pd.read_sql(consulta_pedidos, db_engine)

    columnas_entregas = _columnas_tabla(
        db_engine,
        "logistica",
        "entregas",
    )

    if columnas_entregas:
        id_entrega = _primera_columna_disponible(
            columnas_entregas,
            ["id_pedido", "pedido_id"],
        )
        fecha_entrega = _primera_columna_disponible(
            columnas_entregas,
            [
                "fecha_entrega_real",
                "fecha_entrega",
                "entregado_en",
            ],
        )
        fecha_reintento = _primera_columna_disponible(
            columnas_entregas,
            [
                "fecha_nuevo_intento",
                "fecha_reintento",
                "fecha_reprogramada",
            ],
        )

        if id_entrega is not None and (
            fecha_entrega is not None
            or fecha_reintento is not None
        ):
            partes = [
                f'CAST("{id_entrega}" AS TEXT) AS id_pedido'
            ]

            if fecha_entrega is not None:
                partes.append(
                    f'MAX("{fecha_entrega}") AS '
                    '"fecha_entrega_desde_entregas"'
                )

            if fecha_reintento is not None:
                partes.append(
                    f'MAX("{fecha_reintento}") AS '
                    '"fecha_reintento_desde_entregas"'
                )

            consulta_entregas = text(
                "SELECT "
                + ", ".join(partes)
                + " FROM logistica.entregas "
                + f'GROUP BY "{id_entrega}"'
            )

            entregas = pd.read_sql(
                consulta_entregas,
                db_engine,
            )

            reales = reales.merge(
                entregas,
                on="id_pedido",
                how="left",
            )

            if "fecha_entrega_desde_entregas" in reales:
                reales["fecha_entrega_real"] = (
                    reales["fecha_entrega_desde_entregas"]
                    .combine_first(reales["fecha_entrega_real"])
                )
                reales.drop(
                    columns=["fecha_entrega_desde_entregas"],
                    inplace=True,
                )

            if "fecha_reintento_desde_entregas" in reales:
                reales["fecha_nuevo_intento_real"] = (
                    reales["fecha_reintento_desde_entregas"]
                    .combine_first(
                        reales["fecha_nuevo_intento_real"]
                    )
                )
                reales.drop(
                    columns=["fecha_reintento_desde_entregas"],
                    inplace=True,
                )

    if reales.empty:
        return reales

    reales["id_pedido"] = reales["id_pedido"].astype(str)

    for columna in [
        "fecha_planificada_real",
        "fecha_primer_intento_real",
        "fecha_nuevo_intento_real",
        "fecha_entrega_real",
        "fecha_cancelacion_real",
    ]:
        reales[columna] = pd.to_datetime(
            reales[columna],
            errors="coerce",
        ).dt.date

    print(
        "Pedidos logísticos disponibles para cruce: "
        f"{reales['id_pedido'].nunique():,}"
    )

    return reales


def enriquecer_pedidos_con_operacion(
    pedidos: pd.DataFrame,
    operacion_real: pd.DataFrame,
) -> pd.DataFrame:
    """
    Conserva el ciclo operativo sintético generado originalmente
    y sustituye sus valores únicamente cuando existe información
    logística real para el pedido.

    No vuelve a simular pedidos.
    """
    resultado = pedidos.copy()

    if "estado_pedido" not in resultado.columns:
        raise KeyError(
            "No existe la columna 'estado_pedido' "
            "en el DataFrame de pedidos."
        )

    # Guarda el estado comercial original antes de cualquier
    # sustitución por información logística real.
    resultado["estado_comercial_inicial"] = (
        resultado["estado_pedido"]
    )

    # Por defecto todos los pedidos conservan el ciclo sintético
    # generado en generar_pedidos_y_lineas().
    resultado["origen_datos_operativos"] = "SINTETICO"

    if operacion_real.empty:
        print("Pedidos con datos operativos reales: 0")
        print(
            "Pedidos con ciclo operativo sintético: "
            f"{len(resultado):,}"
        )
        return resultado

    operacion_real = operacion_real.copy()

    # La tabla logística trabaja con un identificador entero.
    operacion_real["id_pedido_logistica"] = pd.to_numeric(
        operacion_real["id_pedido"],
        errors="coerce",
    ).astype("Int64")

    operacion_real.drop(
        columns=["id_pedido"],
        inplace=True,
    )

    resultado["id_pedido_logistica"] = pd.to_numeric(
        resultado["id_pedido_logistica"],
        errors="coerce",
    ).astype("Int64")

    resultado = resultado.merge(
        operacion_real,
        on="id_pedido_logistica",
        how="left",
        validate="many_to_one",
    )

    columnas_reales_necesarias = [
        "estado_logistico_real",
        "fecha_planificada_real",
        "fecha_primer_intento_real",
        "fecha_nuevo_intento_real",
        "fecha_entrega_real",
        "fecha_cancelacion_real",
        "numero_intentos_real",
        "resultado_primer_intento_real",
        "motivo_no_entrega_real",
    ]

    for columna in columnas_reales_necesarias:
        if columna not in resultado.columns:
            resultado[columna] = None

    resultado["_tiene_dato_real"] = (
        resultado["estado_logistico_real"].notna()
        | resultado["fecha_entrega_real"].notna()
        | resultado["fecha_nuevo_intento_real"].notna()
        | resultado["fecha_primer_intento_real"].notna()
    )

    indices_reales = resultado.index[
        resultado["_tiene_dato_real"]
    ]

    for indice in indices_reales:
        estado_real = normalizar_estado_logistico(
            resultado.at[
                indice,
                "estado_logistico_real",
            ]
        )

        fecha_solicitada = resultado.at[
            indice,
            "fecha_entrega_solicitada",
        ]

        fecha_entrega_real = resultado.at[
            indice,
            "fecha_entrega_real",
        ]

        fecha_primer_intento_real = resultado.at[
            indice,
            "fecha_primer_intento_real",
        ]

        fecha_nuevo_intento_real = resultado.at[
            indice,
            "fecha_nuevo_intento_real",
        ]

        fecha_cancelacion_real = resultado.at[
            indice,
            "fecha_cancelacion_real",
        ]

        # Una entrega registrada prevalece sobre cualquier estado.
        if pd.notna(fecha_entrega_real):
            estado_real = "Entregado"

        resultado.at[
            indice,
            "estado_pedido",
        ] = estado_real

        if pd.notna(fecha_primer_intento_real):
            resultado.at[
                indice,
                "fecha_primer_intento",
            ] = fecha_primer_intento_real

        elif estado_real in {
            "Entregado",
            "Reprogramado",
            "Rechazado",
        }:
            resultado.at[
                indice,
                "fecha_primer_intento",
            ] = fecha_solicitada

        else:
            resultado.at[
                indice,
                "fecha_primer_intento",
            ] = None

        resultado.at[
            indice,
            "fecha_nuevo_intento",
        ] = (
            fecha_nuevo_intento_real
            if pd.notna(fecha_nuevo_intento_real)
            else None
        )

        resultado.at[
            indice,
            "fecha_entrega",
        ] = (
            fecha_entrega_real
            if pd.notna(fecha_entrega_real)
            else None
        )

        resultado.at[
            indice,
            "fecha_cancelacion",
        ] = (
            fecha_cancelacion_real
            if pd.notna(fecha_cancelacion_real)
            else None
        )

        intentos_reales = resultado.at[
            indice,
            "numero_intentos_real",
        ]

        if pd.notna(intentos_reales):
            numero_intentos = int(intentos_reales)

        elif estado_real == "Entregado":
            numero_intentos = (
                2
                if pd.notna(fecha_nuevo_intento_real)
                else 1
            )

        elif estado_real in {
            "Reprogramado",
            "Rechazado",
        }:
            numero_intentos = 1

        else:
            numero_intentos = 0

        resultado.at[
            indice,
            "numero_intentos",
        ] = numero_intentos

        resultado_primer_intento_real = resultado.at[
            indice,
            "resultado_primer_intento_real",
        ]

        if pd.notna(resultado_primer_intento_real):
            resultado_primer_intento = (
                resultado_primer_intento_real
            )

        elif (
            estado_real == "Entregado"
            and pd.isna(fecha_nuevo_intento_real)
        ):
            resultado_primer_intento = "Entregado"

        elif estado_real == "Rechazado":
            resultado_primer_intento = "Rechazado"

        elif estado_real == "Cancelado":
            resultado_primer_intento = "No aplica"

        else:
            resultado_primer_intento = "No entregado"

        resultado.at[
            indice,
            "resultado_primer_intento",
        ] = resultado_primer_intento

        motivo_real = resultado.at[
            indice,
            "motivo_no_entrega_real",
        ]

        resultado.at[
            indice,
            "motivo_no_entrega",
        ] = (
            motivo_real
            if pd.notna(motivo_real)
            else None
        )

        resultado.at[
            indice,
            "es_reprogramado",
        ] = (
            estado_real == "Reprogramado"
            or pd.notna(fecha_nuevo_intento_real)
        )

        resultado.at[
            indice,
            "origen_datos_operativos",
        ] = "REAL"

    # ========================================================
    # RECÁLCULO DE INDICADORES
    # ========================================================

    resultado["es_entregado"] = (
        resultado["estado_pedido"]
        == "Entregado"
    )

    resultado["es_cancelado"] = (
        resultado["estado_pedido"]
        == "Cancelado"
    )

    resultado["es_reprogramado"] = (
        resultado["es_reprogramado"]
        .fillna(False)
        .astype(bool)
    )

    fecha_solicitada = pd.to_datetime(
        resultado["fecha_entrega_solicitada"],
        errors="coerce",
    )

    fecha_entrega = pd.to_datetime(
        resultado["fecha_entrega"],
        errors="coerce",
    )

    resultado["es_evaluable_otif"] = (
        fecha_solicitada.dt.date <= FECHA_FIN
    ) & resultado["estado_pedido"].isin(
        [
            "Entregado",
            "Cancelado",
            "Rechazado",
        ]
    )

    resultado["es_on_time"] = (
        resultado["es_entregado"]
        & fecha_entrega.notna()
        & (
            fecha_entrega.dt.date
            <= fecha_solicitada.dt.date
        )
    )

    # Aproximación temporal hasta disponer de cantidad entregada.
    resultado["es_in_full"] = (
        resultado["es_entregado"]
    )

    resultado["es_otif"] = (
        resultado["es_evaluable_otif"]
        & resultado["es_on_time"]
        & resultado["es_in_full"]
    )

    # Para los pedidos sintéticos se conserva el indicador generado
    # originalmente junto con el registro de incidencia.
    resultado["tiene_incidencia"] = (
        resultado["tiene_incidencia"]
        .fillna(False)
        .astype(bool)
    )

    # Para pedidos con datos reales, cuando no existe una tabla específica
    # de incidencias asociada, se infiere la existencia de una incidencia
    # a partir del ciclo operativo disponible.
    mascara_reales = (
        resultado["origen_datos_operativos"]
        == "REAL"
    )

    resultado.loc[
        mascara_reales,
        "tiene_incidencia",
    ] = (
        resultado.loc[
            mascara_reales,
            "motivo_no_entrega",
        ].notna()
        | resultado.loc[
            mascara_reales,
            "es_reprogramado",
        ]
        | resultado.loc[
            mascara_reales,
            "estado_pedido",
        ].isin(
            [
                "Rechazado",
            ]
        )
    )

    columnas_auxiliares = [
        "_tiene_dato_real",
        "fecha_planificada_real",
        "fecha_primer_intento_real",
        "fecha_nuevo_intento_real",
        "fecha_entrega_real",
        "fecha_cancelacion_real",
        "numero_intentos_real",
        "resultado_primer_intento_real",
        "motivo_no_entrega_real",
    ]

    resultado.drop(
        columns=[
            columna
            for columna in columnas_auxiliares
            if columna in resultado.columns
        ],
        inplace=True,
    )

    cantidad_reales = int(
        (
            resultado["origen_datos_operativos"]
            == "REAL"
        ).sum()
    )

    cantidad_sinteticos = int(
        (
            resultado["origen_datos_operativos"]
            == "SINTETICO"
        ).sum()
    )

    print(
        "Pedidos con datos operativos reales: "
        f"{cantidad_reales:,}"
    )

    print(
        "Pedidos con ciclo operativo sintético: "
        f"{cantidad_sinteticos:,}"
    )

    return resultado


# ============================================================
# CLIENTES
# ============================================================

def cargar_clientes(db_engine: Engine) -> pd.DataFrame:
    """
    Lee los clientes activos existentes en la base logística.
    """
    consulta = text(
        """
        SELECT
            id_cliente,
            nombre,
            COALESCE(tipo, 'B') AS tipo
        FROM logistica.clientes
        WHERE activo = TRUE
        ORDER BY id_cliente
        """
    )

    clientes = pd.read_sql(consulta, db_engine)

    if clientes.empty:
        raise ValueError(
            "No se encontraron clientes activos en "
            "logistica.clientes."
        )

    clientes["tipo"] = (
        clientes["tipo"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    print(f"Clientes activos encontrados: {len(clientes)}")

    return clientes


def crear_perfiles_clientes(
    clientes: pd.DataFrame,
) -> dict[int, dict[str, Any]]:
    """
    Crea un perfil comercial persistente para cada cliente.

    Estos valores no se guardan como clasificaciones de negocio.
    Solo controlan la generación natural de sus pedidos.
    """
    perfiles: dict[int, dict[str, Any]] = {}

    for cliente in clientes.itertuples(index=False):
        tipo = cliente.tipo

        if tipo == "A":
            frecuencia_mensual = random.uniform(12, 20)
            lineas_promedio = random.uniform(4.5, 7.0)
            cantidad_media = random.uniform(7, 15)
            descuento_habitual = random.uniform(5, 12)

        elif tipo == "C":
            frecuencia_mensual = random.uniform(2, 6)
            lineas_promedio = random.uniform(1.5, 3.5)
            cantidad_media = random.uniform(2, 7)
            descuento_habitual = random.uniform(0, 6)

        else:
            frecuencia_mensual = random.uniform(6, 12)
            lineas_promedio = random.uniform(3.0, 5.5)
            cantidad_media = random.uniform(4, 10)
            descuento_habitual = random.uniform(2, 9)

        preferencias_categoria = np.random.dirichlet(
            np.ones(len(CATEGORIAS)) * 2
        )

        perfiles[int(cliente.id_cliente)] = {
            "tipo": tipo,
            "frecuencia_mensual": frecuencia_mensual,
            "lineas_promedio": lineas_promedio,
            "cantidad_media": cantidad_media,
            "descuento_habitual": descuento_habitual,
            "preferencias_categoria": preferencias_categoria,
        }

    return perfiles


# ============================================================
# PRODUCTOS
# ============================================================

def generar_productos(
    cantidad: int = CANTIDAD_PRODUCTOS,
) -> tuple[pd.DataFrame, np.ndarray]:
    """
    Genera productos neutrales.

    La popularidad se utiliza solo internamente para generar pedidos.
    No se guarda como atributo del producto.
    """
    productos: list[dict[str, Any]] = []

    # Distribución de popularidad: pocos productos concentran
    # más probabilidades de aparecer en pedidos.
    posiciones = np.arange(1, cantidad + 1)

    popularidad = 1 / np.power(posiciones, 0.85)
    popularidad = popularidad / popularidad.sum()

    # Barajamos la popularidad para evitar que Producto 1 sea
    # necesariamente el producto más vendido.
    np.random.shuffle(popularidad)

    for numero in range(1, cantidad + 1):
        categoria = random.choice(CATEGORIAS)
        subcategoria = random.choice(SUBCATEGORIAS)
        marca = random.choice(MARCAS)

        # Coste con distribución lognormal:
        # muchos productos de coste medio y pocos valores altos.
        coste_unitario = np.random.lognormal(
            mean=5.5,
            sigma=0.65,
        )

        coste_unitario = min(max(coste_unitario, 60), 4_500)

        margen_base = random.uniform(0.18, 0.48)

        precio_lista = coste_unitario / (1 - margen_base)

        # Peso independiente del precio.
        peso_unitario = np.random.lognormal(
            mean=-0.25,
            sigma=0.75,
        )

        peso_unitario = min(max(peso_unitario, 0.05), 18)

        # Volumen aproximado, manteniendo variabilidad.
        volumen_unitario = peso_unitario * random.uniform(
            0.001,
            0.008,
        )

        fecha_alta = FECHA_INICIO - timedelta(
            days=random.randint(30, 1_500)
        )

        # Aproximadamente un 18 % de los productos estarán discontinuados.
        es_discontinuado = random.random() < 0.18

        if es_discontinuado:
            estado_producto = "Discontinuado"
            activo = False

            # La fecha de discontinuación nunca puede ser anterior al alta
            fecha_discontinuado = fecha_alta + timedelta(
                days=random.randint(
                    90,
                    max(
                        90,
                        (FECHA_FIN - fecha_alta).days,
                    ),
                )
            )

            # Si por algún motivo supera FECHA_FIN, la limitamos
            if fecha_discontinuado > FECHA_FIN:
                fecha_discontinuado = FECHA_FIN

        else:
            estado_producto = "Activo"
            activo = True
            fecha_discontinuado = None

        productos.append(
            {
                "id_producto": f"PRD{numero:04d}",
                "sku": f"SKU{numero:04d}",
                "producto": f"Producto {numero}",
                "categoria": categoria,
                "subcategoria": subcategoria,
                "marca": marca,
                "coste_unitario": redondear(
                    coste_unitario,
                    2,
                ),
                "precio_lista": redondear(
                    precio_lista,
                    2,
                ),
                "peso_unitario_kg": redondear(
                    peso_unitario,
                    3,
                ),
                "volumen_unitario_m3": redondear(
                    volumen_unitario,
                    4,
                ),
                "activo": activo,
                "fecha_alta": fecha_alta,
                "estado_producto": estado_producto,
                "fecha_discontinuado": fecha_discontinuado,
            }
        )

    productos_df = pd.DataFrame(productos)
    print(
    productos_df[
        [
            "id_producto",
            "activo",
            "estado_producto",
            "fecha_discontinuado",
        ]
    ].head(20)
)

    print(
        "Productos discontinuados generados:",
        productos_df["fecha_discontinuado"].notna().sum(),
    )

    return productos_df, popularidad


# ============================================================
# PEDIDOS
# ============================================================

def calcular_numero_pedidos(
    frecuencia_mensual: float,
) -> int:
    """
    Calcula cuántos pedidos generará un cliente en seis meses.
    Introduce una variación aleatoria moderada.
    """
    meses = max(
        (FECHA_FIN - FECHA_INICIO).days / 30.44,
        1,
    )

    esperado = frecuencia_mensual * meses

    variacion = np.random.normal(
        loc=1.0,
        scale=0.12,
    )

    cantidad = int(round(esperado * variacion))

    return max(cantidad, 1)


def generar_fecha_pedido() -> date:
    """
    Genera una fecha de pedido dentro del periodo.

    Reduce la probabilidad de domingos y mantiene más actividad
    entre lunes y viernes.
    """
    total_dias = (FECHA_FIN - FECHA_INICIO).days

    while True:
        desplazamiento = random.randint(0, total_dias)
        fecha = FECHA_INICIO + timedelta(days=desplazamiento)

        dia_semana = fecha.weekday()

        probabilidad_aceptacion = {
            0: 1.00,  # lunes
            1: 1.00,
            2: 1.00,
            3: 1.00,
            4: 0.95,
            5: 0.35,
            6: 0.08,
        }[dia_semana]

        if random.random() <= probabilidad_aceptacion:
            return fecha


def elegir_productos_pedido(
    productos: pd.DataFrame,
    popularidad_global: np.ndarray,
    preferencias_categoria: np.ndarray,
    cantidad_lineas: int,
) -> pd.DataFrame:
    """
    Selecciona productos combinando:

    - popularidad global;
    - preferencia de categoría del cliente;
    - aleatoriedad.

    No se repite un producto dentro del mismo pedido.
    """
    mapa_preferencias = {
        categoria: preferencias_categoria[indice]
        for indice, categoria in enumerate(CATEGORIAS)
    }

    pesos_categoria = (
        productos["categoria"]
        .map(mapa_preferencias)
        .astype(float)
        .to_numpy()
    )

    probabilidades = popularidad_global * pesos_categoria
    probabilidades = probabilidades / probabilidades.sum()

    indices = np.random.choice(
        productos.index.to_numpy(),
        size=min(cantidad_lineas, len(productos)),
        replace=False,
        p=probabilidades,
    )

    return productos.loc[indices]


def generar_pedidos_y_lineas(
    clientes: pd.DataFrame,
    productos: pd.DataFrame,
    popularidad_global: np.ndarray,
    perfiles_clientes: dict[int, dict[str, Any]],
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Genera:

    - cabeceras de pedidos comerciales;
    - líneas de pedido;
    - incidencias sintéticas asociadas a los pedidos.

    En este paso se crea la estructura de incidencias, aunque
    todavía no se generan registros dentro de ella.
    """
    pedidos: list[dict[str, Any]] = []
    lineas: list[dict[str, Any]] = []
    incidencias: list[dict[str, Any]] = []

    correlativo_pedido = 1

    for cliente in clientes.itertuples(index=False):
        id_cliente = int(cliente.id_cliente)
        perfil = perfiles_clientes[id_cliente]

        numero_pedidos = calcular_numero_pedidos(
            perfil["frecuencia_mensual"]
        )

        fechas_cliente = sorted(
            generar_fecha_pedido()
            for _ in range(numero_pedidos)
        )

        for fecha_pedido in fechas_cliente:
            # Identificador comercial, visible en la demo.
            id_pedido = f"PED{correlativo_pedido:07d}"

            # Identificador entero para relacionar el pedido sintético
            # con logistica.incidencias_planificacion.
            #
            # Se utilizan valores negativos para evitar colisiones
            # con pedidos reales del esquema logistica.
            id_pedido_logistica = -correlativo_pedido

            fecha_entrega_solicitada = (
                fecha_entrega_desde_pedido(
                    fecha_pedido
                )
            )

            resultado_operativo = generar_ciclo_operativo(
                fecha_pedido=fecha_pedido,
                fecha_entrega_solicitada=fecha_entrega_solicitada,
                fecha_actual=FECHA_FIN,
            )

            cantidad_lineas_objetivo = int(
                round(
                    np.random.normal(
                        loc=perfil["lineas_promedio"],
                        scale=1.2,
                    )
                )
            )

            cantidad_lineas_objetivo = max(
                1,
                min(cantidad_lineas_objetivo, 9),
            )

            productos_pedido = elegir_productos_pedido(
                productos=productos,
                popularidad_global=popularidad_global,
                preferencias_categoria=perfil[
                    "preferencias_categoria"
                ],
                cantidad_lineas=cantidad_lineas_objetivo,
            )

            descuento_pedido = np.random.normal(
                loc=perfil["descuento_habitual"],
                scale=2.0,
            )

            descuento_pedido = min(
                max(descuento_pedido, 0),
                18,
            )

            importe_bruto_pedido = 0.0
            importe_neto_pedido = 0.0
            coste_producto_pedido = 0.0
            margen_bruto_pedido = 0.0
            peso_total_pedido = 0.0

            for producto in productos_pedido.itertuples(
                index=False
            ):
                cantidad = int(
                    round(
                        np.random.lognormal(
                            mean=np.log(
                                max(
                                    perfil["cantidad_media"],
                                    1,
                                )
                            ),
                            sigma=0.45,
                        )
                    )
                )

                cantidad = max(1, min(cantidad, 60))

                # Pequeña variación comercial sobre
                # el precio de lista.
                variacion_precio = random.uniform(
                    0.97,
                    1.03,
                )

                precio_unitario = (
                    float(producto.precio_lista)
                    * variacion_precio
                )

                descuento_linea = min(
                    max(
                        descuento_pedido
                        + random.uniform(-1.5, 1.5),
                        0,
                    ),
                    20,
                )

                importe_bruto = (
                    cantidad
                    * precio_unitario
                )

                importe_neto = (
                    importe_bruto
                    * (
                        1
                        - descuento_linea / 100
                    )
                )

                coste_total = (
                    cantidad
                    * float(producto.coste_unitario)
                )

                margen_bruto = (
                    importe_neto
                    - coste_total
                )

                peso_total = (
                    cantidad
                    * float(producto.peso_unitario_kg)
                )

                lineas.append(
                    {
                        "id_pedido": id_pedido,
                        "id_producto": producto.id_producto,
                        "cantidad": cantidad,
                        "precio_unitario": redondear(
                            precio_unitario,
                            2,
                        ),
                        "descuento_pct": redondear(
                            descuento_linea,
                            2,
                        ),
                        "importe_bruto": redondear(
                            importe_bruto,
                            2,
                        ),
                        "importe_neto": redondear(
                            importe_neto,
                            2,
                        ),
                        "coste_total": redondear(
                            coste_total,
                            2,
                        ),
                        "margen_bruto": redondear(
                            margen_bruto,
                            2,
                        ),
                        "peso_total_kg": redondear(
                            peso_total,
                            3,
                        ),
                    }
                )

                importe_bruto_pedido += importe_bruto
                importe_neto_pedido += importe_neto
                coste_producto_pedido += coste_total
                margen_bruto_pedido += margen_bruto
                peso_total_pedido += peso_total

            incidencia = resultado_operativo["incidencia"]

            if incidencia is not None:
                fecha_registro_incidencia = datetime.combine(
                    resultado_operativo["fecha_primer_intento"],
                    datetime.min.time(),
                ).replace(
                    hour=random.randint(9, 18),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59),
                )

                incidencias.append(
                    {
                        "id_pedido": id_pedido_logistica,
                        "fecha_entrega": resultado_operativo[
                            "fecha_entrega"
                        ],
                        "cliente": str(cliente.nombre),
                        "tipo_incidencia": incidencia[
                            "tipo_incidencia"
                        ],
                        "gravedad": incidencia["gravedad"],
                        "accion_sugerida": incidencia[
                            "accion_sugerida"
                        ],
                        "resuelta": incidencia["resuelta"],
                        "fecha_registro": (
                            fecha_registro_incidencia
                        ),
                        "origen": "SEED_COMERCIAL",
                        "estado_incidencia": incidencia[
                            "estado_incidencia"
                        ],
                        "observacion": incidencia[
                            "observacion"
                        ],
                        "motivo": incidencia["motivo"],
                        "fecha_reintento": incidencia[
                            "fecha_reintento"
                        ],
                    }
                )

            pedidos.append(
                {
                    "id_pedido": id_pedido,

                    # Nueva clave para relacionar el pedido comercial
                    # con incidencias_planificacion.
                    "id_pedido_logistica": (
                        id_pedido_logistica
                    ),

                    "fecha_pedido": fecha_pedido,
                    "fecha_entrega_solicitada": (
                        fecha_entrega_solicitada
                    ),
                    "fecha_primer_intento": resultado_operativo[
                        "fecha_primer_intento"
                    ],
                    "fecha_nuevo_intento": resultado_operativo[
                        "fecha_nuevo_intento"
                    ],
                    "fecha_entrega": resultado_operativo[
                        "fecha_entrega"
                    ],
                    "fecha_cancelacion": resultado_operativo[
                        "fecha_cancelacion"
                    ],
                    "id_cliente": id_cliente,
                    "canal": random.choices(
                        population=CANALES,
                        weights=[42, 25, 23, 10],
                        k=1,
                    )[0],
                    "estado_pedido": resultado_operativo[
                        "estado_pedido"
                    ],
                    "numero_intentos": resultado_operativo[
                        "numero_intentos"
                    ],
                    "resultado_primer_intento": resultado_operativo[
                        "resultado_primer_intento"
                    ],
                    "motivo_no_entrega": resultado_operativo[
                        "motivo_no_entrega"
                    ],
                    "tiene_incidencia": resultado_operativo[
                        "tiene_incidencia"
                    ],
                    "es_entregado": resultado_operativo[
                        "es_entregado"
                    ],
                    "es_cancelado": resultado_operativo[
                        "es_cancelado"
                    ],
                    "es_reprogramado": resultado_operativo[
                        "es_reprogramado"
                    ],
                    "es_evaluable_otif": resultado_operativo[
                        "es_evaluable_otif"
                    ],
                    "es_on_time": resultado_operativo[
                        "es_on_time"
                    ],
                    "es_in_full": resultado_operativo[
                        "es_in_full"
                    ],
                    "es_otif": resultado_operativo[
                        "es_otif"
                    ],
                    "origen_datos_operativos": "SINTETICO",
                    "forma_pago": random.choices(
                        population=FORMAS_PAGO,
                        weights=[18, 22, 48, 12],
                        k=1,
                    )[0],
                    "descuento_pct": redondear(
                        descuento_pedido,
                        2,
                    ),
                    "importe_bruto": redondear(
                        importe_bruto_pedido,
                        2,
                    ),
                    "importe_neto": redondear(
                        importe_neto_pedido,
                        2,
                    ),
                    "coste_producto": redondear(
                        coste_producto_pedido,
                        2,
                    ),
                    "margen_bruto": redondear(
                        margen_bruto_pedido,
                        2,
                    ),
                    "peso_total_kg": redondear(
                        peso_total_pedido,
                        2,
                    ),
                    "cantidad_lineas": len(
                        productos_pedido
                    ),
                    "fecha_registro": (
                        seleccionar_fecha_registro(
                            fecha_pedido
                        )
                    ),
                }
            )

            correlativo_pedido += 1

    pedidos_df = pd.DataFrame(pedidos)
    lineas_df = pd.DataFrame(lineas)

    # Se indican expresamente las columnas para que el DataFrame
    # conserve su estructura incluso cuando no haya incidencias.
    incidencias_df = pd.DataFrame(
        incidencias,
        columns=[
            "id_pedido",
            "fecha_entrega",
            "cliente",
            "tipo_incidencia",
            "gravedad",
            "accion_sugerida",
            "resuelta",
            "fecha_registro",
            "origen",
            "estado_incidencia",
            "observacion",
            "motivo",
            "fecha_reintento",
        ],
    )

    return (
        pedidos_df,
        lineas_df,
        incidencias_df,
    )


# ============================================================
# CONTROLES DE CALIDAD
# ============================================================

def validar_datos(
    productos: pd.DataFrame,
    pedidos: pd.DataFrame,
    lineas: pd.DataFrame,
) -> None:
    """
    Ejecuta controles antes de insertar los datos.
    """
    if productos.empty:
        raise ValueError("No se generaron productos.")

    if pedidos.empty:
        raise ValueError("No se generaron pedidos.")

    if lineas.empty:
        raise ValueError("No se generaron líneas de pedido.")

    if productos["id_producto"].duplicated().any():
        raise ValueError(
            "Existen productos con id_producto duplicado."
        )

    if productos["sku"].duplicated().any():
        raise ValueError("Existen SKU duplicados.")

    if pedidos["id_pedido"].duplicated().any():
        raise ValueError(
            "Existen pedidos con id_pedido duplicado."
        )

    if (lineas["cantidad"] <= 0).any():
        raise ValueError(
            "Existen líneas con cantidad menor o igual a cero."
        )

    if (pedidos["importe_neto"] <= 0).any():
        raise ValueError(
            "Existen pedidos con importe neto no válido."
        )

    if (pedidos["peso_total_kg"] <= 0).any():
        raise ValueError(
            "Existen pedidos sin peso."
        )

    control_lineas = (
        lineas.groupby(
            "id_pedido",
            as_index=False,
        )
        .agg(
            importe_bruto_lineas=(
                "importe_bruto",
                "sum",
            ),
            importe_neto_lineas=(
                "importe_neto",
                "sum",
            ),
            coste_lineas=(
                "coste_total",
                "sum",
            ),
            margen_lineas=(
                "margen_bruto",
                "sum",
            ),
            peso_lineas=(
                "peso_total_kg",
                "sum",
            ),
            cantidad_lineas_real=(
                "id_producto",
                "count",
            ),
        )
        .merge(
            pedidos[
                [
                    "id_pedido",
                    "importe_bruto",
                    "importe_neto",
                    "coste_producto",
                    "margen_bruto",
                    "peso_total_kg",
                    "cantidad_lineas",
                ]
            ],
            on="id_pedido",
            how="left",
        )
    )

    control_lineas["dif_importe_neto"] = (
        control_lineas["importe_neto_lineas"]
        - control_lineas["importe_neto"]
    ).abs()

    control_lineas["dif_coste"] = (
        control_lineas["coste_lineas"]
        - control_lineas["coste_producto"]
    ).abs()

    control_lineas["dif_peso"] = (
        control_lineas["peso_lineas"]
        - control_lineas["peso_total_kg"]
    ).abs()

    if control_lineas["dif_importe_neto"].max() > 0.10:
        raise ValueError(
            "La suma de importes de líneas no coincide "
            "con la cabecera."
        )

    if control_lineas["dif_coste"].max() > 0.10:
        raise ValueError(
            "La suma de costes de líneas no coincide "
            "con la cabecera."
        )

    if control_lineas["dif_peso"].max() > 0.10:
        raise ValueError(
            "La suma de pesos de líneas no coincide "
            "con la cabecera."
        )

    if not (
        control_lineas["cantidad_lineas_real"]
        == control_lineas["cantidad_lineas"]
    ).all():
        raise ValueError(
            "La cantidad de líneas de la cabecera no coincide "
            "con el detalle."
        )

    entregados_sin_fecha = pedidos[
        (pedidos["estado_pedido"] == "Entregado")
        & pedidos["fecha_entrega"].isna()
    ]

    if not entregados_sin_fecha.empty:
        raise ValueError(
            "Existen pedidos entregados sin fecha de entrega."
        )

    reprogramados_sin_fecha = pedidos[
        pedidos["es_reprogramado"]
        & pedidos["fecha_nuevo_intento"].isna()
    ]

    if not reprogramados_sin_fecha.empty:
        raise ValueError(
            "Existen pedidos reprogramados sin fecha de nuevo intento."
        )

    cancelados_sin_fecha = pedidos[
        (pedidos["estado_pedido"] == "Cancelado")
        & pedidos["fecha_cancelacion"].isna()
    ]

    # Los datos reales pueden no disponer todavía de fecha de cancelación;
    # se informa, pero no se impide la carga.
    if not cancelados_sin_fecha.empty:
        print(
            "Aviso: pedidos cancelados sin fecha de cancelación: "
            f"{len(cancelados_sin_fecha):,}"
        )

    print("Controles de calidad superados correctamente.")


# ============================================================
# CARGA EN POSTGRESQL
# ============================================================

def asegurar_columnas_operativas(
    db_engine: Engine,
) -> None:
    """
    Añade a comercial.fact_pedidos las columnas necesarias para
    almacenar el ciclo operativo y calcular OTIF en Power BI.
    """
    sentencias = [
        (
            "estado_comercial_inicial",
            "VARCHAR(40)",
        ),
        (
            "estado_logistico_real",
            "VARCHAR(80)",
        ),
        (
            "fecha_primer_intento",
            "DATE",
        ),
        (
            "fecha_nuevo_intento",
            "DATE",
        ),
        (
            "fecha_entrega",
            "DATE",
        ),
        (
            "fecha_cancelacion",
            "DATE",
        ),
        (
            "numero_intentos",
            "INTEGER",
        ),
        (
            "resultado_primer_intento",
            "VARCHAR(80)",
        ),
        (
            "motivo_no_entrega",
            "VARCHAR(160)",
        ),
        (
            "origen_datos_operativos",
            "VARCHAR(20)",
        ),
        (
            "es_entregado",
            "BOOLEAN",
        ),
        (
            "es_cancelado",
            "BOOLEAN",
        ),
        (
            "es_reprogramado",
            "BOOLEAN",
        ),
        (
            "es_evaluable_otif",
            "BOOLEAN",
        ),
        (
            "es_on_time",
            "BOOLEAN",
        ),
        (
            "es_in_full",
            "BOOLEAN",
        ),
        (
            "es_otif",
            "BOOLEAN",
        ),
    ]

    with db_engine.begin() as conexion:
        for nombre, tipo_sql in sentencias:
            conexion.execute(
                text(
                    "ALTER TABLE comercial.fact_pedidos "
                    f'ADD COLUMN IF NOT EXISTS "{nombre}" '
                    f"{tipo_sql}"
                )
            )

    print(
        "Estructura de comercial.fact_pedidos preparada "
        "para datos operativos."
    )


def limpiar_datos_comerciales(
    db_engine: Engine,
) -> None:
    """
    Elimina los datos comerciales anteriores y las incidencias
    sintéticas generadas por este seed.
    """
    with db_engine.begin() as conexion:
        conexion.execute(
            text(
                """
                DELETE FROM logistica.incidencias_planificacion
                WHERE origen = 'SEED_COMERCIAL'
                """
            )
        )

        conexion.execute(
            text(
                """
                TRUNCATE TABLE
                    comercial.fact_lineas_pedido,
                    comercial.fact_pedidos,
                    comercial.dim_productos
                RESTART IDENTITY CASCADE
                """
            )
        )

    print(
        "Datos comerciales e incidencias sintéticas "
        "anteriores eliminados."
    )


def insertar_datos(
    db_engine: Engine,
    productos: pd.DataFrame,
    pedidos: pd.DataFrame,
    lineas: pd.DataFrame,
    incidencias: pd.DataFrame,
) -> None:
    """
    Inserta productos, pedidos, líneas e incidencias sintéticas.
    """

    productos.to_sql(
        name="dim_productos",
        con=db_engine,
        schema="comercial",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    pedidos.to_sql(
        name="fact_pedidos",
        con=db_engine,
        schema="comercial",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500,
    )

    lineas.to_sql(
        name="fact_lineas_pedido",
        con=db_engine,
        schema="comercial",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1_000,
    )

    if not incidencias.empty:
        incidencias.to_sql(
            name="incidencias_planificacion",
            con=db_engine,
            schema="logistica",
            if_exists="append",
            index=False,
            method="multi",
            chunksize=500,
        )

    print("Datos insertados correctamente en PostgreSQL.")
    print(
        "Incidencias sintéticas insertadas: "
        f"{len(incidencias):,}"
    )


# ============================================================
# RESUMEN
# ============================================================

def mostrar_resumen(
    productos: pd.DataFrame,
    pedidos: pd.DataFrame,
    lineas: pd.DataFrame,
) -> None:
    ventas_entregadas = pedidos.loc[
        pedidos["estado_pedido"] == "Entregado",
        "importe_neto",
    ].sum()

    pedidos_evaluables = int(
        pedidos["es_evaluable_otif"].sum()
    )
    pedidos_otif = int(pedidos["es_otif"].sum())
    otif = (
        pedidos_otif / pedidos_evaluables
        if pedidos_evaluables
        else 0
    )

    print("\n" + "=" * 60)
    print("RESUMEN DE GENERACIÓN COMERCIAL")
    print("=" * 60)
    print(f"Periodo: {FECHA_INICIO} a {FECHA_FIN}")
    print(f"Productos: {len(productos):,}")
    print(f"Pedidos: {len(pedidos):,}")
    print(f"Líneas: {len(lineas):,}")
    print(
        "Clientes con pedidos: "
        f"{pedidos['id_cliente'].nunique():,}"
    )
    print(
        "Importe neto total: "
        f"{pedidos['importe_neto'].sum():,.2f}"
    )
    print(
        "Ventas entregadas: "
        f"{ventas_entregadas:,.2f}"
    )
    print(
        "Margen bruto total: "
        f"{pedidos['margen_bruto'].sum():,.2f}"
    )
    print(
        "Peso total generado: "
        f"{pedidos['peso_total_kg'].sum():,.2f} kg"
    )

    print("\nPedidos por estado:")
    print(
        pedidos["estado_pedido"]
        .value_counts()
        .to_string()
    )

    print("\nOrigen de los datos operativos:")
    print(
        pedidos["origen_datos_operativos"]
        .value_counts()
        .to_string()
    )

    print(
        "\nOTIF demo: "
        f"{otif:.2%} "
        f"({pedidos_otif:,}/{pedidos_evaluables:,})"
    )

    print("\nPedidos por mes:")
    pedidos_mes = (
        pedidos.assign(
            mes=pd.to_datetime(
                pedidos["fecha_pedido"]
            ).dt.to_period("M")
        )
        .groupby("mes")
        .size()
    )

    print(pedidos_mes.to_string())
    print("=" * 60)


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def ejecutar(modo: str) -> None:
    inicializar_semilla()

    print("Iniciando generación de datos comerciales.")
    print(f"Modo seleccionado: {modo}")
    print(f"Periodo: {FECHA_INICIO} a {FECHA_FIN}")

    clientes = cargar_clientes(engine)

    perfiles_clientes = crear_perfiles_clientes(
        clientes
    )

    productos, popularidad_global = generar_productos()

    pedidos, lineas, incidencias = generar_pedidos_y_lineas(
    clientes=clientes,
    productos=productos,
    popularidad_global=popularidad_global,
    perfiles_clientes=perfiles_clientes,
)

    operacion_real = cargar_operacion_logistica(engine)

    pedidos = enriquecer_pedidos_con_operacion(
        pedidos=pedidos,
        operacion_real=operacion_real,
    )

    validar_datos(
        productos=productos,
        pedidos=pedidos,
        lineas=lineas,
    )

    asegurar_columnas_operativas(engine)

    if modo == "reconstruir":
        limpiar_datos_comerciales(engine)

    insertar_datos(
        db_engine=engine,
        productos=productos,
        pedidos=pedidos,
        lineas=lineas,
        incidencias=incidencias,
    )

    mostrar_resumen(
        productos=productos,
        pedidos=pedidos,
        lineas=lineas,
    )


def obtener_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generador de datos comerciales sintéticos "
            "para PostgreSQL."
        )
    )

    parser.add_argument(
        "--modo",
        choices=["reconstruir", "agregar"],
        default="reconstruir",
        help=(
            "'reconstruir' elimina y vuelve a generar los datos. "
            "'agregar' conserva los datos existentes."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    argumentos = obtener_argumentos()

    try:
        ejecutar(argumentos.modo)

    except Exception as error:
        print("\nERROR DURANTE LA GENERACIÓN")
        print("-" * 60)
        print(type(error).__name__)
        print(str(error))
        raise