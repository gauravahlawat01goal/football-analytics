"""
Deep Dive 1.6: Second-Half Vulnerability.
Run from repo root: poetry run python scripts/analysis/06_second_half.py

Note: This script uses inline helper functions (cohens_d, effect_label, mw_test)
rather than importing from notebook_helpers, as per the original notebook design.
"""
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

warnings.filterwarnings('ignore')

DATA_DIR    = Path('data/processed')
META_DIR    = DATA_DIR / 'metadata'
FIXTURES_DIR = DATA_DIR / 'fixtures'

FIG_DIR = Path('figures/06_second_half')
FIG_DIR.mkdir(parents=True, exist_ok=True)

KLOPP_COLOR = '#c8102e'
Y1_COLOR    = '#f6eb61'
Y2_COLOR    = '#00b2a9'
SEASON_COLORS  = {'2023-24': KLOPP_COLOR, '2024-25': Y1_COLOR, '2025-26': Y2_COLOR}
SEASON_LABELS  = {'2023-24': 'Klopp 23-24', '2024-25': 'Slot Y1 24-25', '2025-26': 'Slot Y2 25-26'}
SEASON_ORDER   = ['2023-24', '2024-25', '2025-26']
TICK_LABELS    = ['Klopp\n23-24', 'Slot Y1\n24-25', 'Slot Y2\n25-26']

plt.rcParams.update({
    'figure.dpi': 120,
    'font.size': 11,
    'axes.spines.top': False,
    'axes.spines.right': False,
})
print('Setup complete.')


# ── Helper functions (inline — per notebook design) ───────────────────────────
def cohens_d(a, b):
    """Cohen's d using pooled SD. Positive = group a > group b."""
    pooled_sd = np.sqrt((np.std(a, ddof=1)**2 + np.std(b, ddof=1)**2) / 2)
    if pooled_sd == 0:
        return 0.0
    return (np.mean(a) - np.mean(b)) / pooled_sd


def effect_label(d):
    d = abs(d)
    if d < 0.2:  return 'negligible'
    if d < 0.5:  return 'small'
    if d < 0.8:  return 'medium'
    return 'large'


def mw_test(a, b, label=''):
    """Mann-Whitney U; returns (U, p, d). Reports results inline."""
    a, b = np.array(a), np.array(b)
    d = cohens_d(a, b)
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan, d
    U, p = stats.mannwhitneyu(a, b, alternative='two-sided')
    return float(U), float(p), d


def get_goals(df, desc):
    """Extract goals for a given description label from a scores DataFrame slice."""
    row = df[df['description'] == desc]
    return int(row['goals'].iloc[0]) if len(row) == 1 else np.nan


print('Helper functions defined.')

# ── Load fixture metadata ─────────────────────────────────────────────────────
meta = pd.read_csv(META_DIR / 'fixture_season_mapping.csv')
processed = meta[meta['has_processed_data'] == True].copy()
print(f'Processing {len(processed)} fixtures across {processed["season"].nunique()} seasons')
print(processed.groupby(['season', 'manager']).size().rename('fixtures'))

# ── Section 1: Goals by Period ────────────────────────────────────────────────
CONFIRMATORY_ALPHA = 0.05 / 4  # Bonferroni over 4 period metrics

period_rows = []
skipped_scores = []

for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']
    date   = meta_row['date']

    path = FIXTURES_DIR / str(fid) / 'scores.csv'
    if not path.exists():
        skipped_scores.append(fid)
        continue

    scores = pd.read_csv(path)

    lfc = scores[scores['participant_id'] == 8]
    opp = scores[scores['participant_id'] != 8]

    if len(opp['participant_id'].unique()) != 1:
        import warnings as _w
        _w.warn(f'Fixture {fid}: unexpected opponent participant count — skipping')
        skipped_scores.append(fid)
        continue

    lfc_h1_cum  = get_goals(lfc, '1ST_HALF')
    lfc_full    = get_goals(lfc, '2ND_HALF')
    opp_h1_cum  = get_goals(opp, '1ST_HALF')
    opp_full    = get_goals(opp, '2ND_HALF')

    lfc_h2  = (lfc_full - lfc_h1_cum) if (not np.isnan(lfc_h1_cum) and not np.isnan(lfc_full)) else np.nan
    opp_h2  = (opp_full - opp_h1_cum) if (not np.isnan(opp_h1_cum) and not np.isnan(opp_full)) else np.nan

    period_rows.append({
        'fixture_id': fid,
        'season':     season,
        'date':       date,
        'lfc_h1':     lfc_h1_cum,
        'lfc_h2':     lfc_h2,
        'lfc_total':  lfc_full,
        'opp_h1':     opp_h1_cum,
        'opp_h2':     opp_h2,
        'opp_total':  opp_full,
    })

if skipped_scores:
    print(f'Skipped {len(skipped_scores)} fixtures missing scores.csv')

