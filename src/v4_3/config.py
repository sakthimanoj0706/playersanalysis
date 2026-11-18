"""Configuration and hyperparameters for SupeRR Intelligence V4.3."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

from src.config import PROJECT_ROOT


@dataclass(frozen=True)
class V43Config:
    """Immutable configuration for V4.3 pipeline reproducibility."""

    random_seed: int = 2026
    data_dir: Path = PROJECT_ROOT / "data"
    output_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_3"
    artifacts_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_3" / "artifacts"
    plots_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_3" / "plots"
    docs_dir: Path = PROJECT_ROOT / "docs" / "v4_3"

    # Cross-validation and chronological split settings
    n_cv_folds: int = 5
    oot_cutoff_year: int = 2024

    # Hierarchical Empirical-Bayes venue par shrinkage hyperparameters
    eb_min_innings_for_var: int = 2
    eb_default_prior_weight: float = 10.0

    # Resource curve & Expected Runs (ER) settings
    standard_t20_balls: int = 120
    er_n_bins_balls: int = 20

    # Team strength Elo-like / Bayesian prior (strictly pre-match)
    team_elo_base: float = 1500.0
    team_elo_k: float = 24.0
    team_elo_home_adv: float = 0.0

    # Win Probability logistic regularization
    wp_c_grid: Tuple[float, ...] = (0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0)
    wp_calibration_bins: int = 10

    # Extras codebook (verified from raw data)
    extras_codebook: Dict[int, str] = field(
        default_factory=lambda: {
            1: "Overstep",
            2: "wide",
            3: "legbyes",
            4: "byes",
            5: "other",
            6: "None",
            7: "Penalty",
        }
    )

    def ensure_dirs(self) -> None:
        """Create V4.3 output, artifact, plot, and documentation directories."""
        for d in (self.output_dir, self.artifacts_dir, self.plots_dir, self.docs_dir):
            d.mkdir(parents=True, exist_ok=True)


DEFAULT_CONFIG = V43Config()
