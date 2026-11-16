"""Consistent Plotly chart builders for SupeRR Intelligence V4.2."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from dashboard.data_loader import NAVY, NAVY_MID, RR_PINK, TEAL_POS


def _apply_base_layout(fig: go.Figure, title: str, height: int = 380) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        autosize=True,
        title=dict(text=title, font=dict(color=NAVY, size=13), x=0.01, xanchor="left"),
        height=height,
        margin=dict(l=12, r=20, t=52, b=16),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font=dict(color=NAVY, size=12),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0.0,
            font=dict(color=NAVY, size=11),
        ),
    )
    fig.update_xaxes(automargin=True)
    fig.update_yaxes(automargin=True)
    return fig


def dataset_coverage_chart() -> go.Figure:
    """Visualize delivery reconciliation from raw rows to validated legal balls."""
    labels = [
        "Super Over Isolated",
        "Non-Legal / Extras",
        "Validated Legal Balls",
        "Regular Deliveries (Inn 1-2)",
    ]
    values = [26, 8037, 185951, 193988]
    colors = [RR_PINK, "#94A3B8", TEAL_POS, NAVY]
    fig = go.Figure(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            marker_color=colors,
            text=[f"{v:,}" for v in values],
            textposition="auto",
            hovertemplate="%{y}: %{x:,} deliveries<extra></extra>",
        )
    )
    _apply_base_layout(fig, "Delivery Audit & Coverage (837 Matches)", height=270)
    fig.update_layout(showlegend=False, margin=dict(l=10, r=24, t=44, b=10))
    fig.update_xaxes(title="Deliveries", tickfont=dict(color=NAVY), gridcolor="#E2E8F0", range=[0, 215000])
    fig.update_yaxes(tickfont=dict(color=NAVY))
    return fig


def dumbbell_shift_chart(df: pd.DataFrame, is_bowler: bool, title: str) -> go.Figure:
    """Normal -> High-Stress Dumbbell Shift in natural positive cricket units."""
    plot_df = df.sort_values("shortlist_rank_display", ascending=False).copy()
    if is_bowler:
        lo_vals = -plot_df["raw_lo_perf"]
        hi_vals = -plot_df["raw_hi_perf"]
        lo_lbl = "Normal Baseline (Runs Conceded/100b)"
        hi_lbl = "High Scoring Threat (Runs Conceded/100b)"
        x_title = "Batter Runs Conceded per 100 Legal Balls (lower = tighter)"
    else:
        lo_vals = plot_df["raw_lo_perf"]
        hi_vals = plot_df["raw_hi_perf"]
        lo_lbl = "Normal Baseline (Strike Rate)"
        hi_lbl = "High Resource Stress (Strike Rate)"
        x_title = "Batting Strike Rate (Runs per 100 Balls Faced; higher = faster)"

    fig = go.Figure()
    for name, x0, x1 in zip(plot_df["player_name"], lo_vals, hi_vals):
        if pd.notna(x0) and pd.notna(x1):
            fig.add_trace(
                go.Scatter(
                    x=[x0, x1],
                    y=[name, name],
                    mode="lines",
                    line=dict(color="#CBD5E1", width=3),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    fig.add_trace(
        go.Scatter(
            x=lo_vals,
            y=plot_df["player_name"],
            mode="markers",
            name=lo_lbl,
            marker=dict(color="#64748B", size=10),
            hovertemplate="%{y}<br>Normal: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=hi_vals,
            y=plot_df["player_name"],
            mode="markers",
            name=hi_lbl,
            marker=dict(color=RR_PINK, size=11, symbol="diamond"),
            hovertemplate="%{y}<br>High Stress: %{x:.2f}<extra></extra>",
        )
    )
    _apply_base_layout(fig, title, height=390)
    fig.update_xaxes(title=x_title, title_font=dict(color=NAVY), tickfont=dict(color=NAVY), gridcolor="#E2E8F0")
    fig.update_yaxes(tickfont=dict(color=NAVY), gridcolor="#F1F5F9")
    return fig


def eb_forest_chart(df: pd.DataFrame, mu0: float, title: str) -> go.Figure:
    """EB Delta Forest Plot with 95% Bootstrap CI and Cohort Mean mu0 reference line."""
    plot_df = df.sort_values("shortlist_rank_display", ascending=False).copy()
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=plot_df["eb_delta"],
            y=plot_df["player_name"],
            mode="markers",
            name="EB Δ (FWL + REML)",
            marker=dict(color=NAVY, size=10),
            error_x=dict(
                type="data",
                symmetric=False,
                array=(plot_df["eb_boot_ci_high"] - plot_df["eb_delta"]).fillna(0).clip(lower=0),
                arrayminus=(plot_df["eb_delta"] - plot_df["eb_boot_ci_low"]).fillna(0).clip(lower=0),
                color="#94A3B8",
                thickness=1.8,
            ),
            hovertemplate="%{y}<br>EB Δ: %{x:.2f}<extra></extra>",
        )
    )
    fig.add_vline(
        x=mu0,
        line_width=2,
        line_dash="dash",
        line_color=RR_PINK,
        annotation_text=f"Cohort Mean μ₀ = {mu0:.2f}",
        annotation_position="top left",
        annotation_font=dict(color=RR_PINK, size=11),
    )
    _apply_base_layout(fig, title, height=390)
    fig.update_layout(showlegend=False)
    fig.update_xaxes(
        title="EB Δ (95% Boot CI; right of μ₀ = above cohort)",
        title_font=dict(color=NAVY),
        tickfont=dict(color=NAVY),
        gridcolor="#E2E8F0",
    )
    fig.update_yaxes(tickfont=dict(color=NAVY), gridcolor="#F1F5F9")
    return fig


def comparison_sample_chart(df: pd.DataFrame) -> go.Figure:
    """Compare high-stress vs normal-stress ball exposure across compared players."""
    fig = go.Figure()
    fig.add_trace(go.Bar(name="High-Stress Balls", x=df["player_name"], y=df["n_hi"], marker_color=RR_PINK))
    fig.add_trace(go.Bar(name="Normal-Stress Balls", x=df["player_name"], y=df["n_lo"], marker_color=NAVY))
    _apply_base_layout(fig, "Sample Exposure Comparison (High-Stress vs Normal Balls)", height=320)
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickfont=dict(color=NAVY))
    fig.update_yaxes(title="Deliveries", tickfont=dict(color=NAVY), gridcolor="#E2E8F0")
    return fig


def rr_2026_contrib_chart(df: pd.DataFrame) -> go.Figure:
    """Visualize RR 2026 player runs and wickets share."""
    top_r = df.sort_values("runs_share_pct", ascending=False).head(8).iloc[::-1]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Runs Share (%)", y=top_r["player_name"], x=top_r["runs_share_pct"], orientation="h", marker_color=NAVY))
    fig.add_trace(go.Bar(name="Wickets Share (%)", y=top_r["player_name"], x=top_r["wickets_share_pct"], orientation="h", marker_color=RR_PINK))
    _apply_base_layout(fig, "RR 2026 Squad Contribution Share (Runs % vs Wickets %)", height=330)
    fig.update_layout(barmode="group")
    fig.update_xaxes(title="Team Share (%)", tickfont=dict(color=NAVY), gridcolor="#E2E8F0")
    fig.update_yaxes(tickfont=dict(color=NAVY))
    return fig


def rr_component_chart(df: pd.DataFrame, score_col: str) -> go.Figure:
    """Diagnostic breakdown of unweighted RR scouting sub-scores alongside final weighted fit."""
    top_pool = df.sort_values(score_col, ascending=False).head(10).iloc[::-1]
    fig = go.Figure()
    for col_name, lbl, clr in [
        ("phase_exec_score", "Phase Execution", NAVY),
        ("role_need_score", "Tactical Role Need", NAVY_MID),
        ("pressure_v42_score", "V4.2 Pressure", RR_PINK),
        ("sample_conf_score", "Sample Confidence", "#64748B"),
        ("balance_ipl_score", "T20 Exposure", "#94A3B8"),
    ]:
        fig.add_trace(go.Bar(name=lbl, y=top_pool["player_name"], x=top_pool[col_name], orientation="h", marker_color=clr))
    _apply_base_layout(fig, "Top 10 Non-RR Candidates — Unweighted Component Diagnostics (0–100 each)", height=370)
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="Sum of Unweighted Component Sub-Scores (see tables for weighted RR Fit Score)", tickfont=dict(color=NAVY), gridcolor="#E2E8F0")
    fig.update_yaxes(tickfont=dict(color=NAVY))
    return fig