period_df = pd.DataFrame(period_rows)
period_df['date'] = pd.to_datetime(period_df['date'])

print(f'\nPeriod data loaded: {len(period_df)} fixtures')
print()
print('Goals per half by season (means):')
print(period_df.groupby('season')[['lfc_h1', 'lfc_h2', 'opp_h1', 'opp_h2']].mean().round(2))

# Statistical tests
print('\n=== H1 vs H2 Goals — Statistical Summary ===')
print(f'Confirmatory Bonferroni alpha = {CONFIRMATORY_ALPHA:.4f}\n')

season_period = {s: period_df[period_df['season'] == s] for s in SEASON_ORDER}

print('Within-season LFC scored: H1 vs H2 (Wilcoxon signed-rank, paired):')
for s in SEASON_ORDER:
    d = season_period[s].dropna(subset=['lfc_h1', 'lfc_h2'])
    if len(d) >= 3:
        _, p = stats.wilcoxon(d['lfc_h1'], d['lfc_h2'])
        diff = d['lfc_h2'].mean() - d['lfc_h1'].mean()
        print(f'  {SEASON_LABELS[s]}: H1={d["lfc_h1"].mean():.2f}, H2={d["lfc_h2"].mean():.2f}, '
              f'diff={diff:+.2f}, p={p:.4f}')

print()
print('Cross-season LFC goals — H1:')
k_h1  = season_period['2023-24']['lfc_h1'].dropna()
y1_h1 = season_period['2024-25']['lfc_h1'].dropna()
y2_h1 = season_period['2025-26']['lfc_h1'].dropna()
_, p_kv2, d_kv2 = mw_test(k_h1.values, y2_h1.values)
_, p_y1y2, d_y1y2 = mw_test(y1_h1.values, y2_h1.values)
pct = (y2_h1.mean() - k_h1.mean()) / k_h1.mean() * 100 if k_h1.mean() != 0 else np.nan
print(f'  Klopp: {k_h1.mean():.2f} | Y1: {y1_h1.mean():.2f} | Y2: {y2_h1.mean():.2f} ({pct:+.1f}% Klopp->Y2)')
print(f'  Klopp vs Y2: d={d_kv2:.2f} ({effect_label(d_kv2)}), p={p_kv2:.4f} '
      f'{"SIGNIFICANT" if not np.isnan(p_kv2) and p_kv2 < CONFIRMATORY_ALPHA else "—"}')
print(f'  Y1 vs Y2 [exploratory]: d={d_y1y2:.2f}, p={p_y1y2:.4f}')

print()
print('Cross-season LFC goals — H2:')
k_h2  = season_period['2023-24']['lfc_h2'].dropna()
y1_h2 = season_period['2024-25']['lfc_h2'].dropna()
y2_h2 = season_period['2025-26']['lfc_h2'].dropna()
_, p_kv2, d_kv2 = mw_test(k_h2.values, y2_h2.values)
_, p_y1y2, d_y1y2 = mw_test(y1_h2.values, y2_h2.values)
pct = (y2_h2.mean() - k_h2.mean()) / k_h2.mean() * 100 if k_h2.mean() != 0 else np.nan
print(f'  Klopp: {k_h2.mean():.2f} | Y1: {y1_h2.mean():.2f} | Y2: {y2_h2.mean():.2f} ({pct:+.1f}% Klopp->Y2)')
print(f'  Klopp vs Y2: d={d_kv2:.2f} ({effect_label(d_kv2)}), p={p_kv2:.4f} '
      f'{"SIGNIFICANT" if not np.isnan(p_kv2) and p_kv2 < CONFIRMATORY_ALPHA else "—"}')
print(f'  Y1 vs Y2 [exploratory]: d={d_y1y2:.2f}, p={p_y1y2:.4f}')

print()
print('Cross-season opponent goals — H2 (conceded):')
k_opp_h2  = season_period['2023-24']['opp_h2'].dropna()
y1_opp_h2 = season_period['2024-25']['opp_h2'].dropna()
y2_opp_h2 = season_period['2025-26']['opp_h2'].dropna()
_, p_kv2, d_kv2 = mw_test(k_opp_h2.values, y2_opp_h2.values)
_, p_y1y2, d_y1y2 = mw_test(y1_opp_h2.values, y2_opp_h2.values)
pct = (y2_opp_h2.mean() - k_opp_h2.mean()) / k_opp_h2.mean() * 100 if k_opp_h2.mean() != 0 else np.nan
print(f'  Klopp: {k_opp_h2.mean():.2f} | Y1: {y1_opp_h2.mean():.2f} | Y2: {y2_opp_h2.mean():.2f} ({pct:+.1f}% Klopp->Y2)')
print(f'  Klopp vs Y2: d={d_kv2:.2f} ({effect_label(d_kv2)}), p={p_kv2:.4f} '
      f'{"SIGNIFICANT" if not np.isnan(p_kv2) and p_kv2 < CONFIRMATORY_ALPHA else "—"}')
