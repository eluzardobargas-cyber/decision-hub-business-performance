# Decision Hub – Business Performance

[English](README.md) | **Español**

## Visión del proyecto

**Decision Hub – Business Performance** es un MVP de plataforma integral de apoyo a la toma de decisiones que conecta datos operativos, comerciales y de gestión en un mismo entorno.

El proyecto combina automatización de procesos, optimización operativa, persistencia de datos y Business Intelligence con el objetivo de transformar la actividad diaria en información accionable para distintos niveles de la organización.

El MVP actual utiliza un escenario de distribución y actividad comercial como entorno demostrativo, pero su arquitectura está concebida para evolucionar hacia un modelo corporativo más amplio, incorporando nuevas áreas, fuentes de información y reglas de negocio.

> El objetivo no es únicamente visualizar qué ocurrió, sino conectar datos, operación y análisis para facilitar decisiones sobre qué hacer a continuación.

---

## Un enfoque integral

Decision Hub se estructura en dos capas complementarias que comparten una misma base de información:

### Capa operativa — Decision Hub | Operations

Desarrollada principalmente con **Python, PostgreSQL, Streamlit y Google OR-Tools**, permite gestionar y analizar parte del proceso operativo de distribución.

Entre las capacidades implementadas se encuentran:

- preparación y validación de pedidos planificables;
- clasificación de pedidos según reglas operativas;
- asignación de pedidos y vehículos;
- optimización de rutas mediante Google OR-Tools;
- control de capacidades y restricciones operativas;
- identificación y diagnóstico de pedidos no asignados;
- gestión de excepciones y salidas adicionales;
- reprogramación de pedidos;
- registro y seguimiento de incidencias;
- estimación de distancias, tiempos y costes operativos;
- visualización geográfica de rutas;
- generación de información de ruta para el repartidor;
- envío de la ruta mediante WhatsApp para su consulta desde dispositivos móviles;
- persistencia de resultados en PostgreSQL.

### Capa analítica — Business Performance & Management Analytics

La capa de **Power BI** amplía la visión operativa y conecta la actividad logística con indicadores comerciales, de inventario, costes, servicio y rentabilidad.

El objetivo es proporcionar diferentes niveles de análisis dentro de un mismo entorno: desde el seguimiento operativo por parte de managers hasta una visión ejecutiva del rendimiento del negocio.

El modelo permite trabajar con indicadores relacionados, entre otros, con:

- inventario y cobertura;
- ventas;
- margen y costes;
- OTIF y cumplimiento operativo;
- incidencias y reprogramaciones;
- riesgo de inventario;
- productos y clientes;
- concentración y evolución del negocio;
- exposición operativa y comercial.

De esta forma, la operación no se analiza de manera aislada: sus resultados pueden relacionarse con el impacto comercial, económico y de servicio.

---

## El proyecto en acción

Las siguientes vistas muestran cómo Decision Hub conecta la toma de decisiones operativas con el análisis del negocio dentro de un mismo entorno.

### Flujo operativo — Decision Hub | Operations

La aplicación desarrollada en Streamlit acompaña el flujo operativo desde la planificación y la gestión de excepciones hasta la ejecución de las rutas.

#### Resumen de operaciones

![Resumen de operaciones de Decision Hub](assets/images/operations-overview.png)

Vista general de la planificación operativa con indicadores clave, utilización de la flota, distancia estimada, tiempo operativo, coste y rutas generadas.

#### Gestión de excepciones

![Gestión de excepciones de Decision Hub](assets/images/exception-management.png)

Vista de diagnóstico para los pedidos que no pudieron ser asignados respetando las restricciones operativas configuradas, facilitando el análisis de la excepción y la posterior toma de decisiones.

#### Ejecución de rutas

![Ejecución de rutas de Decision Hub](assets/images/route-execution.png)

Vista orientada al repartidor con representación geográfica de la ruta y las paradas asignadas, posibilidad de compartir la ruta mediante WhatsApp para su consulta desde el móvil y registro del resultado de cada entrega. El repartidor puede confirmar el pedido como entregado, rechazado o no entregado, indicando el motivo cuando corresponda.

### Análisis de Business Performance — Power BI

