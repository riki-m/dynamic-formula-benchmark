from __future__ import annotations

from contextlib import contextmanager

from src.config import SQLSERVER_CONNECTION_STRING


def _import_pyodbc():
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError(
            "pyodbc is required for SQL Server execution. Install dependencies from requirements.txt first."
        ) from exc
    return pyodbc


@contextmanager
def get_connection():
    pyodbc = _import_pyodbc()
    connection = pyodbc.connect(SQLSERVER_CONNECTION_STRING)
    try:
        yield connection
    finally:
        connection.close()


def table_has_rows(table_name: str) -> bool:
    with get_connection() as connection:
        cursor = connection.cursor()
        row = cursor.execute(f"SELECT TOP 1 1 FROM {table_name}").fetchone()
        return row is not None


def load_formulas() -> list[dict]:
    with get_connection() as connection:
        cursor = connection.cursor()
        rows = cursor.execute(
            """
            SELECT targil_id, targil, tnai, targil_false
            FROM t_targil
            ORDER BY targil_id
            """
        ).fetchall()

    return [
        {
            "targil_id": row[0],
            "targil": row[1],
            "tnai": row[2],
            "targil_false": row[3],
        }
        for row in rows
    ]


def iter_data_rows(batch_size: int):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT data_id, a, b, c, d
            FROM t_data
            ORDER BY data_id
            """
        )

        columns = [column[0] for column in cursor.description]
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield [dict(zip(columns, row)) for row in rows]


def reset_method_results(method: str) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM t_results WHERE method = ?", method)
        cursor.execute("DELETE FROM t_log WHERE method = ?", method)
        connection.commit()


def insert_results(calculated_rows: list[tuple[int, int, str, float]]) -> None:
    if not calculated_rows:
        return

    with get_connection() as connection:
        cursor = connection.cursor()
        max_row = cursor.execute("SELECT ISNULL(MAX(result_id), 0) FROM t_results").fetchone()
        next_result_id = int(max_row[0]) + 1
        payload = []
        for data_id, targil_id, method, result in calculated_rows:
            payload.append((next_result_id, data_id, targil_id, method, result))
            next_result_id += 1

        cursor.fast_executemany = True
        cursor.executemany(
            """
            INSERT INTO t_results (result_id, data_id, targil_id, method, result)
            VALUES (?, ?, ?, ?, ?)
            """,
            payload,
        )
        connection.commit()


def insert_log(formula_id: int, method: str, runtime_seconds: float, records_processed: int) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()
        max_row = cursor.execute("SELECT ISNULL(MAX(log_id), 0) FROM t_log").fetchone()
        next_log_id = int(max_row[0]) + 1
        cursor.execute(
            """
            INSERT INTO t_log (log_id, targil_id, method, run_time, records_processed)
            VALUES (?, ?, ?, ?, ?)
            """,
            next_log_id,
            formula_id,
            method,
            runtime_seconds,
            records_processed,
        )
        connection.commit()
