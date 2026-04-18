"""
Deep Dive 1.4: Game-State Tactical Shifts.
Run from repo root: poetry run python scripts/analysis/02_game_state_tactics.py
"""
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings

warnings.filterwarnings('ignore')

PROCESSED_DIR = Path("data/processed")
FIXTURES_DIR = PROCESSED_DIR / "fixtures"
METADATA_DIR = PROCESSED_DIR / "metadata"
FIG_DIR = Path("figures/02_game_state")
FIG_DIR.mkdir(parents=True, exist_ok=True)

LIVERPOOL_ID = 8
SEASON_LABELS = {21646: "Klopp 23-24", 23614: "Slot Y1 24-25", 25583: "Slot Y2 25-26"}
SEASON_SHORT = {21646: "Klopp", 23614: "Y1", 25583: "Y2"}
SEASON_IDS = [21646, 23614, 25583]
SEASON_COLORS = {21646: "#c8102e", 23614: "#f6eb61", 25583: "#00b2a9"}
STATE_COLORS = {"WIN": "#2E7D32", "DRAW": "#F57C00", "LOSS": "#C62828"}
STATE_ORDER = ["WIN", "DRAW", "LOSS"]

from liverpool_strategy.analysis.game_state import (
    get_lfc_is_home, reconstruct_game_states, get_state_at_minute, final_score
)
from liverpool_strategy.analysis.notebook_helpers import cohens_d, effect_label, mw_test

# ── Load fixture metadata ─────────────────────────────────────────────────────
fixture_map = pd.read_csv(METADATA_DIR / "fixture_season_mapping.csv")
processed = fixture_map[fixture_map["has_processed_data"] == True].copy()

processed["lfc_is_home"] = processed["fixture_id"].apply(
    lambda fid: get_lfc_is_home(fid, FIXTURES_DIR, LIVERPOOL_ID)
)
processed = processed.dropna(subset=["lfc_is_home"]).copy()
processed["lfc_is_home"] = processed["lfc_is_home"].astype(bool)

season_counts = processed.groupby("season_id")["fixture_id"].count()
print(f"Fixtures with processed data: {len(processed)}")
for sid in SEASON_IDS:
    n = season_counts.get(sid, 0)
    home = processed[(processed["season_id"] == sid) & (processed["lfc_is_home"] == True)].shape[0]
    print(f"  {SEASON_LABELS[sid]}: {n} fixtures ({home} home, {n - home} away)")

# ── Build game state intervals for all fixtures ───────────────────────────────
fixture_states = {}

for _, row in processed.iterrows():
    fid = int(row["fixture_id"])
    events_path = FIXTURES_DIR / str(fid) / "events.csv"
    if not events_path.exists():
        continue

    events_df = pd.read_csv(events_path)
    intervals = reconstruct_game_states(events_df, row["lfc_is_home"])

    lfc_g, opp_g = final_score(intervals)
    if lfc_g > opp_g:
        result = "W"
    elif lfc_g < opp_g:
        result = "L"
    else:
        result = "D"

    fixture_states[fid] = {
        "intervals": intervals,
        "season_id": int(row["season_id"]),
        "season": row["season"],
        "manager": row["manager"],
        "lfc_is_home": row["lfc_is_home"],
        "lfc_goals": lfc_g,
        "opp_goals": opp_g,
        "result": result,
        "n_goals": lfc_g + opp_g,
    }

print(f"\nGame states built for {len(fixture_states)} fixtures")

# ── Validation: reconstructed scores vs scores.csv ───────────────────────────
mismatches = []
scores_checked = 0

for fid, meta in fixture_states.items():
    scores_path = FIXTURES_DIR / str(fid) / "scores.csv"
    if not scores_path.exists():
        continue

    sc = pd.read_csv(scores_path)
    current = sc[sc["description"] == "CURRENT"]
    if current.empty:
        lfc_sc = sc[sc["participant_id"] == LIVERPOOL_ID]["goals"].sum()
    else:
        lfc_row = current[current["participant_id"] == LIVERPOOL_ID]
        lfc_sc = int(lfc_row["goals"].iloc[0]) if not lfc_row.empty else None

    if lfc_sc is not None:
        scores_checked += 1
        if lfc_sc != meta["lfc_goals"]:
            mismatches.append({
                "fixture_id": fid,
                "reconstructed_lfc": meta["lfc_goals"],
                "scores_csv_lfc": lfc_sc,
                "season": meta["season"],
            })

