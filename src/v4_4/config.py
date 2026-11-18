"""Configuration for SupeRR Intelligence V4.4."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from src.config import PROJECT_ROOT


@dataclass(frozen=True)
class V44Config:
    """Immutable configuration for V4.4 pipeline."""

    random_seed: int = 2026
    data_dir: Path = PROJECT_ROOT / "data"
    cricsheet_dir: Path = PROJECT_ROOT / "data" / "external" / "cricsheet"
    output_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_4"
    artifacts_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_4" / "artifacts"
    plots_dir: Path = PROJECT_ROOT / "data" / "outputs" / "v4_4" / "plots"
    docs_dir: Path = PROJECT_ROOT / "docs" / "v4_4"

    ipl_json_url: str = "https://cricsheet.org/downloads/ipl_json.zip"
    t20i_json_url: str = "https://cricsheet.org/downloads/t20s_male_json.zip"

    n_cv_folds: int = 5
    oot_cutoff_year: int = 2024
    standard_t20_balls: int = 120
    team_elo_base: float = 1500.0
    team_elo_k: float = 24.0
    li_thresholds: Tuple[float, ...] = (1.00, 1.25, 1.50, 1.75, 2.00)

    def ensure_dirs(self) -> None:
        for d in (self.cricsheet_dir, self.output_dir, self.artifacts_dir, self.plots_dir, self.docs_dir):
            d.mkdir(parents=True, exist_ok=True)


DEFAULT_V44_CONFIG = V44Config()
