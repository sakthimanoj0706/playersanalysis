"""Configuration for SupeRR Intelligence V5.0 (Competition-Independent T20 Engine)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from src.config import PROJECT_ROOT


@dataclass(frozen=True)
class V50Config:
    """Immutable configuration for V5.0 pipeline."""

    random_seed: int = 2026
    data_dir: Path = PROJECT_ROOT / "data"
    v44_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_4"
    v43_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_3"
    v42_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_2"
    output_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v5_0"
    artifacts_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v5_0" / "artifacts"
    plots_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v5_0" / "plots"
    docs_dir: Path = PROJECT_ROOT / "docs" / "v5_0"

    # Competition scope (general engine, no franchise-specific logic)
    supported_formats: Tuple[str, ...] = ("T20", "T20I")

    # Cross-validation, OOT, bootstrap, and split-half settings
    n_cv_folds: int = 5
    oot_cutoff_year: int = 2024
    n_bootstrap: int = 200
    n_split_half: int = 50

    # Asymmetric Ridge regularization grids
    alpha_main_default: float = 250.0
    alpha_main_grid: Tuple[float, ...] = (150.0, 250.0, 500.0)
    alpha_int_grid: Tuple[float, ...] = (500.0, 750.0, 1000.0, 1500.0, 2500.0, 4000.0)
    alpha_context: float = 250.0

    # Pressure scales & thresholds
    li_global_hp_threshold: float = 1.50
    li_thresholds: Tuple[float, ...] = (1.00, 1.25, 1.50, 1.75, 2.00)

    # Post-fit primary eligibility gate (n_HP, n_Total, m_HP)
    min_hp_opportunities: int = 100
    min_total_opportunities: int = 300
    min_hp_matches: int = 12

    # Innings-specific secondary eligibility gate
    min_inn_hp_opportunities: int = 40
    min_inn_total_opportunities: int = 150
    min_inn_hp_matches: int = 5

    # Archetype non-inferiority tolerance (runs per 100 deliveries)
    clutch_non_inferiority_tol: float = 5.0

    def ensure_dirs(self) -> None:
        for d in (self.output_dir, self.artifacts_dir, self.plots_dir, self.docs_dir):
            d.mkdir(parents=True, exist_ok=True)


DEFAULT_V50_CONFIG = V50Config()
