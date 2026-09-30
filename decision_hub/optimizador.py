# optimizador.py

from datetime import datetime

import pandas as pd

from clasificador_pedidos import clasificar_pedidos
from gestion_incidencias import (
    limpiar_incidencias,
    registrar_incidencia,
    cerrar_incidencias_planificacion_asignadas,
)
from matriz_distancias import crear_matriz_distancias, crear_matriz_tiempos_min
from or_tools_engine import optimizar_rutas
from persistencia import guardar_rutas
from repositorio import cargar_deposito, cargar_flota, cargar_pedidos_planificables
from seed_pedidos import resolver_fechas


MAPA_DIAS = {
    0: "LUN",
    1: "MAR",
    2: "MIE",
    3: "JUE",
    4: "VIE",
    5: "SAB",
    6: "DOM",
}

PERFILES_FLOTA = {
    "CADENA": ["Grande"],
    "APOYO": ["Mediano"],
    "COMERCIO": ["Urbano"],
}

REASIGNACION_PERMITIDA = {
    "CADENA": [],
    "APOYO": ["COMERCIO"],
    "COMERCIO": ["APOYO"],
}


def crear_id_ejecucion(fecha_entrega):
    marca = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"RUN-{fecha_entrega}-{marca}"


def obtener_dia_operativo(fecha):
    return MAPA_DIAS[fecha.weekday()]


def preparar_pedidos_para_optimizador(fecha_entrega):
    pedidos = cargar_pedidos_planificables(fecha_entrega)
    deposito = cargar_deposito()

    if pedidos.empty:
        print("No hay pedidos planificables para la fecha indicada.")
        return pd.DataFrame()

    deposito = deposito.copy()

    if "barrio" not in deposito.columns:
        deposito["barrio"] = ""

    deposito["id_pedido"] = 0
    deposito["fecha_entrega"] = fecha_entrega
    deposito["peso_kg"] = 0
    deposito["prioridad_pedido"] = "NORMAL"
    deposito["estado_planificacion"] = "DEPOSITO"
    deposito["demanda"] = 0
    deposito["prioridad"] = "normal"


    pedidos = pedidos.copy()

    if "barrio" not in pedidos.columns:
        pedidos["barrio"] = ""

    pedidos["demanda"] = pedidos["peso_kg"]
    pedidos["prioridad"] = pedidos["prioridad_pedido"].str.lower()

    columnas = [
        "id_pedido",
        "id_cliente",
        "nombre",
        "direccion",
        "barrio",
        "lat",
        "lon",
        "tipo",
        "estado_cliente",
        "prioridad",
        "estado_planificacion",
        "demanda",
        "demora",
        "abre",
        "cierra",
        "es_deposito",
    ]

    datos = pd.concat([deposito[columnas], pedidos[columnas]], ignore_index=True)
    return clasificar_pedidos(datos)


def obtener_flota_por_grupo(flota, grupo):
    palabras = PERFILES_FLOTA.get(grupo, [])

    if not palabras:
        return pd.DataFrame()

    filtro = False
    for palabra in palabras:
        filtro = filtro | flota["descripcion"].str.contains(
            palabra,
            case=False,
            na=False,
        )

    flota_grupo = flota[filtro].copy()
    flota_grupo["perfil_camion"] = grupo
    flota_grupo.reset_index(drop=True, inplace=True)
    return flota_grupo


def optimizar_grupo(datos, flota, grupo, ids_excluir=None, origen_asignacion="PRINCIPAL"):
    ids_excluir = set(ids_excluir or [])

    deposito = datos[datos["grupo_logistico"] == "DEPOSITO"].copy()
    pedidos_grupo = datos[
        (datos["grupo_logistico"] == grupo)
        & (~datos["id_pedido"].isin(ids_excluir))
    ].copy()

    if pedidos_grupo.empty:
        return []

    datos_grupo = pd.concat([deposito, pedidos_grupo], ignore_index=True)
    flota_grupo = obtener_flota_por_grupo(flota, grupo)

    if flota_grupo.empty:
        return []

    matriz_tiempos = crear_matriz_tiempos_min(datos_grupo)
    matriz_distancias = crear_matriz_distancias(datos_grupo)


    rutas = optimizar_rutas(
        clientes=datos_grupo,
        flota=flota_grupo,
        matriz_tiempos=matriz_tiempos,
        matriz_distancias=matriz_distancias,
    )

    for ruta in rutas:
        ruta["origen_asignacion"] = origen_asignacion

    return rutas

