import os
import re
import pytest

FIXTURE_TERMS = [
    r"North Operations",
    r"West Operations",
    r"East Operations",
    r"South Operations",
    r"Central Operations",
    r"2025-08-01",
    r"2025-09-01",
    r"738",
    r"785",
    r"948",
    r"752",
]

def get_production_py_files():
    prod_files = ["app.py"]
    for folder in ["src", "pages"]:
        if os.path.exists(folder):
            for root, _, files in os.walk(folder):
                for f in files:
                    if f.endswith(".py"):
                        prod_files.append(os.path.join(root, f))
    return prod_files

def test_zero_fixture_leaks_in_production_code():
    violations = []
    prod_files = get_production_py_files()
    
    for fpath in prod_files:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
            for pattern in FIXTURE_TERMS:
                matches = re.findall(pattern, content, flags=re.IGNORECASE)
                if matches:
                    violations.append(f"{fpath}: found '{pattern}' {len(matches)} time(s)")
                    
    assert len(violations) == 0, f"Fixture leak detected in production code:\n" + "\n".join(violations)