print(f"Validated {scores_checked} fixtures against scores.csv")
print(f"Mismatches: {len(mismatches)}")
if mismatches:
    print(pd.DataFrame(mismatches).to_string(index=False))

# ── Part 2: Win / Draw / Loss record by season ────────────────────────────────
records = []
for fid, meta in fixture_states.items():
    records.append({
        "fixture_id": fid,
        "season_id": meta["season_id"],
        "season": meta["season"],
        "result": meta["result"],
        "lfc_goals": meta["lfc_goals"],
        "opp_goals": meta["opp_goals"],
        "n_goals": meta["n_goals"],
        "lfc_is_home": meta["lfc_is_home"],
    })

results_df = pd.DataFrame(records)

summary = []
for sid in SEASON_IDS:
    sub = results_df[results_df["season_id"] == sid]
    n = len(sub)
    wins = (sub["result"] == "W").sum()
    draws = (sub["result"] == "D").sum()
    losses = (sub["result"] == "L").sum()
    gf = sub["lfc_goals"].sum()
    ga = sub["opp_goals"].sum()
    pts = wins * 3 + draws
    ppg = pts / n if n > 0 else 0
    summary.append({
        "Season": SEASON_LABELS[sid],
        "Games": n,
        "W": wins, "D": draws, "L": losses,
        "GF": gf, "GA": ga, "GD": gf - ga,
        "Pts": pts, "PPG": round(ppg, 2),
    })

summary_df = pd.DataFrame(summary)
print("\nMatch outcome summary:")
print(summary_df.to_string(index=False))

# Plot: outcome distribution
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
fig.suptitle("Match Outcome Distribution by Season", fontsize=14, fontweight="bold", y=1.02)

ax = axes[0]
season_names = [SEASON_LABELS[sid] for sid in SEASON_IDS]
wins_list  = [summary_df.loc[summary_df["Season"] == SEASON_LABELS[sid], "W"].iloc[0] for sid in SEASON_IDS]
draws_list = [summary_df.loc[summary_df["Season"] == SEASON_LABELS[sid], "D"].iloc[0] for sid in SEASON_IDS]
losses_list= [summary_df.loc[summary_df["Season"] == SEASON_LABELS[sid], "L"].iloc[0] for sid in SEASON_IDS]

x = np.arange(len(SEASON_IDS))
w = 0.55
ax.bar(x, wins_list, w, label="Win",  color=STATE_COLORS["WIN"],  alpha=0.85)
ax.bar(x, draws_list, w, bottom=wins_list, label="Draw", color=STATE_COLORS["DRAW"], alpha=0.85)
ax.bar(x, losses_list, w, bottom=[wins_list[i] + draws_list[i] for i in range(3)],
       label="Loss", color=STATE_COLORS["LOSS"], alpha=0.85)

for i, sid in enumerate(SEASON_IDS):
    ppg = summary_df.loc[summary_df["Season"] == SEASON_LABELS[sid], "PPG"].iloc[0]
    total = wins_list[i] + draws_list[i] + losses_list[i]
    ax.text(i, total + 0.5, f"{ppg} PPG", ha="center", va="bottom", fontsize=9, fontweight="bold")

ax.set_xticks(x)
ax.set_xticklabels(season_names, fontsize=9)
ax.set_ylabel("Number of matches")
ax.set_title("W/D/L Record")
ax.legend(loc="upper right", fontsize=8)
ax.set_ylim(0, max([w + d + l for w, d, l in zip(wins_list, draws_list, losses_list)]) + 5)

ax2 = axes[1]
ppg_vals = [summary_df.loc[summary_df["Season"] == SEASON_LABELS[sid], "PPG"].iloc[0] for sid in SEASON_IDS]
bars = ax2.bar(x, ppg_vals, w, color=[SEASON_COLORS[sid] for sid in SEASON_IDS], alpha=0.85)
for bar, ppg in zip(bars, ppg_vals):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
             f"{ppg:.2f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