print(f'  Y1 vs Y2 [exploratory]: d={d_y1y2:.2f}, p={p_y1y2:.4f}')

# Plot: goals by half
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('Goals by Half — Liverpool Scored vs Conceded', fontsize=14, fontweight='bold')

for col_idx, s in enumerate(SEASON_ORDER):
    d = season_period[s].dropna(subset=['lfc_h1', 'lfc_h2', 'opp_h1', 'opp_h2'])

    ax_top = axes[0, col_idx]
    bp = ax_top.boxplot(
        [d['lfc_h1'].values, d['lfc_h2'].values],
        patch_artist=True,
        medianprops={'color': 'black', 'linewidth': 2},
    )
    for patch in bp['boxes']:
        patch.set_facecolor(SEASON_COLORS[s])
        patch.set_alpha(0.8)

    rng = np.random.default_rng(42)
    for i, vals in enumerate([d['lfc_h1'].values, d['lfc_h2'].values], 1):
        jitter = rng.uniform(-0.12, 0.12, len(vals))
        ax_top.scatter(i + jitter, vals, color=SEASON_COLORS[s], alpha=0.3, s=20, zorder=3)

    means = [d['lfc_h1'].mean(), d['lfc_h2'].mean()]
    ax_top.plot([1, 2], means, 'D-', color='black', markersize=8, zorder=5)
    for i, m in enumerate(means, 1):
        ax_top.text(i, m + 0.06, f'{m:.2f}', ha='center', fontsize=10, fontweight='bold')

    ax_top.set_xticks([1, 2])
    ax_top.set_xticklabels(['1st Half', '2nd Half'])
    ax_top.set_title(f'{SEASON_LABELS[s]}\nLFC Goals Scored', fontsize=11, fontweight='bold')
    ax_top.set_ylabel('Goals per Match')
    ax_top.grid(axis='y', alpha=0.3)

    ax_bot = axes[1, col_idx]
    bp2 = ax_bot.boxplot(
        [d['opp_h1'].values, d['opp_h2'].values],
        patch_artist=True,
        medianprops={'color': 'black', 'linewidth': 2},
    )
    for patch in bp2['boxes']:
        patch.set_facecolor('#e57373')
        patch.set_alpha(0.7)

    for i, vals in enumerate([d['opp_h1'].values, d['opp_h2'].values], 1):
        jitter = rng.uniform(-0.12, 0.12, len(vals))
        ax_bot.scatter(i + jitter, vals, color='#c62828', alpha=0.3, s=20, zorder=3)

    means2 = [d['opp_h1'].mean(), d['opp_h2'].mean()]
    ax_bot.plot([1, 2], means2, 'D-', color='black', markersize=8, zorder=5)
    for i, m in enumerate(means2, 1):
        ax_bot.text(i, m + 0.06, f'{m:.2f}', ha='center', fontsize=10, fontweight='bold')

    ax_bot.set_xticks([1, 2])
    ax_bot.set_xticklabels(['1st Half', '2nd Half'])
    ax_bot.set_title(f'{SEASON_LABELS[s]}\nGoals Conceded', fontsize=11, fontweight='bold')
    ax_bot.set_ylabel('Goals per Match')
    ax_bot.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'goals_by_half.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "goals_by_half.png"}')

# ── Section 2: Goal Timing Distribution ──────────────────────────────────────
goal_rows = []
skipped_events = []
total_dropped_goals = 0

for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']
    date   = meta_row['date']

    events_path = FIXTURES_DIR / str(fid) / 'events.csv'
    scores_path = FIXTURES_DIR / str(fid) / 'scores.csv'

    if not events_path.exists() or not scores_path.exists():
        skipped_events.append(fid)
        continue

    events = pd.read_csv(events_path)
    scores = pd.read_csv(scores_path)

    lfc_row = scores[scores['participant_id'] == 8]
    if len(lfc_row) == 0:
        skipped_events.append(fid)
        continue
    lfc_is_home = lfc_row.iloc[0]['participant'] == 'home'

    goal_events = events[events['result'].notna()].copy()
    if len(goal_events) == 0:
        continue

    all_periods = sorted(events['period_id'].dropna().unique())
    period_to_half = {}
    if len(all_periods) >= 1:
        period_to_half[all_periods[0]] = 'H1'
    if len(all_periods) >= 2:
        period_to_half[all_periods[1]] = 'H2'
    for p in all_periods[2:]:
        period_to_half[p] = 'H2'

    goal_events['minute_num'] = pd.to_numeric(goal_events['minute'], errors='coerce')
    goal_events = goal_events.sort_values(['minute_num', 'sort_order'])

    prev_home, prev_away = 0, 0
    fixture_dropped = 0
    for _, ev in goal_events.iterrows():
        try:
            parts = str(ev['result']).split('-')
            if len(parts) != 2:
                continue
            curr_home = int(parts[0])
            curr_away = int(parts[1])
        except (ValueError, AttributeError):
            continue

        if curr_home > prev_home:
            scorer_is_home = True
        elif curr_away > prev_away:
            scorer_is_home = False
        else:
            fixture_dropped += 1
            prev_home, prev_away = curr_home, curr_away
            continue

        lfc_scored = (scorer_is_home == lfc_is_home)

        minute = ev['minute']
        extra  = ev.get('extra_minute', np.nan)
        try:
            minute = float(minute)
        except (TypeError, ValueError):
            prev_home, prev_away = curr_home, curr_away
            continue

        half = period_to_half.get(ev.get('period_id'), 'H2')

        if minute <= 15:
            bin_label = '0-15'
        elif minute <= 30:
            bin_label = '15-30'
        elif minute <= 45:
            bin_label = '30-45'
        elif minute <= 60:
            bin_label = '45-60'
        elif minute <= 75:
            bin_label = '60-75'
        else:
            bin_label = '75-90+'

        goal_rows.append({
            'fixture_id': fid,
            'season':     season,
            'date':       date,
            'minute':     minute,
            'extra_min':  extra,
            'lfc_scored': lfc_scored,
            'bin_15':     bin_label,
            'half':       half,
        })

        prev_home, prev_away = curr_home, curr_away

    if fixture_dropped > 0:
        print(f'  WARNING: {fixture_dropped} goal event(s) dropped for fixture {fid} '
              f'due to ambiguous same-minute ordering.')
        total_dropped_goals += fixture_dropped

