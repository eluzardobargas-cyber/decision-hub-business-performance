# app_db.py

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL


# ---------------------------------------------------------
# Carga de configuración
# ---------------------------------------------------------
# En desarrollo local, las credenciales se leen desde .env.
# En el despliegue, Streamlit proporcionará estas mismas
# variables de entorno mediante su sistema de Secrets.
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)


# ---------------------------------------------------------
# Parámetros de conexión
# ---------------------------------------------------------
DB_USER = os.getenv("DECISION_HUB_DB_USER")
DB_PASSWORD = os.getenv("DECISION_HUB_DB_PASSWORD")
DB_HOST = os.getenv("DECISION_HUB_DB_HOST", "localhost")
DB_PORT = os.getenv("DECISION_HUB_DB_PORT", "5433")
DB_NAME = os.getenv("DECISION_HUB_DB_NAME")

# PostgreSQL local no requiere SSL.
# Neon sí lo requiere, por lo que esta variable solo se
# configurará en el entorno desplegado.
DB_SSLMODE = os.getenv("DECISION_HUB_DB_SSLMODE")


# ---------------------------------------------------------
# Construcción segura de la URL
# ---------------------------------------------------------
# URL.create evita construir manualmente una cadena con
# usuario y contraseña, especialmente útil si la contraseña
# contiene caracteres especiales.
connection_query = {}

if DB_SSLMODE:
    connection_query["sslmode"] = DB_SSLMODE

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query=connection_query,
)


# ---------------------------------------------------------
# Motor SQLAlchemy
# ---------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)