ax2.set_xticks(x)
ax2.set_xticklabels(season_names, fontsize=9)
ax2.set_ylabel("Points per game")
ax2.set_title("Points per Game")
ax2.set_ylim(0, 3.0)
ax2.axhline(2.0, color="grey", linestyle="--", linewidth=0.8, alpha=0.6)

plt.tight_layout()
plt.savefig(FIG_DIR / "outcome_distribution.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {FIG_DIR / 'outcome_distribution.png'}")

# ── Part 3: Lead Management ───────────────────────────────────────────────────
transition_records = []

for fid, meta in fixture_states.items():
    intervals = meta["intervals"]
    sid = meta["season_id"]

    states_seq = [s for (_, _, _, s) in intervals]

    ever_led = any(s == "WIN" for s in states_seq)
    ever_trailed = any(s == "LOSS" for s in states_seq)

    lead_blown = False
    comeback = False
    for i in range(1, len(states_seq)):
        if states_seq[i - 1] == "WIN" and states_seq[i] in ("DRAW", "LOSS"):
            lead_blown = True
        if states_seq[i - 1] == "LOSS" and states_seq[i] in ("DRAW", "WIN"):
            comeback = True

    final_state = states_seq[-1]
    lead_held = (ever_led and final_state == "WIN")
    lead_blown_perm = (ever_led and final_state != "WIN" and lead_blown)

    bc_path = FIXTURES_DIR / str(fid) / "ball_coordinates.csv"
    if bc_path.exists():
        bc_meta = pd.read_csv(bc_path, usecols=["estimated_minute"]).dropna()
        match_duration = int(np.ceil(bc_meta["estimated_minute"].max())) if len(bc_meta) > 0 else 90
    else:
        match_duration = 90

    minutes_in_state = {"WIN": 0, "DRAW": 0, "LOSS": 0}
    for i, (m, _lg, _og, s) in enumerate(intervals):
        end = intervals[i + 1][0] if i + 1 < len(intervals) else match_duration
        end = min(end, match_duration)
        start = min(m, match_duration)
        duration = max(0, end - start)
        minutes_in_state[s] = minutes_in_state.get(s, 0) + duration

    total_minutes = sum(minutes_in_state.values()) or match_duration

    transition_records.append({
        "fixture_id": fid,
        "season_id": sid,
        "season": meta["season"],
        "result": meta["result"],
        "match_duration": match_duration,
        "ever_led": ever_led,
        "ever_trailed": ever_trailed,
        "lead_blown": lead_blown,
        "comeback": comeback,
        "lead_held": lead_held,
        "lead_blown_perm": lead_blown_perm,
        "minutes_win": minutes_in_state["WIN"],
        "minutes_draw": minutes_in_state["DRAW"],
        "minutes_loss": minutes_in_state["LOSS"],
        "pct_win": minutes_in_state["WIN"] / total_minutes,
        "pct_draw": minutes_in_state["DRAW"] / total_minutes,
        "pct_loss": minutes_in_state["LOSS"] / total_minutes,
    })

trans_df = pd.DataFrame(transition_records)

lead_summary = []
for sid in SEASON_IDS:
    sub = trans_df[trans_df["season_id"] == sid]
    n = len(sub)
    ever_led_n = sub['ever_led'].sum()
    ever_trailed_n = sub['ever_trailed'].sum()
    lead_held_n = sub['lead_held'].sum()
    lead_blown_n = sub['lead_blown_perm'].sum()
    comeback_n = sub['comeback'].sum()
    lead_summary.append({
        "Season": SEASON_SHORT[sid],
        "Games": n,
        "Ever Led": f"{ever_led_n} ({ever_led_n/n*100:.0f}%)",
        "Ever Trailed": f"{ever_trailed_n} ({ever_trailed_n/n*100:.0f}%)",
        "Lead Held": f"{lead_held_n} of {ever_led_n}",
        "Lead Blown": f"{lead_blown_n} of {ever_led_n}",
        "Comeback": f"{comeback_n} of {ever_trailed_n}",
        "% Time Winning": f"{sub['pct_win'].mean()*100:.1f}%",
    })

