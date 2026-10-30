"""Export FastAPI OpenAPI schema to JSON for TypeScript client generation."""

from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from backend.app.main import create_app


def export_openapi(output_path: Path) -> None:
    app = create_app()
    schema = app.openapi()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"OpenAPI schema exported ({len(schema.get('paths', {}))} paths) to {output_path}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "frontend" / "src" / "api" / "openapi.json"
    export_openapi(out)