if skipped_events:
    print(f'Skipped {len(skipped_events)} fixtures missing events or scores csv')
if total_dropped_goals > 0:
    print(f'TOTAL dropped goal events across all fixtures: {total_dropped_goals}')
else:
    print('No goal events dropped — all same-minute orderings resolved cleanly.')

goals_df = pd.DataFrame(goal_rows)
goals_df['date'] = pd.to_datetime(goals_df['date'])

print(f'\nGoal events parsed: {len(goals_df)}')
print()
print('Goals parsed by season and scorer:')
print(goals_df.groupby(['season', 'lfc_scored']).size().unstack(fill_value=0))

# Per-match by 15-min bin
n_fixtures = processed.groupby('season').size()

BIN_ORDER = ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90+']

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Goal Timing Distribution — 15-Minute Intervals',
             fontsize=13, fontweight='bold')

for ax, lfc_scored, panel_title in [
    (axes[0], True,  'Liverpool Goals Scored'),
    (axes[1], False, 'Goals Conceded'),
]:
    subset = goals_df[goals_df['lfc_scored'] == lfc_scored]

    x = np.arange(len(BIN_ORDER))
    width = 0.27

    for i, s in enumerate(SEASON_ORDER):
        counts = subset[subset['season'] == s]['bin_15'].value_counts()
        vals = [counts.get(b, 0) / n_fixtures.get(s, 1) for b in BIN_ORDER]
        offset = (i - 1) * width
        bars = ax.bar(x + offset, vals, width,
                      label=SEASON_LABELS[s], color=SEASON_COLORS[s],
                      alpha=0.85, edgecolor='white')

    ax.set_xticks(x)
    ax.set_xticklabels(BIN_ORDER, fontsize=10)
    ax.set_xlabel('Match minute interval')
    ax.set_ylabel('Goals per match')
    ax.set_title(panel_title, fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)
    ax.axvspan(2.5, 5.6, alpha=0.04, color='gray', label='2nd half')
    ax.axvline(2.5, color='gray', linewidth=1, linestyle='--', alpha=0.5)
    ax.text(0.44, 0.97, 'H2 ->', transform=ax.transAxes, fontsize=9, alpha=0.6, va='top')

plt.tight_layout()
plt.savefig(FIG_DIR / 'goal_timing_15min.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "goal_timing_15min.png"}')

print()
print('Goals scored per match by 15-min bin (normalised by fixtures):')
for s in SEASON_ORDER:
    lfc_scored_s = goals_df[(goals_df['season'] == s) & (goals_df['lfc_scored'] == True)]
    counts = lfc_scored_s['bin_15'].value_counts()
    vals = {b: round(counts.get(b, 0) / n_fixtures.get(s, 1), 3) for b in BIN_ORDER}
    print(f'  {SEASON_LABELS[s]}: {vals}')

print()
print('Goals conceded per match by 15-min bin:')
for s in SEASON_ORDER:
    opp_s = goals_df[(goals_df['season'] == s) & (goals_df['lfc_scored'] == False)]
    counts = opp_s['bin_15'].value_counts()
    vals = {b: round(counts.get(b, 0) / n_fixtures.get(s, 1), 3) for b in BIN_ORDER}
    print(f'  {SEASON_LABELS[s]}: {vals}')

# ── Section 3: Ball Zone by Match Minute ─────────────────────────────────────
MIN_BINS = [0, 15, 30, 45, 60, 75, 91]
BIN_LABELS_TIME = ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90+']

