"""Phase 5: Four Pressure Archetypes Classification & Quadrant Plots for V5.0."""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.v5_0.config import DEFAULT_V50_CONFIG, V50Config

ARCHETYPE_COLORS = {
    "ELITE CLUTCH PERFORMER": "#0F766E",
    "CRISIS / RESCUE SPECIALIST": "#2563EB",
    "PRESSURE-SENSITIVE GENERAL PERFORMER": "#D97706",
    "BELOW-AVERAGE UNDER PRESSURE": "#DC2626",
    "UNCLASSIFIED / INSUFFICIENT EVIDENCE": "#64748B",
}


def classify_player_archetypes(
    df: pd.DataFrame,
    tol: float = DEFAULT_V50_CONFIG.clutch_non_inferiority_tol,
) -> pd.DataFrame:
    """
    Mutually exclusive archetype classification using paired bootstrap 95% intervals
    and post-fit exposure eligibility. Never forces uncertain players into a category.
    """
    out = df.copy()
    archetypes = []
    subtypes = []

    for _, r in out.iterrows():
        if not bool(r["eligible"]):
            archetypes.append("UNCLASSIFIED / INSUFFICIENT EVIDENCE")
            subtypes.append("INELIGIBLE_LOW_EXPOSURE")
            continue

        c_lo_m, c_hi_m = float(r["ci_low_main"]), float(r["ci_high_main"])
        c_lo_p, c_hi_p = float(r["ci_low_pres"]), float(r["ci_high_pres"])
        c_lo_hp, c_hi_hp = float(r["ci_low_hp"]), float(r["ci_high_hp"])
        pres = float(r["pressure_interaction_per100"])
        hp = float(r["combined_hp_per100"])

        # Priority 1: ELITE CLUTCH PERFORMER
        if (c_lo_m > 0.0) and (c_lo_hp > 0.0) and ((c_lo_p > -tol) or (pres >= 0.0)):
            archetypes.append("ELITE CLUTCH PERFORMER")
            subtypes.append("PRESSURE_IMPROVER" if pres > 0.0 else "PRESSURE_RESILIENT_ELITE")
        # Priority 2: BELOW-AVERAGE UNDER PRESSURE (not "below replacement")
        elif c_hi_hp < 0.0:
            archetypes.append("BELOW-AVERAGE UNDER PRESSURE")
            subtypes.append("SIGNIFICANTLY_BELOW_ROLE_AVERAGE_HP")
        # Priority 3: PRESSURE-SENSITIVE GENERAL PERFORMER
        elif (c_lo_m > 0.0) and (c_hi_p < 0.0):
            archetypes.append("PRESSURE-SENSITIVE GENERAL PERFORMER")
            subtypes.append("GENERAL_ELITE_WITH_HP_DROP")
        # Priority 4: CRISIS / RESCUE SPECIALIST
        elif (c_lo_p > 0.0) and (hp > 0.0):
            archetypes.append("CRISIS / RESCUE SPECIALIST")
            subtypes.append("SIGNIFICANT_PRESSURE_UPLIFT")
        else:
            archetypes.append("UNCLASSIFIED / INSUFFICIENT EVIDENCE")
            subtypes.append("INTERVALS_SPAN_ZERO")

    out["archetype"] = archetypes
    out["archetype_subtype"] = subtypes
    return out


def save_archetype_quadrant_plot(
    df: pd.DataFrame,
    role: str,
    out_path: str,
) -> None:
    """Generate quadrant scatter plot (X=Main contribution, Y=Pressure uplift) with 95% CIs."""
    el = df[df["eligible"]].copy()
    fig = go.Figure()

    for arch, grp in el.groupby("archetype"):
        fig.add_trace(
            go.Scatter(
                x=grp["main_effect_per100"],
                y=grp["pressure_interaction_per100"],
                mode="markers",
                name=arch,
                marker=dict(
                    size=np.clip(np.sqrt(grp["n_hp_global"]) * 0.9, 6, 18),
                    color=ARCHETYPE_COLORS.get(arch, "#64748B"),
                    opacity=0.85,
                    line=dict(width=1, color="#FFFFFF"),
                ),
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=(grp["ci_high_main"] - grp["main_effect_per100"]).values,
                    arrayminus=(grp["main_effect_per100"] - grp["ci_low_main"]).values,
                    thickness=0.8,
                    width=0,
                    color="rgba(100,116,139,0.35)",
                ),
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=(grp["ci_high_pres"] - grp["pressure_interaction_per100"]).values,
                    arrayminus=(grp["pressure_interaction_per100"] - grp["ci_low_pres"]).values,
                    thickness=0.8,
                    width=0,
                    color="rgba(100,116,139,0.35)",
                ),
                text=grp["player_name"] + "<br>HP balls: " + grp["n_hp_global"].astype(str) + "<br>Archetype: " + grp["archetype"],
                hoverinfo="text",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="#94A3B8")
    fig.add_vline(x=0, line_dash="dash", line_color="#94A3B8")
    fig.update_layout(
        title=f"V5.0 {role.title()} Pressure Archetype Quadrant (Eligible Pool: n={len(el)})",
        xaxis_title="Baseline Main Contribution (runs / 100 deliveries)",
        yaxis_title="High-Pressure Uplift (LI_global >= 1.50, runs / 100 deliveries)",
        template="plotly_white",
        width=900,
        height=600,
    )
    fig.write_html(out_path)