La capa analítica complementa la planificación operativa con análisis de gestión y visión ejecutiva. La implementación actual en Power BI incluye dos páginas desarrolladas: **Executive Overview** e **Inventory**.

#### Executive Overview

![Executive Overview de Decision Hub](assets/images/executive-overview.png)

Vista ejecutiva interactiva de ventas, rentabilidad, cobertura de inventario y nivel de servicio, incluyendo comparaciones respecto al mes anterior y análisis multidimensional del negocio.

#### Inventory

![Análisis de inventario de Decision Hub](assets/images/inventory-analysis.png)

Vista de apoyo a la decisión sobre inventario que combina valor de inventario, cobertura, riesgo crítico, venta perdida estimada, evolución del riesgo, relevancia comercial y rentabilidad por producto.

---

## Arquitectura de la solución

```text
                     DECISION HUB
                  Business Performance
                          │
          ┌───────────────┴───────────────┐
          │                               │
   CAPA OPERATIVA                  CAPA ANALÍTICA
          │                               │
 Python / Streamlit                    Power BI
 Google OR-Tools                          │
 Folium / OpenStreetMap                   │
          │                               │
          └──────────── PostgreSQL ───────┘
                          │
              Datos operativos y comerciales
                          │
                          ▼
                 TOMA DE DECISIONES
```

PostgreSQL actúa como capa central de datos, permitiendo conectar los procesos operativos con el modelo analítico.

El proyecto utiliza actualmente los esquemas:

```text
analytics
comercial
logistica
```

Esta separación facilita mantener diferenciadas las estructuras operativas, comerciales y analíticas sin perder la posibilidad de relacionarlas.

---

## Flujo operativo

De forma simplificada, la planificación sigue el siguiente proceso:

```text
Pedidos
   ↓
Validación
   ↓
Clasificación
   ↓
Preparación para optimización
   ↓
Asignación de flota
   ↓
Google OR-Tools
   ↓
Rutas y planificación
   ↓
Excepciones / incidencias / reprogramaciones
   ↓
Persistencia en PostgreSQL
   ↓
Streamlit + Power BI
   ↓
Información para la toma de decisiones
```

La aplicación Streamlit funciona como interfaz operativa, mientras que Power BI proporciona una capa complementaria de análisis y seguimiento gerencial.

---

## Optimización y cálculo de rutas

El motor utiliza **Google OR-Tools** para resolver la asignación y planificación considerando las restricciones configuradas en el modelo.

En el entorno demostrativo actual, las matrices de distancia se calculan mediante la fórmula de **Haversine** y los tiempos se estiman utilizando una velocidad media configurable.

Esta separación entre el motor de optimización y la fuente de distancias permite que, en una evolución futura, la matriz pueda ser sustituida por servicios de ruteo basados en red vial y tráfico sin necesidad de rediseñar la lógica principal de optimización.

Las rutas se representan geográficamente mediante **Folium y OpenStreetMap**.

---

## Modelo de costes

El MVP incorpora un modelo configurable para estimar el impacto económico de la planificación, considerando conceptos como:

- coste asociado al vehículo;
- distancia recorrida;
- coste por hora del operario/conductor;
- tiempo operativo;
- número de paradas;
- salidas adicionales.

El coste del tiempo de trabajo se calcula a partir de un coste horario configurable del operario. El modelo está preparado para diferenciar el coste de la jornada ordinaria y, cuando se active la lógica correspondiente, aplicar un factor adicional para las horas extraordinarias.
En el caso de una salida adicional realizada por el mismo vehículo durante la misma jornada, el modelo contempla los costes variables y el tiempo adicional de preparación sin duplicar el coste fijo del vehículo.

Los valores utilizados actualmente son parámetros demostrativos y no representan costes corporativos auditados.

En una implementación productiva, estos parámetros podrían alimentarse desde sistemas financieros, flota, recursos humanos, combustible, mantenimiento u otras fuentes corporativas.

---

## Datos sintéticos y entorno demostrativo

El proyecto utiliza datos sintéticos para disponer de un entorno controlado en el que validar la arquitectura, las reglas operativas, los procesos de optimización y el modelo analítico sin depender de información corporativa confidencial.

