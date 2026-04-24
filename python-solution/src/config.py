from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "benchmark.db"
DATABASE_PATH = Path(os.getenv("DATABASE_PATH", DEFAULT_DATABASE_PATH))
DEFAULT_BATCH_SIZE = int(os.getenv("FORMULA_BATCH_SIZE", "5000"))
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").lower()
SQLSERVER_CONNECTION_STRING = os.getenv(
    "SQLSERVER_CONNECTION_STRING",
    "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=DynamicFormulaBenchmark;Trusted_Connection=yes;",
)

METHOD_PYTHON_EVAL = "python_eval"
