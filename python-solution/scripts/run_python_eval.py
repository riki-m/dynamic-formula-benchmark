from __future__ import annotations

import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = Path(__file__).resolve().parents[1]
for entry in (PROJECT_ROOT, PYTHON_ROOT):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from src.config import DEFAULT_BATCH_SIZE, METHOD_PYTHON_EVAL
from src.db import get_connection, initialize_database, iter_data_rows, reset_method_results, table_has_rows
from src.formula_runtime import FormulaDefinition, evaluate_formula, prepare_formula


def load_formulas() -> list[FormulaDefinition]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT targil_id, targil, tnai, targil_false
            FROM t_targil
            ORDER BY targil_id
            """
        ).fetchall()

    return [
        FormulaDefinition(
            targil_id=row["targil_id"],
            targil=row["targil"],
            tnai=row["tnai"],
            targil_false=row["targil_false"],
        )
        for row in rows
    ]


def insert_results(calculated_rows: list[tuple[int, int, str, float]]) -> None:
    with get_connection() as connection:
        max_result_id_row = connection.execute("SELECT COALESCE(MAX(result_id), 0) AS max_id FROM t_results").fetchone()
        next_result_id = max_result_id_row["max_id"] + 1

        payload = []
        for data_id, targil_id, method, result in calculated_rows:
            payload.append((next_result_id, data_id, targil_id, method, result))
            next_result_id += 1

        connection.executemany(
            """
            INSERT INTO t_results (result_id, data_id, targil_id, method, result)
            VALUES (?, ?, ?, ?, ?)
            """,
            payload,
        )
        connection.commit()


def insert_log(formula_id: int, runtime_seconds: float, records_processed: int) -> None:
    with get_connection() as connection:
        max_log_id_row = connection.execute("SELECT COALESCE(MAX(log_id), 0) AS max_id FROM t_log").fetchone()
        next_log_id = max_log_id_row["max_id"] + 1
        connection.execute(
            """
            INSERT INTO t_log (log_id, targil_id, method, run_time, records_processed)
            VALUES (?, ?, ?, ?, ?)
            """,
            (next_log_id, formula_id, METHOD_PYTHON_EVAL, runtime_seconds, records_processed),
        )
        connection.commit()


def run() -> None:
    initialize_database()

    if not table_has_rows("t_data"):
        raise RuntimeError("t_data is empty. Run python-solution/scripts/seed_data.py first.")

    reset_method_results(METHOD_PYTHON_EVAL)

    formulas = load_formulas()

    print(f"Loaded {len(formulas)} formulas")
    print(f"Running with batch size {DEFAULT_BATCH_SIZE:,}")

    for formula in formulas:
        print(f"Running formula {formula.targil_id}: {formula.targil}")
        started_at = time.perf_counter()
        prepared_formula = prepare_formula(formula)
        total_processed = 0

        for batch in iter_data_rows(DEFAULT_BATCH_SIZE):
            calculated_rows = []
            for row in batch:
                result = evaluate_formula(prepared_formula, row)
                calculated_rows.append((row["data_id"], formula.targil_id, METHOD_PYTHON_EVAL, result))
            insert_results(calculated_rows)
            total_processed += len(batch)

        runtime_seconds = time.perf_counter() - started_at
        insert_log(formula.targil_id, runtime_seconds, total_processed)
        print(f"Finished formula {formula.targil_id} in {runtime_seconds:.4f} seconds for {total_processed:,} rows")


if __name__ == "__main__":
    run()
