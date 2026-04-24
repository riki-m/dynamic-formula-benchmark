from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = Path(__file__).resolve().parents[1]
for entry in (PROJECT_ROOT, PYTHON_ROOT):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from src.db import get_connection, initialize_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed t_data with random numeric values")
    parser.add_argument("--rows", type=int, default=1_000_000, help="Number of rows to generate")
    parser.add_argument("--batch-size", type=int, default=10_000, help="Insert batch size")
    return parser.parse_args()


def build_batch(start_id: int, batch_size: int) -> list[tuple[int, float, float, float, float]]:
    rows = []
    for offset in range(batch_size):
        data_id = start_id + offset
        a = round(random.uniform(1, 1000), 4)
        b = round(random.uniform(1, 1000), 4)
        c = round(random.uniform(1, 1000), 4)
        d = round(random.uniform(1, 1000), 4)
        rows.append((data_id, a, b, c, d))
    return rows


def seed_data(rows_count: int, batch_size: int) -> None:
    initialize_database()

    with get_connection() as connection:
        connection.execute("DELETE FROM t_data")
        connection.commit()

        insert_sql = """
        INSERT INTO t_data (data_id, a, b, c, d)
        VALUES (?, ?, ?, ?, ?)
        """

        current_id = 1
        while current_id <= rows_count:
            current_batch_size = min(batch_size, rows_count - current_id + 1)
            batch = build_batch(current_id, current_batch_size)
            connection.executemany(insert_sql, batch)
            connection.commit()
            current_id += current_batch_size
            print(f"Inserted {current_id - 1:,} / {rows_count:,} rows")


if __name__ == "__main__":
    arguments = parse_args()
    seed_data(arguments.rows, arguments.batch_size)
