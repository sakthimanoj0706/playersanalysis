"""Phase C & D — Context-Adjusted Baselines, Common-Support FWL Contrast, EB & Match Bootstrap."""
from __future__ import annotations

from math import sqrt
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
from scipy import optimize, sparse
from scipy.sparse.linalg import lsqr
from scipy.special import ndtr


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Standard normal CDF vectorized cleanly via scipy.special.ndtr."""
    return ndtr(np.asarray(x, dtype=float))


def estimate_heterogeneity(
    delta: np.ndarray,
    se: np.ndarray,
    method: str = "dl",
) -> Dict[str, float]:
    """Estimate random-effects population mean mu0 and between-player variance tau2."""
    valid = np.isfinite(delta) & np.isfinite(se) & (se > 0.0)
    d = delta[valid]
    s = se[valid]
    k = len(d)
    if k < 5:
        return {"mu0": 0.0, "tau2": 0.0, "tau": 0.0, "Q": 0.0, "df": 0, "I2": 0.0, "k_eff": np.inf}

    v = s ** 2
    w_fe = 1.0 / v
    mu_fe = float(np.sum(w_fe * d) / np.sum(w_fe))
    Q = float(np.sum(w_fe * (d - mu_fe) ** 2))
    df = k - 1
    C = float(np.sum(w_fe) - np.sum(w_fe ** 2) / np.sum(w_fe))
    tau2_dl = max(0.0, (Q - df) / max(C, 1e-9))
    I2 = max(0.0, (Q - df) / Q) if Q > 0 else 0.0

    if method == "reml":
        def _neg_reml(t2: float) -> float:
            wt = 1.0 / (v + t2)
            sw = np.sum(wt)
            mu = np.sum(wt * d) / sw
            return 0.5 * (np.sum(np.log(v + t2)) + np.log(sw) + np.sum(wt * (d - mu) ** 2))

        opt = optimize.minimize_scalar(_neg_reml, bounds=(0.0, max(500.0, 20.0 * float(np.var(d)))), method="bounded")
        tau2 = float(max(0.0, opt.x))
        wt = 1.0 / (v + tau2)
        mu0 = float(np.sum(wt * d) / np.sum(wt))
    else:
        tau2 = tau2_dl
        if tau2 > 0:
            wt = 1.0 / (v + tau2)
            mu0 = float(np.sum(wt * d) / np.sum(wt))
        else:
            mu0 = mu_fe

    tau = float(sqrt(tau2))
    med_v = float(np.median(v))
    k_eff = float(med_v / tau2) if tau2 > 1e-12 else float("inf")
    return {
        "mu0": mu0,
        "tau2": tau2,
        "tau": tau,
        "Q": Q,
        "df": int(df),
        "I2": float(I2),
        "k_eff": k_eff,
    }


def compute_match_cluster_bootstrap(
    match_stats: pd.DataFrame,
    id_col: str,
    span: float = 0.75,
    n_iter: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Fast vectorized B=2,000 match-clustered bootstrap for raw FWL contrast SE and 95% CI."""
    rng = np.random.default_rng(seed)
    rows = []
    for pid, grp in match_stats.groupby(id_col, sort=True):
        sxx_m = grp["sxx_m"].values.astype(float)
        sxy_m = grp["sxy_m"].values.astype(float)
        m_cnt = len(sxx_m)
        if m_cnt < 2 or np.sum(sxx_m) <= 1e-9:
            rows.append({
                id_col: pid,
                "boot_mean": np.nan,
                "boot_se": np.nan,
                "boot_ci_low": np.nan,
                "boot_lcb95": np.nan,
                "boot_ci_high": np.nan,
                "boot_prob_pos": np.nan,
            })
            continue
        idx = rng.integers(0, m_cnt, size=(n_iter, m_cnt))
        sum_xx = sxx_m[idx].sum(axis=1)
        sum_xy = sxy_m[idx].sum(axis=1)
        valid = sum_xx > 1e-6
        if valid.sum() < 50:
            rows.append({
                id_col: pid,
                "boot_mean": np.nan,
                "boot_se": np.nan,
                "boot_ci_low": np.nan,
                "boot_lcb95": np.nan,
                "boot_ci_high": np.nan,
                "boot_prob_pos": np.nan,
            })
            continue
        draws = span * (sum_xy[valid] / sum_xx[valid])
        rows.append({
            id_col: pid,
            "boot_mean": float(np.mean(draws)),
            "boot_se": float(np.std(draws, ddof=1)),
            "boot_ci_low": float(np.percentile(draws, 2.5)),
            "boot_lcb95": float(np.percentile(draws, 5.0)),
            "boot_ci_high": float(np.percentile(draws, 97.5)),
            "boot_prob_pos": float(np.mean(draws > 0.0)),
        })
    return pd.DataFrame(rows)


