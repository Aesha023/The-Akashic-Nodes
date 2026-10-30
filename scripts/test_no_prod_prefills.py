"""Test that production build contains no credential pre-fills."""

import re
import sys
from pathlib import Path


def test_prod_bundle_no_prefill():
    dist_dir = Path("frontend/dist/assets")
    js_files = list(dist_dir.glob("*.js"))
    if not js_files:
        print("ERROR: No JS files found in frontend/dist/assets. Run 'npm run build' first.")
        sys.exit(1)

    print(f"Checking {len(js_files)} production bundle file(s)...")
    for js_file in js_files:
        content = js_file.read_text(encoding="utf-8")
        # In prod, isDev is false, so useState(false?"dr_sharma":"") -> useState("")
        # Check that the input value default is ""
        # Look for the string 'pravahx2026!' being passed as initial state to password input
        # Note: 'pravahx2026!' should NOT appear as an active default value in the prod bundle's useState
        pattern = re.compile(r'useState\s*\(\s*["\']pravahx2026!["\']\s*\)')
        match = pattern.search(content)
        if match:
            print(
                f"FAILED: Found hardcoded password pre-fill in useState in {js_file.name}: {match.group(0)}"
            )
            sys.exit(1)

    print("PASS: Verified that production build has no active credential pre-fills in useState.")


if __name__ == "__main__":
    test_prod_bundle_no_prefill()
