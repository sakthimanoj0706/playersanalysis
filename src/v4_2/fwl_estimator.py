"""V4.2 Complete Penalized FWL Estimator, Option B Hierarchical REML Model, and Valid Bootstrap.

Fixes the two P0 defects identified in V4.1:
1. Complete Frisch-Waugh-Lovell (FWL) partial regression:
   Residualizes BOTH outcome y AND the full common-support player pressure
   interaction matrix W against the complete nuisance design
   Z = [state, match, player, opponent], avoiding V4.1's incomplete
   stratum-only predictor centering.
   Also provides exact unpenalized OLS verification (for synthetic tests) and
   Option B joint hierarchical REML random-slope comparison.
2. Consistent REML bootstrap without deterministic tie-breaking:
   Uses exact REML heterogeneity estimation inside every bootstrap replicate,
   handles tied EB scores with average ranks and fractional Top-10 membership,
   exports all 5 required uncertainty intervals, and validates the
   nuisance-orthogonalized match-cluster score bootstrap against full nuisance
   + pressure-proxy refits.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import scipy.linalg as la
import scipy.sparse as sp
from scipy.stats import rankdata

from src.v4_1.eligibility_and_validation import V41_OPERATIONAL_PRECISION_GATE
from src.v4_1.hierarchical_v41 import estimate_heterogeneity


def _stratified_cs_flags(
    df: pd.DataFrame,
    player_col: str,
    p_col: str,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
) -> Tuple[np.ndarray, pd.Series]:
    """Identify common-support strata (player x match_format) having >=1 hi AND >=1 lo delivery."""
    stratum_col = "match_format" if "match_format" in df.columns else None
    p_vals = df[p_col].values.astype(float)
    tmp = pd.DataFrame(
        {
            "player": df[player_col].values,
            "stratum": df[stratum_col].astype(str).values if stratum_col else np.full(len(df), "ALL"),
            "match_id": df["match_id"].values,
            "is_hi": p_vals >= hi_thr,
            "is_lo": p_vals <= lo_thr,
        }
    )
    ps = tmp.groupby(["player", "stratum"], sort=False).agg(nh=("is_hi", "sum"), nl=("is_lo", "sum"))
    cs_pairs = set(ps[(ps["nh"] >= 1) & (ps["nl"] >= 1)].index.tolist())
    row_pairs = list(zip(tmp["player"].values, tmp["stratum"].values))
    cs_mask = np.fromiter((pair in cs_pairs for pair in row_pairs), dtype=bool, count=len(tmp))
    cs_matches = tmp.loc[cs_mask].groupby("player", sort=False)["match_id"].nunique()
    return cs_mask, cs_matches


def _build_state_matrix(df: pd.DataFrame) -> sp.csr_matrix:
    """Build nuisance contextual state matrix X_state WITHOUT pressure decile p_dec.

    Includes intercept + (innings | phase | match_format | season) contextual indicators.
    Deliberately excludes p_dec so complete FWL residualization does not strip continuous
    pressure signal from W.
    """
    n = len(df)
    parts = [df["innings"].astype(str)]
    for col in ("phase", "match_format", "season"):
        if col in df.columns:
            parts.append(df[col].astype(str))
    skey = parts[0]
    for p_s in parts[1:]:
        skey = skey + "|" + p_s
    sc = pd.Categorical(skey)
    rows = np.arange(n, dtype=np.int32)
    X_grp = sp.csr_matrix((np.ones(n, dtype=np.float64), (rows, sc.codes)), shape=(n, len(sc.categories)))
    X_int = sp.csr_matrix(np.ones((n, 1), dtype=np.float64))
    return sp.hstack([X_int, X_grp[:, 1:] if X_grp.shape[1] > 1 else sp.csr_matrix((n, 0))], format="csr")


def _compute_zone_raw_stats(
    df: pd.DataFrame,
    player_col: str,
    p_col: str,
    y_col: str,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
) -> pd.DataFrame:
    """Compute exact hi (>=hi_thr), lo (<=lo_thr), and all-non-high (<hi_thr) exposure & raw means."""
    work = df[[player_col, "match_id", "weight", p_col, y_col]].copy()
    work["wy"] = work["weight"] * work[y_col]
    work["is_hi"] = work[p_col] >= hi_thr
    work["is_lo"] = work[p_col] <= lo_thr
    work["is_nonhi"] = work[p_col] < hi_thr

    out = work.groupby(player_col, sort=False).agg(
        total_balls=("weight", "sum"),
        total_matches=("match_id", "nunique"),
        raw_overall_perf=("wy", "sum"),
    )
    out["raw_overall_perf"] = out["raw_overall_perf"] / out["total_balls"].clip(lower=1e-9)

    for label, flag in [("hi", "is_hi"), ("lo", "is_lo"), ("nonhi", "is_nonhi")]:
        sub = work[work[flag]]
        if len(sub) == 0:
            out[f"n_{label}"] = 0.0
            out[f"{label}_matches"] = 0
            out[f"raw_{label}_perf"] = np.nan
            continue
        agg = sub.groupby(player_col, sort=False).agg(
            w=("weight", "sum"),
            m=("match_id", "nunique"),
            wy=("wy", "sum"),
        )
        out[f"n_{label}"] = out.index.map(agg["w"]).fillna(0.0).astype(float)
        out[f"{label}_matches"] = out.index.map(agg["m"]).fillna(0).astype(int)
        perf = agg["wy"] / agg["w"].clip(lower=1e-9)
        out[f"raw_{label}_perf"] = out.index.map(perf).astype(float)

    out["raw_hi_minus_lo_delta"] = out["raw_hi_minus_lo"] = (
        out["raw_hi_perf"] - out["raw_lo_perf"]
    )
    out["raw_hi_minus_all_non_high_delta"] = out["raw_hi_perf"] - out["raw_nonhi_perf"]
    out = out.reset_index().rename(columns={player_col: "player_id"})
    return out


def _build_full_nuisance_and_interaction(
    df: pd.DataFrame,
    player_col: str,
    opp_col: str,
    p_col: str,
    y_col: str,
    lam_state: float,
    lam_match: float,
    lam_player: float,
    lam_opp: float,
    use_cs_mask: bool = True,
    p_center: float = 0.5,
) -> Dict[str, Any]:
    """Assemble Z = [state, match, player, opp], penalties Lambda_Z, and pressure interaction W."""
    cs_mask, cs_matches = _stratified_cs_flags(df, player_col, p_col) if use_cs_mask else (
        np.ones(len(df), dtype=bool),
        df.groupby(player_col)["match_id"].nunique(),
    )

    p_vals = df[p_col].values.astype(float)
    w_obs = df["weight"].values.astype(float)
    y_vals = df[y_col].values.astype(float)
    match_codes, match_uniques = pd.factorize(df["match_id"], sort=False)

    X_state = _build_state_matrix(df)
    n = len(df)
    p_codes, p_uniques = pd.factorize(df[player_col], sort=False)
    o_codes, o_uniques = pd.factorize(df[opp_col], sort=False)
    rows = np.arange(n, dtype=np.int32)
    ones = np.ones(n, dtype=np.float64)
    X_match = sp.csr_matrix((ones, (rows, match_codes)), shape=(n, len(match_uniques)))
    X_player = sp.csr_matrix((ones, (rows, p_codes)), shape=(n, len(p_uniques)))
    X_opp = sp.csr_matrix((ones, (rows, o_codes)), shape=(n, len(o_uniques)))

    if lam_state == 0.0 and lam_match == 0.0 and lam_player == 0.0 and lam_opp == 0.0:
        # Rank-full unpenalized nuisance design for exact OLS comparison on synthetic/small data
        # Keep intercept inside X_state, drop first column of match/player/opp to avoid dummy trap.
        Z = sp.hstack(
            [
                X_state,
                X_match[:, 1:] if X_match.shape[1] > 1 else sp.csr_matrix((n, 0)),
                X_player[:, 1:] if X_player.shape[1] > 1 else sp.csr_matrix((n, 0)),
                X_opp[:, 1:] if X_opp.shape[1] > 1 else sp.csr_matrix((n, 0)),
            ],
            format="csr",
        )
        pen = np.zeros(Z.shape[1], dtype=np.float64)
    else:
        Z = sp.hstack([X_state, X_match, X_player, X_opp], format="csr")
        pen = np.concatenate(
            [
                np.full(X_state.shape[1], float(lam_state), dtype=np.float64),
                np.full(X_match.shape[1], float(lam_match), dtype=np.float64),
                np.full(X_player.shape[1], float(lam_player), dtype=np.float64),
                np.full(X_opp.shape[1], float(lam_opp), dtype=np.float64),
            ]
        )
        pen[0] = 0.0  # Never shrink the global intercept

    # Common-support player pressure matrix W: only rows inside common-support strata
    # and players who actually have >= 1 common-support row
    cs_pids = pd.unique(df.loc[cs_mask, player_col])
    pid_to_wcol = {pid: idx for idx, pid in enumerate(cs_pids)}
    w_row_mask = cs_mask & df[player_col].isin(pid_to_wcol).values
    w_rows = np.flatnonzero(w_row_mask).astype(np.int32)
    w_cols = df.iloc[w_rows][player_col].map(pid_to_wcol).values.astype(np.int32)
    w_data = (p_vals[w_rows] - p_center).astype(np.float64)
    W = sp.csr_matrix((w_data, (w_rows, w_cols)), shape=(n, len(cs_pids)))

    return {
        "Z": Z,
        "pen": pen,
        "W": W,
        "y": y_vals,
        "w_obs": w_obs,
        "p_vals": p_vals,
        "match_codes": match_codes,
        "match_uniques": match_uniques,
        "cs_pids": cs_pids,
        "cs_matches": cs_matches,
        "cs_mask": cs_mask,
        "p_uniques": p_uniques,
        "p_codes": p_codes,
        "block_dims": {
            "state": int(X_state.shape[1]),
            "match": int(X_match.shape[1]),
            "player": int(X_player.shape[1]),
            "opp": int(X_opp.shape[1]),
        },
    }


def _solve_complete_penalized_fwl(
    design: Dict[str, Any],
    span: float = 0.75,
    cluster_scale: float = 1.0,
) -> Dict[str, Any]:
    """Solve Schur-exact penalized FWL + residualized-W comparison + CR1 match sandwich."""
    Z: sp.csr_matrix = design["Z"]
    pen: np.ndarray = design["pen"]
    W: sp.csr_matrix = design["W"]
    y: np.ndarray = design["y"]
    w_obs: np.ndarray = design["w_obs"]
    match_codes: np.ndarray = design["match_codes"]
    M = len(design["match_uniques"])
    N = Z.shape[0]
    K = W.shape[1]

    sqrt_w = np.sqrt(np.clip(w_obs, 0.0, None))
    Dw = sp.diags(w_obs)
    Zw = Dw @ Z  # w * Z

    unpenalized = bool(np.all(pen == 0.0))

    ZtDZ = (Z.T @ Zw).toarray()
    A = ZtDZ + np.diag(pen)

    ZtDy = Z.T @ (w_obs * y)
    B_W = (Zw.T @ W).toarray()  # P_Z x K
    W_col_sq = np.asarray((W.multiply(W).T @ w_obs)).ravel()  # diagonal of W^T D W
    WtDy = np.asarray(W.T @ (w_obs * y)).ravel()

    if unpenalized and N <= 10000 and Z.shape[1] <= 1000:
        # Exact linear least squares on weighted design (avoids squaring condition number on Z^T D Z)
        sqrt_w_col = sqrt_w[:, None]
        Zw_half = Z.toarray() * sqrt_w_col
        yw_half = y * sqrt_w
        Ww_half = W.toarray() * sqrt_w_col
        theta_y, *_ = la.lstsq(Zw_half, yw_half, cond=1e-12)
        Theta_W, *_ = la.lstsq(Zw_half, Ww_half, cond=1e-12)
    elif unpenalized:
        # Minimum-norm solve if Z is large and unpenalized
        theta_y, *_ = la.lstsq(A, ZtDy, cond=1e-11)
        Theta_W, *_ = la.lstsq(A, B_W, cond=1e-11)
    else:
        c, low = la.cho_factor(A, check_finite=False)
        theta_y = la.cho_solve((c, low), ZtDy, check_finite=False)
        Theta_W = la.cho_solve((c, low), B_W, check_finite=False)

    # Exact nuisance-residualized y_tilde = y - Z theta_y
    y_tilde = y - Z @ theta_y

    # 1) Schur-exact normal matrix G_schur = W^T D W_tilde = W^T D (I - H_Z) W
    G_schur = np.diag(W_col_sq) - (B_W.T @ Theta_W)
    G_schur = 0.5 * (G_schur + G_schur.T)
    rhs_schur = WtDy - (B_W.T @ theta_y)

    # 2) Pure residual-on-residual W_tilde^T D W_tilde and W_tilde^T D y_tilde (identity check vs unpenalized)
    # W_tilde^T D W_tilde = W^T D W - 2 B_W^T Theta_W + Theta_W^T (Z^T D Z) Theta_W
    G_res = np.diag(W_col_sq) - 2.0 * (B_W.T @ Theta_W) + (Theta_W.T @ (ZtDZ @ Theta_W))
    G_res = 0.5 * (G_res + G_res.T)
    rhs_res = WtDy - (B_W.T @ theta_y) - (Theta_W.T @ ZtDy) + (Theta_W.T @ (ZtDZ @ theta_y))

    # Guard degenerate columns (players with zero within-nuisance variation)
    diag_g = np.diag(G_schur)
    valid_cols = diag_g > 1e-8
    beta_fwl = np.full(K, np.nan, dtype=np.float64)
    beta_res = np.full(K, np.nan, dtype=np.float64)
    G_inv_sub = None
    beta_sub = np.zeros(int(valid_cols.sum()), dtype=np.float64)

    if np.any(valid_cols):
        Gs = G_schur[np.ix_(valid_cols, valid_cols)]
        rs = rhs_schur[valid_cols]
        # Small ridge only if strictly singular due to disconnected component when pen==0
        try:
            L_g, low_g = la.cho_factor(Gs, check_finite=False)
            beta_sub = la.cho_solve((L_g, low_g), rs, check_finite=False)
            G_inv_sub = la.cho_solve((L_g, low_g), np.eye(Gs.shape[0]), check_finite=False)
        except la.LinAlgError:
            beta_sub, *_ = la.lstsq(Gs, rs, cond=1e-11)
            G_inv_sub = la.pinv(Gs, rtol=1e-11)
        beta_fwl[valid_cols] = beta_sub

        G_r_sub = G_res[np.ix_(valid_cols, valid_cols)]
        r_r_sub = rhs_res[valid_cols]
        b_r_sub, *_ = la.lstsq(G_r_sub, r_r_sub, cond=1e-11)
        beta_res[valid_cols] = b_r_sub

    # Recover exact nuisance coefficients theta_hat = theta_y - Theta_W @ beta
    theta_hat = theta_y.copy()
    if np.any(valid_cols):
        theta_hat = theta_y - Theta_W[:, valid_cols] @ beta_sub

    e = y - (Z @ theta_hat)
    if np.any(valid_cols):
        beta_clean = np.where(valid_cols, beta_fwl, 0.0)
        e = e - (W @ beta_clean)

    # Residual scale sigma^2
    df_eff = max(N - (int(Z.shape[1]) + int(valid_cols.sum())) if unpenalized else N - int(valid_cols.sum()), 1)
    sigma2 = float(np.sum(w_obs * (e ** 2)) / df_eff)

    # Match-level orthogonalized score vectors:
    # s_tilde_m = (W_m - Z_m Theta_W)^T D_m e_m = W_m^T D_m e_m - (Z_m^T D_m e_m)^T Theta_W
    we = w_obs * e
    M_idx = sp.csr_matrix(
        (np.ones(N, dtype=np.float64), (match_codes, np.arange(N, dtype=np.int32))),
        shape=(M, N),
    )
    W_weighted = W.multiply(we[:, None])
    Z_weighted = Z.multiply(we[:, None])
    Wm_e = (M_idx @ W_weighted).toarray()  # M x K
    Zm_e = (M_idx @ Z_weighted).toarray()  # M x P_Z
    S_tilde = Wm_e - (Zm_e @ Theta_W)  # M x K exact match scores!

    se_fwl = np.full(K, np.nan, dtype=np.float64)
    U_match = np.zeros((M, K), dtype=np.float64)
    cov_cr = np.zeros((K, K), dtype=np.float64)
    if np.any(valid_cols) and G_inv_sub is not None:
        S_sub = S_tilde[:, valid_cols]
        cs_matches_vec = np.array([int(design["cs_matches"].get(pid, 2)) for pid in design["cs_pids"]], dtype=np.float64)
        mi_sub = cs_matches_vec[valid_cols]
        cr1_vec = (np.maximum(mi_sub, 2.0) / np.maximum(mi_sub - 1.0, 1.0)) * cluster_scale
        meat_sub = S_sub.T @ S_sub
        cov_unscaled = G_inv_sub @ meat_sub @ G_inv_sub.T
        se_cr_raw = np.sqrt(np.clip(np.diag(cov_unscaled), 1e-12, None))
        se_cr_adj = se_cr_raw * np.sqrt(cr1_vec)
        naive_se_sub = np.sqrt(np.clip(sigma2 * np.diag(G_inv_sub), 1e-12, None))
        se_final_sub = np.maximum(se_cr_adj, naive_se_sub)
        scale_factor = se_final_sub / np.maximum(se_cr_raw, 1e-12)

        cov_sub = cov_unscaled * np.outer(scale_factor, scale_factor)
        cov_cr[np.ix_(valid_cols, valid_cols)] = cov_sub
        se_fwl[valid_cols] = se_final_sub
        # U_match calibrated so sum_m U_{m,j}^2 == (se_fwl[j] * span)^2 identically
        U_sub = (S_sub @ G_inv_sub.T) * (scale_factor[None, :] * span)
        U_match[:, valid_cols] = U_sub

    # Regularization gap metrics between Schur-exact penalized FWL and residual-on-residual
    reg_gap = np.abs(beta_fwl[valid_cols] - beta_res[valid_cols]) * span if np.any(valid_cols) else np.array([0.0])

    return {
        "beta_fwl": beta_fwl,
        "beta_res": beta_res,
        "delta_fwl": beta_fwl * span,
        "delta_res": beta_res * span,
        "se_fwl": se_fwl * span,
        "theta_hat": theta_hat,
        "theta_y": theta_y,
        "y_tilde": y_tilde,
        "e": e,
        "sigma2": sigma2,
        "G_schur": G_schur,
        "G_inv_sub": G_inv_sub,
        "valid_cols": valid_cols,
        "S_tilde": S_tilde,
        "U_match": U_match,
        "cov_cr_delta": cov_cr * (span ** 2),
        "reg_gap_max_delta": float(np.max(reg_gap)),
        "reg_gap_median_delta": float(np.median(reg_gap)),
        "n_obs": int(N),
        "n_matches": int(M),
        "n_cs_players": int(K),
        "n_valid_players": int(valid_cols.sum()),
        "span": float(span),
    }


def _apply_reml_eb(
    delta: np.ndarray,
    se: np.ndarray,
    pool_mask: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    """Run strictly consistent REML Empirical Bayes pooling over well-identified pool estimates."""
    finite = np.isfinite(delta) & np.isfinite(se) & (se > 0.0) & (se < 500.0)
    k = len(delta)
    eb = np.full(k, np.nan, dtype=np.float64)
    eb_sd = np.full(k, np.nan, dtype=np.float64)
    w = np.full(k, np.nan, dtype=np.float64)
    if finite.sum() < 2:
        het = {"mu0": 0.0, "tau2": 0.0, "tau": 0.0, "Q": 0.0, "df": 0, "I2": 0.0, "k_eff": int(finite.sum())}
        return eb, eb_sd, w, het

    if pool_mask is not None and int((finite & pool_mask).sum()) >= 6:
        reml_mask = finite & pool_mask
    else:
        reml_mask = finite

    het = estimate_heterogeneity(delta[reml_mask], se[reml_mask], method="reml")
    tau2 = max(float(het["tau2"]), 0.0)
    mu0 = float(het["mu0"])

    if tau2 <= 1e-12:
        w[finite] = 0.0
        eb[finite] = mu0
        eb_sd[finite] = 0.0
    else:
        w_f = tau2 / (tau2 + (se[finite] ** 2))
        w[finite] = w_f
        eb[finite] = w_f * delta[finite] + (1.0 - w_f) * mu0
        eb_sd[finite] = np.sqrt(np.clip(w_f * (se[finite] ** 2), 0.0, None))
    return eb, eb_sd, w, het


def fit_v42_option_a_fwl(
    df: pd.DataFrame,
    player_col: str,
    opp_col: str,
    p_col: str,
    y_col: str,
    lam_state: float = 60.0,
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    span: float = 0.75,
    hi_thr: float = 0.75,
    lo_thr: float = 0.25,
    eligibility_gate: Optional[Dict[str, Any]] = None,
    use_cs_mask: bool = True,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Option A: Complete Penalized FWL Partial Regression + REML Empirical Bayes."""
    gate = eligibility_gate or V41_OPERATIONAL_PRECISION_GATE
    design = _build_full_nuisance_and_interaction(
        df=df,
        player_col=player_col,
        opp_col=opp_col,
        p_col=p_col,
        y_col=y_col,
        lam_state=lam_state,
        lam_match=lam_match,
        lam_player=lam_player,
        lam_opp=lam_opp,
        use_cs_mask=use_cs_mask,
    )
    fwl = _solve_complete_penalized_fwl(design, span=span)
    zones = _compute_zone_raw_stats(df, player_col, p_col, y_col, hi_thr=hi_thr, lo_thr=lo_thr)
    z_map = zones.set_index("player_id")
    cs_pids = design["cs_pids"]
    cs_nhi = np.array([float(z_map.loc[p, "n_hi"]) if p in z_map.index else 0.0 for p in cs_pids])
    cs_nlo = np.array([float(z_map.loc[p, "n_lo"]) if p in z_map.index else 0.0 for p in cs_pids])
    cs_mat = np.array([int(design["cs_matches"].get(p, 0)) for p in cs_pids])
    pool_mask_cs = (
        (cs_nhi >= 30.0)
        & (cs_nlo >= 30.0)
        & (cs_mat >= 5)
        & np.isfinite(fwl["se_fwl"])
        & (fwl["se_fwl"] <= 30.0)
    )

    eb, eb_sd, eb_w, het = _apply_reml_eb(fwl["delta_fwl"], fwl["se_fwl"], pool_mask=pool_mask_cs)

    fwl_df = pd.DataFrame(
        {
            "player_id": cs_pids,
            "beta_fwl": fwl["beta_fwl"],
            "beta_res_fwl": fwl["beta_res"],
            "delta_unshrunk": fwl["delta_fwl"],
            "delta_res_fwl": fwl["delta_res"],
            "se_delta": fwl["se_fwl"],
            "eb_weight": eb_w,
            "eb_delta": eb,
            "eb_vs_pop_mean_delta": eb - float(het["mu0"]),
            "eb_cond_sd": eb_sd,
            "lower_confidence_bound": eb - 1.96 * eb_sd,
            "upper_confidence_bound": eb + 1.96 * eb_sd,
            "eb_cond_ci_low": eb - 1.96 * eb_sd,
            "eb_cond_ci_high": eb + 1.96 * eb_sd,
            "cs_matches": cs_mat,
        }
    )

    out = zones.merge(fwl_df, on="player_id", how="left")

    # Apply operational precision floor (honestly documented, NOT called empirically optimal)
    min_hi = gate.get("min_hi_balls", gate.get("min_n_hi", 50))
    min_lo = gate.get("min_lo_balls", gate.get("min_n_lo", 30))
    eligible = (
        (out["n_hi"] >= min_hi)
        & (out["n_lo"] >= min_lo)
        & (out["cs_matches"] >= gate["min_cs_matches"])
        & out["se_delta"].notna()
        & (out["se_delta"] <= gate["max_se_delta"])
        & out["eb_delta"].notna()
    )
    out["eligible"] = eligible
    out["eligibility_tier"] = np.where(
        out["eligible"],
        "ELIGIBLE_OPERATIONAL_FLOOR",
        np.where(out["delta_unshrunk"].notna(), "LOW_PRECISION_OR_EXPOSURE", "NO_COMMON_SUPPORT"),
    )

    meta = {
        "estimator": "OPTION_A_COMPLETE_PENALIZED_FWL_REML",
        "het": het,
        "pool_mask_cs": pool_mask_cs,
        "n_cs_players": fwl["n_cs_players"],
        "n_valid_players": fwl["n_valid_players"],
        "n_pool_players": int(pool_mask_cs.sum()),
        "n_eligible": int(out["eligible"].sum()),
        "reg_gap_max_delta": fwl["reg_gap_max_delta"],
        "reg_gap_median_delta": fwl["reg_gap_median_delta"],
        "sigma2": fwl["sigma2"],
        "lam_state": lam_state,
        "lam_match": lam_match,
        "lam_player": lam_player,
        "lam_opp": lam_opp,
        "span": span,
        "design": design,
        "fwl": fwl,
    }
    return out, meta