print("\nLead management summary:")
print(pd.DataFrame(lead_summary).to_string(index=False))

# Plot: lead management
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
fig.suptitle("Lead Management by Season", fontsize=14, fontweight="bold", y=1.02)

ax = axes[0]
for i, sid in enumerate(SEASON_IDS):
    sub = trans_df[trans_df["season_id"] == sid]
    means = [sub["pct_win"].mean(), sub["pct_draw"].mean(), sub["pct_loss"].mean()]
    x = np.arange(3) + i * 0.28 - 0.28
    ax.bar(x, [m * 100 for m in means], 0.25,
           color=SEASON_COLORS[sid], alpha=0.85,
           label=SEASON_SHORT[sid])
ax.set_xticks([0, 1, 2])
ax.set_xticklabels(["Winning", "Level", "Losing"])
ax.set_ylabel("% of match time")
ax.set_title("Avg % Time in Each State")
ax.legend(fontsize=8)

ax2 = axes[1]
for i, sid in enumerate(SEASON_IDS):
    sub = trans_df[trans_df["season_id"] == sid]
    ever_led = sub[sub["ever_led"]]
    if len(ever_led) == 0:
        continue
    held_pct = ever_led["lead_held"].mean() * 100
    blown_pct = ever_led["lead_blown"].mean() * 100
    x = np.arange(2) + i * 0.28 - 0.28
    ax2.bar(x, [held_pct, blown_pct], 0.25,
            color=SEASON_COLORS[sid], alpha=0.85, label=SEASON_SHORT[sid])
ax2.set_xticks([0, 1])
ax2.set_xticklabels(["Lead Held", "Lead Blown"])
ax2.set_ylabel("% of matches where Liverpool led")
ax2.set_title("Lead Held vs Lead Blown")
ax2.legend(fontsize=8)

ax3 = axes[2]
for i, sid in enumerate(SEASON_IDS):
    sub = trans_df[trans_df["season_id"] == sid]
    ever_trailed = sub[sub["ever_trailed"]]
    if len(ever_trailed) == 0:
        continue
    comeback_pct = ever_trailed["comeback"].mean() * 100
    no_comeback_pct = 100 - comeback_pct
    x = np.arange(2) + i * 0.28 - 0.28
    ax3.bar(x, [comeback_pct, no_comeback_pct], 0.25,
            color=SEASON_COLORS[sid], alpha=0.85, label=SEASON_SHORT[sid])
ax3.set_xticks([0, 1])
ax3.set_xticklabels(["Comeback", "No Comeback"])
ax3.set_ylabel("% of matches where Liverpool trailed")
ax3.set_title("Comeback Rate")
ax3.legend(fontsize=8)

plt.tight_layout()
plt.savefig(FIG_DIR / "lead_management.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {FIG_DIR / 'lead_management.png'}")

# ── Statistical tests ─────────────────────────────────────────────────────────
print("\n=== STATISTICAL TESTS — % of match time in WIN state ===")

# Bonferroni threshold for 3 game-state comparisons (WIN%, DRAW%, LOSS%)
ALPHA_GAME_STATE = 0.05 / 3

klopp_win = trans_df[trans_df["season_id"] == 21646]["pct_win"].values
y1_win    = trans_df[trans_df["season_id"] == 23614]["pct_win"].values
y2_win    = trans_df[trans_df["season_id"] == 25583]["pct_win"].values

U, p, d = mw_test(klopp_win, y2_win)
print(f"\n[CONFIRMATORY] Klopp vs Slot Y2 — % time winning")
print(f"  Klopp: {np.mean(klopp_win):.1%} +/- {np.std(klopp_win, ddof=1):.1%}")
print(f"  Slot Y2: {np.mean(y2_win):.1%} +/- {np.std(y2_win, ddof=1):.1%}")
print(f"  Mann-Whitney U={U:.1f}, p={p:.4f}, d={d:.2f}")
print(f"  Game-state threshold (a/3={ALPHA_GAME_STATE:.4f}): {'SIGNIFICANT' if p < ALPHA_GAME_STATE else 'not significant'}")

