"""
Deep Dive 2.1: Wirtz Integration Analysis.
Run from repo root: poetry run python scripts/analysis/05_wirtz_integration.py
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

from liverpool_strategy.analysis.notebook_helpers import (
    cohens_d, effect_label, mw_test,
    KLOPP_COLOR, Y1_COLOR, Y2_COLOR,
    SEASON_COLORS, SEASON_LABELS, SEASON_ORDER,
    setup_plot_style, get_data_dirs,
)

warnings.filterwarnings('ignore')

dirs = get_data_dirs(base="data/processed")
DATA_DIR     = dirs.data
META_DIR     = dirs.meta
FIXTURES_DIR = dirs.fixtures

FIG_DIR = Path("figures/05_wirtz")
FIG_DIR.mkdir(parents=True, exist_ok=True)

WIRTZ_COLOR    = '#ff7043'
NO_WIRTZ_COLOR = '#90a4ae'
WIRTZ_ID = 37429246

setup_plot_style()
print('Setup complete.')

# ── Section 1: Load fixture metadata and identify Wirtz starts ────────────────
meta = pd.read_csv(META_DIR / 'fixture_season_mapping.csv')
processed = meta[meta['has_processed_data'] == True].copy()

y2_fixtures = processed[processed['season'] == '2025-26'].copy()
print(f'Y2 processed fixtures: {len(y2_fixtures)}')

if len(y2_fixtures) == 0:
    raise FileNotFoundError(
        "No Y2 fixtures found with has_processed_data=True in fixture_season_mapping.csv."
    )

wirtz_starts = set()
fixtures_with_lineups = set()
skipped_lineups = []

for _, row in y2_fixtures.iterrows():
    fid = row['fixture_id']
    path = FIXTURES_DIR / str(fid) / 'lineups.csv'
    if not path.exists():
        skipped_lineups.append(fid)
        continue

    fixtures_with_lineups.add(fid)
    lineups = pd.read_csv(path)
    lfc_starters = lineups[
        (lineups['team_id'] == 8) &
        (lineups['starting'].isin([True, 1, 'True', 'true', '1']))
    ]
    if WIRTZ_ID in lfc_starters['player_id'].values:
        wirtz_starts.add(fid)

if skipped_lineups:
    print(f'  Skipped {len(skipped_lineups)} fixtures missing lineups.csv: {skipped_lineups}')

y2_fixtures = y2_fixtures[
    y2_fixtures['fixture_id'].isin(fixtures_with_lineups)
].copy()

print(f'Y2 fixtures with lineups available: {len(y2_fixtures)}')

if len(y2_fixtures) == 0:
    raise FileNotFoundError("No Y2 fixtures with lineups.csv were found.")

y2_fixtures['wirtz_started'] = y2_fixtures['fixture_id'].isin(wirtz_starts)

n_wirtz    = y2_fixtures['wirtz_started'].sum()
n_no_wirtz = (~y2_fixtures['wirtz_started']).sum()
print(f'\nWirtz-start fixtures (Y2):    {n_wirtz}')
print(f'Non-Wirtz-start fixtures (Y2): {n_no_wirtz}')
print(f'Total Y2 fixtures used:        {len(y2_fixtures)}')

if len(wirtz_starts) == 0 and len(y2_fixtures) > 0:
    raise ValueError(
        "Wirtz (player_id=37429246) was not found as a starter in any Y2 fixture. "
        "Check the 'starting' column format in lineups.csv."
    )

if n_wirtz < 5 or n_no_wirtz < 5:
    print(
        '\nSTATISTICAL LIMITATION: One group has fewer than 5 observations. '
        'All with/without comparisons are descriptive only.'
    )
elif n_wirtz < 10 or n_no_wirtz < 10:
    print(
        '\nNOTE: Sample sizes are modest (one group < 10). '
        'Statistical tests have limited power — interpret effect sizes alongside p-values.'
    )

# ── Load statistics.csv for all processed fixtures ────────────────────────────
all_seasons = processed.copy()

ATTACKING_METRICS = {
    117: 'key_passes',
    580: 'big_chances_created',
    42:  'shots_total',
    86:  'shots_on_target',
}

stats_rows = []
skipped_stats = []
for _, row in all_seasons.iterrows():
    fid = row['fixture_id']
    path = FIXTURES_DIR / str(fid) / 'statistics.csv'
    if not path.exists():
        skipped_stats.append(fid)
        continue
    df = pd.read_csv(path)
    lfc = df[df['participant_id'] == 8].copy()
    lfc['fixture_id'] = fid
    lfc['season']     = row['season']
    lfc['date']       = row['date']
    stats_rows.append(lfc)

if skipped_stats:
    print(f'Skipped {len(skipped_stats)} fixtures missing statistics.csv')

if not stats_rows:
    raise FileNotFoundError('No statistics.csv files found for any processed fixtures')

stats_all = pd.concat(stats_rows, ignore_index=True)

att_pivot = (
    stats_all[stats_all['type_id'].isin(ATTACKING_METRICS)]
    .assign(metric=lambda x: x['type_id'].map(ATTACKING_METRICS))
    .pivot_table(
        index=['fixture_id', 'season', 'date'],
        columns='metric',
        values='value',
        aggfunc='first',
    )
    .reset_index()
)

att_pivot = att_pivot.merge(
    y2_fixtures[['fixture_id', 'wirtz_started']],
    on='fixture_id',
    how='left',
)

att_pivot['date'] = pd.to_datetime(att_pivot['date'])
att_pivot_y2 = att_pivot[att_pivot['season'] == '2025-26'].copy()

print(f'\nFixture-level attacking metrics: {att_pivot.shape}')
print(f'Y2 rows: {len(att_pivot_y2)}')
print()
print('Y2 attacking output — Wirtz vs no-Wirtz (means):')
print(att_pivot_y2.groupby('wirtz_started')[['key_passes', 'big_chances_created', 'shots_total', 'shots_on_target']].mean().round(2))

# ── Section 2: Statistical Tests — With vs Without Wirtz ─────────────────────
ALPHA_BONFERRONI_WIRTZ = 0.05 / 4
print(f'\nBonferroni-corrected alpha = {ALPHA_BONFERRONI_WIRTZ:.4f} (4 metrics)\n')

wirtz_df    = att_pivot_y2[att_pivot_y2['wirtz_started'] == True]
no_wirtz_df = att_pivot_y2[att_pivot_y2['wirtz_started'] == False]

test_metrics = [
    ('key_passes',          'Key Passes'),
    ('big_chances_created', 'Big Chances Created'),
    ('shots_total',         'Shots Total'),
    ('shots_on_target',     'Shots On Target'),
]

results = []
for col, label in test_metrics:
    w   = wirtz_df[col].dropna() if col in wirtz_df.columns else pd.Series(dtype=float)
    nw  = no_wirtz_df[col].dropna() if col in no_wirtz_df.columns else pd.Series(dtype=float)
    U, p, d = mw_test(w.values, nw.values)
    pct = (w.mean() - nw.mean()) / nw.mean() * 100 if len(nw) > 0 and nw.mean() != 0 else np.nan
    sig = 'SIGNIFICANT' if (not np.isnan(p) and p < ALPHA_BONFERRONI_WIRTZ) else '—'

    print(f'{label}')
    print(f'  Wirtz-start: {w.mean():.2f} +/- {w.std():.2f}  (n={len(w)})')
    print(f'  No-Wirtz:    {nw.mean():.2f} +/- {nw.std():.2f}  (n={len(nw)})')
    if not np.isnan(p):
        print(f'  U={U:.0f}, p={p:.4f}, d={d:.2f} ({effect_label(d)}) {sig}')
        if not np.isnan(pct):
            direction = 'HIGHER' if pct > 0 else 'LOWER'
            print(f'  Wirtz start: {pct:+.1f}% vs non-start ({direction})')
    else:
        print(f'  Insufficient data for test (n too small). d={d:.2f} ({effect_label(d)})')
    print()

    results.append({
        'Metric': label,
        'Wirtz mean': round(w.mean(), 2) if len(w) else np.nan,
        'No-Wirtz mean': round(nw.mean(), 2) if len(nw) else np.nan,
        'Delta%': round(pct, 1) if not np.isnan(pct) else np.nan,
        'd': round(d, 2),
        'p': round(p, 4) if not np.isnan(p) else np.nan,
    })

results_df = pd.DataFrame(results)
print('Summary table:')
print(results_df.to_string(index=False))

# ── Plot: Wirtz vs no-Wirtz box plots ────────────────────────────────────────
fig, axes = plt.subplots(1, 4, figsize=(16, 6))
fig.suptitle(f'Attacking Output: Wirtz Start vs Non-Start (Y2 only)\n'
             f'(n={len(wirtz_df)} with Wirtz, n={len(no_wirtz_df)} without)',
             fontsize=12, fontweight='bold')

for ax, (col, label) in zip(axes, test_metrics):
    w_vals  = wirtz_df[col].dropna().values if col in wirtz_df.columns else np.array([])
    nw_vals = no_wirtz_df[col].dropna().values if col in no_wirtz_df.columns else np.array([])

    if len(w_vals) == 0 and len(nw_vals) == 0:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        continue

    data  = [nw_vals, w_vals]
    bp = ax.boxplot(
        data,
        patch_artist=True,
        widths=0.5,
        medianprops={'color': 'black', 'linewidth': 2},
    )
    bp['boxes'][0].set_facecolor(NO_WIRTZ_COLOR)
    bp['boxes'][0].set_alpha(0.8)
    bp['boxes'][1].set_facecolor(WIRTZ_COLOR)
    bp['boxes'][1].set_alpha(0.8)

    rng = np.random.default_rng(42)
    for i, (vals, color) in enumerate(zip(data, [NO_WIRTZ_COLOR, WIRTZ_COLOR]), 1):
        if len(vals) > 0:
            jitter = rng.uniform(-0.15, 0.15, len(vals))
            ax.scatter(i + jitter, vals, color=color, alpha=0.4, s=25, zorder=3)

    for i, d_arr in enumerate(data, 1):
        if len(d_arr) > 0:
            m = np.mean(d_arr)
            ax.plot(i, m, 'D', color='black', markersize=8, zorder=5)
            ax.text(i, m + 0.3, f'{m:.1f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_xticks([1, 2])
    ax.set_xticklabels(['No Wirtz', 'Wirtz\nStart'], fontsize=10)
    ax.set_title(label, fontsize=11, fontweight='bold')
    ax.set_ylabel('Per Match')
    ax.grid(axis='y', alpha=0.3)

    row = results_df[results_df['Metric'] == label].iloc[0]
    if not np.isnan(row['p']):
        p_str = f"p={row['p']:.3f}" if row['p'] >= 0.001 else 'p<0.001'
        ax.text(0.5, 0.95,
                f'd={row["d"]:.2f}\n{p_str}',
                transform=ax.transAxes,
                ha='center', va='top', fontsize=9, style='italic',
                color='darkred' if row['p'] < ALPHA_BONFERRONI_WIRTZ else 'gray')

plt.tight_layout()
plt.savefig(FIG_DIR / 'wirtz_attacking_boxplots.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "wirtz_attacking_boxplots.png"}')

# ── Section 3: Spatial Analysis ───────────────────────────────────────────────
coord_fixtures = []
skipped_coords = []

for _, row in y2_fixtures.iterrows():
    fid = row['fixture_id']
    path = FIXTURES_DIR / str(fid) / 'ball_coordinates.csv'
    if not path.exists():
        skipped_coords.append(fid)
        continue

    coords = pd.read_csv(path, usecols=['x', 'y', 'pitch_zone'])
    n_total = len(coords)
    att = coords[coords['pitch_zone'] == 'attacking_third']

    coord_fixtures.append({
        'fixture_id':         fid,
        'wirtz_started':      row['wirtz_started'],
        'n_coords':           n_total,
        'att_third_pct':      len(att) / n_total * 100 if n_total > 0 else np.nan,
        'att_mean_x':         att['x'].mean() if len(att) > 0 else np.nan,
        'att_mean_y':         att['y'].mean() if len(att) > 0 else np.nan,
        'att_mean_y_central': abs(att['y'] - 0.5).mean() if len(att) > 0 else np.nan,
    })

if skipped_coords:
    print(f'Skipped {len(skipped_coords)} Y2 fixtures missing ball_coordinates.csv')

if not coord_fixtures:
    print('No ball_coordinates data available for Y2. Spatial analysis skipped.')
    coord_y2 = None
else:
    coord_y2 = pd.DataFrame(coord_fixtures)
    print(f'\nBall coordinates loaded for {len(coord_y2)} Y2 fixtures')
    print('\nAttacking-third presence and spatial position (Wirtz vs no-Wirtz):')
    print(coord_y2.groupby('wirtz_started')[
        ['att_third_pct', 'att_mean_x', 'att_mean_y', 'att_mean_y_central']
    ].mean().round(3))

if coord_y2 is not None:
    spatial_metrics = [
        ('att_third_pct',      'Attacking Third\nOccupancy %'),
        ('att_mean_x',         'Mean x in attacking_third\n(x>0.67)'),
        ('att_mean_y_central', 'Mean |y - 0.5|\n(smaller = more central)'),
    ]

    print('\nSpatial tests (Wirtz vs no-Wirtz, Y2):')
    for col, label in spatial_metrics:
        w   = coord_y2[coord_y2['wirtz_started'] == True][col].dropna()
        nw  = coord_y2[coord_y2['wirtz_started'] == False][col].dropna()
        U, p, d = mw_test(w.values, nw.values)
        pct = (w.mean() - nw.mean()) / nw.mean() * 100 if len(nw) > 0 and nw.mean() != 0 else np.nan
        if not np.isnan(p):
            print(f'  {col}: Wirtz {w.mean():.3f} vs no-Wirtz {nw.mean():.3f} | '
                  f'd={d:.2f} ({effect_label(d)}), p={p:.4f}')
        else:
            print(f'  {col}: Wirtz {w.mean():.3f} vs no-Wirtz {nw.mean():.3f} | '
                  f'd={d:.2f} ({effect_label(d)}) — insufficient n for test')

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle('Ball Position in Attacking Third: Wirtz vs No-Wirtz (Y2)',
                 fontsize=12, fontweight='bold')

    for ax, (col, title) in zip(axes, spatial_metrics):
        w_vals  = coord_y2[coord_y2['wirtz_started'] == True][col].dropna().values
        nw_vals = coord_y2[coord_y2['wirtz_started'] == False][col].dropna().values

        bp = ax.boxplot(
            [nw_vals, w_vals], patch_artist=True,
            medianprops={'color': 'black', 'linewidth': 2},
        )
        bp['boxes'][0].set_facecolor(NO_WIRTZ_COLOR); bp['boxes'][0].set_alpha(0.8)
        bp['boxes'][1].set_facecolor(WIRTZ_COLOR);    bp['boxes'][1].set_alpha(0.8)

        rng = np.random.default_rng(42)
        for i, (vals, color) in enumerate(zip([nw_vals, w_vals], [NO_WIRTZ_COLOR, WIRTZ_COLOR]), 1):
            if len(vals) > 0:
                jitter = rng.uniform(-0.12, 0.12, len(vals))
                ax.scatter(i + jitter, vals, color=color, alpha=0.4, s=25, zorder=3)

        for i, vals in enumerate([nw_vals, w_vals], 1):
            if len(vals) > 0:
                m = np.mean(vals)
                ax.plot(i, m, 'D', color='black', markersize=8, zorder=5)

        ax.set_xticks([1, 2])
        ax.set_xticklabels(['No Wirtz', 'Wirtz\nStart'], fontsize=10)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / 'wirtz_spatial_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved {FIG_DIR / "wirtz_spatial_comparison.png"}')

# ── Section 4: Temporal Integration Trend ────────────────────────────────────
att_y2_sorted = att_pivot_y2.sort_values('date').reset_index(drop=True)
att_y2_sorted['match_number'] = np.arange(1, len(att_y2_sorted) + 1)

trend_metrics = [
    ('big_chances_created', 'Big Chances Created'),
    ('shots_on_target',     'Shots On Target'),
    ('key_passes',          'Key Passes'),
]

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Y2 Attacking Metrics by Match Number (temporal integration trend)',
             fontsize=12, fontweight='bold')

print('\nIntegration slope test (Wirtz-start fixtures only, Spearman rank correlation):')
for ax, (col, label) in zip(axes, trend_metrics):
    if col not in att_y2_sorted.columns:
        ax.text(0.5, 0.5, f'{col}\nnot available', ha='center', va='center', transform=ax.transAxes)
        continue

    for started, color, marker in [(True, WIRTZ_COLOR, 'o'), (False, NO_WIRTZ_COLOR, 's')]:
        subset = att_y2_sorted[att_y2_sorted['wirtz_started'] == started]
        lbl = 'Wirtz start' if started else 'No Wirtz'
        ax.scatter(subset['match_number'], subset[col],
                   color=color, marker=marker, s=50, alpha=0.8, zorder=3, label=lbl)

        if started and len(subset) >= 3:
            valid = subset[['match_number', col]].dropna()
            if len(valid) >= 3:
                rho, p = stats.spearmanr(valid['match_number'], valid[col])
                m_ols, b_ols = np.polyfit(valid['match_number'], valid[col], 1)
                x_range = np.array([valid['match_number'].min(), valid['match_number'].max()])
                ax.plot(x_range, m_ols * x_range + b_ols, color=color, linewidth=2,
                        label=f'Wirtz trend (rho={rho:.2f}, p={p:.3f})')

    ax.set_xlabel('Match number (Y2 chronological)')
    ax.set_ylabel(label)
    ax.set_title(label + '\nSpearman trend (directional only)',
                 fontsize=10, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

for col, label in trend_metrics:
    if col not in att_y2_sorted.columns:
        continue
    subset = att_y2_sorted[att_y2_sorted['wirtz_started'] == True][['match_number', col]].dropna()
    if len(subset) >= 3:
        rho, p = stats.spearmanr(subset['match_number'], subset[col])
        print(f'  {label}: rho={rho:+.3f}, p={p:.3f} '
              f'({"upward" if rho > 0 else "downward"} trend) [directional only]')
    else:
        print(f'  {label}: insufficient Wirtz-start data for trend test')

plt.tight_layout()
plt.savefig(FIG_DIR / 'wirtz_temporal_trend.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "wirtz_temporal_trend.png"}')

# ── Section 5: Wirtz-Era Y2 vs Y1 Baseline ───────────────────────────────────
att_y1    = att_pivot[att_pivot['season'] == '2024-25']
att_klopp = att_pivot[att_pivot['season'] == '2023-24']
att_wirtz = att_pivot_y2[att_pivot_y2['wirtz_started'] == True]
att_no_wirtz = att_pivot_y2[att_pivot_y2['wirtz_started'] == False]

summary_rows = []
for grp_label, df in [
    ('Klopp 23-24',          att_klopp),
    ('Slot Y1 24-25',        att_y1),
    ('Y2 – No Wirtz',        att_no_wirtz),
    ('Y2 – Wirtz Start',     att_wirtz),
]:
    row = {'Group': grp_label, 'N': len(df)}
    for col, _ in test_metrics:
        if col in df.columns:
            row[col] = round(df[col].mean(), 2)
        else:
            row[col] = np.nan
    summary_rows.append(row)

summary = pd.DataFrame(summary_rows).set_index('Group')
print('\n=== Attacking Metrics Comparison: Context Table ===')
print(summary.to_string())
print()
print('(Wirtz-era Y2 vs Y1 — exploratory context only. Not a causal claim.)')

# Grouped bar chart
metrics_plot = [('key_passes', 'Key Passes'), ('big_chances_created', 'Big Chances\nCreated'),
                ('shots_total', 'Shots Total'), ('shots_on_target', 'Shots On\nTarget')]
groups = ['Klopp 23-24', 'Slot Y1 24-25', 'Y2 – No Wirtz', 'Y2 – Wirtz Start']
group_colors = [KLOPP_COLOR, Y1_COLOR, NO_WIRTZ_COLOR, WIRTZ_COLOR]

fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(metrics_plot))
width = 0.2

for i, (grp, color) in enumerate(zip(groups, group_colors)):
    vals = [summary.loc[grp, col] if col in summary.columns else np.nan
            for col, _ in metrics_plot]
    offset = (i - 1.5) * width
    bars = ax.bar(x + offset, vals, width, label=grp,
                  color=color, alpha=0.85, edgecolor='white')
    for bar, val in zip(bars, vals):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.05,
                    f'{val:.1f}', ha='center', fontsize=8, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels([label for _, label in metrics_plot], fontsize=11)
ax.set_ylabel('Per Match Average')
ax.set_title('Attacking Output: Wirtz-Era Y2 vs Historical Baselines\n'
             '(Y2 sub-groups are exploratory context — not causal)',
             fontsize=12, fontweight='bold')
ax.legend(fontsize=10, loc='upper right')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'wirtz_vs_baselines.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "wirtz_vs_baselines.png"}')

# ── Section 6: Final Summary ──────────────────────────────────────────────────
print('\n=== WIRTZ INTEGRATION — KEY FINDINGS SUMMARY ===')
print()
print(f'Y2 fixtures analysed: {len(y2_fixtures)}')
print(f'  Wirtz started: {n_wirtz}')
print(f'  Wirtz absent:  {n_no_wirtz}')
print()

if len(results) > 0:
    print('Attacking output (Wirtz-start vs no-start within Y2):')
    for _, row in results_df.iterrows():
        if not np.isnan(row['p']):
            sig_flag = ' [sig at Bonferroni alpha]' if row['p'] < ALPHA_BONFERRONI_WIRTZ else ''
            if not np.isnan(row['Delta%']):
                direction = 'HIGHER' if row['Delta%'] > 0 else 'LOWER'
                print(f'  {row["Metric"]}: {row["Delta%"]:+.1f}% ({direction}) | d={row["d"]:.2f} ({effect_label(row["d"])}), p={row["p"]:.3f}{sig_flag}')
            else:
                print(f'  {row["Metric"]}: Delta%=N/A | d={row["d"]:.2f} ({effect_label(row["d"])}), p={row["p"]:.3f}{sig_flag}')
        else:
            print(f'  {row["Metric"]}: d={row["d"]:.2f} ({effect_label(row["d"])}) — n too small for MW test')

print()
print('Context vs Y1 baseline (exploratory — not causal):')
for col, label in test_metrics:
    if col in summary.columns:
        y1_val = summary.loc['Slot Y1 24-25', col]
        w_val  = summary.loc['Y2 – Wirtz Start', col]
        if not np.isnan(y1_val) and not np.isnan(w_val):
            pct = (w_val - y1_val) / y1_val * 100
            print(f'  {label}: Wirtz Y2 {w_val:.2f} vs Y1 {y1_val:.2f} ({pct:+.1f}%)')

print('\nScript complete. All figures saved to figures/05_wirtz/')
