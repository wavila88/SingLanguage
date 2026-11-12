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

    def save_static_sample(self, label, hands):
        """Save one static sample: `{"hands": [...]}` as points, which training skips (it reads only arrays)."""
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO samples (epression_id, points, kind) "
                "SELECT id, %s, 'static' FROM epression WHERE label = %s RETURNING id",
                (Jsonb({"hands": hands}), label),
            )
            if cur.fetchone() is None:
                raise ValueError(f"Expresion desconocida: {label}")

    def save_motion_sample(self, label, frames):
        """Save a motion sample (no points of its own) and its frames together, or nothing."""
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute(
                "INSERT INTO samples (epression_id, kind) "
                "SELECT id, 'motion' FROM epression WHERE label = %s RETURNING id",
                (label,),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(f"Expresion desconocida: {label}")
            cur.executemany(
                "INSERT INTO sample_frames (sample_id, frame_index, ms, hands) VALUES (%s, %s, %s, %s)",
                [(row[0], frame["index"], frame["ms"], Jsonb(frame["hands"])) for frame in frames],
            )

    def open_expression(self, label, kind):
        """Create the expression if it is new and return how many samples of `kind` it has."""
        with self._conn.transaction(), self._conn.cursor() as cur:
            cur.execute("INSERT INTO epression (label) VALUES (%s) ON CONFLICT (label) DO NOTHING", (label,))
            cur.execute(
                "SELECT COUNT(*) FROM samples s JOIN epression e ON e.id = s.epression_id "
                "WHERE e.label = %s AND s.kind = %s",
                (label, kind),
            )
            return cur.fetchone()[0]

    def load_motion_samples(self):
        """(label, frames) for every motion sample, each with its frames in order."""
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT e.label, s.id, f.frame_index, f.ms, f.hands FROM samples s "
                "JOIN epression e ON e.id = s.epression_id JOIN sample_frames f ON f.sample_id = s.id "
                "WHERE s.kind = 'motion' ORDER BY s.id, f.frame_index"
            )
            samples = {}
            for label, sample_id, index, ms, hands in cur.fetchall():
                samples.setdefault(sample_id, (label, []))[1].append({"index": index, "ms": ms, "hands": hands})
            return list(samples.values())

    def load_samples(self):
        """(label, 63 points) for every one-hand static sample: the old vowel rows and the new rows with one hand.

        Two-hand static samples are left out because the vowel model is a one-hand model.
        """
        with self._conn.cursor() as cur:
            cur.execute(
                "SELECT lower(trim(l.label)), CASE WHEN jsonb_typeof(s.points) = 'array' THEN s.points "
                "ELSE s.points -> 'hands' -> 0 -> 'points' END FROM samples s "
                "JOIN epression l ON l.id = s.epression_id "
                "WHERE s.kind = 'static' AND (jsonb_typeof(s.points) = 'array' "
                "OR jsonb_array_length(s.points -> 'hands') = 1) ORDER BY s.id"
            )
            return [(label, points) for label, points in cur.fetchall()]