zone_time_rows = []
skipped_coords = []

for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']

    path = FIXTURES_DIR / str(fid) / 'ball_coordinates.csv'
    if not path.exists():
        skipped_coords.append(fid)
        continue

    coords = pd.read_csv(path, usecols=['estimated_minute', 'pitch_zone'])
    coords = coords.dropna(subset=['estimated_minute'])

    if len(coords) == 0:
        skipped_coords.append(fid)
        continue

    coords['em_capped'] = coords['estimated_minute'].clip(upper=90.99)

    coords['bin'] = pd.cut(
        coords['em_capped'],
        bins=MIN_BINS,
        labels=BIN_LABELS_TIME,
        right=True,
        include_lowest=True,
    )

    row = {'fixture_id': fid, 'season': season}
    for bl in BIN_LABELS_TIME:
        bin_coords = coords[coords['bin'] == bl]
        n_bin = len(bin_coords)
        row[f'n_{bl}']       = n_bin
        row[f'att_pct_{bl}'] = (
            (bin_coords['pitch_zone'] == 'attacking_third').sum() / n_bin * 100
            if n_bin > 0 else np.nan
        )
    zone_time_rows.append(row)

if skipped_coords:
    print(f'\nSkipped {len(skipped_coords)} fixtures missing / empty ball_coordinates.csv')

if not zone_time_rows:
    print('No ball_coordinates data found. Section 3 disabled.')
    zone_time_df = None
else:
    zone_time_df = pd.DataFrame(zone_time_rows)
    print(f'\nBall zone-time data loaded for {len(zone_time_df)} fixtures')
    att_cols = [f'att_pct_{b}' for b in BIN_LABELS_TIME]
    print('Mean attacking-third % by 15-min bin and season:')
    print(zone_time_df.groupby('season')[att_cols].mean().round(1))

