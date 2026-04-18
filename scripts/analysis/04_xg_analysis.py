"""
xG and Attacking Quality Analysis (Understat Tier 2).
Run from repo root: poetry run python scripts/analysis/04_xg_analysis.py
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from mplsoccer import VerticalPitch

from liverpool_strategy.analysis.notebook_helpers import (
    cohens_d, effect_label,
    SEASON_COLORS, SEASON_LABELS, SEASON_ORDER,
    setup_plot_style, get_data_dirs, season_tick_labels,
)

warnings.filterwarnings('ignore')

dirs = get_data_dirs(base="data/processed")
DATA_DIR      = dirs.data
META_DIR      = dirs.meta
FIXTURES_DIR  = dirs.fixtures
UNDERSTAT_DIR = dirs.understat

FIG_DIR = Path("figures/04_xg")
FIG_DIR.mkdir(parents=True, exist_ok=True)

setup_plot_style()
TICK_LABELS = season_tick_labels(short=True)
print('Setup complete.')

# ── Load Understat data ───────────────────────────────────────────────────────
match_xg = pd.read_csv(UNDERSTAT_DIR / 'match_xg.csv')
match_xg['date'] = pd.to_datetime(match_xg['date'])

shots = pd.read_csv(UNDERSTAT_DIR / 'shots.csv')
shots['date'] = pd.to_datetime(shots['date'])

print(f'Match xG: {len(match_xg)} matches')
print(f'Shots: {len(shots)} shots')
print()
print(match_xg.groupby(['season', 'manager']).size().rename('matches'))
print()
print('Match xG per season:')
print(match_xg.groupby('season')[['lfc_xg', 'opp_xg', 'lfc_goals', 'opp_goals']].mean().round(3))

ALPHA_BONFERRONI = 0.05 / 4  # 4 main xG metrics

season_data = {s: match_xg[match_xg['season'] == s] for s in SEASON_ORDER}

# ── Section 1: Match-level xG statistical tests ───────────────────────────────
print('\n=== Match-level xG Statistical Tests ===')
print(f'Confirmatory alpha = {ALPHA_BONFERRONI:.4f} (Bonferroni-corrected)\n')

for metric, label in [
    ('lfc_xg', 'LFC xG for'),
    ('opp_xg', 'xG Against (opponent xG)'),
    ('lfc_goals', 'LFC Goals'),
    ('opp_goals', 'Goals Against'),
]:
    k = season_data['2023-24'][metric]
    y1 = season_data['2024-25'][metric]
    y2 = season_data['2025-26'][metric]

    _, p_kv2 = stats.mannwhitneyu(k, y2, alternative='two-sided')
    d_kv2 = cohens_d(k.values, y2.values)
    sig = 'SIGNIFICANT' if p_kv2 < ALPHA_BONFERRONI else '—'

    _, p_y1y2 = stats.mannwhitneyu(y1, y2, alternative='two-sided')
    d_y1y2 = cohens_d(y1.values, y2.values)
    pct = (y2.mean() - y1.mean()) / y1.mean() * 100

    print(f'{label}')
    print(f'  Klopp: {k.mean():.3f} | Y1: {y1.mean():.3f} | Y2: {y2.mean():.3f}')
    print(f'  Klopp vs Y2: d={d_kv2:.2f} ({effect_label(d_kv2)}), p={p_kv2:.4f} {sig}')
    print(f'  Y1 vs Y2 [explore]: {pct:+.1f}%, d={d_y1y2:.2f}, p={p_y1y2:.4f}')
    print()

# Plot: xG per match violin plots
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
fig.suptitle('Liverpool xG per Match by Season', fontsize=14, fontweight='bold')

for ax, (metric, title, invert) in zip(axes, [
    ('lfc_xg', 'xG For (Liverpool)', False),
    ('opp_xg', 'xG Against (Opponent)', True),
]):
    data_per_season = [season_data[s][metric].values for s in SEASON_ORDER]

    parts = ax.violinplot(data_per_season, positions=range(3), showmedians=True, showextrema=False)
    for pc, s in zip(parts['bodies'], SEASON_ORDER):
        pc.set_facecolor(SEASON_COLORS[s])
        pc.set_alpha(0.7)
    parts['cmedians'].set_color('black')
    parts['cmedians'].set_linewidth(2)

    for i, (d, s) in enumerate(zip(data_per_season, SEASON_ORDER)):
        jitter = np.random.default_rng(42).uniform(-0.07, 0.07, len(d))
        ax.scatter(i + jitter, d, color=SEASON_COLORS[s], alpha=0.3, s=25, zorder=3)
        mean = np.mean(d)
        ax.plot(i, mean, 'D', color='black', markersize=9, zorder=5)
        ax.text(i, mean + 0.08, f'{mean:.2f}', ha='center', fontsize=10, fontweight='bold')

    ax.set_xticks(range(3))
    ax.set_xticklabels(TICK_LABELS)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.set_ylabel('xG per Match')
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'xg_per_match.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "xg_per_match.png"}')

# ── Section 2: xG vs Actual Goals — Luck or Quality? ─────────────────────────
match_xg['xg_overperf'] = match_xg['lfc_goals'] - match_xg['lfc_xg']
match_xg['xga_overperf'] = match_xg['opp_goals'] - match_xg['opp_xg']

print('xG Overperformance (Goals - xG) per season:')
for s in SEASON_ORDER:
    d = match_xg[match_xg['season'] == s]['xg_overperf']
    t, p = stats.ttest_1samp(d, 0)
    print(f'  {SEASON_LABELS[s]}: mean={d.mean():+.3f}, std={d.std():.3f}, p={p:.4f} ({"sig" if p < 0.05 else "not sig"})')

print()
print('xGA Overperformance (Goals Conceded - xG Against):')
for s in SEASON_ORDER:
    d = match_xg[match_xg['season'] == s]['xga_overperf']
    t, p = stats.ttest_1samp(d, 0)
    print(f'  {SEASON_LABELS[s]}: mean={d.mean():+.3f}, std={d.std():.3f}, p={p:.4f}')

print()
print('Interpretation: consistent ~-0.2 underperformance for attacking across all seasons')
print('-> Y2 regression is NOT a luck story — xG itself has declined')

# Plot: xG vs Goals scatter
fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharex=True, sharey=True)
fig.suptitle('xG vs Actual Goals per Match (each dot = 1 match)', fontsize=13, fontweight='bold')

for ax, s in zip(axes, SEASON_ORDER):
    d = season_data[s]
    ax.scatter(d['lfc_xg'], d['lfc_goals'], color=SEASON_COLORS[s], alpha=0.7, s=50, zorder=3)
    max_val = max(d['lfc_xg'].max(), d['lfc_goals'].max()) + 0.5
    ax.plot([0, max_val], [0, max_val], 'k--', alpha=0.4, linewidth=1, label='Goals = xG')
    m, b, r, p, _ = stats.linregress(d['lfc_xg'], d['lfc_goals'])
    x_line = np.linspace(d['lfc_xg'].min(), d['lfc_xg'].max(), 50)
    ax.plot(x_line, m * x_line + b, color=SEASON_COLORS[s], linewidth=2, label=f'Trend (r={r:.2f})')

    mean_xg = d['lfc_xg'].mean()
    mean_g = d['lfc_goals'].mean()
    ax.text(0.05, 0.95, f'Mean xG: {mean_xg:.2f}\nMean Goals: {mean_g:.2f}\nDiff: {mean_g-mean_xg:+.2f}',
            transform=ax.transAxes, fontsize=9, va='top',
            bbox={'facecolor': 'white', 'alpha': 0.8, 'pad': 3})

    ax.set_xlabel('Liverpool xG')
    ax.set_ylabel('Liverpool Goals')
    ax.set_title(SEASON_LABELS[s], fontsize=11, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'xg_vs_goals_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "xg_vs_goals_scatter.png"}')

# ── Section 3: Shot Volume vs Shot Quality ────────────────────────────────────
match_counts = match_xg.groupby('season').size().rename('n_matches')
shot_metrics = shots.groupby('season').agg(
    total_shots=('xg', 'count'),
    total_xg=('xg', 'sum'),
    mean_xg_per_shot=('xg', 'mean'),
).join(match_counts)

shot_metrics['shots_per_match'] = shot_metrics['total_shots'] / shot_metrics['n_matches']
shot_metrics['xg_per_match'] = shot_metrics['total_xg'] / shot_metrics['n_matches']

print('\nShot metrics by season:')
print(shot_metrics[['n_matches', 'shots_per_match', 'mean_xg_per_shot', 'xg_per_match']].round(3))

print()
print('Y1 vs Y2 changes:')
y1_row = shot_metrics.loc['2024-25']
y2_row = shot_metrics.loc['2025-26']
for col in ['shots_per_match', 'mean_xg_per_shot', 'xg_per_match']:
    pct = (y2_row[col] - y1_row[col]) / y1_row[col] * 100
    print(f'  {col}: {pct:+.1f}%')

# Plot: Volume vs quality
fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle('Shot Volume and Quality by Season', fontsize=13, fontweight='bold')

for ax, (metric, title) in zip(axes, [
    ('shots_per_match', 'Shots per Match'),
    ('mean_xg_per_shot', 'Avg xG per Shot\n(Shot Quality)'),
    ('xg_per_match', 'Total xG per Match'),
]):
    vals = [shot_metrics.loc[s, metric] for s in SEASON_ORDER]
    bars = ax.bar(range(3), vals,
                  color=[SEASON_COLORS[s] for s in SEASON_ORDER],
                  alpha=0.85, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                f'{val:.2f}', ha='center', fontsize=11, fontweight='bold')

    ax.set_xticks(range(3))
    ax.set_xticklabels(TICK_LABELS, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_ylabel(title.split('\n')[0])
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'shot_volume_quality.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "shot_volume_quality.png"}')

# Statistical test on xG per match
k_xg = shots[shots['season'] == '2023-24'].groupby('understat_match_id')['xg'].sum()
y1_xg = shots[shots['season'] == '2024-25'].groupby('understat_match_id')['xg'].sum()
y2_xg = shots[shots['season'] == '2025-26'].groupby('understat_match_id')['xg'].sum()

_, p_kv2 = stats.mannwhitneyu(k_xg, y2_xg, alternative='two-sided')
d_kv2 = cohens_d(k_xg.values, y2_xg.values)
_, p_y1y2 = stats.mannwhitneyu(y1_xg, y2_xg, alternative='two-sided')
d_y1y2 = cohens_d(y1_xg.values, y2_xg.values)

print(f'\nTotal xG per match — Klopp vs Y2: d={d_kv2:.2f}, p={p_kv2:.4f} {"SIGNIFICANT" if p_kv2 < ALPHA_BONFERRONI else "—"}')
print(f'Total xG per match — Y1 vs Y2 [exploratory]: d={d_y1y2:.2f}, p={p_y1y2:.4f}')

# ── Section 4: Shot Locations ─────────────────────────────────────────────────
shots['pitch_x'] = shots['x'].astype(float) * 105
shots['pitch_y'] = shots['y'].astype(float) * 68

fig, axes = plt.subplots(1, 3, figsize=(16, 7))
fig.suptitle('Liverpool Shot Locations by Season\n(each dot = one shot, size = xG)',
             fontsize=13, fontweight='bold')

pitch = VerticalPitch(pitch_type='tracab', pitch_length=105, pitch_width=68,
                      half=True, pitch_color='grass', line_color='white',
                      line_zorder=2)

for ax, s in zip(axes, SEASON_ORDER):
    pitch.draw(ax=ax)
    d = shots[shots['season'] == s]
    goals = d[d['result'] == 'Goal']
    non_goals = d[d['result'] != 'Goal']

    pitch.scatter(
        non_goals['pitch_x'], non_goals['pitch_y'],
        s=non_goals['xg'].astype(float) * 300 + 20,
        c=SEASON_COLORS[s], alpha=0.4, ax=ax, zorder=3
    )
    pitch.scatter(
        goals['pitch_x'], goals['pitch_y'],
        s=goals['xg'].astype(float) * 300 + 40,
        c='white', edgecolors=SEASON_COLORS[s], linewidths=2,
        ax=ax, zorder=4
    )

    n_shots = len(d)
    n_goals_count = len(goals)
    mean_xg = d['xg'].astype(float).mean()
    ax.set_title(f'{SEASON_LABELS[s]}\n{n_shots} shots | {n_goals_count} goals | avg xG: {mean_xg:.3f}',
                 fontsize=10, pad=10)

plt.tight_layout()
plt.savefig(FIG_DIR / 'shot_locations.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "shot_locations.png"}')

# Shot distance distribution
fig, ax = plt.subplots(figsize=(10, 5))

for s in SEASON_ORDER:
    d = shots[shots['season'] == s]['pitch_x']
    ax.hist(d, bins=20, range=(52, 105), density=True, alpha=0.55,
            color=SEASON_COLORS[s], label=SEASON_LABELS[s], edgecolor='white')
    ax.axvline(d.mean(), color=SEASON_COLORS[s], linewidth=2, linestyle='--', alpha=0.9)

ax.set_xlabel('Shot x-position (0=own goal, 105=opponent goal)')
ax.set_ylabel('Density')
ax.set_title('Shot Distance from Goal — Distribution by Season\n(dashed line = season mean)', fontsize=12)
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.axvline(105 - 16.5, color='gray', linewidth=1, alpha=0.5, linestyle=':')
ax.text(105 - 16.5, ax.get_ylim()[1] * 0.9, 'penalty area', ha='right', fontsize=8, alpha=0.7)

plt.tight_layout()
plt.savefig(FIG_DIR / 'shot_distance_dist.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "shot_distance_dist.png"}')

for s in SEASON_ORDER:
    d = shots[shots['season'] == s]['pitch_x']
    in_box = (d >= 105 - 16.5).mean() * 100
    print(f'{SEASON_LABELS[s]}: mean x={d.mean():.1f}m, {in_box:.1f}% inside penalty box')

# ── Section 5: Set Piece xG Analysis ─────────────────────────────────────────
situation_xg = shots.groupby(['season', 'situation']).agg(
    count=('xg', 'count'),
    total_xg=('xg', 'sum'),
    mean_xg=('xg', 'mean'),
).round(3)

print('\nxG by situation and season:')
print(situation_xg.to_string())

n_matches = match_xg.groupby('season').size()
print()
print('Per-match breakdown (xG contribution):')
for s in SEASON_ORDER:
    n = n_matches[s]
    for sit in ['OpenPlay', 'FromCorner', 'SetPiece', 'DirectFreekick', 'Penalty']:
        subset = shots[(shots['season'] == s) & (shots['situation'] == sit)]
        if len(subset) > 0:
            print(f'  {SEASON_LABELS[s]} | {sit}: {len(subset)/n:.2f} shots/match, {subset["xg"].sum()/n:.3f} xG/match')

# Set piece vs open play
shots['is_set_piece'] = shots['situation'].isin(['FromCorner', 'SetPiece', 'DirectFreekick', 'Penalty'])
sp_summary = shots.groupby(['season', 'is_set_piece'])['xg'].sum().unstack()
sp_summary.columns = ['Open Play xG', 'Set Piece xG']

for s in SEASON_ORDER:
    n = n_matches[s]
    sp_summary.loc[s, 'Open Play xG/match'] = sp_summary.loc[s, 'Open Play xG'] / n
    sp_summary.loc[s, 'Set Piece xG/match'] = sp_summary.loc[s, 'Set Piece xG'] / n

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Open Play vs Set Piece xG — The Trent Effect', fontsize=13, fontweight='bold')

for ax, col in zip(axes, ['Open Play xG/match', 'Set Piece xG/match']):
    vals = [sp_summary.loc[s, col] for s in SEASON_ORDER]
    bars = ax.bar(range(3), vals,
                  color=[SEASON_COLORS[s] for s in SEASON_ORDER],
                  alpha=0.85, edgecolor='white', linewidth=1.5)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
                f'{val:.3f}', ha='center', fontsize=11, fontweight='bold')
    ax.set_xticks(range(3))
    ax.set_xticklabels(TICK_LABELS)
    ax.set_title(col, fontsize=11, fontweight='bold')
    ax.set_ylabel('xG per Match')
    ax.grid(axis='y', alpha=0.3)

y1_sp = sp_summary.loc['2024-25', 'Set Piece xG/match']
y2_sp = sp_summary.loc['2025-26', 'Set Piece xG/match']
pct_sp = (y2_sp - y1_sp) / y1_sp * 100
axes[1].text(1.5, max(sp_summary.loc[s, 'Set Piece xG/match'] for s in SEASON_ORDER) * 0.85,
             f'Y1->Y2: {pct_sp:+.1f}%', ha='center', fontsize=10,
             color='darkred', fontweight='bold')

plt.tight_layout()
plt.savefig(FIG_DIR / 'set_piece_xg.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "set_piece_xg.png"}')

# ── Section 6: Summary Table ──────────────────────────────────────────────────
summary_rows = []
# Re-derive season_data now that xg_overperf column has been added
season_data_full = {s: match_xg[match_xg['season'] == s] for s in SEASON_ORDER}
for s in SEASON_ORDER:
    n = n_matches[s]
    d = shots[shots['season'] == s]
    m = season_data_full[s]

    row = {
        'Season': SEASON_LABELS[s],
        'Matches': n,
        'Goals/match': m['lfc_goals'].mean(),
        'xG/match': m['lfc_xg'].mean(),
        'Goals - xG': m['xg_overperf'].mean(),
        'Shots/match': len(d) / n,
        'xG/shot': d['xg'].mean(),
        'Open Play xG/match': d[~d['is_set_piece']]['xg'].sum() / n,
        'Set Piece xG/match': d[d['is_set_piece']]['xg'].sum() / n,
        'xGA/match': season_data[s]['opp_xg'].mean(),
    }
    summary_rows.append(row)

summary = pd.DataFrame(summary_rows).set_index('Season')
print('\n=== Attacking Quality Summary ===')
print(summary.round(3).to_string())

print()
print('=== Key Findings ===')
k_row = summary.loc['Klopp 23-24']
y2_row = summary.loc['Slot Y2 25-26']
for col in ['Goals/match', 'xG/match', 'Shots/match', 'xG/shot', 'Set Piece xG/match']:
    pct = (y2_row[col] - k_row[col]) / k_row[col] * 100
    print(f'  {col}: Klopp {k_row[col]:.3f} -> Y2 {y2_row[col]:.3f} ({pct:+.1f}%)')

print('\nScript complete. All figures saved to figures/04_xg/')
