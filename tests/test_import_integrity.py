"""Regression tests for import integrity across app.py, pages, core, and modules.
Ensures no missing symbols or broken imports exist anywhere in the application.
"""
import ast
import importlib
import pathlib
import pytest


def test_app_and_pages_import_symbols_exist():
    """Verify that every imported symbol in app.py and all pages actually exists in its source module."""
    root_dir = pathlib.Path(__file__).parent.parent
    files_to_check = [root_dir / "app.py"] + list((root_dir / "pages").glob("*.py"))
    
    missing_symbols = []
    
    for file_path in files_to_check:
        with open(file_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module_name = node.module
                if not module_name:
                    continue
                # Only check internal modules (core, modules, src)
                if module_name.startswith(("core", "modules", "src")):
                    try:
                        mod = importlib.import_module(module_name)
                    except Exception as exc:
                        missing_symbols.append(f"{file_path.name}: Failed to import module '{module_name}': {exc}")
                        continue
                    
                    for alias in node.names:
                        symbol_name = alias.name
                        if symbol_name == "*":
                            continue
                        if not hasattr(mod, symbol_name):
                            missing_symbols.append(
                                f"{file_path.name}: Symbol '{symbol_name}' not found in module '{module_name}'"
                            )
                            
    assert not missing_symbols, "Found missing import symbols:\n" + "\n".join(missing_symbols)


def test_all_enterprise_packages_have_init():
    """Verify that core and all modules have explicit __init__.py files."""
    root_dir = pathlib.Path(__file__).parent.parent
    assert (root_dir / "core" / "__init__.py").exists(), "core/__init__.py is missing"
    assert (root_dir / "modules" / "__init__.py").exists(), "modules/__init__.py is missing"
    
    for module_dir in (root_dir / "modules").iterdir():
        if module_dir.is_dir() and not module_dir.name.startswith((".", "__")):
            init_file = module_dir / "__init__.py"
            assert init_file.exists(), f"{module_dir.name}/__init__.py is missing"


def test_clean_import_all_modules():
    """Verify that all core and module subpackages can be imported cleanly without error."""
    modules_to_test = [
        "core.constants",
        "core.models",
        "core.security",
        "core.state",
        "modules.actions.tracker",
        "modules.analysis.stats_engine",
        "modules.analysis.method_recommender",
        "modules.diagnostics.root_cause_engine",
        "modules.forecasting.simulator",
        "modules.ingestion.parser",
        "modules.insights.engine",
        "modules.kpi_engine.engine",
        "modules.mapping.mapper",
        "modules.profiling.profiler",
        "modules.quality.engine",
        "modules.recommendations.engine",
        "modules.reporting.export_builder",
    ]
    for mod in modules_to_test:
        imported = importlib.import_module(mod)
        assert imported is not None
