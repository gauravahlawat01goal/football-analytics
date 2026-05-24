---
layout: post
title: "Liverpool's xG decline isn't bad luck"
date: 2026-04-18
thread_num: 1
status: live
status_label: "Live"
data_source: "Understat · full 38-match season · SportsMonks"
description: "Three seasons of data show Liverpool's attacking xG fell 29% in Slot Y2 — from 2.49 to 1.77 per match. Full season, 38 matches. The decline is visible before the finishing, not in it."
excerpt: "Liverpool's attacking xG fell from 2.49 (Klopp) to 1.77 (Slot Y2) — a 29% drop across the full 38-match season. Shot volume declined, shot quality declined, set-piece output halved. The problem starts before finishing."
---

Ask most Liverpool fans what went wrong this season and they'll tell you the same thing: bad luck, near misses, posts, goalkeepers. The idea that the results don't reflect the performances. That things will turn.

Three seasons of data say something different.

## The question the numbers can answer

Expected goals gives us a clean test. If Liverpool were simply unlucky, xG would stay high while goals lagged behind. If xG itself falls, the problem starts before finishing: chance creation.

Here is the full picture across all three seasons:

| Season | xG / match | Goals / match | Gap |
|--------|-----------|---------------|-----|
| Klopp 2023–24 | 2.49 | 2.26 | −0.23 |
| Slot Y1 2024–25 | 2.45 | 2.26 | −0.19 |
| Slot Y2 2025–26 | **1.77** | **1.66** | −0.11 |

*Source: Understat. Slot Y2: 38 of 38 matches — season complete.*

<figure class="post-figure">
  <img src="{{ '/assets/figures/xg_per_match.png' | relative_url }}" alt="xG per match by season: Klopp 2.49, Slot Y1 2.45, Slot Y2 1.77" />
  <figcaption>xG per match across three seasons. The Y2 drop is the sharpest single-season change of the three.</figcaption>
</figure>

The key is not just the xG column. It is the gap.

## The column that reframes the argument

Most people will look at the xG/match column and feel the drop. 2.49 to 1.77. Twenty-nine percent. That's the headline. But the column that matters most is the one nobody talks about first: **the gap**.

Klopp: −0.23. Slot Y1: −0.19. Slot Y2 at 30 matches: −0.21.

<div class="insight-callout">
  <div class="insight-label">The key insight</div>
  <p>For the first 30 matches of Y2, Liverpool underperformed their xG by <strong>the same margin as every previous season</strong>. The finishing was no worse. The problem was upstream: fewer chances, and worse ones. Matches 31–37 saw an unusual run of overperformance (+0.57 gap across those seven games). Then the final match — 2.99 xG at Brentford, one goal scored — pulled the full-season gap back to −0.11. The late scoring was variance; the underlying xG of 1.77/match, down 29% from Klopp's 2.49, was not.</p>
</div>

The full-season gap of −0.11 sits closer to the historical −0.19 to −0.23 range than the brief mid-season overperformance suggested. xG/match at 1.77 is the lowest of the three seasons by a distance, and the final match confirmed it: when Liverpool created 2.99 xG and scored once, that was not an anomaly — it was the season in miniature.

## Both levers broke simultaneously

This is what makes Y2 different from Y1. Slot's first season made sense as a model:

| Season | Shots / match | xG / shot |
|--------|--------------|-----------|
| Klopp 2023–24 | 20.8 | 0.123 |
| Slot Y1 2024–25 | 17.1 | **0.146** |
| Slot Y2 2025–26 | **15.5** | 0.118 |

*Shots and xG/shot based on the first 30 matches of Y2 (shot-level pull). Match-level xG updated to 38 matches (full season).*

Slot Y1 took fewer shots but made them count. The shots Liverpool did take were measurably higher quality — 0.146 xG per shot versus Klopp's 0.123. The total xG barely moved (2.45 vs 2.49), goals were identical (2.26/match), and a Premier League title followed. There was a coherent logic to it.