U2, p2, d2 = mw_test(y1_win, y2_win)
print(f"\n[EXPLORATORY] Slot Y1 vs Slot Y2 — % time winning")
print(f"  Slot Y1: {np.mean(y1_win):.1%} +/- {np.std(y1_win, ddof=1):.1%}")
print(f"  Slot Y2: {np.mean(y2_win):.1%} +/- {np.std(y2_win, ddof=1):.1%}")
print(f"  Mann-Whitney U={U2:.1f}, p={p2:.4f}, d={d2:.2f}")
print(f"  Nominal p < 0.05 -> {'directional signal' if p2 < 0.05 else 'no signal'}")

klopp_loss = trans_df[trans_df["season_id"] == 21646]["pct_loss"].values
y1_loss    = trans_df[trans_df["season_id"] == 23614]["pct_loss"].values
y2_loss    = trans_df[trans_df["season_id"] == 25583]["pct_loss"].values

print("\n--- % time losing ---")
U3, p3, d3 = mw_test(klopp_loss, y2_loss)
print(f"\n[CONFIRMATORY] Klopp vs Slot Y2 — % time losing")
print(f"  Klopp: {np.mean(klopp_loss):.1%} +/- {np.std(klopp_loss, ddof=1):.1%}")
print(f"  Slot Y2: {np.mean(y2_loss):.1%} +/- {np.std(y2_loss, ddof=1):.1%}")
print(f"  Mann-Whitney U={U3:.1f}, p={p3:.4f}, d={d3:.2f}")
print(f"  Game-state threshold (a/3={ALPHA_GAME_STATE:.4f}): {'SIGNIFICANT' if p3 < ALPHA_GAME_STATE else 'not significant'}")

# ── Part 4: Goals by Game State ───────────────────────────────────────────────
goal_state_records = []

for fid, meta in fixture_states.items():
    intervals = meta["intervals"]
    sid = meta["season_id"]

    for i in range(1, len(intervals)):
        prev_min, prev_lfc, prev_opp, prev_state = intervals[i - 1]
        curr_min, curr_lfc, curr_opp, curr_state = intervals[i]

        if curr_lfc > prev_lfc:
            scorer = "liverpool"
        elif curr_opp > prev_opp:
            scorer = "opponent"
        else:
            scorer = "unknown"

        goal_state_records.append({
            "fixture_id": fid,
            "season_id": sid,
            "season": meta["season"],
            "minute": curr_min,
            "scorer": scorer,
            "state_before": prev_state,
            "state_after": curr_state,
        })

goals_by_state_df = pd.DataFrame(goal_state_records)

print(f"\nTotal goal events: {len(goals_by_state_df)}")
print(f"Liverpool goals: {(goals_by_state_df['scorer'] == 'liverpool').sum()}")
print(f"Opponent goals: {(goals_by_state_df['scorer'] == 'opponent').sum()}")

for scorer_type, label in [("liverpool", "Goals SCORED by Liverpool"), ("opponent", "Goals CONCEDED by Liverpool")]:
    sub = goals_by_state_df[goals_by_state_df["scorer"] == scorer_type]
    pivot = sub.groupby(["season_id", "state_before"]).size().unstack(fill_value=0)
    pivot.index = [SEASON_SHORT[sid] for sid in pivot.index]
    print(f"\n{label} (by game state at time of goal):")
    cols = [c for c in STATE_ORDER if c in pivot.columns]
    counts = trans_df.groupby("season_id")["fixture_id"].count()
    print(pivot[cols].to_string())
    print("  (per match averages:)")
    for sid in SEASON_IDS:
        n = counts.get(sid, 1)
        sname = SEASON_SHORT[sid]
        if sname in pivot.index:
            row = pivot.loc[sname, cols]
            per_match = (row / n).round(2)
            print(f"    {sname}: " + " | ".join([f"{c}={v:.2f}" for c, v in zip(cols, per_match)]))

# Plot: goals by game state
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Goals Scored and Conceded by Game State", fontsize=14, fontweight="bold", y=1.02)

