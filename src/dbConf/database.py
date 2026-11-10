import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

load_dotenv()

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def connect(url):
    return psycopg.connect(url)


def connect_from_env():
    return connect(os.environ["DATABASE_URL"])


def create_sample_tables(conn):
    with conn.transaction():
        conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))


class PostgresSampleRepository:
    def __init__(self, conn):
        self._conn = conn

    def save_sample(self, label, points):
        flat = [value for point in points for value in point]
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO samples (epression_id, points) "
                "SELECT id, %s FROM epression WHERE label = %s RETURNING id",
                (Jsonb(flat), label),
            )
            if cur.fetchone() is None:
                raise ValueError(f"Vocal desconocida: {label}")
