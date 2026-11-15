"""Phase 2 Research: Empirical Comparison of Candidate Pressure Methodologies."""

from __future__ import annotations

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.v4_2.pressure_revalidation import build_v42_delivery_dataset
from src.v4_2.fwl_estimator import fit_v42_option_a_fwl
from src.v4_1.eligibility_and_validation import V41_OPERATIONAL_PRECISION_GATE

ROOT = Path(__file__).resolve().parents[1]


def _eligible_mask(df: pd.DataFrame) -> pd.Series:
    g = V41_OPERATIONAL_PRECISION_GATE
    return (
        (df["n_hi"] >= g["min_hi_balls"])
        & (df["n_lo"] >= g["min_lo_balls"])
        & (df["cs_matches"] >= g["min_cs_matches"])
        & (df["se_delta"] <= g["max_se_delta"])
        & df["eb_delta"].notna()
    )


def _oot_claim_c(df_sub: pd.DataFrame, player_col: str, opp_col: str, p_col: str, y_col: str) -> tuple[float, float, int]:
    years = pd.to_datetime(df_sub["match_date"], errors="coerce").dt.year
    tr = df_sub[years < 2023].copy()
    te = df_sub[years >= 2023].copy()
    tr_est, _ = fit_v42_option_a_fwl(tr, player_col, opp_col, p_col, y_col, span=0.75)
    te_est, _ = fit_v42_option_a_fwl(te, player_col, opp_col, p_col, y_col, span=0.75)
    tr_el = tr_est[_eligible_mask(tr_est)][["player_id", "eb_delta"]].rename(columns={"eb_delta": "tr_eb"})
    te_el = te_est[_eligible_mask(te_est)][["player_id", "eb_delta"]].rename(columns={"eb_delta": "te_eb"})
    m = tr_el.merge(te_el, on="player_id", how="inner")
    if len(m) < 3:
        return np.nan, np.nan, int(len(m))
    rho, pval = spearmanr(m["tr_eb"], m["te_eb"])
    return float(rho), float(pval), int(len(m))