for ax_idx, (scorer_type, title) in enumerate([
    ("liverpool", "Goals Scored by Liverpool"),
    ("opponent",  "Goals Conceded by Liverpool"),
]):
    ax = axes[ax_idx]
    sub = goals_by_state_df[goals_by_state_df["scorer"] == scorer_type]

    plot_data = []
    for sid in SEASON_IDS:
        n = trans_df[trans_df["season_id"] == sid]["fixture_id"].count()
        for state in STATE_ORDER:
            count = sub[(sub["season_id"] == sid) & (sub["state_before"] == state)].shape[0]
            plot_data.append({"season_id": sid, "state": state, "per_match": count / n if n > 0 else 0})

    plot_df = pd.DataFrame(plot_data)

    x = np.arange(len(STATE_ORDER))
    width = 0.25
    for i, sid in enumerate(SEASON_IDS):
        vals = [plot_df[(plot_df["season_id"] == sid) & (plot_df["state"] == s)]["per_match"].iloc[0]
                for s in STATE_ORDER]
        bars = ax.bar(x + (i - 1) * width, vals, width,
                      color=SEASON_COLORS[sid], alpha=0.85, label=SEASON_SHORT[sid])
        for bar, v in zip(bars, vals):
            if v > 0.02:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                        f"{v:.2f}", ha="center", va="bottom", fontsize=7)

    ax.set_xticks(x)
    ax.set_xticklabels([f"From {s}" for s in STATE_ORDER])
    ax.set_ylabel("Goals per match")
    ax.set_title(title)
    ax.legend(fontsize=8)

plt.tight_layout()
plt.savefig(FIG_DIR / "goals_by_game_state.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {FIG_DIR / 'goals_by_game_state.png'}")

# ── Part 5: Ball Territory by Game State ─────────────────────────────────────
coord_frames = []

for fid, meta in fixture_states.items():
    bc_path = FIXTURES_DIR / str(fid) / "ball_coordinates.csv"
    if not bc_path.exists():
        continue

    bc = pd.read_csv(bc_path, usecols=["fixture_id", "estimated_minute", "x", "y",
                                        "pitch_zone", "distance_to_goal"])
    bc = bc.dropna(subset=["estimated_minute", "x"])

    intervals = meta["intervals"]
    boundary_mins = [iv[0] for iv in intervals]
    boundary_states = [iv[3] for iv in intervals]

    def lookup_state(minute, b_mins=boundary_mins, b_states=boundary_states):
        idx = np.searchsorted(b_mins, minute, side='right') - 1
        idx = max(0, min(idx, len(b_states) - 1))
        return b_states[idx]

    bc["game_state"] = bc["estimated_minute"].apply(lookup_state)
    bc["season_id"] = meta["season_id"]
    bc["season"] = meta["season"]
    coord_frames.append(bc)

coords_df = pd.concat(coord_frames, ignore_index=True)
print(f"\nBall coordinates loaded: {len(coords_df):,} rows")
print("\nGame state distribution:")
print(coords_df["game_state"].value_counts())

# Zone distribution by game state
zone_order = ["defensive_third", "middle_third", "attacking_third"]

zone_summary = (
    coords_df
    .groupby(["season_id", "game_state", "pitch_zone"])
    .size()
    .reset_index(name="count")
)
zone_totals = coords_df.groupby(["season_id", "game_state"]).size().reset_index(name="total")
zone_summary = zone_summary.merge(zone_totals, on=["season_id", "game_state"])
zone_summary["pct"] = zone_summary["count"] / zone_summary["total"] * 100

print("\nPitch zone % when Liverpool are WINNING:")
win_zones = zone_summary[zone_summary["game_state"] == "WIN"].copy()
win_pivot = win_zones.pivot_table(index="season_id", columns="pitch_zone", values="pct").reindex(SEASON_IDS)
win_pivot.index = [SEASON_SHORT[sid] for sid in SEASON_IDS]
print(win_pivot[[z for z in zone_order if z in win_pivot.columns]].round(1).to_string())

print("\nPitch zone % when Liverpool are DRAWING:")
draw_zones = zone_summary[zone_summary["game_state"] == "DRAW"].copy()
draw_pivot = draw_zones.pivot_table(index="season_id", columns="pitch_zone", values="pct").reindex(SEASON_IDS)
draw_pivot.index = [SEASON_SHORT[sid] for sid in SEASON_IDS]
print(draw_pivot[[z for z in zone_order if z in draw_pivot.columns]].round(1).to_string())

