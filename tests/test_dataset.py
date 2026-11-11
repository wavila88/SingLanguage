import os
import uuid

import pytest

from dbConf.database import PostgresSampleRepository, connect, create_sample_tables


def points():
    return [(float(i), float(i) + 0.5, float(i) + 0.25) for i in range(21)]


@pytest.fixture
def conn():
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL no configurada")
    connection = connect(url)
    create_sample_tables(connection)
    yield connection
    connection.close()


def test_second_save_appends_sample_to_its_epression_and_keeps_first(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM samples")
        last_id = cur.fetchone()[0]

    try:
        repo = PostgresSampleRepository(conn)
        repo.save_sample("e", points())
        repo.save_sample("e", points())

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM epression WHERE label = 'e'")
            assert cur.fetchone()[0] == 1
            cur.execute(
                "SELECT s.id, l.label, jsonb_array_length(s.points) FROM samples s "
                "JOIN epression l ON l.id = s.epression_id WHERE s.id > %s ORDER BY s.id",
                (last_id,),
            )
            rows = cur.fetchall()

        assert len(rows) == 2
        assert all(label == "e" and length == 63 for _, label, length in rows)
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM samples WHERE id > %s", (last_id,))


def test_opening_an_expression_twice_creates_one_row_and_counts_per_kind(conn):
    label = f"prueba_{uuid.uuid4().hex[:8]}"
    repo = PostgresSampleRepository(conn)
    try:
        assert repo.open_expression(label, "static") == 0
        assert repo.open_expression(label, "static") == 0
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM epression WHERE label = %s", (label,))
            assert cur.fetchone()[0] == 1
            cur.execute("SELECT id FROM epression WHERE label = %s", (label,))
            expression_id = cur.fetchone()[0]
            cur.execute("INSERT INTO samples (epression_id, points, kind) VALUES (%s, '[]', 'static')", (expression_id,))
            cur.execute("INSERT INTO samples (epression_id, points, kind) VALUES (%s, '[]', 'motion')", (expression_id,))
            cur.execute("INSERT INTO samples (epression_id, points, kind) VALUES (%s, '[]', 'motion')", (expression_id,))

        assert repo.open_expression(label, "static") == 1
        assert repo.open_expression(label, "motion") == 2
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM epression WHERE label = %s", (label,))


def test_samples_saved_before_the_kind_column_count_as_static(conn):
    repo = PostgresSampleRepository(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM samples")
        last_id = cur.fetchone()[0]
    try:
        before = repo.open_expression("a", "static")
        repo.save_sample("a", points())

        assert repo.open_expression("a", "static") == before + 1
        assert repo.open_expression("a", "motion") == 0
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM samples WHERE id > %s", (last_id,))
