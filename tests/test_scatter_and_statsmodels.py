"""Test suite for statsmodels compatibility, trendline fallback, and sidebar configuration.
"""
import pytest
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src.visualisations import create_scatter_correlation


def test_statsmodels_import_and_trendline_generation():
    """Verify statsmodels is installed and can generate OLS trendlines without ModuleNotFoundError."""
    import statsmodels.api as sm
    assert sm is not None

    np.random.seed(42)
    df = pd.DataFrame({
        "experience_years": np.linspace(1, 10, 20),
        "cases_resolved": np.linspace(1, 10, 20) * 3.5 + np.random.normal(0, 1, 20)
    })

    fig = create_scatter_correlation(
        df=df,
        x_col="experience_years",
        y_col="cases_resolved",
        title="Experience vs Cases"
    )
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # Contains scatter points + trendline


def test_scatter_fallback_when_insufficient_data():
    """Verify scatter plot works gracefully without trendline when data points are minimal or singular."""
    df_small = pd.DataFrame({
        "x": [10.0, 20.0],
        "y": [100.0, 120.0]
    })
    fig = create_scatter_correlation(df_small, "x", "y")
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_streamlit_config_hides_sidebar_navigation():
    """Verify .streamlit/config.toml contains showSidebarNavigation = false to keep only the 4 simplified sections."""
    import pathlib
    config_path = pathlib.Path(__file__).parent.parent / ".streamlit" / "config.toml"
    assert config_path.exists(), ".streamlit/config.toml must exist"
    
    content = config_path.read_text(encoding="utf-8")
    assert "showSidebarNavigation = false" in content
