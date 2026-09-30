# clasificador_pedidos.py


PERFIL_POR_GRUPO = {
    "DEPOSITO": "DEPOSITO",
    "CADENA": "GRANDE",
    "APOYO": "MEDIANO",
    "COMERCIO": "URBANO",
}

ALTERNATIVAS_POR_GRUPO = {
    "CADENA": [],
    "APOYO": ["URBANO"],
    "COMERCIO": ["MEDIANO"],
}


def clasificar_pedidos(datos):
    """
    Clasifica cada pedido segun la logica operativa.

    - DEPOSITO: punto de salida.
    - CADENA: supermercados y cadenas grandes.
    - APOYO: urgentes, nuevos o extraordinarios.
    - COMERCIO: comercios habituales.
    """

    datos = datos.copy()

    def asignar_grupo(fila):
        if bool(fila["es_deposito"]):
            return "DEPOSITO"

        tipo = str(fila["tipo"]).strip().lower()
        prioridad = str(fila["prioridad"]).strip().lower()
        estado_cliente = str(fila["estado_cliente"]).strip().lower()
        estado_planificacion = str(fila["estado_planificacion"]).strip().upper()

        if tipo == "cadena":
            return "CADENA"

        if (
            prioridad == "urgente"
            or estado_cliente == "nuevo"
            or estado_planificacion == "EXTRAORDINARIO"
        ):
            return "APOYO"

        return "COMERCIO"

    datos["grupo_logistico"] = datos.apply(asignar_grupo, axis=1)
    datos["perfil_preferido"] = datos["grupo_logistico"].map(PERFIL_POR_GRUPO)
    datos["perfiles_alternativos"] = datos["grupo_logistico"].map(
        ALTERNATIVAS_POR_GRUPO
    )

    return datos