print("\nPitch zone % when Liverpool are LOSING:")
loss_zones = zone_summary[zone_summary["game_state"] == "LOSS"].copy()
loss_pivot = loss_zones.pivot_table(index="season_id", columns="pitch_zone", values="pct").reindex(SEASON_IDS)
loss_pivot.index = [SEASON_SHORT[sid] for sid in SEASON_IDS]
print(loss_pivot[[z for z in zone_order if z in loss_pivot.columns]].round(1).to_string())

# Aggregate to per-fixture means before statistical testing (anti-pseudoreplication)
fixture_zone_state = (
    coords_df
    .groupby(["fixture_id", "season_id", "season", "game_state", "pitch_zone"])
    .size()
    .unstack(fill_value=0)
    .apply(lambda x: x / x.sum() * 100, axis=1)
    .reset_index()
)

# Note: unit of observation is (fixture × game_state) — a match with WIN and DRAW intervals
# contributes two rows. This inflates n relative to a pure per-fixture design.
# Test: attacking_third % when winning — Klopp vs Y2
if "attacking_third" in fixture_zone_state.columns:
    win_data = fixture_zone_state[fixture_zone_state["game_state"] == "WIN"]
    k_att = win_data[win_data["season_id"] == 21646]["attacking_third"].dropna()
    y2_att = win_data[win_data["season_id"] == 25583]["attacking_third"].dropna()
    if len(k_att) > 3 and len(y2_att) > 3:
        _, p = stats.mannwhitneyu(k_att, y2_att, alternative='two-sided')
        d = (np.mean(k_att) - np.mean(y2_att)) / np.sqrt(
            (np.std(k_att, ddof=1)**2 + np.std(y2_att, ddof=1)**2) / 2
        )
        print(f"\nAttacking third % when winning — Klopp vs Y2: "
              f"Klopp={k_att.mean():.1f}% vs Y2={y2_att.mean():.1f}%, d={d:.3f}, p={p:.4f}")

# Plot: zone distribution by game state (stacked bars)
zone_colors = {
    "defensive_third": "#B71C1C",
    "middle_third": "#F57C00",
    "attacking_third": "#1B5E20",
}

fig, axes = plt.subplots(1, 3, figsize=(16, 5))
fig.suptitle("Ball Zone Distribution by Game State and Season\n(absolute pitch zones)",
             fontsize=13, fontweight="bold", y=1.03)

for ax_idx, state in enumerate(STATE_ORDER):
    ax = axes[ax_idx]
    sub = zone_summary[zone_summary["game_state"] == state]

    x = np.arange(len(SEASON_IDS))
    bottoms = np.zeros(len(SEASON_IDS))

    for zone in zone_order:
        vals = []
        for sid in SEASON_IDS:
            row = sub[(sub["season_id"] == sid) & (sub["pitch_zone"] == zone)]
            vals.append(row["pct"].iloc[0] if not row.empty else 0)

        ax.bar(x, vals, 0.55, bottom=bottoms,
               color=zone_colors[zone], alpha=0.85,
               label=zone.replace("_third", "").replace("_", " ").title())

        for xi, v in zip(x, vals):
            if v > 3:
                ax.text(xi, bottoms[xi] + v / 2, f"{v:.0f}%",
                        ha="center", va="center", fontsize=8, color="white", fontweight="bold")
        bottoms += np.array(vals)

    ax.set_xticks(x)
    ax.set_xticklabels([SEASON_SHORT[sid] for sid in SEASON_IDS])
    ax.set_ylabel("% of ball coordinates" if ax_idx == 0 else "")
    ax.set_title(f"When {state}")
    ax.set_ylim(0, 110)
    if ax_idx == 2:
        ax.legend(loc="upper right", fontsize=7)

plt.tight_layout()
plt.savefig(FIG_DIR / "ball_zones_by_game_state.png", dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved {FIG_DIR / 'ball_zones_by_game_state.png'}")

print("\nScript complete. All figures saved to figures/02_game_state/")
