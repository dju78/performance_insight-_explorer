import os
import sys
import ast
import py_compile
import importlib
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SRC_MODULES = [
    "src.audit",
    "src.comparisons",
    "src.export",
    "src.ingestion",
    "src.insights",
    "src.mapping",
    "src.metrics",
    "src.powerpoint",
    "src.profiling",
    "src.quality",
    "src.recommendations",
    "src.reporting",
    "src.root_cause",
    "src.state",
    "src.trends",
    "src.visualisations"
]

@pytest.mark.parametrize("mod_name", SRC_MODULES)
def test_import_src_modules(mod_name):
    """Smoke test: verify every backend src module can be imported without error."""
    mod = importlib.import_module(mod_name)
    assert mod is not None


def test_syntax_and_import_resolution_app():
    """Verify app.py syntax compiles cleanly and all internal imports exist."""
    app_path = os.path.join(ROOT, "app.py")
    py_compile.compile(app_path, doraise=True)
    
    with open(app_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=app_path)
        
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("src."):
                mod = importlib.import_module(node.module)
                for alias in node.names:
                    assert hasattr(mod, alias.name), f"app.py cannot import '{alias.name}' from '{node.module}'"


def test_syntax_and_import_resolution_pages():
    """Verify every page in pages/ compiles cleanly and all internal imports exist."""
    pages_dir = os.path.join(ROOT, "pages")
    page_files = [f for f in os.listdir(pages_dir) if f.endswith(".py")]
    assert len(page_files) >= 12, "Expected at least 12 page modules"
    
    for page in page_files:
        page_path = os.path.join(pages_dir, page)
        py_compile.compile(page_path, doraise=True)
        
        with open(page_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=page_path)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("src."):
                    mod = importlib.import_module(node.module)
                    for alias in node.names:
                        assert hasattr(mod, alias.name), f"{page} cannot import '{alias.name}' from '{node.module}'"