def generar_ruta_para_excepcion(
    fecha_entrega,
    id_pedido,
    camion,
):
    """
    Calcula una ruta independiente para un pedido pendiente,
    utilizando exclusivamente el camión seleccionado.

    No guarda la ruta ni modifica la incidencia.
    """

    datos = preparar_pedidos_para_optimizador(
        fecha_entrega
    )

    if datos.empty:
        raise ValueError(
            "No existen pedidos planificables para la fecha."
        )

    deposito = datos[
        datos["grupo_logistico"] == "DEPOSITO"
    ].copy()

    pedido = datos[
        datos["id_pedido"] == int(id_pedido)
    ].copy()

    if pedido.empty:
        raise ValueError(
            "El pedido pendiente no se encuentra disponible "
            "para la fecha seleccionada."
        )

    flota = cargar_flota()

    flota_camion = flota[
        flota["descripcion"]
        .astype(str)
        .str.strip()
        .str.casefold()
        == str(camion).strip().casefold()
    ].copy()

    if flota_camion.empty:
        raise ValueError(
            "No se encontró el camión seleccionado."
        )

    peso_pedido = float(
        pedido.iloc[0]["demanda"] or 0
    )

    capacidad_camion = float(
        flota_camion.iloc[0]["capacidad_kg"] or 0
    )

    if peso_pedido > capacidad_camion:
        raise ValueError(
            "El pedido supera la capacidad total "
            "del camión seleccionado."
        )

    datos_salida = pd.concat(
        [deposito, pedido],
        ignore_index=True,
    )

    flota_camion["perfil_camion"] = (
        "EXCEPCION_MANUAL"
    )

    flota_camion.reset_index(
        drop=True,
        inplace=True,
    )

    matriz_tiempos = crear_matriz_tiempos_min(
        datos_salida
    )

    matriz_distancias = crear_matriz_distancias(
        datos_salida
    )

    rutas = optimizar_rutas(
        clientes=datos_salida,
        flota=flota_camion,
        matriz_tiempos=matriz_tiempos,
        matriz_distancias=matriz_distancias,
    )

    rutas = [
        ruta
        for ruta in rutas
        if int(ruta.get("id_pedido") or 0)
        == int(id_pedido)
    ]

    if not rutas:
        raise ValueError(
            "El motor no encontró una ruta viable para el "
            "pedido y el camión seleccionados. Revisa la "
            "ventana horaria o utiliza otra alternativa."
        )

    ventana_apertura = pedido.iloc[0].get("abre")
    ventana_cierre = pedido.iloc[0].get("cierra")

    for ruta in rutas:
        ruta["origen_asignacion"] = (
            "ASIGNACION_MANUAL"
        )
        ruta["estado_asignacion"] = (
            "ASIGNADO_MANUAL"
        )
        ruta["ventana_apertura"] = (
            ventana_apertura
        )
        ruta["ventana_cierre"] = ventana_cierre

    return rutas

def pedidos_no_asignados(datos, rutas):
    pedidos_planificables = datos[datos["es_deposito"] == False].copy()
    ids_asignados = {r["id_pedido"] for r in rutas}
    return pedidos_planificables[
        ~pedidos_planificables["id_pedido"].isin(ids_asignados)
    ].copy()


