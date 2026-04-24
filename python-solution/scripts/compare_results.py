from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOT = Path(__file__).resolve().parents[1]
for entry in (PROJECT_ROOT, PYTHON_ROOT):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from src.db import get_connection, initialize_database


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare calculation results between two methods")
    parser.add_argument("--base-method", required=True, help="Reference method name")
    parser.add_argument("--compare-method", required=True, help="Method name to compare against the reference")
    parser.add_argument("--tolerance", type=float, default=1e-9, help="Allowed floating point tolerance")
    parser.add_argument("--limit", type=int, default=20, help="Maximum mismatches to print")
    return parser.parse_args()


def count_rows_for_method(method: str) -> int:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total_rows FROM t_results WHERE method = ?",
            (method,),
        ).fetchone()
    return int(row["total_rows"])


def compare_methods(base_method: str, compare_method: str, tolerance: float, limit: int) -> None:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                base.data_id,
                base.targil_id,
                base.result AS base_result,
                candidate.result AS compare_result
            FROM t_results AS base
            LEFT JOIN t_results AS candidate
                ON candidate.data_id = base.data_id
               AND candidate.targil_id = base.targil_id
               AND candidate.method = ?
            WHERE base.method = ?
            ORDER BY base.targil_id, base.data_id
            """,
            (compare_method, base_method),
        ).fetchall()

    mismatches = []
    missing_rows = 0
    total_mismatch_count = 0

    for row in rows:
        compare_value = row["compare_result"]
        if compare_value is None:
            missing_rows += 1
            total_mismatch_count += 1
            if len(mismatches) < limit:
                mismatches.append(
                    {
                        "data_id": row["data_id"],
                        "targil_id": row["targil_id"],
                        "base_result": row["base_result"],
                        "compare_result": None,
                    }
                )
            continue

        if not math.isclose(row["base_result"], compare_value, rel_tol=tolerance, abs_tol=tolerance):
            total_mismatch_count += 1
            if len(mismatches) < limit:
                mismatches.append(
                    {
                        "data_id": row["data_id"],
                        "targil_id": row["targil_id"],
                        "base_result": row["base_result"],
                        "compare_result": compare_value,
                    }
                )

    base_count = count_rows_for_method(base_method)
    compare_count = count_rows_for_method(compare_method)

    print(f"Base method: {base_method}")
    print(f"Compare method: {compare_method}")
    print(f"Base row count: {base_count:,}")
    print(f"Compare row count: {compare_count:,}")
    print(f"Rows checked: {len(rows):,}")
    print(f"Missing rows in compare method: {missing_rows:,}")
    print(f"Total mismatches found: {total_mismatch_count:,}")

    if mismatches:
        print("\nSample mismatches:")
        for item in mismatches:
            print(
                "data_id={data_id}, targil_id={targil_id}, base_result={base_result}, compare_result={compare_result}".format(
                    **item
                )
            )
    else:
        print("\nAll compared rows matched within tolerance.")


if __name__ == "__main__":
    initialize_database()
    args = parse_args()
    compare_methods(args.base_method, args.compare_method, args.tolerance, args.limit)
