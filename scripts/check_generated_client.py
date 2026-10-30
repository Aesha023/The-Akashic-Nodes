"""Verify generated TypeScript client is not stale against FastAPI OpenAPI schema."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from scripts.export_openapi import export_openapi


def main() -> None:
    openapi_file = repo_root / "frontend" / "src" / "api" / "openapi.json"
    generated_ts = repo_root / "frontend" / "src" / "api" / "generated.ts"

    # 1. Export schema
    export_openapi(openapi_file)

    # 2. Check git diff on generated files
    cmd = ["git", "diff", "--exit-code", str(openapi_file), str(generated_ts)]
    res = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True)
    if res.returncode != 0:
        print("ERROR: Generated TypeScript API client is STALE! Run 'npm run codegen' or 'python scripts/export_openapi.py && npx openapi-typescript frontend/src/api/openapi.json -o frontend/src/api/generated.ts'.")
        print(res.stdout)
        print(res.stderr)
        sys.exit(1)
    print("SUCCESS: Generated TypeScript API client is up to date with FastAPI schema.")


if __name__ == "__main__":
    main()