def fit_v42_option_b_reml_joint(
    design: Dict[str, Any],
    fwl: Dict[str, Any],
    span: float = 0.75,
    max_em_iter: int = 25,
    tol: float = 1e-4,
    het_init: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Option B: Proper Joint Hierarchical Random-Slope Model with Empirical REML/EM Variance Estimation.

    Instead of setting an arbitrary fixed Ridge lam_slope (like 3500), updates
    lam_slope = sigma^2 / tau2_beta empirically from the between-player slope
    heterogeneity and cluster-calibrated posterior variance.
    """
    valid = fwl["valid_cols"]
    K_all = len(design["cs_pids"])
    G_sub = fwl["G_schur"][np.ix_(valid, valid)]
    beta_fwl_sub = fwl["beta_fwl"][valid]
    r_sub = G_sub @ beta_fwl_sub
    K = int(valid.sum())
    if K < 2:
        return pd.DataFrame({"player_id": design["cs_pids"], "eb_delta_opt_b": np.nan}), {"tau2_delta": 0.0}

    # Estimate initial tau2_beta from Option A REML
    if het_init is None:
        _, _, _, het0 = _apply_reml_eb(fwl["delta_fwl"], fwl["se_fwl"])
    else:
        het0 = het_init
    tau2_beta = max(float(het0["tau2"]) / (span ** 2), 1e-6)
    sigma2 = max(float(fwl["sigma2"]), 1e-6)

    # Cluster inflation factor per player from Option A sandwich vs model variance
    G_inv_diag = np.clip(np.diag(fwl["G_inv_sub"]), 1e-12, None)
    var_cr_beta = np.clip((fwl["se_fwl"][valid] / span) ** 2, 1e-12, None)
    deff = np.clip(var_cr_beta / (sigma2 * G_inv_diag), 1.0, 25.0)
    median_deff = float(np.median(deff))

    mu_beta = float(np.median(beta_fwl_sub))
    beta_post = np.full(K, mu_beta, dtype=np.float64)
    post_sd = np.zeros(K, dtype=np.float64)

    for it in range(max_em_iter):
        lam_slope = min(sigma2 * median_deff / max(tau2_beta, 1e-10), 1e9)
        H = G_sub + lam_slope * np.eye(K)
        H_inv = la.inv(H)
        beta_new = H_inv @ (r_sub + lam_slope * np.full(K, mu_beta))
        post_var_diag = np.clip(sigma2 * median_deff * np.diag(H_inv), 0.0, None)
        post_sd = np.sqrt(post_var_diag)

        mu_new = float(np.mean(beta_new))
        # Empirical variance component update: E[sum((beta_i - mu)^2)] / K - posterior trace term
        tau2_new = float(np.mean((beta_new - mu_new) ** 2 + post_var_diag))
        if np.max(np.abs(beta_new - beta_post)) * span < tol and abs(tau2_new - tau2_beta) * (span ** 2) < tol:
            beta_post = beta_new
            mu_beta = mu_new
            tau2_beta = tau2_new
            break
        beta_post = beta_new
        mu_beta = mu_new
        tau2_beta = max(tau2_new, 0.0)

    delta_opt_b = np.full(K_all, np.nan, dtype=np.float64)
    sd_opt_b = np.full(K_all, np.nan, dtype=np.float64)
    delta_opt_b[valid] = beta_post * span
    sd_opt_b[valid] = post_sd * span

    out = pd.DataFrame(
        {
            "player_id": design["cs_pids"],
            "eb_delta_opt_b": delta_opt_b,
            "eb_sd_opt_b": sd_opt_b,
        }
    )
    meta = {
        "estimator": "OPTION_B_JOINT_HIERARCHICAL_REML_EM",
        "mu_delta": float(mu_beta * span),
        "tau2_delta": float(tau2_beta * (span ** 2)),
        "tau_delta": float(np.sqrt(max(tau2_beta, 0.0)) * span),
        "implied_lam_slope": float(sigma2 * median_deff / max(tau2_beta, 1e-10)),
        "median_cluster_deff": median_deff,
        "em_iters": it + 1,
    }
    return out, meta


def fractional_top_k_membership(scores: np.ndarray, k: int = 10) -> np.ndarray:
    """Exact tie-aware Top-K membership summing to min(K, valid_count) without player_id tie-breaks.

    If m players tie at the cutoff boundary leaving r < m slots remaining, each receives r / m.
    """
    n = len(scores)
    mem = np.zeros(n, dtype=np.float64)
    valid = np.isfinite(scores)
    if not np.any(valid):
        return mem
    v_idx = np.flatnonzero(valid)
    v_scores = scores[v_idx]
    # Round tiny floating-point noise at 1e-12 so mathematically identical EB ties (tau2==0) tie cleanly
    rounded = np.round(v_scores, 10)
    uniq_desc = np.sort(np.unique(rounded))[::-1]
    remaining = float(min(k, len(v_idx)))
    for val in uniq_desc:
        if remaining <= 0.0:
            break
        tie_mask = rounded == val
        m = int(np.sum(tie_mask))
        if m <= remaining:
            mem[v_idx[tie_mask]] = 1.0
            remaining -= m
        else:
            mem[v_idx[tie_mask]] = remaining / float(m)
            remaining = 0.0
    return mem


def average_ranks_desc(scores: np.ndarray) -> np.ndarray:
    """Exact tie-aware average rank (highest score = rank 1), never breaking ties by player_id."""
    out = np.full(len(scores), np.nan, dtype=np.float64)
    valid = np.isfinite(scores)
    if not np.any(valid):
        return out
    rounded = np.round(scores[valid], 10)
    out[valid] = rankdata(-rounded, method="average")
    return out


def run_v42_match_cluster_bootstrap(
    fwl_df: pd.DataFrame,
    fwl: Dict[str, Any],
    eligible_mask: Optional[np.ndarray] = None,
    pool_mask: Optional[np.ndarray] = None,
    n_iter: int = 2000,
    seed: int = 42,
    top_k: int = 10,
) -> pd.DataFrame:
    """Valid match-cluster bootstrap using REML in every replicate and exact average/fractional ranks.

    Exports all 5 required uncertainty summaries:
      1. unshrunk_boot_ci_low / unshrunk_boot_ci_high
      2. eb_cond_ci_low / eb_cond_ci_high (via primary model)
      3. eb_boot_ci_low / eb_boot_ci_high
      4. boot_rank_ci_low / boot_rank_ci_high (+ boot_rank_median)
      5. prob_top_10 (+ mcse_prob_top_10, boot_iters)
    """
    rng = np.random.default_rng(seed)
    U: np.ndarray = fwl["U_match"]  # M x K
    M, K = U.shape
    delta0 = fwl["delta_fwl"].copy()
    se0 = fwl["se_fwl"].copy()
    valid = fwl["valid_cols"] & np.isfinite(delta0) & np.isfinite(se0) & (se0 < 500.0)

    if eligible_mask is None:
        elig_sub = np.ones(K, dtype=bool)
    else:
        elig_sub = np.asarray(eligible_mask, dtype=bool)

    if pool_mask is not None and int((valid & pool_mask).sum()) >= 6:
        reml_pool = np.asarray(pool_mask, dtype=bool)[valid]
    else:
        reml_pool = np.ones(int(valid.sum()), dtype=bool)

    U_v = U[:, valid]
    U_v_sq = U_v ** 2
    d0_v = delta0[valid]
    el_v = elig_sub[valid]
    Kv = int(valid.sum())

    delta_draws = np.full((n_iter, K), np.nan, dtype=np.float64)
    eb_draws = np.full((n_iter, K), np.nan, dtype=np.float64)
    rank_draws = np.full((n_iter, K), np.nan, dtype=np.float64)
    top10_acc = np.zeros(K, dtype=np.float64)
    tau2_draws = np.zeros(n_iter, dtype=np.float64)

    p_uni = np.full(M, 1.0 / max(M, 1), dtype=np.float64)
    for b in range(n_iter):
        counts = rng.multinomial(M, p_uni).astype(np.float64)
        diff = counts - 1.0
        d_b = d0_v + diff @ U_v
        # Resampled cluster sandwich SE vector using cluster multiplicities (floored to prevent zero-var blowup)
        var_b = counts @ U_v_sq
        # Ensure players omitted in rare extreme draws fall back cleanly to valid variance floor
        se_b = np.sqrt(np.maximum(var_b, 0.25 * (se0[valid] ** 2)))
        het_b = estimate_heterogeneity(d_b[reml_pool], se_b[reml_pool], method="reml")
        tau2_b = max(float(het_b["tau2"]), 0.0)
        mu0_b = float(het_b["mu0"])
        tau2_draws[b] = tau2_b
        if tau2_b <= 1e-12:
            eb_b = np.full(Kv, mu0_b, dtype=np.float64)
        else:
            w_b = tau2_b / (tau2_b + se_b ** 2)
            eb_b = w_b * d_b + (1.0 - w_b) * mu0_b

        delta_draws[b, valid] = d_b
        eb_draws[b, valid] = eb_b

        # Rank strictly among eligible players using average ranks and fractional Top-K membership
        eb_for_rank = np.where(el_v, eb_b, np.nan)
        r_b = average_ranks_desc(eb_for_rank)
        t_b = fractional_top_k_membership(eb_for_rank, k=top_k)
        rank_draws[b, valid] = r_b
        top10_acc[valid] += t_b

    prob_top10 = top10_acc / float(n_iter)
    prob_top10[~elig_sub] = np.nan
    mcse = np.sqrt(np.clip(prob_top10 * (1.0 - prob_top10), 0.0, 1.0) / float(n_iter))

    unsh_lo = np.full(K, np.nan, dtype=np.float64)
    unsh_hi = np.full(K, np.nan, dtype=np.float64)
    eb_lo = np.full(K, np.nan, dtype=np.float64)
    eb_hi = np.full(K, np.nan, dtype=np.float64)
    rk_lo = np.full(K, np.nan, dtype=np.float64)
    rk_med = np.full(K, np.nan, dtype=np.float64)
    rk_hi = np.full(K, np.nan, dtype=np.float64)

    if np.any(valid):
        unsh_lo[valid], unsh_hi[valid] = np.nanpercentile(delta_draws[:, valid], [2.5, 97.5], axis=0)
        eb_lo[valid], eb_hi[valid] = np.nanpercentile(eb_draws[:, valid], [2.5, 97.5], axis=0)
    el_valid = valid & elig_sub
    if np.any(el_valid):
        rk_lo[el_valid], rk_med[el_valid], rk_hi[el_valid] = np.nanpercentile(
            rank_draws[:, el_valid], [2.5, 50.0, 97.5], axis=0
        )

    res = pd.DataFrame(
        {
            "player_id": fwl_df["player_id"].values,
            "unshrunk_boot_ci_low": unsh_lo,
            "unshrunk_boot_ci_high": unsh_hi,
            "eb_boot_ci_low": eb_lo,
            "eb_boot_ci_high": eb_hi,
            "boot_rank_ci_low": rk_lo,
            "boot_rank_median": rk_med,
            "boot_rank_ci_high": rk_hi,
            "prob_top_10": prob_top10,
            "mcse_prob_top_10": mcse,
            "boot_iters": int(n_iter),
            "boot_zero_tau2_share": float(np.mean(tau2_draws <= 1e-12)),
            "boot_tau_median": float(np.median(np.sqrt(tau2_draws))),
        }
    )
    return res


def verify_score_bootstrap_vs_full_refit(
    df: pd.DataFrame,
    player_col: str,
    opp_col: str,
    p_col: str,
    y_col: str,
    cs_pids: np.ndarray,
    fwl: Dict[str, Any],
    lam_state: float = 60.0,
    lam_match: float = 60.0,
    lam_player: float = 60.0,
    lam_opp: float = 60.0,
    span: float = 0.75,
    n_refits: int = 40,
    seed: int = 123,
    refit_proxy_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
) -> Dict[str, Any]:
    """Prove agreement between fast nuisance-orthogonalized score bootstrap and full nuisance+FWL refits.

    Resamples identical match-cluster multiplier weights c_m^* across both methods and compares
    the resulting replicate delta correlation and SE ratio.
    """
    rng = np.random.default_rng(seed)
    U = fwl["U_match"]
    K = len(cs_pids)
    valid = fwl["valid_cols"] & np.isfinite(fwl["delta_fwl"]) & (fwl["se_fwl"] < 100.0)
    delta0 = fwl["delta_fwl"]
    pids = np.asarray(cs_pids)

    full_deltas = np.full((n_refits, K), np.nan, dtype=np.float64)
    score_deltas = np.full((n_refits, K), np.nan, dtype=np.float64)

    match_uniques = pd.factorize(df["match_id"], sort=False)[1]
    base_weight = df["weight"].values.astype(np.float64)
    df_match_idx = pd.factorize(df["match_id"], sort=False)[0]
    p_uni = np.full(len(match_uniques), 1.0 / len(match_uniques))
    M = len(match_uniques)
    cr_unscale = np.sqrt(max(M - 1, 1) / max(M, 1))

    for r in range(n_refits):
        counts = rng.multinomial(M, p_uni).astype(np.float64)
        score_deltas[r, valid] = delta0[valid] + (counts - 1.0) @ (U[:, valid] * cr_unscale)

        df_r = df.copy()
        df_r["weight"] = base_weight * counts[df_match_idx]
        df_nz = df_r[df_r["weight"] > 0].copy()
        if refit_proxy_fn is not None:
            rep_idx = np.repeat(np.arange(len(df)), counts[df_match_idx].astype(int))
            df_fit = df.iloc[rep_idx].reset_index(drop=True)
            df_nz = refit_proxy_fn(df_fit, df_nz)
        design_r = _build_full_nuisance_and_interaction(
            df_nz, player_col, opp_col, p_col, y_col,
            lam_state, lam_match, lam_player, lam_opp, use_cs_mask=True,
        )
        fwl_r = _solve_complete_penalized_fwl(design_r, span=span)
        map_r = dict(zip(design_r["cs_pids"], fwl_r["delta_fwl"]))
        for idx, pid in enumerate(pids):
            if pid in map_r:
                full_deltas[r, idx] = map_r[pid]

    # Compare per-player replicate correlations and SE ratios over well-sampled players
    corrs = []
    se_ratios = []
    for j in np.flatnonzero(valid):
        ok = np.isfinite(full_deltas[:, j]) & np.isfinite(score_deltas[:, j])
        if ok.sum() < max(15, n_refits // 2):
            continue
        sd_f = np.std(full_deltas[ok, j], ddof=1)
        sd_s = np.std(score_deltas[ok, j], ddof=1)
        if sd_f > 1e-6 and sd_s > 1e-6:
            corrs.append(float(np.corrcoef(full_deltas[ok, j], score_deltas[ok, j])[0, 1]))
            se_ratios.append(float(sd_s / sd_f))

    return {
        "n_refits": int(n_refits),
        "n_players_compared": int(len(corrs)),
        "median_replicate_corr": float(np.median(corrs)) if corrs else np.nan,
        "p10_replicate_corr": float(np.percentile(corrs, 10)) if corrs else np.nan,
        "median_se_ratio_score_over_full": float(np.median(se_ratios)) if se_ratios else np.nan,
    }
