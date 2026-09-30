# validacion_pedidos.py

from datetime import datetime
from sqlalchemy import text

from app_db import engine
from parametros import (
    ESTADO_PROGRAMADO,
    ESTADO_EXTRAORDINARIO,
    ESTADO_PENDIENTE_VALIDACION,
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


def obtener_dia_operativo(fecha_entrega):
    if isinstance(fecha_entrega, str):
        fecha_entrega = datetime.strptime(fecha_entrega, "%Y-%m-%d").date()

    return MAPA_DIAS[fecha_entrega.weekday()]


def validar_pedidos(fecha_entrega):

    dia_operativo = obtener_dia_operativo(fecha_entrega)

    with engine.begin() as conn:

        pedidos = conn.execute(
            text("""
                SELECT
                    p.id_pedido,
                    p.id_cliente,
                    p.fecha_entrega,
                    c.nombre,
                    c.activo,
                    c.dias_asignados
                FROM logistica.pedidos p
                JOIN logistica.clientes c
                    ON p.id_cliente = c.id_cliente
                WHERE p.fecha_entrega = :fecha_entrega
            """),
            {"fecha_entrega": fecha_entrega}
        ).mappings().all()

        total = 0
        programados = 0
        extraordinarios = 0
        pendientes = 0

        for pedido in pedidos:

            total += 1

            if not pedido["activo"]:
                estado = ESTADO_PENDIENTE_VALIDACION
                observacion = "Cliente inactivo"

            else:
                dias_cliente = [
                    d.strip().upper()
                    for d in pedido["dias_asignados"].split(",")
                ]

                if dia_operativo in dias_cliente:
                    estado = ESTADO_PROGRAMADO
                    observacion = "Pedido coincide con día asignado"
                    programados += 1

                else:
                    estado = ESTADO_EXTRAORDINARIO
                    observacion = "Pedido fuera del día asignado; se intentará incorporar automáticamente"
                    extraordinarios += 1

            if estado == ESTADO_PENDIENTE_VALIDACION:
                pendientes += 1

            conn.execute(
                text("""
                    UPDATE logistica.pedidos
                    SET
                        estado_planificacion = :estado,
                        observaciones = :observacion
                    WHERE id_pedido = :id_pedido
                """),
                {
                    "estado": estado,
                    "observacion": observacion,
                    "id_pedido": pedido["id_pedido"],
                }
            )

    print("✅ Validación de pedidos finalizada")
    print(f"Fecha entrega: {fecha_entrega}")
    print(f"Día operativo: {dia_operativo}")
    print(f"Total pedidos: {total}")
    print(f"Programados: {programados}")
    print(f"Extraordinarios: {extraordinarios}")
    print(f"Pendientes validación: {pendientes}")


if __name__ == "__main__":
    from seed_pedidos import resolver_fechas

    _, fecha_entrega = resolver_fechas()
    validar_pedidos(fecha_entrega)