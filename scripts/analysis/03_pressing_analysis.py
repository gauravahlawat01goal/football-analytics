"""
Deep Dive 1.2: Pressing Trigger Analysis.
Run from repo root: poetry run python scripts/analysis/03_pressing_analysis.py
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from liverpool_strategy.analysis.notebook_helpers import (
    cohens_d, effect_label, mw_test,
    SEASON_COLORS, SEASON_LABELS, SEASON_ORDER,
    setup_plot_style, get_data_dirs, season_tick_labels,
    KLOPP_COLOR, Y1_COLOR, Y2_COLOR,
)

warnings.filterwarnings('ignore')

dirs = get_data_dirs(base="data/processed")
DATA_DIR     = dirs.data
META_DIR     = dirs.meta
FIXTURES_DIR = dirs.fixtures
FBREF_DIR    = dirs.fbref

FIG_DIR = Path("figures/03_pressing")
FIG_DIR.mkdir(parents=True, exist_ok=True)

setup_plot_style()
TICK_LABELS = season_tick_labels(short=True)
print('Setup complete.')

# ── Load statistics.csv for all processed fixtures ────────────────────────────
meta = pd.read_csv(META_DIR / 'fixture_season_mapping.csv')
processed = meta[meta['has_processed_data'] == True].copy()
print(f'Processing {len(processed)} fixtures...')

stats_rows = []
for _, row in processed.iterrows():
    fid = row['fixture_id']
    path = FIXTURES_DIR / str(fid) / 'statistics.csv'
    if path.exists():
        df = pd.read_csv(path)
        df['fixture_id'] = fid
        df['season'] = row['season']
        df['manager'] = row['manager']
        df['date'] = row['date']
        stats_rows.append(df)

if not stats_rows:
    raise FileNotFoundError('No statistics.csv files found for processed fixtures.')

stats_all = pd.concat(stats_rows, ignore_index=True)
lfc_stats = stats_all[stats_all['participant_id'] == 8].copy()
print(f'Loaded {lfc_stats["fixture_id"].nunique()} LFC fixtures')

PRESSING_METRICS = {
    78: 'tackles',
    100: 'interceptions',
    56: 'fouls',
    46: 'ball_safe',
    80: 'passes',
    81: 'successful_passes',
}

pivot = lfc_stats[lfc_stats['type_id'].isin(PRESSING_METRICS)].copy()
pivot['metric'] = pivot['type_id'].map(PRESSING_METRICS)
fixture_metrics = pivot.pivot_table(
    index=['fixture_id', 'season', 'manager', 'date'],
    columns='metric',
    values='value',
    aggfunc='first'
).reset_index()

has_tackles = 'tackles' in fixture_metrics.columns
has_interceptions = 'interceptions' in fixture_metrics.columns

if has_tackles and has_interceptions:
    fixture_metrics['defensive_actions'] = (
        fixture_metrics['tackles'].fillna(0) + fixture_metrics['interceptions'].fillna(0)
    )
elif has_tackles:
    fixture_metrics['defensive_actions'] = fixture_metrics['tackles'].fillna(0)
elif has_interceptions:
    fixture_metrics['defensive_actions'] = fixture_metrics['interceptions'].fillna(0)
else:
    fixture_metrics['defensive_actions'] = 0.0

print(f'Fixture-level pressing metrics shape: {fixture_metrics.shape}')
print(fixture_metrics.groupby('season')[['tackles', 'interceptions', 'fouls', 'defensive_actions']].mean().round(2))

# ── Section 1: Statistical tests ─────────────────────────────────────────────
seasons = ['2023-24', '2024-25', '2025-26']
season_data = {s: fixture_metrics[fixture_metrics['season'] == s] for s in seasons}

CONFIRMATORY_ALPHA = 0.05 / 4  # Bonferroni over 4 pressing metrics

print('\n=== Pressing Volume: Statistical Tests ===')
print(f'Confirmatory alpha (Bonferroni-corrected) = {CONFIRMATORY_ALPHA:.4f}\n')

for metric in ['tackles', 'interceptions', 'defensive_actions', 'fouls']:
    if metric not in fixture_metrics.columns:
        continue
    k = season_data['2023-24'][metric].dropna()
    y1 = season_data['2024-25'][metric].dropna()
    y2 = season_data['2025-26'][metric].dropna()

    _, p_klopp_y2 = stats.mannwhitneyu(k, y2, alternative='two-sided')
    d_klopp_y2 = cohens_d(k.values, y2.values)
    sig_conf = 'SIGNIFICANT' if p_klopp_y2 < CONFIRMATORY_ALPHA else '—'

    _, p_y1_y2 = stats.mannwhitneyu(y1, y2, alternative='two-sided')
    d_y1_y2 = cohens_d(y1.values, y2.values)
    pct_change_y1_y2 = (y2.mean() - y1.mean()) / y1.mean() * 100

    print(f'{metric.upper()}')
    print(f'  Klopp: {k.mean():.2f} +/- {k.std():.2f}  |  Y1: {y1.mean():.2f} +/- {y1.std():.2f}  |  Y2: {y2.mean():.2f} +/- {y2.std():.2f}')
    print(f'  Klopp vs Y2: p={p_klopp_y2:.4f}, d={d_klopp_y2:.2f} ({effect_label(d_klopp_y2)}) -> {sig_conf}')
    print(f'  Y1 vs Y2 [exploratory]: {pct_change_y1_y2:+.1f}%, d={d_y1_y2:.2f}, p={p_y1_y2:.4f}')
    print()

# ── Plot: Pressing volume violin + strip plots ────────────────────────────────
season_order = ['2023-24', '2024-25', '2025-26']

fig, axes = plt.subplots(1, 3, figsize=(15, 6))
fig.suptitle('Liverpool Pressing Volume by Season', fontsize=14, fontweight='bold', y=1.01)

plot_metrics = [
    ('tackles', 'Tackles per Match'),
    ('interceptions', 'Interceptions per Match'),
    ('defensive_actions', 'Defensive Actions\n(Tackles + Interceptions)'),
]

for ax, (metric, title) in zip(axes, plot_metrics):
    data_for_plot = [fixture_metrics[fixture_metrics['season'] == s][metric].dropna().values
                     for s in season_order]

    parts = ax.violinplot(data_for_plot, positions=range(3), showmedians=True, showextrema=False)
    for i, (pc, s) in enumerate(zip(parts['bodies'], season_order)):
        pc.set_facecolor(SEASON_COLORS[s])
        pc.set_alpha(0.7)
    parts['cmedians'].set_color('black')
    parts['cmedians'].set_linewidth(2)

    for i, (d, s) in enumerate(zip(data_for_plot, season_order)):
        jitter = np.random.default_rng(42).uniform(-0.08, 0.08, len(d))
        ax.scatter(i + jitter, d, color=SEASON_COLORS[s], alpha=0.35, s=20, zorder=3)

    for i, d in enumerate(data_for_plot):
        mean_val = np.mean(d)
        ax.plot(i, mean_val, 'D', color='black', markersize=8, zorder=5)
        y_offset = 0.5
        ax.text(i, mean_val + y_offset, f'{mean_val:.1f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_xticks(range(3))
    ax.set_xticklabels(TICK_LABELS)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_ylabel('Count per Match')
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'pressing_volume.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "pressing_volume.png"}')

# ── Section 2: Fouls as pressing proxy ───────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Fouls Committed and Ball Safe — Pressing Aggression Proxies', fontsize=13, fontweight='bold')

for ax, (metric, title, desc) in zip(axes, [
    ('fouls', 'Fouls Committed', 'High pressing = more fouls'),
    ('ball_safe', 'Ball Safe (Clearances)', 'High press = fewer deep clearances needed'),
]):
    if metric not in fixture_metrics.columns:
        ax.text(0.5, 0.5, f'{metric} not available', ha='center', va='center')
        continue

    data_for_plot = [fixture_metrics[fixture_metrics['season'] == s][metric].dropna().values
                     for s in season_order]

    bp = ax.boxplot(data_for_plot, patch_artist=True, notch=False,
                    medianprops={'color': 'black', 'linewidth': 2})
    for patch, s in zip(bp['boxes'], season_order):
        patch.set_facecolor(SEASON_COLORS[s])
        patch.set_alpha(0.8)

    means = [np.mean(d) for d in data_for_plot]
    ax.plot(range(1, 4), means, 'D-', color='black', markersize=7, linewidth=1.5, zorder=5, label='Mean')
    for i, m in enumerate(means, 1):
        ax.text(i, m + 0.3, f'{m:.1f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_xticks(range(1, 4))
    ax.set_xticklabels(TICK_LABELS)
    ax.set_title(f'{title}\n({desc})', fontsize=11)
    ax.set_ylabel('Count per Match')
    ax.grid(axis='y', alpha=0.3)
    ax.legend(fontsize=9)

plt.tight_layout()
plt.savefig(FIG_DIR / 'pressing_fouls_ballsafe.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "pressing_fouls_ballsafe.png"}')

# ── Section 3: FBRef PPDA (if available) ─────────────────────────────────────
ppda_path = FBREF_DIR / 'ppda.csv'
ppda_available = ppda_path.exists()

if ppda_available:
    ppda_df = pd.read_csv(ppda_path)
    print(f'FBRef PPDA data loaded: {len(ppda_df)} rows')

    ppda_col = next((c for c in ppda_df.columns if 'ppda' in c.lower() and 'att' not in c.lower()), None)
    if ppda_col:
        fig, ax = plt.subplots(figsize=(8, 5))
        season_ppda = [ppda_df[ppda_df['season'] == s][ppda_col].dropna().values for s in season_order]
        bp = ax.boxplot(season_ppda, patch_artist=True,
                        medianprops={'color': 'black', 'linewidth': 2})
        for patch, s in zip(bp['boxes'], season_order):
            patch.set_facecolor(SEASON_COLORS[s])
            patch.set_alpha(0.8)

        means = [np.mean(d) if len(d) > 0 else np.nan for d in season_ppda]
        ax.plot(range(1, 4), means, 'D-', color='black', markersize=7, zorder=5)
        for i, m in enumerate(means, 1):
            if not np.isnan(m):
                ax.text(i, m - 0.3, f'{m:.1f}', ha='center', fontsize=10, fontweight='bold')

        ax.set_xticks(range(1, 4))
        ax.set_xticklabels(TICK_LABELS)
        ax.set_title('FBRef PPDA per Match (Lower = More Pressing)', fontsize=12, fontweight='bold')
        ax.set_ylabel('PPDA')
        ax.invert_yaxis()
        ax.grid(axis='y', alpha=0.3)
        plt.tight_layout()
        plt.savefig(FIG_DIR / 'fbref_ppda.png', dpi=150, bbox_inches='tight')
        plt.close()
        print(f'Saved {FIG_DIR / "fbref_ppda.png"}')
else:
    print('FBRef PPDA data not yet available.')
    print('To fetch: run `poetry run python scripts/07_fetch_fbref_ppda.py`')

# ── Section 4: Ball Zone Analysis ────────────────────────────────────────────
coord_rows = []
for _, row in processed.iterrows():
    fid = row['fixture_id']
    path = FIXTURES_DIR / str(fid) / 'ball_coordinates.csv'
    if path.exists():
        df = pd.read_csv(path, usecols=['pitch_zone'])
        df['fixture_id'] = fid
        df['season'] = row['season']
        coord_rows.append(df)

if not coord_rows:
    print('No ball_coordinates.csv files found — territorial proxy section disabled.')
    zone_fixture = None
else:
    coords = pd.concat(coord_rows, ignore_index=True)
    zone_fixture = (
        coords.groupby(['fixture_id', 'season', 'pitch_zone'])
        .size()
        .unstack(fill_value=0)
        .apply(lambda x: x / x.sum(), axis=1)
        * 100
    ).reset_index()
    print('Zone percentages (per-fixture means):')
    print(zone_fixture.groupby('season')[['attacking_third', 'middle_third', 'defensive_third']].mean().round(1))

if zone_fixture is not None:
    zones = ['defensive_third', 'middle_third', 'attacking_third']
    zone_titles = ['Defensive Third %', 'Middle Third %', 'Attacking Third %']

    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    fig.suptitle('Ball Zone Distribution by Season\n(territorial proxy — not possession-normalised)',
                 fontsize=12, fontweight='bold')

    for ax, zone, title in zip(axes, zones, zone_titles):
        data_for_plot = [zone_fixture[zone_fixture['season'] == s][zone].dropna().values
                         for s in season_order]
        bp = ax.boxplot(data_for_plot, patch_artist=True,
                        medianprops={'color': 'black', 'linewidth': 2})
        for patch, s in zip(bp['boxes'], season_order):
            patch.set_facecolor(SEASON_COLORS[s])
            patch.set_alpha(0.8)

        means = [np.mean(d) for d in data_for_plot]
        for i, (m, d) in enumerate(zip(means, data_for_plot), 1):
            ax.text(i, np.median(d) + 0.5, f'{m:.1f}%', ha='center', fontsize=9, fontweight='bold')

        ax.set_xticks(range(1, 4))
        ax.set_xticklabels(TICK_LABELS, fontsize=9)
        ax.set_title(title, fontsize=11)
        ax.set_ylabel('% of ball coordinates')
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / 'pressing_ball_zones.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved {FIG_DIR / "pressing_ball_zones.png"}')

    k_def = zone_fixture[zone_fixture['season'] == '2023-24']['defensive_third'].dropna()
    y2_def = zone_fixture[zone_fixture['season'] == '2025-26']['defensive_third'].dropna()
    _, p = stats.mannwhitneyu(k_def, y2_def, alternative='two-sided')
    d = cohens_d(k_def.values, y2_def.values)
    print(f'Defensive third % — Klopp vs Y2: mean {k_def.mean():.1f}% vs {y2_def.mean():.1f}%, d={d:.2f}, p={p:.4f}')

# ── Section 5: Summary statistics ────────────────────────────────────────────
summary_rows = []
for s in season_order:
    d = fixture_metrics[fixture_metrics['season'] == s]
    z = zone_fixture[zone_fixture['season'] == s] if zone_fixture is not None else pd.DataFrame()
    row = {
        'Season': SEASON_LABELS[s],
        'Fixtures': len(d),
        'Tackles/match': d['tackles'].mean() if 'tackles' in d.columns else np.nan,
        'Interceptions/match': d['interceptions'].mean() if 'interceptions' in d.columns else np.nan,
        'Def. Actions/match': d['defensive_actions'].mean() if 'defensive_actions' in d.columns else np.nan,
        'Fouls/match': d['fouls'].mean() if 'fouls' in d.columns else np.nan,
        'Ball Safe/match': d['ball_safe'].mean() if 'ball_safe' in d.columns else np.nan,
        'Defensive Third %': z['defensive_third'].mean() if len(z) > 0 and 'defensive_third' in z.columns else np.nan,
        'Attacking Third %': z['attacking_third'].mean() if len(z) > 0 and 'attacking_third' in z.columns else np.nan,
    }
    summary_rows.append(row)

summary = pd.DataFrame(summary_rows)
numeric_cols = [c for c in summary.columns if c not in ('Season', 'Fixtures')]
print('\n=== Summary Statistics ===')
print(summary.set_index('Season')[numeric_cols].round(1).to_string())

# Plot: Normalised % change from Klopp baseline
fig, ax = plt.subplots(figsize=(11, 6))

metrics_for_chart = ['Tackles/match', 'Interceptions/match', 'Def. Actions/match', 'Fouls/match', 'Ball Safe/match']
klopp_vals = summary.set_index('Season').loc['Klopp 23-24', metrics_for_chart]

x = np.arange(len(metrics_for_chart))
width = 0.27

for i, (s, label) in enumerate([
    ('2023-24', 'Klopp 23-24'),
    ('2024-25', 'Slot Y1 24-25'),
    ('2025-26', 'Slot Y2 25-26'),
]):
    vals = summary.set_index('Season').loc[label, metrics_for_chart]
    pct_change = ((vals - klopp_vals) / klopp_vals * 100).values
    bars = ax.bar(x + (i - 1) * width, pct_change, width, label=label,
                  color=SEASON_COLORS[s], alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, pct_change):
        if abs(val) > 1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.5 if val >= 0 else -2),
                    f'{val:+.0f}%', ha='center', va='bottom' if val >= 0 else 'top', fontsize=8)

ax.axhline(0, color='black', linewidth=1)
ax.set_xticks(x)
ax.set_xticklabels([m.replace('/', '/\n') for m in metrics_for_chart], fontsize=10)
ax.set_ylabel('% change from Klopp 23-24 baseline')
ax.set_title('Pressing Metric Changes vs Klopp Baseline', fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'pressing_pct_change.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "pressing_pct_change.png"}')

print('\nScript complete. All figures saved to figures/03_pressing/')