def main() -> None:
    df, _, _ = build_v42_delivery_dataset(ROOT / "data")
    df_bat = df[df["is_ball_faced"] == 1].copy()
    df_bat["y_bat"] = df_bat["batter_runs"].astype(float) * 100.0
    df_bat["weight"] = 1.0
    df_bat["bat_pressure_phase_strat"] = df_bat.groupby(["innings", "phase"])["bat_pressure"].rank(pct=True, method="average")

    df_bowl = df[df["is_legal_ball"] == 1].copy()
    df_bowl["y_bowl"] = -df_bowl["batter_runs"].astype(float) * 100.0
    df_bowl["weight"] = 1.0
    df_bowl["bowl_pressure_phase_strat"] = df_bowl.groupby(["innings", "phase"])["bowl_pressure"].rank(pct=True, method="average")

    # Baseline Top 10 sets
    base_bat, _ = fit_v42_option_a_fwl(df_bat, "striker_id", "bowler_id", "bat_pressure", "y_bat", span=0.75)
    base_bat_el = base_bat[_eligible_mask(base_bat)].sort_values("eb_delta", ascending=False)
    base_bat_top10 = set(base_bat_el.head(10)["player_id"].tolist())

    base_bowl, _ = fit_v42_option_a_fwl(df_bowl, "bowler_id", "striker_id", "bowl_pressure", "y_bowl", span=0.75)
    base_bowl_el = base_bowl[_eligible_mask(base_bowl)].sort_values("eb_delta", ascending=False)
    base_bowl_top10 = set(base_bowl_el.head(10)["player_id"].tolist())

    rows = []
    specs = [
        ("V4_2_Current_Wicket_Depletion_Anomaly", "batter", df_bat, "striker_id", "bowler_id", "y_bat", "bat_pressure",
         "Percentile of innings-stage wicket-depletion anomaly (1 - ((10-w)/10)^gamma - E[.|inn,over])",
         "100% balls faced (837 matches)"),
        ("Full_RUW_Resource_Depletion", "batter", df_bat, "striker_id", "bowler_id", "y_bat", "BAT_DEPLETION_FULL_RUW",
         "Percentile of full R(u,w) remaining-resource depletion combining balls-decay b and wicket-elasticity gamma",
         "100% balls faced (837 matches)"),
        ("Phase_Stratified_Wicket_Depletion", "batter", df_bat, "striker_id", "bowler_id", "y_bat", "bat_pressure_phase_strat",
         "Percentile of wicket-depletion anomaly ranked within (innings, phase) so openers and finishers face balanced high/low tiers",
         "100% balls faced (837 matches)"),
        ("V4_2_Current_Expected_Scoring_Threat", "bowler", df_bowl, "bowler_id", "striker_id", "y_bowl", "bowl_pressure",
         "Percentile of pre-delivery Ridge(alpha=10) expected batter runs/100b across innings, phase, format, wkts, balls",
         "100% legal deliveries (185,951 balls / 837 matches)"),
        ("Phase_Stratified_Scoring_Threat", "bowler", df_bowl, "bowler_id", "striker_id", "y_bowl", "bowl_pressure_phase_strat",
         "Percentile of expected scoring threat ranked within (innings, phase) isolating within-phase threat spikes",
         "100% legal deliveries (185,951 balls / 837 matches)"),
    ]

    for name, role, df_sub, p_col_id, opp_col_id, y_col, pr_col, defn, avail in specs:
        est, meta = fit_v42_option_a_fwl(df_sub, p_col_id, opp_col_id, pr_col, y_col, span=0.75)
        el = est[_eligible_mask(est)].sort_values("eb_delta", ascending=False)
        top10 = set(el.head(10)["player_id"].tolist())
        base_top10 = base_bat_top10 if role == "batter" else base_bowl_top10
        base_el = base_bat_el if role == "batter" else base_bowl_el
        merged = base_el[["player_id", "eb_delta"]].rename(columns={"eb_delta": "eb_b"}).merge(
            el[["player_id", "eb_delta"]].rename(columns={"eb_delta": "eb_c"}),
            on="player_id",
        )
        spear = float(spearmanr(merged["eb_b"], merged["eb_c"])[0]) if len(merged) >= 3 else np.nan
        oot_rho, oot_p, oot_n = _oot_claim_c(df_sub, p_col_id, opp_col_id, pr_col, y_col)
        hi_deliv = int((df_sub[pr_col] >= 0.875).sum())

        rows.append({
            "methodology_id": name,
            "discipline": role,
            "pressure_definition": defn,
            "data_availability": avail,
            "eligible_players": int(len(el)),
            "high_pressure_deliveries": hi_deliv,
            "model_equation": "Complete Penalized FWL (y and W residualized on Z) + REML EB (span=0.75)",
            "reml_mu0": round(float(meta["het"]["mu0"]), 3),
            "reml_tau": round(float(meta["het"]["tau"]), 3),
            "reml_i2_pct": round(100.0 * float(meta["het"]["I2"]), 1),
            "median_se_delta": round(float(el["se_delta"].median()), 2),
            "oot_claim_c_rho": round(oot_rho, 3) if pd.notna(oot_rho) else np.nan,
            "oot_claim_c_p": round(oot_p, 4) if pd.notna(oot_p) else np.nan,
            "oot_n_overlap": oot_n,
            "spearman_vs_v42_baseline": round(spear, 4),
            "top10_overlap_vs_v42": int(len(top10 & base_top10)),
            "limitations": "No chase runs required / RRR / target leverage (0/837 zero-extras matches)",
            "selection_status": "SELECTED_PRIMARY_BASELINE" if "V4_2_Current" in name else "EVALUATED_ALTERNATIVE",
        })

    rows.append({
        "methodology_id": "Calibrated_Chase_Leverage_WPA_Blocked",
        "discipline": "both",
        "pressure_definition": "True pre-delivery win-probability leverage / required-run-rate deficit using exact score & target",
        "data_availability": "BLOCKED (0/837 zero-extras matches; 342/390 non-DLS run-margin reconciliations fail; 0 external scorecards)",
        "eligible_players": 0,
        "high_pressure_deliveries": 0,
        "model_equation": "N/A — blocked by categorical extras1_runs codebook and missing multi-run extras",
        "reml_mu0": np.nan,
        "reml_tau": np.nan,
        "reml_i2_pct": np.nan,
        "median_se_delta": np.nan,
        "oot_claim_c_rho": np.nan,
        "oot_claim_c_p": np.nan,
        "oot_n_overlap": 0,
        "spearman_vs_v42_baseline": np.nan,
        "top10_overlap_vs_v42": 0,
        "limitations": "Cannot be estimated without fabricating missing team totals and targets",
        "selection_status": "BLOCKED_BY_SOURCE_DATA",
    })

    out = pd.DataFrame(rows)
    out.to_csv(ROOT / "PRESSURE_METHODOLOGY_COMPARISON.csv", index=False)
    print(out[["methodology_id", "discipline", "eligible_players", "reml_mu0", "reml_tau", "reml_i2_pct", "oot_claim_c_rho", "spearman_vs_v42_baseline", "top10_overlap_vs_v42", "selection_status"]].to_string(index=False))


if __name__ == "__main__":
    main()
