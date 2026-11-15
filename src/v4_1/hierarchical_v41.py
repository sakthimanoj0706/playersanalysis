"""V4.1 Sections 2, 5, 6, 7 — Aliased Resource Stress, Two-Stage FWL+REML, Joint Hierarchical Slope & Complete-Ranking Match Bootstrap."""
from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from scipy import optimize, sparse
from scipy.sparse.linalg import lsqr
from scipy.special import ndtr


def add_v41_pressure_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Attach canonical V4.1 terminology aliases while preserving V4 compatibility columns."""
    out = df.copy()
    if "bat_pressure" in out.columns:
        out["BATTING_RESOURCE_STRESS"] = out["bat_pressure"]
    if "bowl_pressure" in out.columns:
        out["BOWLING_SCORING_THREAT"] = out["bowl_pressure"]
    return out


def estimate_heterogeneity(
    delta: np.ndarray,
    se: np.ndarray,
    method: str = "reml",
) -> Dict[str, float]:
    """Random-effects heterogeneity estimation (REML or DerSimonian-Laird)."""
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

        if Q <= df + 1e-12:
            tau2 = 0.0
        else:
            opt = optimize.minimize_scalar(
                _neg_reml,
                bounds=(0.0, max(500.0, 20.0 * float(np.var(d)))),
                method="bounded",
            )
            nll_zero = float(_neg_reml(0.0))
            tau2 = 0.0 if nll_zero <= float(opt.fun) + 1e-9 else float(max(0.0, opt.x))
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


def _solve_stage1_ridge(
    work: pd.DataFrame,
    id_col: str,
    opp_col: str,
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    include_p_slope: bool = False,
    lam_slope: float = 1500.0,
) -> Dict[str, Any]:
    """Solve sparse Ridge main effects (and optionally simultaneous player pressure slopes)."""
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
    rx = np.arange(n)

    Xs = sparse.csr_matrix((np.ones(n), (rx, sc.codes)), shape=(n, ns))
    Xm = sparse.csr_matrix((np.ones(n), (rx, mc.codes)), shape=(n, nm))
    Xp = sparse.csr_matrix((np.ones(n), (rx, pc.codes)), shape=(n, np_))
    Xo = sparse.csr_matrix((np.ones(n), (rx, oc.codes)), shape=(n, no))

    if include_p_slope:
        p_c = work["p"].values - 0.5
        Xb = sparse.csr_matrix((p_c, (rx, pc.codes)), shape=(n, np_))
        X_main = sparse.hstack([Xs, Xm, Xp, Xb, Xo], format="csr")
        pen = sparse.diags(np.concatenate([
            np.full(ns, 0.1),
            np.full(nm, sqrt(lam_match)),
            np.full(np_, sqrt(lam_player)),
            np.full(np_, sqrt(lam_slope)),
            np.full(no, sqrt(lam_opp)),
        ]))
        c = lsqr(
            sparse.vstack([X_main, pen], format="csr"),
            np.concatenate([work["y"].values, np.zeros(X_main.shape[1])]),
            atol=1e-7, btol=1e-7,
        )[0]
        off_p = ns + nm
        off_b = off_p + np_
        off_o = off_b + np_
        return {
            "alpha_state": Xs.dot(c[:ns]),
            "u_match": Xm.dot(c[ns:off_p]),
            "theta_player": pd.Series(c[off_p:off_b], index=pc.categories),
            "beta_joint": pd.Series(c[off_b:off_o], index=pc.categories),
            "psi_opp": Xo.dot(c[off_o:]),
            "y_hat": X_main.dot(c),
        }

    X_main = sparse.hstack([Xs, Xm, Xp, Xo], format="csr")
    pen = sparse.diags(np.concatenate([
        np.full(ns, 0.1),
        np.full(nm, sqrt(lam_match)),
        np.full(np_, sqrt(lam_player)),
        np.full(no, sqrt(lam_opp)),
    ]))
    c = lsqr(
        sparse.vstack([X_main, pen], format="csr"),
        np.concatenate([work["y"].values, np.zeros(X_main.shape[1])]),
        atol=1e-7, btol=1e-7,
    )[0]
    off_p = ns + nm
    off_o = off_p + np_
    return {
        "alpha_state": Xs.dot(c[:ns]),
        "u_match": Xm.dot(c[ns:off_p]),
        "theta_player": pd.Series(c[off_p:off_o], index=pc.categories),
        "beta_joint": None,
        "psi_opp": Xo.dot(c[off_o:]),
        "y_hat": X_main.dot(c),
    }


def fit_v41_two_stage(
    df: pd.DataFrame,
    role: str = "batter",
    outcome: str = "batter_runs",
    scale: float = 100.0,
    p_col: str | None = None,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
    span: float = 0.75,
    strata_cols: Tuple[str, ...] = ("match_format",),
    eb_method: str = "reml",
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    min_pool_hi: int = 30,
    min_pool_lo: int = 30,
    max_pool_se: float = 30.0,
    shuffle_pressure_seed: int | None = None,
) -> Tuple[pd.DataFrame, Dict[str, Any], pd.DataFrame, pd.DataFrame]:
    """
    Fit V4.1 Two-Stage Context-Adjusted FWL + Empirical Bayes Contrast Model.
    Fixes V4's unintended 0.625 contrast span to exact canonical 0.75, exposes explicit
    raw vs context-adjusted performance columns, and preserves match sufficient stats
    for correlated global match-cluster ranking bootstrap.
    """
    if role == "batter":
        work = df[df["is_ball_faced"] == 1].copy()
        id_col, name_col, opp_col = "striker_id", "striker_name", "bowler_id"
        p_col = p_col or ("BATTING_RESOURCE_STRESS" if "BATTING_RESOURCE_STRESS" in work.columns else "bat_pressure")
    else:
        work = df[df["is_legal_ball"] == 1].copy()
        id_col, name_col, opp_col = "bowler_id", "bowler_name", "striker_id"
        p_col = p_col or ("BOWLING_SCORING_THREAT" if "BOWLING_SCORING_THREAT" in work.columns else "bowl_pressure")

    work["y"] = work[outcome].values.astype(float) * scale
    work["p"] = work[p_col].values.astype(float)
    if shuffle_pressure_seed is not None:
        rng = np.random.default_rng(shuffle_pressure_seed)
        work["p"] = rng.permutation(work["p"].values)

    work["p_dec"] = np.clip((work["p"] * 10.0).astype(int), 0, 9)
    work["is_hi"] = work["p"] >= hi_thr
    work["is_lo"] = work["p"] <= lo_thr
    work["is_norm_zone"] = ~work["is_hi"]

    sol = _solve_stage1_ridge(
        work, id_col=id_col, opp_col=opp_col,
        lam_match=lam_match, lam_player=lam_player, lam_opp=lam_opp,
        include_p_slope=False,
    )
    work["alpha_state"] = sol["alpha_state"]
    work["u_match"] = sol["u_match"]
    work["psi_opp"] = sol["psi_opp"]
    work["alpha_pfs"] = work.groupby(["innings", "phase", "match_format", "season"])["alpha_state"].transform("mean")
    work["alpha_pq_resid"] = work["alpha_state"] - work["alpha_pfs"]
    work["context_par"] = work["alpha_state"] + work["u_match"] + work["psi_opp"]
    work["resid"] = work["y"].values - sol["y_hat"]
    work["resid_no_pl"] = work["y"].values - work["context_par"].values
    resid_var = float(work["resid"].var(ddof=1))

    # Common-support within-stratum FWL regression on context-adjusted residuals
    work["stratum"] = work[list(strata_cols)].astype(str).agg("|".join, axis=1)
    ps = work.groupby([id_col, "stratum"]).agg(nh=("is_hi", "sum"), nl=("is_lo", "sum"))
    cs_idx = ps[(ps["nh"] >= 1) & (ps["nl"] >= 1)].index
    sub = work[work.set_index([id_col, "stratum"]).index.isin(cs_idx)].copy()

    sub["pt"] = sub["p"] - sub.groupby([id_col, "stratum"])["p"].transform("mean")
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
        n_m=("y", "size"),
    )
    m_fwl = m_fwl.merge(fwl_agg[[id_col, "sxx", "sxy"]], on=id_col, how="left")
    m_fwl["beta_hat"] = np.where(m_fwl["sxx"] > 1e-9, m_fwl["sxy"] / np.maximum(m_fwl["sxx"], 1e-9), 0.0)
    m_fwl["u_m2"] = (m_fwl["sxy_m"] - m_fwl["beta_hat"] * m_fwl["sxx_m"]) ** 2
    se_agg = m_fwl.groupby(id_col, as_index=False).agg(
        sum_u2=("u_m2", "sum"),
        m_cnt=("match_id", "nunique"),
    )

    unadj_all = work.groupby(id_col, as_index=False).agg(
        player_name=(name_col, "last"),
        total_balls=("y", "size"),
        total_matches=("match_id", "nunique"),
        raw_overall_performance=("y", "mean"),
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
        raw_high_performance=("y", "mean"),
        context_adjusted_high_performance=("resid_no_pl", "mean"),
        mean_p_hi=("p", "mean"),
        hi_alpha_pfs=("alpha_pfs", "mean"),
        hi_alpha_pq=("alpha_pq_resid", "mean"),
        hi_match_opp=("u_match", "mean"),
        hi_opp_only=("psi_opp", "mean"),
    )
    lo_agg = lo_work.groupby(id_col, as_index=False).agg(
        lo_matches=("match_id", "nunique"),
        raw_low_performance=("y", "mean"),
        context_adjusted_low_performance=("resid_no_pl", "mean"),
        mean_p_lo=("p", "mean"),
    )
    norm_agg = norm_work.groupby(id_col, as_index=False).agg(
        norm_matches=("match_id", "nunique"),
        raw_normal_performance=("y", "mean"),
        context_adjusted_normal_performance=("resid_no_pl", "mean"),
        mean_p_norm=("p", "mean"),
        norm_alpha_pfs=("alpha_pfs", "mean"),
        norm_alpha_pq=("alpha_pq_resid", "mean"),
        norm_match_opp=("u_match", "mean"),
        norm_opp_only=("psi_opp", "mean"),
    )

    hi_m = hi_work.groupby([id_col, "match_id"], as_index=False).agg(
        hi_m_mean=("resid_no_pl", "mean"),
        hi_m_n=("resid_no_pl", "size"),
    )
    hi_m_cons = hi_m.groupby(id_col, as_index=False).agg(
        hi_match_pos_rate=("hi_m_mean", lambda s: float(np.mean(s > 0.0))),
        hi_match_iqr=("hi_m_mean", lambda s: float(np.percentile(s, 75) - np.percentile(s, 25)) if len(s) >= 4 else np.nan),
        hi_match_sd=("hi_m_mean", "std"),
    )
    hi_m_se = hi_m.merge(hi_agg[[id_col, "context_adjusted_high_performance"]], on=id_col, how="left")
    hi_m_se["w2"] = (hi_m_se["hi_m_n"] * (hi_m_se["hi_m_mean"] - hi_m_se["context_adjusted_high_performance"])) ** 2
    hi_se_agg = hi_m_se.groupby(id_col, as_index=False).agg(w2=("w2", "sum"), n_tot=("hi_m_n", "sum"), mc=("match_id", "nunique"))
    hi_dof = np.sqrt(np.maximum(hi_se_agg["mc"], 2) / np.maximum(hi_se_agg["mc"] - 1, 1))
    hi_se_agg["hi_cluster_se"] = np.maximum(
        hi_dof * np.sqrt(np.maximum(hi_se_agg["w2"], 0.0)) / np.maximum(hi_se_agg["n_tot"], 1),
        sqrt(resid_var) / np.sqrt(np.maximum(hi_se_agg["n_tot"], 1)),
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

    res["ridge_overall_player_effect"] = res[id_col].map(sol["theta_player"]).fillna(0.0)
    res["raw_observed_delta"] = res["raw_high_performance"] - res["raw_normal_performance"]
    res["raw_hi_minus_lo_delta"] = res["raw_high_performance"] - res["raw_low_performance"]
    res["discrete_context_adjusted_delta"] = (
        res["context_adjusted_high_performance"] - res["context_adjusted_normal_performance"]
    )
    res["context_adjusted_delta"] = np.where(res["sxx"] > 1e-9, span * (res["sxy"] / np.maximum(res["sxx"], 1e-9)), np.nan)
    res["effective_sample_n_eff"] = (span ** 2) * resid_var / np.maximum(
        np.where(res["sxx"] > 1e-9, (span ** 2) * resid_var / np.maximum(res["sxx"], 1e-9), np.nan),
        1e-9,
    )
    # Exact effective paired high/low sample equivalent from Fisher info sxx: 4 * sxx * (span/0.75)^2 ~ effective ball info
    res["effective_sample_size"] = np.round(4.0 * res["sxx"].fillna(0.0), 1)
    res["naive_se"] = np.where(res["sxx"] > 1e-9, span * np.sqrt(resid_var / np.maximum(res["sxx"], 1e-9)), np.nan)
    dof = np.sqrt(np.maximum(res["m_cnt"], 2) / np.maximum(res["m_cnt"] - 1, 1))
    res["cluster_se"] = np.where(
        res["sxx"] > 1e-9,
        span * dof * np.sqrt(np.maximum(res["sum_u2"], 0.0)) / np.maximum(res["sxx"], 1e-9),
        np.nan,
    )
    res["se_delta"] = np.maximum(res["cluster_se"], res["naive_se"])

    pool_mask = (res["n_hi"] >= min_pool_hi) & (res["n_lo"] >= min_pool_lo) & (res["sxx"] > 2.0) & (res["se_delta"] <= max_pool_se)
    het = estimate_heterogeneity(res.loc[pool_mask, "context_adjusted_delta"].values, res.loc[pool_mask, "se_delta"].values, method=eb_method)
    tau2, mu0 = het["tau2"], het["mu0"]

    res["eb_weight"] = np.where((tau2 > 0) & np.isfinite(res["se_delta"]) & (res["se_delta"] > 0), tau2 / (tau2 + res["se_delta"] ** 2), 0.0)
    res["empirical_bayes_delta"] = np.where(np.isfinite(res["context_adjusted_delta"]), mu0 + res["eb_weight"] * (res["context_adjusted_delta"] - mu0), mu0)
    res["post_sd"] = np.where((tau2 > 0) & np.isfinite(res["se_delta"]) & (res["se_delta"] > 0), np.sqrt((tau2 * (res["se_delta"] ** 2)) / (tau2 + res["se_delta"] ** 2)), 0.0)
    res["lower_confidence_bound"] = res["empirical_bayes_delta"] - 1.96 * res["post_sd"]
    res["upper_confidence_bound"] = res["empirical_bayes_delta"] + 1.96 * res["post_sd"]
    res["probability_positive_effect"] = np.where(
        res["post_sd"] > 1e-9,
        ndtr(res["empirical_bayes_delta"].values / np.maximum(res["post_sd"].values, 1e-9)),
        np.where(res["empirical_bayes_delta"] > 0, 1.0, 0.0),
    )

    # High-pressure EB level (kept strictly separate as secondary context diagnostic, never mixed into primary target)
    hi_pool = (res["n_hi"] >= min_pool_hi) & np.isfinite(res["context_adjusted_high_performance"]) & np.isfinite(res["hi_cluster_se"])
    het_hi = estimate_heterogeneity(res.loc[hi_pool, "context_adjusted_high_performance"].values, res.loc[hi_pool, "hi_cluster_se"].values, method=eb_method)
    tau2_hi, mu0_hi = het_hi["tau2"], het_hi["mu0"]
    res["hi_eb_weight"] = np.where((tau2_hi > 0) & np.isfinite(res["hi_cluster_se"]) & (res["hi_cluster_se"] > 0), tau2_hi / (tau2_hi + res["hi_cluster_se"] ** 2), 0.0)
    res["eb_high_performance"] = np.where(np.isfinite(res["context_adjusted_high_performance"]), mu0_hi + res["hi_eb_weight"] * (res["context_adjusted_high_performance"] - mu0_hi), mu0_hi)

    res["role"] = role
    res = res.rename(columns={id_col: "player_id"})
    m_fwl = m_fwl.rename(columns={id_col: "player_id"})

    diag = {
        "role": role,
        "outcome": outcome,
        "scale": scale,
        "p_col": p_col,
        "span": span,
        "eb_method": eb_method,
        "lam_match": lam_match,
        "lam_player": lam_player,
        "lam_opp": lam_opp,
        "resid_sd": float(sqrt(resid_var)),
        "n_deliveries": int(len(work)),
        "n_players": int(len(res)),
        "n_pool_het": int(pool_mask.sum()),
        **het,
        "hi_mu0": mu0_hi,
        "hi_tau": het_hi["tau"],
    }
    return res, diag, m_fwl, work


def fit_joint_hierarchical_slope(
    df: pd.DataFrame,
    role: str = "batter",
    outcome: str = "batter_runs",
    scale: float = 100.0,
    span: float = 0.75,
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    lam_slope: float = 3500.0,
) -> pd.DataFrame:
    """Simultaneous sparse Ridge model estimating alpha_state, u_match, theta_i, b_i*p_c, psi_opp."""
    if role == "batter":
        work = df[df["is_ball_faced"] == 1].copy()
        id_col, opp_col = "striker_id", "bowler_id"
        p_col = "BATTING_RESOURCE_STRESS" if "BATTING_RESOURCE_STRESS" in work.columns else "bat_pressure"
    else:
        work = df[df["is_legal_ball"] == 1].copy()
        id_col, opp_col = "bowler_id", "striker_id"
        p_col = "BOWLING_SCORING_THREAT" if "BOWLING_SCORING_THREAT" in work.columns else "bowl_pressure"

    work["y"] = work[outcome].values.astype(float) * scale
    work["p"] = work[p_col].values.astype(float)
    work["p_dec"] = np.clip((work["p"] * 10.0).astype(int), 0, 9)
    sol = _solve_stage1_ridge(
        work, id_col=id_col, opp_col=opp_col,
        lam_match=lam_match, lam_player=lam_player, lam_opp=lam_opp,
        include_p_slope=True, lam_slope=lam_slope,
    )
    out = pd.DataFrame({
        "player_id": sol["theta_player"].index.astype(int),
        "joint_theta_player": sol["theta_player"].values,
        "joint_delta": span * sol["beta_joint"].values,
    })
    return out


def run_global_match_cluster_bootstrap(
    m_fwl: pd.DataFrame,
    eligible_ids: List[int],
    pool_ids: List[int],
    span: float = 0.75,
    n_iter: int = 1000,
    seed: int = 42,
) -> Tuple[pd.DataFrame, Dict[str, float]]:
    """
    Correlated Complete-Ranking-Level Match-Cluster Bootstrap across all matches simultaneously.
    Preserves cross-player shared-match dependence, re-estimates heterogeneity (mu0, tau2)
    per bootstrap sample, and computes exact rank intervals and Top-10 membership probabilities.
    """
    # Build dense [M x P_pool] matrices of sxx_m and sxy_m over all scoped matches
    all_pids = sorted(set(pool_ids) | set(eligible_ids))
    elig_set = set(eligible_ids)
    elig_mask = np.array([pid in elig_set for pid in all_pids], dtype=bool)

    m_sub = m_fwl[m_fwl["player_id"].isin(all_pids)].copy()
    match_cats = np.sort(m_sub["match_id"].unique())
    p_map = {pid: i for i, pid in enumerate(all_pids)}
    m_map = {mid: i for i, mid in enumerate(match_cats)}
    M, P = len(match_cats), len(all_pids)

    Sxx = np.zeros((M, P), dtype=np.float64)
    Sxy = np.zeros((M, P), dtype=np.float64)
    np.add.at(Sxx, (m_sub["match_id"].map(m_map).values, m_sub["player_id"].map(p_map).values), m_sub["sxx_m"].values)
    np.add.at(Sxy, (m_sub["match_id"].map(m_map).values, m_sub["player_id"].map(p_map).values), m_sub["sxy_m"].values)

    # Empirical shared-match co-occurrence & match-contribution correlation across eligible players
    co_occ = ((Sxx[:, elig_mask] > 0).astype(float).T @ (Sxx[:, elig_mask] > 0).astype(float))
    np.fill_diagonal(co_occ, np.nan)
    mean_shared_matches = float(np.nanmean(co_occ))
    corr_mat = np.corrcoef(Sxy[:, elig_mask].T)
    np.fill_diagonal(corr_mat, np.nan)
    mean_abs_match_corr = float(np.nanmean(np.abs(corr_mat)))

    # Empirical average residual variance scaling factor for SE внутри bootstrap
    rng = np.random.default_rng(seed)
    E_idx = np.where(elig_mask)[0]
    E_cnt = len(E_idx)

    # Approximate resid_var per player from match dispersion for fast vectorized DL inside bootstrap
    tot_xx = Sxx.sum(axis=0)
    tot_xy = Sxy.sum(axis=0)
    beta_0 = np.where(tot_xx > 1e-9, tot_xy / np.maximum(tot_xx, 1e-9), 0.0)
    U_m = Sxy - Sxx * beta_0[None, :]
    sum_u2_0 = (U_m ** 2).sum(axis=0)
    base_v = np.where(tot_xx > 1e-6, (span ** 2) * sum_u2_0 / np.maximum(tot_xx ** 2, 1e-9), 400.0)
    pool_mask = np.array([pid in set(pool_ids) for pid in all_pids], dtype=bool) & (tot_xx > 2.0)

    boot_deltas = np.full((n_iter, E_cnt), np.nan, dtype=float)
    boot_eb = np.full((n_iter, E_cnt), np.nan, dtype=float)
    boot_ranks = np.full((n_iter, E_cnt), np.nan, dtype=float)

    for b in range(n_iter):
        pick = rng.integers(0, M, size=M)
        bx = Sxx[pick].sum(axis=0)
        by = Sxy[pick].sum(axis=0)
        valid_p = bx > 1e-6
        d_b = np.where(valid_p, span * (by / np.maximum(bx, 1e-9)), np.nan)

        # Variance scales inversely with bx relative to original tot_xx
        v_b = np.where(valid_p & (tot_xx > 1e-6), base_v * (tot_xx / np.maximum(bx, 1e-9)), np.nan)
        pm = pool_mask & valid_p & np.isfinite(d_b) & np.isfinite(v_b) & (v_b > 1e-6)
        if pm.sum() >= 10:
            w_fe = 1.0 / v_b[pm]
            sw = np.sum(w_fe)
            mu_fe = float(np.sum(w_fe * d_b[pm]) / sw)
            Q_b = float(np.sum(w_fe * (d_b[pm] - mu_fe) ** 2))
            C_b = float(sw - np.sum(w_fe ** 2) / sw)
            tau2_b = max(0.0, (Q_b - (pm.sum() - 1)) / max(C_b, 1e-9))
            wt_b = 1.0 / (v_b[pm] + max(tau2_b, 1e-9))
            mu0_b = float(np.sum(wt_b * d_b[pm]) / np.sum(wt_b)) if tau2_b > 0 else mu_fe
        else:
            tau2_b, mu0_b = 0.0, 0.0

        w_e = np.where((tau2_b > 0) & np.isfinite(v_b[E_idx]) & (v_b[E_idx] > 0), tau2_b / (tau2_b + v_b[E_idx]), 0.0)
        eb_b = np.where(np.isfinite(d_b[E_idx]), mu0_b + w_e * (d_b[E_idx] - mu0_b), mu0_b)

        boot_deltas[b] = d_b[E_idx]
        boot_eb[b] = eb_b
        # Rank descending (1 = highest EB delta in bootstrap draw b)
        order = np.argsort(-np.where(np.isfinite(eb_b), eb_b, -1e9), kind="mergesort")
        ranks_b = np.empty(E_cnt, dtype=float)
        ranks_b[order] = np.arange(1, E_cnt + 1, dtype=float)
        boot_ranks[b] = ranks_b

    rows = []
    for j, pid_idx in enumerate(E_idx):
        pid = int(all_pids[pid_idx])
        dd = boot_deltas[:, j]
        dd = dd[np.isfinite(dd)]
        rk = boot_ranks[:, j]
        rows.append({
            "player_id": pid,
            "boot_mean_delta": float(np.mean(dd)) if len(dd) else np.nan,
            "boot_se_delta": float(np.std(dd, ddof=1)) if len(dd) > 1 else np.nan,
            "boot_ci_low": float(np.percentile(dd, 2.5)) if len(dd) else np.nan,
            "boot_ci_high": float(np.percentile(dd, 97.5)) if len(dd) else np.nan,
            "boot_prob_pos": float(np.mean(dd > 0.0)) if len(dd) else np.nan,
            "boot_rank_mean": float(np.mean(rk)),
            "boot_rank_median": float(np.median(rk)),
            "boot_rank_ci_low": int(np.percentile(rk, 2.5)),
            "boot_rank_ci_high": int(np.percentile(rk, 97.5)),
            "prob_top_10": float(np.mean(rk <= 10.0)),
        })

    return pd.DataFrame(rows), {
        "bootstrap_iter": int(n_iter),
        "n_matches_resampled": int(M),
        "mean_shared_matches_per_pair": round(mean_shared_matches, 2),
        "mean_abs_pairwise_match_corr": round(mean_abs_match_corr, 4),
    }