if zone_time_df is not None:
    att_cols = [f'att_pct_{b}' for b in BIN_LABELS_TIME]

    fig, ax = plt.subplots(figsize=(12, 6))

    x = np.arange(len(BIN_LABELS_TIME))

    for s in SEASON_ORDER:
        d = zone_time_df[zone_time_df['season'] == s]
        means = d[att_cols].mean().values
        sems  = d[att_cols].sem().values

        ax.plot(x, means, 'o-', color=SEASON_COLORS[s], linewidth=2.5,
                markersize=8, label=SEASON_LABELS[s], zorder=3)
        ax.fill_between(x, means - sems, means + sems,
                         color=SEASON_COLORS[s], alpha=0.15)

    ax.axvspan(2.5, 5.5, alpha=0.04, color='gray')
    ax.axvline(2.5, color='gray', linewidth=1.5, linestyle='--', alpha=0.6)
    ax.text(0.43, 0.98, '<- HT ->', transform=ax.transAxes, fontsize=9, alpha=0.6, va='top')

    ax.set_xticks(x)
    ax.set_xticklabels(BIN_LABELS_TIME, fontsize=11)
    ax.set_xlabel('Match minute interval')
    ax.set_ylabel('Attacking Third Occupancy (%)')
    ax.set_title('Attacking Third Presence by Match Minute\n'
                 '(per-fixture means +/- SE — absolute pitch zones, not Liverpool-direction-normalised)',
                 fontsize=12, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIG_DIR / 'perf_decay_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f'Saved {FIG_DIR / "perf_decay_curve.png"}')

    print()
    print('Statistical test: H1 vs H2 attacking-third presence'
          ' (within-season, Wilcoxon signed-rank, count-weighted bin means):')
    for s in SEASON_ORDER:
        d = zone_time_df[zone_time_df['season'] == s].copy()
        h1_bins = ['0-15', '15-30', '30-45']
        h2_bins = ['45-60', '60-75', '75-90+']

        def weighted_half_mean(row, bins):
            total_n = sum(row.get(f'n_{b}', 0) for b in bins)
            if total_n == 0:
                return np.nan
            return sum(
                row.get(f'att_pct_{b}', 0) * row.get(f'n_{b}', 0)
                for b in bins
                if not np.isnan(row.get(f'att_pct_{b}', np.nan))
            ) / total_n

        d['h1_weighted'] = d.apply(lambda r: weighted_half_mean(r, h1_bins), axis=1)
        d['h2_weighted'] = d.apply(lambda r: weighted_half_mean(r, h2_bins), axis=1)

        valid = d[['h1_weighted', 'h2_weighted']].dropna()
        if len(valid) >= 3:
            _, p = stats.wilcoxon(valid['h1_weighted'], valid['h2_weighted'],
                                  zero_method='wilcox')
            diff = valid['h2_weighted'].mean() - valid['h1_weighted'].mean()
            print(f'  {SEASON_LABELS[s]}: H1 att%={valid["h1_weighted"].mean():.1f}, '
                  f'H2 att%={valid["h2_weighted"].mean():.1f}, '
                  f'Delta={diff:+.2f}pp, p={p:.4f} (exploratory — not Bonferroni corrected)')
        else:
            print(f'  {SEASON_LABELS[s]}: insufficient data for Wilcoxon test')
else:
    print('Section 3 skipped — no ball_coordinates data available.')

# ── Section 4: Substitution Patterns ─────────────────────────────────────────
sub_stats = []
for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']
    path   = FIXTURES_DIR / str(fid) / 'statistics.csv'
    if not path.exists():
        continue
    df = pd.read_csv(path)
    lfc = df[(df['participant_id'] == 8) & (df['type_id'] == 59)]
    if len(lfc) > 0:
        sub_stats.append({'fixture_id': fid, 'season': season, 'substitutions': lfc['value'].iloc[0]})

sub_df = pd.DataFrame(sub_stats) if sub_stats else pd.DataFrame(columns=['fixture_id', 'season', 'substitutions'])
print('\nSubstitutions per match by season (from statistics.csv type_id=59):')
if len(sub_df) > 0:
    print(sub_df.groupby('season')['substitutions'].agg(['mean', 'std', 'count']).round(2))

# Heuristic substitution timing
sub_timing_rows = []

for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']

    path = FIXTURES_DIR / str(fid) / 'events.csv'
    if not path.exists():
        continue

    events = pd.read_csv(path)
    potential_subs = events[
        events['result'].isna() &
        events['info'].isna()
    ].copy()

    if len(potential_subs) == 0:
        continue

    minute_counts = potential_subs.groupby('minute').size()
    sub_minutes   = minute_counts[minute_counts >= 2].index

    for minute in sub_minutes:
        sub_timing_rows.append({
            'fixture_id': fid,
            'season':     season,
            'sub_minute': float(minute),
        })

sub_timing_df = pd.DataFrame(sub_timing_rows) if sub_timing_rows else pd.DataFrame(
    columns=['fixture_id', 'season', 'sub_minute'])

print(f'\nHeuristic substitution events identified: {len(sub_timing_df)}')
print('IMPORTANT: This is a proxy — not direct substitution event data.')

if len(sub_timing_df) > 0:
    print('\nSubstitution timing distribution by season:')
    for s in SEASON_ORDER:
        d = sub_timing_df[(sub_timing_df['season'] == s) & (sub_timing_df['sub_minute'] > 45)]
        if len(d) > 0:
            print(f'  {SEASON_LABELS[s]} (H2 subs): median={d["sub_minute"].median():.0f}min, '
                  f'mean={d["sub_minute"].mean():.1f}min, n={len(d)}')

# Validate heuristic
if len(sub_timing_df) > 0 and len(sub_df) > 0:
    heuristic_counts = (
        sub_timing_df.groupby('fixture_id').size()
        .reset_index(name='heuristic_count')
    )
    comparison = sub_df.merge(heuristic_counts, on='fixture_id', how='left')
    comparison['heuristic_count'] = comparison['heuristic_count'].fillna(0).astype(int)
    comparison['stats_sub_int'] = comparison['substitutions'].astype(int)
    comparison['expected_heuristic'] = comparison['stats_sub_int'] * 2
    comparison['close'] = (
        (comparison['heuristic_count'] - comparison['expected_heuristic']).abs() <= 1
    )

    accuracy = comparison['close'].mean()
    print(f'\nSubstitution heuristic accuracy (within +/-1 of 2×LFC_subs): '
          f'{accuracy:.1%} ({comparison["close"].sum()}/{len(comparison)} fixtures)')
    print('NOTE: If accuracy < 70%, the substitution timing analysis is unreliable.')

# Plot: substitution patterns
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('Substitution Patterns by Season\n(timing = heuristic proxy from event pairs)',
             fontsize=12, fontweight='bold')

ax1 = axes[0]
if len(sub_df) > 0:
    season_subs = {s: sub_df[sub_df['season'] == s]['substitutions'].dropna().values
                   for s in SEASON_ORDER}
    bp = ax1.boxplot(
        [season_subs[s] for s in SEASON_ORDER],
        patch_artist=True,
        medianprops={'color': 'black', 'linewidth': 2},
    )
    for patch, s in zip(bp['boxes'], SEASON_ORDER):
        patch.set_facecolor(SEASON_COLORS[s])
        patch.set_alpha(0.8)
    means = [np.mean(season_subs[s]) if len(season_subs[s]) > 0 else 0 for s in SEASON_ORDER]
    ax1.plot(range(1, 4), means, 'D-', color='black', markersize=8, zorder=5)
    for i, m in enumerate(means, 1):
        ax1.text(i, m + 0.05, f'{m:.1f}', ha='center', fontsize=10, fontweight='bold')
    ax1.set_xticks(range(1, 4))
    ax1.set_xticklabels(TICK_LABELS)
    ax1.set_title('Substitutions per Match\n(statistics.csv type_id=59)', fontsize=11)
    ax1.set_ylabel('Substitutions')
    ax1.grid(axis='y', alpha=0.3)
else:
    ax1.text(0.5, 0.5, 'No substitution data', ha='center', va='center', transform=ax1.transAxes)

ax2 = axes[1]
if len(sub_timing_df) > 0:
    h2_subs = sub_timing_df[sub_timing_df['sub_minute'] > 45]
    if len(h2_subs) > 0:
        for s in SEASON_ORDER:
            d = h2_subs[h2_subs['season'] == s]['sub_minute']
            if len(d) > 0:
                ax2.hist(d, bins=range(45, 96, 5), density=True, alpha=0.5,
                         color=SEASON_COLORS[s], label=SEASON_LABELS[s], edgecolor='white')
                ax2.axvline(d.mean(), color=SEASON_COLORS[s], linewidth=2,
                            linestyle='--', alpha=0.9)
        ax2.set_xlabel('Match minute')
        ax2.set_ylabel('Density')
        ax2.set_title('H2 Substitution Timing Distribution\n(heuristic — paired un-labelled events)',
                      fontsize=11)
        ax2.legend(fontsize=9)
        ax2.grid(alpha=0.3)
        ax2.text(0.98, 0.97,
                 'Proxy: not directly observed sub data',
                 transform=ax2.transAxes, ha='right', va='top', fontsize=8,
                 color='gray', style='italic')
    else:
        ax2.text(0.5, 0.5, 'No H2 sub events found', ha='center', va='center', transform=ax2.transAxes)
else:
    ax2.text(0.5, 0.5, 'No substitution timing data', ha='center', va='center', transform=ax2.transAxes)

plt.tight_layout()
plt.savefig(FIG_DIR / 'sub_timing.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "sub_timing.png"}')

# ── Section 5: Full-Match Attacking Context ───────────────────────────────────
CONTEXT_METRICS = {
    42:  'shots_total',
    580: 'big_chances_created',
    86:  'shots_on_target',
}

ctx_rows = []
for _, meta_row in processed.iterrows():
    fid    = meta_row['fixture_id']
    season = meta_row['season']
    path   = FIXTURES_DIR / str(fid) / 'statistics.csv'
    if not path.exists():
        continue
    df = pd.read_csv(path)
    lfc = df[df['participant_id'] == 8]
    for tid, col in CONTEXT_METRICS.items():
        val = lfc[lfc['type_id'] == tid]['value']
        ctx_rows.append({
            'fixture_id': fid, 'season': season,
            'metric': col,
            'value': val.iloc[0] if len(val) > 0 else np.nan
        })

ctx_df = pd.DataFrame(ctx_rows)
ctx_pivot = ctx_df.pivot_table(
    index=['fixture_id', 'season'], columns='metric', values='value', aggfunc='first'
).reset_index()

ctx_merged = ctx_pivot.merge(period_df[['fixture_id', 'lfc_h1', 'lfc_h2', 'opp_h1', 'opp_h2']],
                              on='fixture_id', how='inner')

print('\nSeason means — full-match attacking context:')
print(ctx_merged.groupby('season')[['shots_total', 'shots_on_target', 'big_chances_created',
                                    'lfc_h1', 'lfc_h2']].mean().round(2))

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle('Full-Match Attacking Context by Season\n'
             '(full-match aggregates only — not split by half)',
             fontsize=12, fontweight='bold')

for ax, (col, label) in zip(axes, [
    ('shots_total',         'Shots Total'),
    ('shots_on_target',     'Shots On Target'),
    ('big_chances_created', 'Big Chances Created'),
]):
    data_per_season = [ctx_merged[ctx_merged['season'] == s][col].dropna().values
                       for s in SEASON_ORDER]

    bp = ax.boxplot(data_per_season, patch_artist=True,
                    medianprops={'color': 'black', 'linewidth': 2})
    for patch, s in zip(bp['boxes'], SEASON_ORDER):
        patch.set_facecolor(SEASON_COLORS[s])
        patch.set_alpha(0.8)

    means = [np.mean(d) if len(d) > 0 else 0 for d in data_per_season]
    ax.plot(range(1, 4), means, 'D-', color='black', markersize=8, zorder=5)
    for i, m in enumerate(means, 1):
        ax.text(i, m + 0.1, f'{m:.1f}', ha='center', fontsize=10, fontweight='bold')

    ax.set_xticks(range(1, 4))
    ax.set_xticklabels(TICK_LABELS, fontsize=9)
    ax.set_title(label, fontsize=11, fontweight='bold')
    ax.set_ylabel('Per Match')
    ax.grid(axis='y', alpha=0.3)

    k_vals  = data_per_season[0]
    y2_vals = data_per_season[2]
    U, p, d = mw_test(k_vals, y2_vals)
    if not np.isnan(p):
        sig = 'SIG' if p < CONFIRMATORY_ALPHA else '—'
        ax.text(0.5, 0.02, f'K vs Y2: d={d:.2f}, p={p:.3f} {sig}',
                transform=ax.transAxes, ha='center', fontsize=8, style='italic')

plt.tight_layout()
plt.savefig(FIG_DIR / 'fullmatch_context.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "fullmatch_context.png"}')

print()
print('Confirmatory tests (Bonferroni alpha = 0.0125):')
for col, label in [('shots_total', 'Shots Total'),
                   ('shots_on_target', 'Shots On Target'),
                   ('big_chances_created', 'Big Chances Created')]:
    k  = ctx_merged[ctx_merged['season'] == '2023-24'][col].dropna().values
    y2 = ctx_merged[ctx_merged['season'] == '2025-26'][col].dropna().values
    U, p, d = mw_test(k, y2)
    pct = (y2.mean() - k.mean()) / k.mean() * 100 if k.mean() != 0 else np.nan
    if not np.isnan(p):
        print(f'  {label}: Klopp {k.mean():.2f} -> Y2 {y2.mean():.2f} ({pct:+.1f}%), '
              f'd={d:.2f} ({effect_label(d)}), p={p:.4f} '
              f'{"SIGNIFICANT" if p < CONFIRMATORY_ALPHA else "—"}')

# ── Section 6: Summary ─────────────────────────────────────────────────────────
print('\n=== SECOND-HALF VULNERABILITY — KEY FINDINGS SUMMARY ===')
print()

print('Goals per half by season (per match):')
print(period_df.groupby('season')[['lfc_h1', 'lfc_h2', 'opp_h1', 'opp_h2']]
      .mean().round(2)
      .rename(columns={'lfc_h1': 'LFC_H1', 'lfc_h2': 'LFC_H2',
                       'opp_h1': 'Opp_H1', 'opp_h2': 'Opp_H2'}))

print()
for s in SEASON_ORDER:
    d = period_df[period_df['season'] == s]
    lfc_h1 = d['lfc_h1'].mean()
    lfc_h2 = d['lfc_h2'].mean()
    opp_h1 = d['opp_h1'].mean()
    opp_h2 = d['opp_h2'].mean()
    ratio  = lfc_h2 / lfc_h1 if lfc_h1 > 0 else np.nan
    print(f'{SEASON_LABELS[s]}:')
    print(f'  LFC goals: H1={lfc_h1:.2f}, H2={lfc_h2:.2f} (H2/H1 ratio: {ratio:.2f})')
    print(f'  Goals conceded: H1={opp_h1:.2f}, H2={opp_h2:.2f}')

if len(goals_df) > 0:
    print()
    print('Goal timing bin with most Y2 goals conceded:')
    y2_conc = goals_df[(goals_df['season'] == '2025-26') & (goals_df['lfc_scored'] == False)]
    n_y2 = n_fixtures['2025-26']
    if len(y2_conc) > 0:
        per_match = (y2_conc['bin_15'].value_counts() / n_y2).round(3)
        peak_bin  = per_match.idxmax()
        print(f'  Peak vulnerability bin: {peak_bin} ({per_match[peak_bin]:.3f} goals/match)')
        print(f'  Full breakdown: {per_match.reindex(BIN_ORDER).to_dict()}')

# Summary visualisation
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle('H1 vs H2 Goal Comparison — Season Overview', fontsize=13, fontweight='bold')

for ax, (side, title) in zip(axes, [(True, 'Liverpool Goals Scored'), (False, 'Goals Conceded')]):
    h1_col = 'lfc_h1' if side else 'opp_h1'
    h2_col = 'lfc_h2' if side else 'opp_h2'

    h1_means = [period_df[period_df['season'] == s][h1_col].mean() for s in SEASON_ORDER]
    h2_means = [period_df[period_df['season'] == s][h2_col].mean() for s in SEASON_ORDER]

    x     = np.arange(3)
    width = 0.38

    bars1 = ax.bar(x - width/2, h1_means, width, label='1st Half',
                   color=[SEASON_COLORS[s] for s in SEASON_ORDER], alpha=0.9,
                   edgecolor='white', hatch='')
    bars2 = ax.bar(x + width/2, h2_means, width, label='2nd Half',
                   color=[SEASON_COLORS[s] for s in SEASON_ORDER], alpha=0.55,
                   edgecolor='white', hatch='//')

    for bars, means in [(bars1, h1_means), (bars2, h2_means)]:
        for bar, m in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{m:.2f}', ha='center', fontsize=9, fontweight='bold')

    ax.set_xticks(x)
    ax.set_xticklabels(TICK_LABELS, fontsize=10)
    ax.set_title(title, fontsize=11, fontweight='bold')
    ax.set_ylabel('Goals per Match')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIG_DIR / 'h1_h2_summary.png', dpi=150, bbox_inches='tight')
plt.close()
print(f'Saved {FIG_DIR / "h1_h2_summary.png"}')

print('\nScript complete. All figures saved to figures/06_second_half/')
