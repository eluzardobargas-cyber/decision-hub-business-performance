# or_tools_engine.py

from datetime import datetime, timedelta

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from parametros import (
    COSTO_FIJO_CAMION,
    COSTO_POR_HORA,
    COSTO_POR_KM,
    COSTO_POR_PARADA,
    HORA_SALIDA,
    JORNADA_MAX_MIN,
)


def convertir_minutos_a_hora(minutos):
    hora_base = datetime.strptime(HORA_SALIDA, "%H:%M")
    return (hora_base + timedelta(minutes=int(minutos))).time()


def _valor(cliente, columna, defecto=None):
    if columna in cliente.index:
        return cliente[columna]
    return defecto


def _costo_estimado(distancia_km, tiempo_total_min, paradas_camion):
    costo_tiempo = (tiempo_total_min / 60) * COSTO_POR_HORA
    costo_distancia = distancia_km * COSTO_POR_KM
    costo_paradas = paradas_camion * COSTO_POR_PARADA
    return round(COSTO_FIJO_CAMION + costo_tiempo + costo_distancia + costo_paradas, 2)


def optimizar_rutas(clientes, flota, matriz_tiempos, matriz_distancias):
    num_nodos = len(clientes)
    num_vehiculos = len(flota)
    depot = 0

    if num_nodos <= 1 or num_vehiculos == 0:
        return []

    manager = pywrapcp.RoutingIndexManager(num_nodos, num_vehiculos, depot)
    routing = pywrapcp.RoutingModel(manager)

    def tiempo_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        tiempo_viaje = int(matriz_tiempos[from_node][to_node])
        tiempo_servicio = int(clientes.iloc[from_node]["demora"])
        return tiempo_viaje + tiempo_servicio

    tiempo_callback_index = routing.RegisterTransitCallback(tiempo_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(tiempo_callback_index)

    routing.AddDimension(
        tiempo_callback_index,
        JORNADA_MAX_MIN,
        JORNADA_MAX_MIN,
        True,
        "Tiempo",
    )

    tiempo_dimension = routing.GetDimensionOrDie("Tiempo")

    for node in range(num_nodos):
        index = manager.NodeToIndex(node)
        apertura = int(clientes.iloc[node]["abre"])
        cierre = int(clientes.iloc[node]["cierra"])
        tiempo_dimension.CumulVar(index).SetRange(apertura, cierre)

    def demanda_callback(from_index):
        from_node = manager.IndexToNode(from_index)
        return int(clientes.iloc[from_node]["demanda"])

    demanda_callback_index = routing.RegisterUnaryTransitCallback(
        demanda_callback
    )

    capacidades = flota["capacidad_kg"].astype(int).tolist()

    routing.AddDimensionWithVehicleCapacity(
        demanda_callback_index,
        0,
        capacidades,
        True,
        "Capacidad",
    )

    for node in range(1, num_nodos):
        index = manager.NodeToIndex(node)
        cliente = clientes.iloc[node]

        prioridad = str(cliente["prioridad"]).lower()
        estado_planificacion = str(cliente["estado_planificacion"]).upper()
        tipo_cliente = str(cliente["tipo"]).lower()

        if prioridad == "urgente":
            penalizacion = 10_000_000
        elif estado_planificacion == "EXTRAORDINARIO":
            penalizacion = 2_000_000
        elif tipo_cliente == "cadena":
            penalizacion = 1_000_000
        else:
            penalizacion = 100_000

        routing.AddDisjunction([index], penalizacion)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.seconds = 10

    solution = routing.SolveWithParameters(search_parameters)

    if solution is None:
        return []

    rutas = []

    for vehicle_id in range(num_vehiculos):
        index = routing.Start(vehicle_id)
        secuencia = 1
        carga_acumulada = 0
        distancia_camion = 0
        tiempo_camion = 0
        paradas_camion = []
        nodo_anterior = None

        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            cliente = clientes.iloc[node]
            tiempo_llegada = solution.Min(tiempo_dimension.CumulVar(index))
            tiempo_servicio = int(cliente["demora"])
            tiempo_salida = tiempo_llegada + tiempo_servicio

            if nodo_anterior is None:
                tiempo_viaje = 0
                distancia_km = 0
            else:
                tiempo_viaje = int(matriz_tiempos[nodo_anterior][node])
                distancia_km = round(float(matriz_distancias[nodo_anterior][node]), 2)

            distancia_camion += distancia_km
            tiempo_camion += tiempo_viaje + tiempo_servicio

            carga_cliente = int(cliente["demanda"])
            carga_acumulada += carga_cliente

            capacidad_camion = int(flota.iloc[vehicle_id]["capacidad_kg"])
            capacidad_restante = capacidad_camion - carga_acumulada

            if not bool(cliente["es_deposito"]):
                paradas_camion.append(
                    {
                        "vehiculo_id": vehicle_id,
                        "id_camion": int(_valor(flota.iloc[vehicle_id], "id_camion", vehicle_id + 1)),
                        "camion": flota.iloc[vehicle_id]["descripcion"],
                        "perfil_camion": _valor(flota.iloc[vehicle_id], "perfil_camion", None),
                        "secuencia": secuencia,
                        "id_pedido": int(cliente["id_pedido"]),
                        "id_cliente": int(_valor(cliente, "id_cliente", 0)),
                        "cliente": cliente["nombre"],
                        "tipo_cliente": cliente["tipo"],
                        "estado_cliente": cliente["estado_cliente"],
                        "estado_planificacion": cliente["estado_planificacion"],
                        "grupo_logistico": _valor(cliente, "grupo_logistico", None),
                        "prioridad": cliente["prioridad"],
                        "carga_kg": carga_cliente,
                        "capacidad_camion_kg": capacidad_camion,
                        "lat": float(cliente["lat"]),
                        "lon": float(cliente["lon"]),
                        "minuto_llegada": int(tiempo_llegada),
                        "hora_llegada": convertir_minutos_a_hora(tiempo_llegada),
                        "hora_salida": convertir_minutos_a_hora(tiempo_salida),
                        "tiempo_viaje_min": tiempo_viaje,
                        "tiempo_servicio_min": tiempo_servicio,
                        "distancia_km": distancia_km,
                        "capacidad_restante": capacidad_restante,
                        "estado_asignacion": "ASIGNADO",
                        "direccion": _valor(cliente, "direccion", ""),
                        "barrio": _valor(cliente, "barrio", ""),
                        "grupo_logistico": _valor(cliente, "grupo_logistico", ""),
                    }
                )
                secuencia += 1

            nodo_anterior = node
            index = solution.Value(routing.NextVar(index))

        costo_camion = _costo_estimado(
            distancia_camion,
            tiempo_camion,
            len(paradas_camion),
        )

        for parada in paradas_camion:
            parada["distancia_total_camion_km"] = round(distancia_camion, 2)
            parada["tiempo_total_camion_min"] = int(tiempo_camion)
            parada["costo_estimado_camion"] = costo_camion

        rutas.extend(paradas_camion)

    return rutas