def intentar_reasignaciones(datos, flota, rutas_iniciales):
    rutas = list(rutas_iniciales)

    pendientes = pedidos_no_asignados(datos, rutas)

    if pendientes.empty:
        return rutas

    camiones_usados = {r["camion"] for r in rutas}

    flota_libre = flota[
        ~flota["descripcion"].isin(camiones_usados)
    ].copy()

    if flota_libre.empty:
        return rutas

    deposito = datos[datos["grupo_logistico"] == "DEPOSITO"].copy()

    datos_rescate = pd.concat(
        [deposito, pendientes],
        ignore_index=True,
    )

    flota_libre["perfil_camion"] = "RESCATE"
    flota_libre.reset_index(drop=True, inplace=True)

    matriz_tiempos = crear_matriz_tiempos_min(datos_rescate)
    matriz_distancias = crear_matriz_distancias(datos_rescate)

    rutas_rescate = optimizar_rutas(
        clientes=datos_rescate,
        flota=flota_libre,
        matriz_tiempos=matriz_tiempos,
        matriz_distancias=matriz_distancias,
    )

    for r in rutas_rescate:
        r["origen_asignacion"] = "REASIGNACION_AUTOMATICA"
        r["estado_asignacion"] = "REASIGNADO"

    rutas.extend(rutas_rescate)

    return rutas


def registrar_pedidos_no_asignados(
    fecha_entrega,
    datos,
    rutas,
    id_ejecucion,
):
    no_asignados = pedidos_no_asignados(
        datos,
        rutas,
    )

    ids_asignados = {
        int(ruta["id_pedido"])
        for ruta in rutas
        if ruta.get("id_pedido") is not None
    }

    # Cerrar incidencias antiguas de los pedidos que
    # sí fueron incorporados a la planificación vigente.
    cerrar_incidencias_planificacion_asignadas(
        fecha_entrega=fecha_entrega,
        ids_asignados=ids_asignados,
    )

    for _, pedido in no_asignados.iterrows():

        registrar_incidencia(
            id_ejecucion=id_ejecucion,
            id_pedido=int(pedido["id_pedido"]),
            fecha_entrega=fecha_entrega,
            cliente=pedido["nombre"],
            tipo="APROBACION_MANUAL",
            gravedad="ALTA",
            motivo=(
                "No fue posible asignar el pedido respetando "
                "capacidad, jornada, ventana horaria y perfiles "
                "de flota."
            ),
            accion=(
                "Revisar manualmente: cambiar día, autorizar "
                "excepción, sumar viaje o modificar ventana horaria."
            ),
        )

    if len(no_asignados) > 0:
        print(
            "Pedidos enviados a aprobación manual: "
            f"{len(no_asignados)}"
        )

    return no_asignados


def ejecutar_optimizacion():
    _, fecha_entrega = resolver_fechas()
    dia_operativa = obtener_dia_operativo(fecha_entrega)
    id_ejecucion = crear_id_ejecucion(fecha_entrega)

    datos = preparar_pedidos_para_optimizador(fecha_entrega)

    if datos.empty:
        return []

    flota = cargar_flota()
    limpiar_incidencias(fecha_entrega)

    rutas = []
    for grupo in ["CADENA", "APOYO", "COMERCIO"]:
        rutas.extend(optimizar_grupo(datos, flota, grupo))

    rutas = intentar_reasignaciones(datos, flota, rutas)

    print(f"\nID ejecucion: {id_ejecucion}")
    print(f"Fecha entrega: {fecha_entrega}")
    print(f"Dia operativo: {dia_operativa}")
    print(f"Pedidos planificables: {len(datos) - 1}")
    print(f"Camiones: {len(flota)}")
    print(f"Paradas generadas: {len(rutas)}")

    for r in rutas:
        print(
            r["camion"],
            "| Secuencia:",
            r["secuencia"],
            "| Cliente:",
            r["cliente"],
            "| Llegada:",
            r.get("hora_llegada"),
            "| Carga:",
            r["carga_kg"],
            "| Grupo:",
            r.get("grupo_logistico"),
            "| Estado:",
            r.get("estado_asignacion"),
        )

    guardar_rutas(
        fecha_entrega=fecha_entrega,
        dia_operativa=dia_operativa,
        rutas=rutas,
        id_ejecucion=id_ejecucion,
    )

    registrar_pedidos_no_asignados(
        fecha_entrega=fecha_entrega,
        datos=datos,
        rutas=rutas,
        id_ejecucion=id_ejecucion,
    )

    return rutas


if __name__ == "__main__":
    ejecutar_optimizacion()