El módulo `comercial` genera actividad comercial sintética y permite construir escenarios relacionados con clientes, productos, pedidos, inventario, forecast, promociones y costes, conectándolos con la operación logística.

La utilización de datos sintéticos permite demostrar el funcionamiento del modelo. La incorporación de datos corporativos reales ampliaría el alcance del análisis, las casuísticas operativas y la precisión de los parámetros utilizados.

---

## Estructura del repositorio

```text
.
├── comercial/
│   ├── __init__.py
│   ├── seed_comercial.py
│   └── seed_decision_hub.py
│
├── decision_hub/
│   ├── __init__.py
│   ├── app.py
│   ├── app_db.py
│   ├── clasificador_pedidos.py
│   ├── gestion_incidencias.py
│   ├── matriz_distancias.py
│   ├── optimizador.py
│   ├── or_tools_engine.py
│   ├── parametros.py
│   ├── persistencia.py
│   ├── repositorio.py
│   ├── seed_clientes.py
│   ├── seed_flota.py
│   ├── seed_pedidos.py
│   └── validacion_pedidos.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── README_ES.md
```

### Componentes principales

`decision_hub/app.py`  
Interfaz Streamlit y orquestación de la planificación operativa.

`decision_hub/or_tools_engine.py`  
Motor de optimización basado en Google OR-Tools.

`decision_hub/optimizador.py`  
Preparación y coordinación del proceso de optimización, asignaciones y excepciones.

`decision_hub/repositorio.py`  
Acceso a los datos operativos almacenados en PostgreSQL.

`decision_hub/persistencia.py`  
Persistencia de rutas y resultados de planificación.

`decision_hub/gestion_incidencias.py`  
Registro y gestión de incidencias operativas.

`decision_hub/matriz_distancias.py`  
Construcción de matrices de distancia y tiempo.

`comercial/`  
Generación e integración de datos sintéticos para la capa comercial y analítica.

---

## Tecnologías

**Backend y procesamiento:** Python, Pandas, NumPy, SQLAlchemy  
**Base de datos:** PostgreSQL  
**Optimización:** Google OR-Tools  
**Aplicación operativa:** Streamlit  
**Mapas:** Folium + OpenStreetMap  
**Business Intelligence:** Microsoft Power BI  
**Configuración:** variables de entorno mediante `python-dotenv`

---

## Configuración local

### 1. Crear un entorno virtual

```bash
python -m venv .venv
```

### 2. Activarlo

En Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar PostgreSQL

Copiar:

```text
.env.example
```

como:

```text
.env
```

y completar las credenciales correspondientes al entorno local.

El archivo `.env` está excluido del repositorio y no debe incluirse en el control de versiones.

### 5. Ejecutar la aplicación

```bash
streamlit run decision_hub/app.py
```

---

## Escalabilidad

Decision Hub está planteado como una arquitectura modular.

El MVP actual demuestra la integración entre operación, logística, actividad comercial, inventario, costes y análisis gerencial. El mismo enfoque puede extenderse progresivamente a otras áreas corporativas mediante nuevas fuentes de datos, modelos y reglas de negocio.

Entre las posibles evoluciones se encuentran:

- integración con ERP y otros sistemas corporativos;
- GPS y posicionamiento de flota;
- matrices de distancia y tiempo basadas en red vial;
- información de tráfico;
- integración de costes corporativos reales;
- nuevas áreas funcionales y fuentes de información;
- automatización adicional de procesos;
- modelos predictivos de demanda, incidencias, tiempos y costes;
- ampliación de indicadores ejecutivos y escenarios de decisión.

El objetivo de esta evolución no es convertir cada área en una aplicación independiente, sino mantener una **visión integrada del negocio** que permita relacionar decisiones operativas con sus efectos comerciales, económicos y de servicio.

---

## Estado del proyecto

**MVP demostrativo en desarrollo.**

La arquitectura funcional y el modelo de decisión están preparados para evolucionar hacia una solución conectada con sistemas corporativos cuando el proyecto avance hacia un entorno de producción.

Las funcionalidades y parámetros actuales deben interpretarse dentro del contexto demostrativo del proyecto.

---
