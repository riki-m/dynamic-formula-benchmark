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
from src.formula_runtime import FormulaDefinition, evaluate_formula, prepare_formula
from src import sqlserver_db


def run() -> None:
    if not sqlserver_db.table_has_rows("t_data"):
        raise RuntimeError("t_data is empty in SQL Server. Run the SQL seed scripts first.")

    sqlserver_db.reset_method_results(METHOD_PYTHON_EVAL)
    formulas = [
        FormulaDefinition(
            targil_id=row["targil_id"],
            targil=row["targil"],
            tnai=row["tnai"],
            targil_false=row["targil_false"],
        )
        for row in sqlserver_db.load_formulas()
    ]

    print(f"Loaded {len(formulas)} formulas from SQL Server")
    print(f"Running with batch size {DEFAULT_BATCH_SIZE:,}")

    for formula in formulas:
        print(f"Running formula {formula.targil_id}: {formula.targil}")
        started_at = time.perf_counter()
        prepared_formula = prepare_formula(formula)
        total_processed = 0

        for batch in sqlserver_db.iter_data_rows(DEFAULT_BATCH_SIZE):
            calculated_rows = []
            for row in batch:
                result = evaluate_formula(prepared_formula, row)
                calculated_rows.append((row["data_id"], formula.targil_id, METHOD_PYTHON_EVAL, result))
            sqlserver_db.insert_results(calculated_rows)
            total_processed += len(batch)

        runtime_seconds = time.perf_counter() - started_at
        sqlserver_db.insert_log(formula.targil_id, METHOD_PYTHON_EVAL, runtime_seconds, total_processed)
        print(f"Finished formula {formula.targil_id} in {runtime_seconds:.4f} seconds for {total_processed:,} rows")


if __name__ == "__main__":
    run()
