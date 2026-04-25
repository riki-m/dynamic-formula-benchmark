from __future__ import annotations

import json
from pathlib import Path
from urllib.request import urlopen

from app.main import build_dashboard_payload
from app.analysis_engine import generate_analysis_pdf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DATA_DIR = PROJECT_ROOT / "report-ui" / "data"
PUBLIC_ASSETS_DIR = PROJECT_ROOT / "report-ui" / "assets"
LOCAL_API_BASE = "http://127.0.0.1:8000"


def main() -> None:
    PUBLIC_DATA_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    dashboard_path = PUBLIC_DATA_DIR / "dashboard.json"
    pdf_path = PUBLIC_ASSETS_DIR / "benchmark-ai-analysis.pdf"
    try:
        with urlopen(f"{LOCAL_API_BASE}/api/dashboard") as response:
            dashboard = json.loads(response.read().decode("utf-8"))
        with urlopen(f"{LOCAL_API_BASE}/api/analysis/download.pdf") as response:
            pdf_bytes = response.read()
    except Exception:
        dashboard = build_dashboard_payload()
        pdf_bytes = generate_analysis_pdf(dashboard["overview"], dashboard["ai_analysis"])

    dashboard_path.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2), encoding="utf-8")
    pdf_path.write_bytes(pdf_bytes)

    print(f"Wrote dashboard snapshot to {dashboard_path}")
    print(f"Wrote public PDF report to {pdf_path}")


if __name__ == "__main__":
    main()
