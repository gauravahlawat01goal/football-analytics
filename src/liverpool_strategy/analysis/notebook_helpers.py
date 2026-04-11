"""
Shared utilities for Liverpool FC analysis notebooks.

Import in any notebook with:

    from liverpool_strategy.analysis.notebook_helpers import (
        cohens_d, effect_label, mw_test,
        SEASON_COLORS, SEASON_LABELS, SEASON_ORDER,
        CONFIRMATORY_LABEL, EXPLORATORY_LABEL,
        setup_plot_style, get_data_dirs,
    )
    DATA_DIR, META_DIR, FIXTURES_DIR = get_data_dirs()
    setup_plot_style()

All notebooks (03–06+) should use these instead of redefining locally.
Notebooks 01 and 02 predate this module and use inline equivalents;
they should be migrated in a follow-up.
"""

from pathlib import Path
from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
from scipy import stats


# ── Season colour palette ────────────────────────────────────────────────────
KLOPP_COLOR: str = "#c8102e"  # Liverpool red
Y1_COLOR: str = "#f6eb61"  # Liverpool gold
Y2_COLOR: str = "#00b2a9"  # teal

SEASON_COLORS: dict[str, str] = {
    "2023-24": KLOPP_COLOR,
    "2024-25": Y1_COLOR,
    "2025-26": Y2_COLOR,
}

SEASON_LABELS: dict[str, str] = {
    "2023-24": "Klopp 23-24",
    "2024-25": "Slot Y1 24-25",
    "2025-26": "Slot Y2 25-26",
}

SEASON_ORDER: list[str] = ["2023-24", "2024-25", "2025-26"]

# ── Analytical framing labels ────────────────────────────────────────────────
CONFIRMATORY_LABEL: str = "confirmatory (Bonferroni-corrected)"
EXPLORATORY_LABEL: str = "exploratory (Y2 partial season — report effect sizes)"


# ── Statistics helpers ───────────────────────────────────────────────────────

def cohens_d(a, b) -> float:
    """Cohen's d effect size using pooled standard deviation.

    Positive value means group *a* > group *b*.
    Returns 0.0 when both groups have zero variance.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    pooled_sd = np.sqrt((np.std(a, ddof=1) ** 2 + np.std(b, ddof=1) ** 2) / 2)
    if pooled_sd == 0:
        return 0.0
    return float((np.mean(a) - np.mean(b)) / pooled_sd)


def effect_label(d: float) -> str:
    """Return a verbal label for a Cohen's d effect size magnitude."""
    d = abs(d)
    if d < 0.2:
        return "negligible"
    if d < 0.5:
        return "small"
    if d < 0.8:
        return "medium"
    return "large"


def mw_test(a, b) -> tuple[float, float, float]:
    """Two-sided Mann-Whitney U test with Cohen's d.

    Returns
    -------
    (U, p, d) where U is the test statistic, p is the two-sided p-value,
    and d is Cohen's d (positive = a > b).

    Returns (nan, nan, d) when either group has fewer than 3 observations.
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    d = cohens_d(a, b)
    if len(a) < 3 or len(b) < 3:
        return float("nan"), float("nan"), d
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return float(U), float(p), d


# ── Data directory helpers ───────────────────────────────────────────────────

class DataDirs(NamedTuple):
    data: Path
    meta: Path
    fixtures: Path
    understat: Path
    fbref: Path


def get_data_dirs(base: str = "../data/processed") -> DataDirs:
    """Return the standard processed-data directory structure.

    Parameters
    ----------
    base : str
        Relative path from the notebook's working directory to
        ``data/processed``. Default works when notebooks are run from
        the ``notebooks/`` directory.
    """
    data_dir = Path(base)
    return DataDirs(
        data=data_dir,
        meta=data_dir / "metadata",
        fixtures=data_dir / "fixtures",
        understat=data_dir / "understat",
        fbref=data_dir / "fbref",
    )


# ── Plotting helpers ─────────────────────────────────────────────────────────

def setup_plot_style() -> None:
    """Apply the standard rcParams style used across all analysis notebooks."""
    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def season_tick_labels(short: bool = False) -> list[str]:
    """Return x-axis tick labels for the three seasons.

    Parameters
    ----------
    short : bool
        If True, returns compact labels suitable for narrow axes.
    """
    if short:
        return ["Klopp\n23-24", "Slot Y1\n24-25", "Slot Y2\n25-26"]
    return ["Klopp 23-24", "Slot Y1 24-25", "Slot Y2 25-26"]
