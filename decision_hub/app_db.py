# app_db.py

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"     #usamos Path(__file__)... para que no influya la carpeta desde donde se abre la terminal 
load_dotenv(ENV_PATH)

DB_USER = os.getenv("DECISION_HUB_DB_USER")
DB_PASSWORD = os.getenv("DECISION_HUB_DB_PASSWORD")
DB_HOST = os.getenv("DECISION_HUB_DB_HOST", "localhost")
DB_PORT = os.getenv("DECISION_HUB_DB_PORT", "5433")
DB_NAME = os.getenv("DECISION_HUB_DB_NAME")

DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
)

engine = create_engine(DATABASE_URL, echo=False, future=True)