Y2 broke that logic. Volume dropped again — from 17.1 to 15.5 shots per match — but this time quality didn't compensate. At 0.118 xG per shot, chance quality fell below even Klopp's level. There was no trade-off happening. Both the volume and the quality of chances declined at the same time, and there was nothing to cushion the fall.

## Set pieces: a specific tactical fingerprint

One part of the xG story is easier to isolate:

| Season | Set-piece xG / match |
|--------|---------------------|
| Klopp 2023–24 | 0.679 |
| Slot Y1 2024–25 | 0.487 |
| Slot Y2 2025–26 | 0.339 |

Set-piece expected goals halved from the Klopp era to Y2. That is not a rounding error — it is roughly a third of a goal per match in expected value, gone. The decline began under Slot Y1 (−28% while Trent Alexander-Arnold was still at the club) and continued after his departure (−30% Y1→Y2). The precise contribution of each factor is the subject of Thread 02: The Trent Effect, Part 1.

*Set-piece xG figures are from the first 30-match Understat shot-level pull; match-level xG is updated to the full 38 matches.*

## The defence held until it didn't

One mitigating factor from Slot's first season deserves credit: the defence. Liverpool conceded an opponent xG of just 1.11 in Y1, the best of the three seasons, which cushioned the attacking efficiency shift. That buffer is gone in Y2.

Opponent xG/match: 1.25 (Klopp) → 1.11 (Slot Y1) → **1.42** (Slot Y2, 38 matches — season complete).

Attack and defence regressed simultaneously. The 1.58 PPG — down from 2.16 under Klopp and 2.21 in Y1 — is not a cluster of near misses. It is the predictable arithmetic of creating fewer, worse chances, while allowing more of them at the other end.

## What independent data confirms

The xG story is reinforced by a separate dataset: SportsMonks match statistics, full Premier League seasons (38 Klopp matches, 38 Y2 matches — season complete). Tested with Mann-Whitney U and Bonferroni correction across 44 metrics (α/44 ≈ 0.00114). The following survived that threshold when comparing Klopp's 2023–24 season to Slot Y2:

- **Ball Safe: −13.9%** (Cohen's d = 1.06 — very large effect)
- **Shots on target: −36.8%** (Cohen's d = 0.90 — large effect)
- **Goal attempts: −29.5%** (Cohen's d = 0.89 — large effect)
- **Tackles per match: −27.0%** (17.8 → 13.0 per match, Cohen's d = 0.93 — large effect)

These are not marginal signals. They are large, consistent, and robust to correction. The press is less intense. The shots are fewer. The quality is lower. The results follow.

What you've been watching this season — the listless phases, the inability to break teams down, the sense that the danger Liverpool used to generate has diminished — is documented in three years of data from two independent sources.

## What this does not prove

This analysis shows association, not causation. It does not isolate Slot's tactical choices from squad changes, Trent Alexander-Arnold's departure, injuries, fixture difficulty, or any other variable. It shows that the decline is visible in attacking xG, shot volume, shot quality, set-piece output, and independent match-stat signals — consistently, across two data sources.

It does not adjust for opponent strength. A tackle count of 13.0/match means different things against different opposition. Opponent-adjusted metrics are planned but not yet complete.

It does not predict next season.

You weren't imagining it.

---

<div class="post-footer-note">
  <p><strong>Data:</strong> Understat (xG figures, full 38-match Y2 season) and SportsMonks API v3 (match statistics, full season). Season complete. xG/shot and set-piece figures based on first 30 matches of Y2 (shot-level pull). Y1-vs-Y2 comparisons are directional signals only; Klopp-vs-Y2 comparisons are statistically confirmed with Bonferroni correction.</p>
  <p><a href="https://github.com/gauravahlawat01goal/football-analytics">Full methodology and analysis code →</a></p>
</div>