def fit_hierarchical_contrast(
    df: pd.DataFrame,
    role: str = "batter",
    outcome: str = "batter_runs",
    scale: float = 100.0,
    p_col: str = "bat_pressure",
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
    strata_cols: Tuple[str, ...] = ("match_format",),
    contrast_mode: str = "fwl",
    eb_method: str = "dl",
    shuffle_pressure_seed: int | None = None,
    bootstrap_iter: int = 2000,
    bootstrap_seed: int = 42,
    damp_match: float = 35.0,
    damp_player: float = 30.0,
    damp_opp: float = 35.0,
    min_pool_hi: int = 30,
    min_pool_lo: int = 30,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Estimate unadjusted baseline, simultaneous Ridge context-adjusted normal baseline,
    within-player common-support contrast Delta_i, EB shrinkage, and 2,000-iter cluster bootstrap.
    """
    if role == "batter":
        work = df[df["is_ball_faced"] == 1].copy()
        id_col, name_col, opp_col = "striker_id", "striker_name", "bowler_id"
    else:
        work = df[df["is_legal_ball"] == 1].copy()
        id_col, name_col, opp_col = "bowler_id", "bowler_name", "striker_id"

    work["y"] = work[outcome].values.astype(float) * scale
    work["p"] = work[p_col].values.astype(float)
    if shuffle_pressure_seed is not None:
        rng = np.random.default_rng(shuffle_pressure_seed)
        work["p"] = rng.permutation(work["p"].values)

    work["p_dec"] = np.clip((work["p"] * 10.0).astype(int), 0, 9)
    work["is_hi"] = work["p"] >= hi_thr
    work["is_lo"] = work["p"] <= lo_thr
    work["is_norm_zone"] = ~work["is_hi"]

    # Simultaneous sparse Ridge: unpenalized/tiny-L2 State_FE + Match_Par + Player_Normal + Opp_Quality
    skey = (
        work["innings"].astype(str) + "|" + work["phase"].astype(str) + "|" +
        work["match_format"].astype(str) + "|" + work["season"].astype(str) + "|" +
        work["p_dec"].astype(str)
    )
    sc = pd.Categorical(skey)
    mc = pd.Categorical(work["match_id"])
    pc = pd.Categorical(work[id_col])
    oc = pd.Categorical(work[opp_col])

    ns, nm, np_, no = len(sc.categories), len(mc.categories), len(pc.categories), len(oc.categories)
    n = len(work)
    row_ix = np.arange(n)

    Xs = sparse.csr_matrix((np.ones(n), (row_ix, sc.codes)), shape=(n, ns))
    Xm = sparse.csr_matrix((np.ones(n), (row_ix, mc.codes)), shape=(n, nm))
    Xp = sparse.csr_matrix((np.ones(n), (row_ix, pc.codes)), shape=(n, np_))
    Xo = sparse.csr_matrix((np.ones(n), (row_ix, oc.codes)), shape=(n, no))
    X_main = sparse.hstack([Xs, Xm, Xp, Xo], format="csr")

    pen_diag = sparse.diags(np.concatenate([
        np.full(ns, 0.1),
        np.full(nm, sqrt(damp_match)),
        np.full(np_, sqrt(damp_player)),
        np.full(no, sqrt(damp_opp)),
    ]))
    coef = lsqr(
        sparse.vstack([X_main, pen_diag], format="csr"),
        np.concatenate([work["y"].values, np.zeros(ns + nm + np_ + no)]),
        atol=1e-7, btol=1e-7,
    )[0]

    player_norm_eff = pd.Series(coef[ns + nm:ns + nm + np_], index=pc.categories)
    work["resid"] = work["y"].values - X_main.dot(coef)
    # Performance holding State + Match + Opponent fixed (player's net execution in that delivery)
    work["resid_no_pl"] = (
        work["y"].values - Xs.dot(coef[:ns]) - Xm.dot(coef[ns:ns + nm]) - Xo.dot(coef[ns + nm + np_:])
    )
    resid_var = float(work["resid"].var(ddof=1))

    # Common-support restriction: strata where player has BOTH >=1 High and >=1 Low delivery
    work["stratum"] = work[list(strata_cols)].astype(str).agg("|".join, axis=1)
    ps = work.groupby([id_col, "stratum"]).agg(nh=("is_hi", "sum"), nl=("is_lo", "sum"))
    cs_idx = ps[(ps["nh"] >= 1) & (ps["nl"] >= 1)].index
    cs_mask = work.set_index([id_col, "stratum"]).index.isin(cs_idx)
    sub = work[cs_mask].copy()

    if contrast_mode == "discrete":
        sub = sub[sub["is_hi"] | sub["is_lo"]].copy()
        sub["x_var"] = sub["is_hi"].astype(float)
        span = 1.0
    else:
        sub["x_var"] = sub["p"].values
        span = float(hi_thr - 0.5 * lo_thr) if lo_thr <= 0.25 else float(hi_thr - lo_thr)
        if contrast_mode == "fwl":
            # Canonical contrast across [p=0.125 (midpoint<=0.25), p=0.875 (midpoint>=0.75)] = 0.75
            span = float(max(hi_thr - (lo_thr * 0.5), 0.50))

    sub["pt"] = sub["x_var"] - sub.groupby([id_col, "stratum"])["x_var"].transform("mean")
    sub["rt"] = sub["resid"] - sub.groupby([id_col, "stratum"])["resid"].transform("mean")
    sub["pp"] = sub["pt"] ** 2
    sub["pr"] = sub["pt"] * sub["rt"]

    fwl_agg = sub.groupby(id_col, as_index=False).agg(
        sxx=("pp", "sum"),
        sxy=("pr", "sum"),
        cs_balls=("y", "size"),
        cs_matches=("match_id", "nunique"),
    )
    m_fwl = sub.groupby([id_col, "match_id"], as_index=False).agg(
        sxx_m=("pp", "sum"),
        sxy_m=("pr", "sum"),
    )
    m_fwl = m_fwl.merge(fwl_agg[[id_col, "sxx", "sxy"]], on=id_col, how="left")
    m_fwl["beta_hat"] = np.where(m_fwl["sxx"] > 1e-9, m_fwl["sxy"] / np.maximum(m_fwl["sxx"], 1e-9), 0.0)
    m_fwl["u_m2"] = (m_fwl["sxy_m"] - m_fwl["beta_hat"] * m_fwl["sxx_m"]) ** 2
    se_agg = m_fwl.groupby(id_col, as_index=False).agg(
        sum_u2=("u_m2", "sum"),
        m_cnt=("match_id", "nunique"),
    )

    # Player summary stats across unadjusted, normal, high-pressure & match consistency
    unadj_all = work.groupby(id_col, as_index=False).agg(
        player_name=(name_col, "last"),
        total_balls=("y", "size"),
        total_matches=("match_id", "nunique"),
        unadj_overall_mean=("y", "mean"),
        n_hi=("is_hi", "sum"),
        n_lo=("is_lo", "sum"),
        n_norm=("is_norm_zone", "sum"),
        formats_played=("match_format", lambda s: ",".join(sorted(s.unique()))),
        last_season=("season", "max"),
    )
    hi_work = work[work["is_hi"]]
    lo_work = work[work["is_lo"]]
    norm_work = work[work["is_norm_zone"]]

    hi_agg = hi_work.groupby(id_col, as_index=False).agg(
        hi_matches=("match_id", "nunique"),
        unadj_hi_mean=("y", "mean"),
        hi_resid_mean=("resid_no_pl", "mean"),
        hi_resid_sd=("resid_no_pl", "std"),
        mean_p_hi=("p", "mean"),
    )
    lo_agg = lo_work.groupby(id_col, as_index=False).agg(
        lo_matches=("match_id", "nunique"),
        unadj_lo_mean=("y", "mean"),
        lo_resid_mean=("resid_no_pl", "mean"),
        mean_p_lo=("p", "mean"),
    )
    norm_agg = norm_work.groupby(id_col, as_index=False).agg(
        norm_matches=("match_id", "nunique"),
        unadj_norm_mean=("y", "mean"),
    )

    # Match-level high-pressure execution & cluster SE for high-pressure residual mean
    hi_m = hi_work.groupby([id_col, "match_id"], as_index=False).agg(
        hi_m_mean=("resid_no_pl", "mean"),
        hi_m_n=("resid_no_pl", "size"),
    )
    hi_m_cons = hi_m.groupby(id_col, as_index=False).agg(
        hi_match_pos_rate=("hi_m_mean", lambda s: float(np.mean(s > 0.0))),
        hi_match_iqr=("hi_m_mean", lambda s: float(np.percentile(s, 75) - np.percentile(s, 25)) if len(s) >= 4 else np.nan),
        hi_match_sd=("hi_m_mean", "std"),
    )
    hi_m_se_df = hi_m.merge(hi_agg[[id_col, "hi_resid_mean"]], on=id_col, how="left")
    hi_m_se_df["w_err2"] = (hi_m_se_df["hi_m_n"] * (hi_m_se_df["hi_m_mean"] - hi_m_se_df["hi_resid_mean"])) ** 2
    hi_se_agg = hi_m_se_df.groupby(id_col, as_index=False).agg(
        hi_w2=("w_err2", "sum"),
        hi_n_tot=("hi_m_n", "sum"),
        hi_mc=("match_id", "nunique"),
    )
    hi_dof = np.sqrt(np.maximum(hi_se_agg["hi_mc"], 2) / np.maximum(hi_se_agg["hi_mc"] - 1, 1))
    hi_se_agg["hi_cluster_se"] = np.maximum(
        hi_dof * np.sqrt(np.maximum(hi_se_agg["hi_w2"], 0.0)) / np.maximum(hi_se_agg["hi_n_tot"], 1),
        sqrt(resid_var) / np.sqrt(np.maximum(hi_se_agg["hi_n_tot"], 1)),
    )

    res = (
        unadj_all
        .merge(hi_agg, on=id_col, how="left")
        .merge(lo_agg, on=id_col, how="left")
        .merge(norm_agg, on=id_col, how="left")
        .merge(hi_m_cons, on=id_col, how="left")
        .merge(hi_se_agg[[id_col, "hi_cluster_se"]], on=id_col, how="left")
        .merge(fwl_agg, on=id_col, how="left")
        .merge(se_agg, on=id_col, how="left")
    )
    for c in ("hi_matches", "lo_matches", "norm_matches", "cs_balls", "cs_matches", "m_cnt"):
        res[c] = res[c].fillna(0).astype(int)

    res["context_adj_normal"] = res[id_col].map(player_norm_eff).fillna(0.0)
    res["unadj_hi_minus_lo"] = res["unadj_hi_mean"] - res["unadj_lo_mean"]
    res["unadj_hi_minus_norm"] = res["unadj_hi_mean"] - res["unadj_norm_mean"]

    res["raw_fwl_delta"] = np.where(res["sxx"] > 1e-9, span * (res["sxy"] / np.maximum(res["sxx"], 1e-9)), np.nan)
    res["naive_se"] = np.where(res["sxx"] > 1e-9, span * np.sqrt(resid_var / np.maximum(res["sxx"], 1e-9)), np.nan)
    dof = np.sqrt(np.maximum(res["m_cnt"], 2) / np.maximum(res["m_cnt"] - 1, 1))
    res["cluster_se"] = np.where(
        res["sxx"] > 1e-9,
        span * dof * np.sqrt(np.maximum(res["sum_u2"], 0.0)) / np.maximum(res["sxx"], 1e-9),
        np.nan,
    )
    res["se_delta"] = np.maximum(res["cluster_se"], res["naive_se"])

    # Heterogeneity & Empirical Bayes on Delta_i
    pool_mask = (res["n_hi"] >= min_pool_hi) & (res["n_lo"] >= min_pool_lo) & (res["sxx"] > 2.0)
    het = estimate_heterogeneity(res.loc[pool_mask, "raw_fwl_delta"].values, res.loc[pool_mask, "se_delta"].values, method=eb_method)
    tau2 = het["tau2"]
    mu0 = het["mu0"]

    res["eb_weight"] = np.where(
        (tau2 > 0) & np.isfinite(res["se_delta"]) & (res["se_delta"] > 0),
        tau2 / (tau2 + res["se_delta"] ** 2),
        0.0,
    )
    res["eb_delta"] = np.where(
        np.isfinite(res["raw_fwl_delta"]),
        mu0 + res["eb_weight"] * (res["raw_fwl_delta"] - mu0),
        mu0,
    )
    res["post_sd"] = np.where(
        (tau2 > 0) & np.isfinite(res["se_delta"]) & (res["se_delta"] > 0),
        np.sqrt((tau2 * (res["se_delta"] ** 2)) / (tau2 + res["se_delta"] ** 2)),
        0.0,
    )
    res["lcb95_delta"] = res["eb_delta"] - 1.96 * res["post_sd"]
    res["ucb95_delta"] = res["eb_delta"] + 1.96 * res["post_sd"]
    res["prob_delta_gt_zero"] = np.where(
        res["post_sd"] > 1e-9,
        _norm_cdf(res["eb_delta"].values / np.maximum(res["post_sd"].values, 1e-9)),
        np.where(res["eb_delta"] > 0, 1.0, 0.0),
    )

    # Separate Empirical Bayes on net high-pressure execution level (resid_no_pl in High pressure)
    hi_pool = (res["n_hi"] >= min_pool_hi) & np.isfinite(res["hi_resid_mean"]) & np.isfinite(res["hi_cluster_se"])
    het_hi = estimate_heterogeneity(res.loc[hi_pool, "hi_resid_mean"].values, res.loc[hi_pool, "hi_cluster_se"].values, method=eb_method)
    tau2_hi, mu0_hi = het_hi["tau2"], het_hi["mu0"]
    res["hi_eb_weight"] = np.where(
        (tau2_hi > 0) & np.isfinite(res["hi_cluster_se"]) & (res["hi_cluster_se"] > 0),
        tau2_hi / (tau2_hi + res["hi_cluster_se"] ** 2),
        0.0,
    )
    res["eb_hi_perf"] = np.where(
        np.isfinite(res["hi_resid_mean"]),
        mu0_hi + res["hi_eb_weight"] * (res["hi_resid_mean"] - mu0_hi),
        mu0_hi,
    )
    res["hi_post_sd"] = np.where(
        (tau2_hi > 0) & np.isfinite(res["hi_cluster_se"]) & (res["hi_cluster_se"] > 0),
        np.sqrt((tau2_hi * (res["hi_cluster_se"] ** 2)) / (tau2_hi + res["hi_cluster_se"] ** 2)),
        0.0,
    )
    res["lcb95_hi_perf"] = res["eb_hi_perf"] - 1.96 * res["hi_post_sd"]

    # Match-clustered bootstrap (run for players with >= 10 cs_matches to keep fast, or >= 2 when requested)
    if bootstrap_iter > 0:
        boot_m = m_fwl[m_fwl[id_col].isin(res.loc[res["m_cnt"] >= 5, id_col])]
        boot_df = compute_match_cluster_bootstrap(boot_m, id_col=id_col, span=span, n_iter=bootstrap_iter, seed=bootstrap_seed)
        res = res.merge(boot_df, on=id_col, how="left")
    else:
        for c in ("boot_mean", "boot_se", "boot_ci_low", "boot_lcb95", "boot_ci_high", "boot_prob_pos"):
            res[c] = np.nan

    diag = {
        "role": role,
        "outcome": outcome,
        "scale": scale,
        "p_col": p_col,
        "hi_thr": hi_thr,
        "lo_thr": lo_thr,
        "span": span,
        "strata_cols": ",".join(strata_cols),
        "contrast_mode": contrast_mode,
        "eb_method": eb_method,
        "resid_sd": float(sqrt(resid_var)),
        "n_deliveries": int(n),
        "n_players": int(len(res)),
        "n_pool_het": int(pool_mask.sum()),
        **het,
        "hi_mu0": mu0_hi,
        "hi_tau": het_hi["tau"],
        "hi_Q": het_hi["Q"],
        "hi_df": het_hi["df"],
    }
    return res, diag
