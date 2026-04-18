"""
Deep Dive 3.1: Statistical Comparison across Klopp, Slot Y1, Slot Y2 seasons.
Run from repo root: poetry run python scripts/analysis/01_statistical_comparison.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
from liverpool_strategy.analysis.notebook_helpers import cohens_d, effect_label, mw_test

warnings.filterwarnings('ignore')

PROCESSED_DIR = Path("data/processed")
FIXTURES_DIR = PROCESSED_DIR / "fixtures"
METADATA_DIR = PROCESSED_DIR / "metadata"
FIG_DIR = Path("figures/01_statistical")
FIG_DIR.mkdir(parents=True, exist_ok=True)

LIVERPOOL_ID = 8
SEASON_LABELS = {21646: "Klopp 23-24", 23614: "Slot Y1 24-25", 25583: "Slot Y2 25-26"}
SEASON_SHORT = {21646: "Klopp", 23614: "Y1", 25583: "Y2"}
SEASON_IDS = [21646, 23614, 25583]
SEASON_COLORS = {21646: "#c8102e", 23614: "#f6eb61", 25583: "#00b2a9"}

# ── Load fixture metadata ─────────────────────────────────────────────────────
fixture_map = pd.read_csv(METADATA_DIR / "fixture_season_mapping.csv")
type_map = pd.read_csv(METADATA_DIR / "type_id_mapping.csv")

processed = fixture_map[fixture_map["has_processed_data"] == True]
print(f"Fixtures: {len(processed)} | Seasons: {processed['season_id'].value_counts().to_dict()}")

# ── Load statistics.csv for all processed fixtures ────────────────────────────
frames = []
for _, row in processed.iterrows():
    f = FIXTURES_DIR / str(int(row["fixture_id"])) / "statistics.csv"
    if f.exists():
        df = pd.read_csv(f)
        df["season_id"] = row["season_id"]
        df["season"] = row["season"]
        df["manager"] = row["manager"]
        frames.append(df)

stats_df = pd.concat(frames, ignore_index=True)
lfc = stats_df[stats_df["participant_id"] == LIVERPOOL_ID].copy()
print(f"Loaded {len(lfc)} rows across {lfc['fixture_id'].nunique()} fixtures")

lfc = lfc.merge(type_map[["type_id", "name", "stat_group"]], on="type_id", how="left")

wide = lfc.pivot_table(index=["fixture_id", "season_id", "season", "manager"],
                        columns="name", values="value", aggfunc="first").reset_index()
wide.columns.name = None
print(f"Shape: {wide.shape} — {wide['season_id'].value_counts().to_dict()}")

stat_cols = [c for c in wide.columns if c not in ["fixture_id", "season_id", "season", "manager"]]
season_means = wide.groupby("season")[stat_cols].agg(["mean", "std"]).round(2)
print("\nSeason means (sample):")
print(season_means.T.head(10))

# ── Helper functions ──────────────────────────────────────────────────────────
BONFERRONI_N = 44  # 44-metric family for confirmatory tests

def run_tests(wide, sid_a, sid_b, label_a, label_b, stat_cols):
    n_tests = BONFERRONI_N
    results = []
    g_a = wide[wide["season_id"] == sid_a]
    g_b = wide[wide["season_id"] == sid_b]
    for col in stat_cols:
        a = g_a[col].dropna()
        b = g_b[col].dropna()
        if len(a) < 3 or len(b) < 3:
            continue
        U, p, d = mw_test(a.values, b.values)
        results.append({
            "metric": col,
            "mean_a": round(a.mean(), 2),
            "mean_b": round(b.mean(), 2),
            "delta": round(b.mean() - a.mean(), 2),
            "pct_change": round((b.mean() - a.mean()) / a.mean() * 100, 1) if a.mean() != 0 else None,
            "p_raw": p,
            "p_bonferroni": round(min(p * n_tests, 1.0), 4),
            "cohens_d": round(d, 3),
            "sig_bonferroni": p * n_tests < 0.05,
            "sig_nominal": p < 0.05,
            "comparison": f"{label_a} vs {label_b}",
            "n_a": len(a),
            "n_b": len(b),
        })
    return pd.DataFrame(results)

# ── Part 1: Confirmatory Analysis — Klopp vs Slot ────────────────────────────
print("\n=== Part 1: Confirmatory Analysis ===")
klopp_v_y1 = run_tests(wide, 21646, 23614, "Klopp 23-24", "Slot Y1 24-25", stat_cols)
klopp_v_y2 = run_tests(wide, 21646, 25583, "Klopp 23-24", "Slot Y2 25-26", stat_cols)

print(f"Klopp vs Y1 — significant (Bonferroni): {klopp_v_y1['sig_bonferroni'].sum()} / {len(klopp_v_y1)}")
print(f"Klopp vs Y2 — significant (Bonferroni): {klopp_v_y2['sig_bonferroni'].sum()} / {len(klopp_v_y2)}")

confirmatory = pd.concat([klopp_v_y1, klopp_v_y2], ignore_index=True)
conf_sig = confirmatory[confirmatory["sig_bonferroni"]].sort_values("cohens_d", key=abs, ascending=False)

print(f"\nConfirmatory significant findings (Bonferroni-corrected, p < 0.05 after ×44):")
print(conf_sig[["comparison", "metric", "mean_a", "mean_b", "pct_change", "p_bonferroni", "cohens_d"]].to_string())

# ── Part 2: Exploratory Analysis — Y1 vs Y2 ─────────────────────────────────
print("\n=== Part 2: Exploratory Analysis (Y1 vs Y2) ===")
y1_v_y2 = run_tests(wide, 23614, 25583, "Slot Y1 24-25", "Slot Y2 25-26", stat_cols)

print(f"Y1 vs Y2 — Bonferroni-significant: {y1_v_y2['sig_bonferroni'].sum()} / {len(y1_v_y2)}")
print(f"Y1 vs Y2 — Nominally significant (p < 0.05, uncorrected): {y1_v_y2['sig_nominal'].sum()} / {len(y1_v_y2)}")

y1_v_y2_ranked = y1_v_y2.sort_values("cohens_d", key=abs, ascending=False).copy()
y1_v_y2_ranked["signal"] = y1_v_y2_ranked.apply(
    lambda r: "corrected" if r["sig_bonferroni"] else ("nominal" if r["sig_nominal"] else "—"),
    axis=1
)

print("\nAll metrics ranked by effect size (Y1 -> Y2):")
print(y1_v_y2_ranked[["metric", "mean_a", "mean_b", "pct_change", "cohens_d", "p_bonferroni", "signal"]].head(20).to_string())

# ── Plot: Effect size heatmap Y1 vs Y2 ───────────────────────────────────────
y1_v_y2_sorted = y1_v_y2.sort_values("cohens_d")

fig, ax = plt.subplots(figsize=(10, 12))
colors = [
    "#d73027" if (d < 0 and sig) else
    "#f46d43" if (d < 0 and nom) else
    "#1a9850" if (d > 0 and sig) else
    "#74c476" if (d > 0 and nom) else
    "#cccccc"
    for d, sig, nom in zip(
        y1_v_y2_sorted["cohens_d"],
        y1_v_y2_sorted["sig_bonferroni"],
        y1_v_y2_sorted["sig_nominal"]
    )
]
ax.barh(y1_v_y2_sorted["metric"], y1_v_y2_sorted["cohens_d"], color=colors, alpha=0.9)
ax.axvline(0, color="black", linewidth=0.8)
ax.axvline(-0.2, color="grey", linewidth=0.5, linestyle="--")
ax.axvline(0.2, color="grey", linewidth=0.5, linestyle="--")
ax.set_xlabel("Cohen's d  (positive = improved in Y2, negative = regressed)")
ax.set_title(
    "Slot Y1 -> Y2: Directional Signals per Metric (Exploratory)\n"
    "Dark = Bonferroni-significant | Mid = Nominally significant | Grey = No signal"
)
legend = [
    mpatches.Patch(color="#d73027", label="Regression (Bonferroni)"),
    mpatches.Patch(color="#f46d43", label="Regression (nominal only)"),
    mpatches.Patch(color="#1a9850", label="Improvement (Bonferroni)"),
    mpatches.Patch(color="#74c476", label="Improvement (nominal only)"),
    mpatches.Patch(color="#cccccc", label="No signal"),
]
ax.legend(handles=legend, loc="lower right", fontsize=8)
plt.tight_layout()
plt.savefig(FIG_DIR / "y1_v_y2_effect_sizes.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"\nSaved {FIG_DIR / 'y1_v_y2_effect_sizes.png'}")

# ── Part 3: Ball Zone Presence Analysis ──────────────────────────────────────
print("\n=== Part 3: Ball Zone Presence Analysis ===")

def compute_attack_episodes(df, gap_threshold_mins=1.0):
    atk = df[df["pitch_zone"] == "attacking_third"].sort_values("estimated_minute").copy()
    if len(atk) < 2:
        return []
    episodes = []
    ep_start = atk["estimated_minute"].iloc[0]
    ep_last = atk["estimated_minute"].iloc[0]
    for t in atk["estimated_minute"].iloc[1:]:
        if t - ep_last <= gap_threshold_mins:
            ep_last = t
        else:
            duration = ep_last - ep_start
            if duration >= 0:
                episodes.append(duration)
            ep_start = t
            ep_last = t
    episodes.append(ep_last - ep_start)
    return episodes

tempo_rows = []
for _, row in processed.iterrows():
    f = FIXTURES_DIR / str(int(row["fixture_id"])) / "ball_coordinates.csv"
    if not f.exists():
        continue
    df = pd.read_csv(f)
    if len(df) < 50 or "pitch_zone" not in df.columns:
        continue

    total = len(df)
    pct_attacking = df["pitch_zone"].eq("attacking_third").sum() / total * 100
    pct_defensive = df["pitch_zone"].eq("defensive_third").sum() / total * 100

    episodes = compute_attack_episodes(df)
    entry_count = len(episodes)
    mean_duration = np.mean(episodes) if episodes else np.nan
    median_duration = np.median(episodes) if episodes else np.nan

    tempo_rows.append({
        "fixture_id": int(row["fixture_id"]),
        "season_id": row["season_id"],
        "season": row["season"],
        "total_coords": total,
        "pct_attacking": round(pct_attacking, 1),
        "pct_defensive": round(pct_defensive, 1),
        "attack_entries": entry_count,
        "mean_attack_duration_mins": round(mean_duration, 2) if not np.isnan(mean_duration) else np.nan,
        "median_attack_duration_mins": round(median_duration, 2) if not np.isnan(median_duration) else np.nan,
    })

tempo_df = pd.DataFrame(tempo_rows)
print(f"Fixtures with ball coordinate data: {len(tempo_df)}")

tempo_summary = tempo_df.groupby("season")[["pct_attacking", "pct_defensive", "attack_entries", "mean_attack_duration_mins"]].agg(["mean", "std"]).round(2)
print(tempo_summary)

# ── Plot: Zone presence bar charts ───────────────────────────────────────────
season_order = ["2023-24", "2024-25", "2025-26"]
season_labels = ["Klopp\n23-24", "Slot Y1\n24-25", "Slot Y2\n25-26"]
palette = ["#e41a1c", "#377eb8", "#4daf4a"]

metrics = [
    ("pct_attacking", "Attacking Third Occupancy (%)", "% of ball coordinates in attacking third"),
    ("attack_entries", "Attack Entries per Match", "Transitions into attacking third per game"),
    ("mean_attack_duration_mins", "Mean Attack Duration (mins)", "Avg length of each attacking spell"),
]

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle("Ball Zone Presence by Season (territorial proxy — not tempo)", fontsize=13, fontweight="bold", y=1.02)

for ax, (col, title, subtitle) in zip(axes, metrics):
    means = [tempo_df[tempo_df["season"] == s][col].mean() for s in season_order]
    sems = [tempo_df[tempo_df["season"] == s][col].sem() for s in season_order]
    bars = ax.bar(season_labels, means, color=palette, alpha=0.85, edgecolor="white")
    ax.errorbar(range(3), means, yerr=sems, fmt="none", color="black", capsize=4, linewidth=1)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel(subtitle, fontsize=8, color="grey")
    ax.set_ylim(bottom=0)
    for bar, mean in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{mean:.1f}", ha="center", va="bottom", fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR / "zone_presence.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {FIG_DIR / 'zone_presence.png'}")

# ── Statistical tests on tempo metrics ───────────────────────────────────────
klopp = tempo_df[tempo_df["season_id"] == 21646]
y1 = tempo_df[tempo_df["season_id"] == 23614]
y2 = tempo_df[tempo_df["season_id"] == 25583]

print("\nTempo metric statistical tests:")
for metric, label in [
    ("pct_attacking", "Attacking Third Occupancy %"),
    ("attack_entries", "Attack Entries per Match"),
    ("mean_attack_duration_mins", "Mean Attack Duration (mins)"),
]:
    a_k, a_y1, a_y2 = klopp[metric].dropna(), y1[metric].dropna(), y2[metric].dropna()
    _, p_k_y1, d_k_y1 = mw_test(a_k.values, a_y1.values)
    _, p_k_y2, d_k_y2 = mw_test(a_k.values, a_y2.values)
    _, p_y1_y2, d_y1_y2 = mw_test(a_y1.values, a_y2.values)
    print(f"\n{label}")
    print(f"  Klopp {a_k.mean():.2f} | Y1 {a_y1.mean():.2f} | Y2 {a_y2.mean():.2f}")
    print(f"  Klopp->Y1: p={p_k_y1:.3f}, d={d_k_y1:.3f} | Klopp->Y2: p={p_k_y2:.3f}, d={d_k_y2:.3f}")
    print(f"  Y1->Y2 (exploratory): p={p_y1_y2:.3f}, d={d_y1_y2:.3f}")

print("\nScript complete. All figures saved to figures/01_statistical/")
