"""Operational Scenario Simulator and Forecasting Engine for Performance Insight Explorer.
Enables what-if modeling across demand volume, staffing/FTE capacity, productivity changes, and SLA targets.
Computes Baseline, Optimistic, and Conservative forecast trajectories with estimation disclosures.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd


def run_scenario_simulation(
    baseline_volume: float,
    baseline_fte: float,
    baseline_productivity: float,
    demand_multiplier: float = 1.0,
    fte_multiplier: float = 1.0,
    productivity_gain_pct: float = 0.0,
    target_sla_days: float = 10.0
) -> Dict[str, Any]:
    """Simulate operational throughput, backlog pressure, and required staffing under multiple scenarios.
    All outputs are explicitly flagged as estimates.
    """
    sim_volume = baseline_volume * demand_multiplier
    sim_fte = baseline_fte * fte_multiplier
    sim_prod = baseline_productivity * (1.0 + (productivity_gain_pct / 100.0))

    # Output capacity
    sim_capacity_output = sim_fte * sim_prod
    net_flow_gap = sim_volume - sim_capacity_output
    capacity_utilization_pct = (sim_volume / sim_capacity_output * 100.0) if sim_capacity_output > 0 else 0.0

    # Staffing requirement to balance demand
    required_fte_for_balance = (sim_volume / sim_prod) if sim_prod > 0 else 0.0
    fte_gap = required_fte_for_balance - sim_fte

    # 3 Scenario Projections (Baseline, Optimistic, Conservative)
    scenarios = {
        "Baseline Projection": {
            "demand": round(sim_volume, 1),
            "fte_capacity": round(sim_fte, 1),
            "effective_productivity": round(sim_prod, 2),
            "projected_throughput": round(min(sim_volume, sim_capacity_output), 1),
            "net_monthly_backlog_growth": round(max(0.0, net_flow_gap), 1),
            "capacity_utilization_pct": round(capacity_utilization_pct, 1),
            "required_fte_balance": round(required_fte_for_balance, 1),
            "fte_surplus_deficit": round(-fte_gap, 1)
        },
        "Optimistic Scenario (+10% Productivity, -5% Inflow)": {
            "demand": round(sim_volume * 0.95, 1),
            "fte_capacity": round(sim_fte, 1),
            "effective_productivity": round(sim_prod * 1.10, 2),
            "projected_throughput": round(min(sim_volume * 0.95, sim_fte * sim_prod * 1.10), 1),
            "net_monthly_backlog_growth": round(max(0.0, (sim_volume * 0.95) - (sim_fte * sim_prod * 1.10)), 1),
            "capacity_utilization_pct": round(((sim_volume * 0.95) / (sim_fte * sim_prod * 1.10) * 100.0) if (sim_fte * sim_prod * 1.10) > 0 else 0.0, 1),
            "required_fte_balance": round((sim_volume * 0.95) / (sim_prod * 1.10), 1),
            "fte_surplus_deficit": round(sim_fte - ((sim_volume * 0.95) / (sim_prod * 1.10)), 1)
        },
        "Conservative Scenario (-10% Productivity, +15% Inflow)": {
            "demand": round(sim_volume * 1.15, 1),
            "fte_capacity": round(sim_fte, 1),
            "effective_productivity": round(sim_prod * 0.90, 2),
            "projected_throughput": round(min(sim_volume * 1.15, sim_fte * sim_prod * 0.90), 1),
            "net_monthly_backlog_growth": round(max(0.0, (sim_volume * 1.15) - (sim_fte * sim_prod * 0.90)), 1),
            "capacity_utilization_pct": round(((sim_volume * 1.15) / (sim_fte * sim_prod * 0.90) * 100.0) if (sim_fte * sim_prod * 0.90) > 0 else 0.0, 1),
            "required_fte_balance": round((sim_volume * 1.15) / (sim_prod * 0.90), 1),
            "fte_surplus_deficit": round(sim_fte - ((sim_volume * 1.15) / (sim_prod * 0.90)), 1)
        }
    }

    return {
        "is_estimate": True,
        "disclaimer": "SCENARIO ESTIMATION: All simulation figures are modeled estimates based on parametric assumptions, not guaranteed outcomes.",
        "assumptions": {
            "demand_multiplier": demand_multiplier,
            "fte_multiplier": fte_multiplier,
            "productivity_gain_pct": productivity_gain_pct,
            "target_sla_days": target_sla_days
        },
        "scenarios": scenarios
    }


def simulate_what_if_scenario(
    baseline_metric: float,
    pct_change: float,
    metric_name: str = "Metric"
) -> Dict[str, Any]:
    """Simulate single-parameter what-if change on a primary performance metric."""
    delta = baseline_metric * (pct_change / 100.0)
    simulated = baseline_metric + delta
    return {
        "metric_name": metric_name,
        "baseline_metric": round(baseline_metric, 2),
        "delta_percentage": round(pct_change, 1),
        "delta_absolute": round(delta, 2),
        "simulated_metric": round(simulated, 2)
    }

