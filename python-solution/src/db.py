import sqlite3
from pathlib import Path

from src.config import DATABASE_PATH


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS t_data (
    data_id INTEGER PRIMARY KEY,
    a REAL NOT NULL,
    b REAL NOT NULL,
    c REAL NOT NULL,
    d REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS t_targil (
    targil_id INTEGER PRIMARY KEY,
    targil TEXT NOT NULL,
    tnai TEXT NULL,
    targil_false TEXT NULL
);

CREATE TABLE IF NOT EXISTS t_results (
    result_id INTEGER PRIMARY KEY,
    data_id INTEGER NOT NULL,
    targil_id INTEGER NOT NULL,
    method TEXT NOT NULL,
    result REAL NULL,
    FOREIGN KEY (data_id) REFERENCES t_data(data_id),
    FOREIGN KEY (targil_id) REFERENCES t_targil(targil_id)
);

CREATE TABLE IF NOT EXISTS t_log (
    log_id INTEGER PRIMARY KEY,
    targil_id INTEGER NOT NULL,
    method TEXT NOT NULL,
    run_time REAL NULL,
    records_processed INTEGER NOT NULL,
    FOREIGN KEY (targil_id) REFERENCES t_targil(targil_id)
);

CREATE INDEX IF NOT EXISTS idx_t_results_data_id ON t_results(data_id);
CREATE INDEX IF NOT EXISTS idx_t_results_targil_id ON t_results(targil_id);
CREATE INDEX IF NOT EXISTS idx_t_results_method ON t_results(method);
CREATE INDEX IF NOT EXISTS idx_t_log_targil_id ON t_log(targil_id);
CREATE INDEX IF NOT EXISTS idx_t_log_method ON t_log(method);
"""


FORMULAS_SQL = """
INSERT OR IGNORE INTO t_targil (targil_id, targil, tnai, targil_false) VALUES
(1, 'a + b', NULL, NULL),
(2, 'c * 2', NULL, NULL),
(3, 'b - a', NULL, NULL),
(4, 'd / 4', NULL, NULL),
(5, '(a + b) * 8', NULL, NULL),
(6, 'sqrt(c^2 + d^2)', NULL, NULL),
(7, 'log(b) + c', NULL, NULL),
(8, 'abs(d - b)', NULL, NULL),
(9, 'b * 2', 'a > 5', 'b / 2'),
(10, 'a + 1', 'b < 10', 'd - 1'),
(11, '1', 'a == c', '0');
"""


def get_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DATABASE_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.executescript(SCHEMA_SQL)
        ensure_column_exists(connection, "t_log", "records_processed", "INTEGER NOT NULL DEFAULT 0")
        connection.executescript(FORMULAS_SQL)
        connection.commit()


def reset_method_results(method: str) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM t_results WHERE method = ?", (method,))
        connection.execute("DELETE FROM t_log WHERE method = ?", (method,))
        connection.commit()


def table_has_rows(table_name: str) -> bool:
    with get_connection() as connection:
        row = connection.execute(f"SELECT 1 FROM {table_name} LIMIT 1").fetchone()
        return row is not None


def database_file() -> Path:
    return DATABASE_PATH


def iter_data_rows(batch_size: int):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            SELECT data_id, a, b, c, d
            FROM t_data
            ORDER BY data_id
            """
        )

        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            yield [dict(row) for row in rows]


def ensure_column_exists(connection: sqlite3.Connection, table_name: str, column_name: str, column_definition: str) -> None:
    existing_columns = {
        row["name"]
        for row in connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    }

    if column_name not in existing_columns:
        connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
        )
