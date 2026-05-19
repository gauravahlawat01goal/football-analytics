---
layout: post
title: "Liverpool's xG decline is real, not bad luck"
date: 2026-04-18
thread_num: 1
status: live
status_label: "Live"
data_source: "Understat · 1,924 shots · 107 matches"
description: "Three seasons of shot data show Liverpool's regression in Slot Y2 is genuine chance quality decline — not finishing variance. All three seasons underperform xG by the same ~0.2/match margin, which is the key to understanding what actually changed."
excerpt: "Liverpool underperform xG by ~0.2 goals per match in all three seasons — Klopp, Slot Y1, and Slot Y2. The finishing hasn't gotten worse. The chances have."
---

Ask most Liverpool fans what went wrong this season and they'll tell you the same thing: bad luck, near misses, posts, goalkeepers. The idea that the results don't reflect the performances. That things will turn.

Three seasons of data say something different.

## The question the numbers can answer

There's a clean way to separate bad luck from genuine decline: expected goals. xG measures the quality of the chances Liverpool create — not whether they went in. If the decline is bad luck, xG stays high and goals underperform it. If xG itself falls, the problem is upstream of the finishing.

Here is the full picture across all three seasons:

| Season | xG / match | Goals / match | Gap |
|--------|-----------|---------------|-----|
| Klopp 2023–24 | 2.49 | 2.26 | −0.23 |
| Slot Y1 2024–25 | 2.45 | 2.26 | −0.19 |
| Slot Y2 2025–26 | **1.74** | **1.68** | −0.06 |

*Source: Understat. Slot Y2: 37 of 38 matches played.*

Spend a moment with that table before reading on.

## The column that ends the argument

Most people will look at the xG/match column and feel the drop. 2.49 to 1.81. Twenty-seven percent. That's the headline. But the column that matters most is the one nobody talks about first: **the gap**.

Klopp: −0.23. Slot Y1: −0.19. Slot Y2 at 30 matches: −0.21.

<div class="insight-callout">
  <div class="insight-label">The key insight</div>
  <p>For the first 30 matches of Y2, Liverpool underperformed their xG by <strong>the same margin as every previous season</strong>. The finishing was no worse. The problem was upstream: fewer chances, and worse ones. The final seven games of the season then saw Liverpool significantly overperform their xG (+0.57 gap), pushing the full-season figure to −0.06. Those late goals were genuine — but they came against a backdrop of 1.74 xG/match, still 30% below Klopp's 2.49.</p>
</div>

The end-of-season finishing surge doesn't rescue the underlying story. xG/match at 1.74 is the lowest of the three seasons by a distance. Liverpool scored more goals than their chances deserved in the final weeks — that is variance, not recovery.

## Both levers broke simultaneously

This is what makes Y2 different from Y1. Slot's first season made sense as a model:

| Season | Shots / match | xG / shot |
|--------|--------------|-----------|
| Klopp 2023–24 | 20.8 | 0.123 |
| Slot Y1 2024–25 | 17.1 | **0.146** |
| Slot Y2 2025–26 | **15.5** | 0.118 |

Slot Y1 took fewer shots but made them count. The shots Liverpool did take were measurably higher quality — 0.146 xG per shot versus Klopp's 0.123. The total xG barely moved (2.45 vs 2.49), goals were identical (2.26/match), and a Premier League title followed. There was a coherent logic to it.

Y2 broke that logic. Volume dropped again — from 17.1 to 15.5 shots per match — but this time quality didn't compensate. At 0.118 xG per shot, chance quality fell below even Klopp's level. There was no trade-off happening. Both the volume and the quality of chances declined at the same time, and there was nothing to cushion the fall.

## Set pieces: a specific, measurable loss

One part of the xG story can be attributed to a specific cause:

| Season | Set-piece xG / match |
|--------|---------------------|
| Klopp 2023–24 | 0.679 |
| Slot Y1 2024–25 | 0.487 |
| Slot Y2 2025–26 | 0.339 |

Set-piece expected goals halved from the Klopp era to Y2. That is not a rounding error — it is half a goal per match in expected value, gone. The decline began under Slot Y1 (−28% while Trent Alexander-Arnold was still at the club) and continued after his departure (−30% Y1→Y2). The precise contribution of each factor is the subject of Thread 02: The Trent Effect, Part 1.

## The defence held until it didn't

One mitigating factor from Slot's first season deserves credit: the defence. Liverpool conceded an opponent xG of just 1.11 in Y1, the best of the three seasons, which cushioned the attacking efficiency shift. That buffer is gone in Y2.

Opponent xG/match: 1.25 (Klopp) → 1.11 (Slot Y1) → **1.42** (Slot Y2, 37 matches).

Attack and defence regressed simultaneously. The 1.63 PPG — down from 2.14 under Klopp and 2.12 in Y1 — is not a cluster of near misses. It is the predictable arithmetic of creating fewer, worse chances, while allowing more of them at the other end.

## What independent data confirms

The xG story is reinforced by a separate dataset: SportsMonks match statistics across 101 processed fixtures. These are tested with Mann-Whitney U tests and Bonferroni correction across 44 metrics — the most conservative multiple-comparison adjustment available. The following survived that threshold when comparing Klopp's 2023–24 season to Slot Y2:

- **Shots on target: −37.2%** (Cohen's d = 0.88 — large effect)
- **Goal attempts: −29.3%** (Cohen's d = 0.87)
- **Tackles per match: −25.7%** (17.9 → 13.3 per match, Cohen's d = 0.86)
- **Ball Safe: −13.5%** (Cohen's d = 1.11 — very large effect)

These are not borderline signals. They are large, consistent, and robust to correction. The press is less intense. The shots are fewer. The quality is lower. The results follow.

What you've been watching this season — the listless phases, the inability to break teams down, the sense that the danger Liverpool used to generate has diminished — is documented in three years of data from two independent sources.

You weren't imagining it.

---

<div class="post-footer-note">
  <p><strong>Data:</strong> Understat (xG figures, 37 Y2 matches) and SportsMonks API v3 (match statistics). Slot Y2: 37 of 38 matches played — one fixture remaining (Brentford, May 24). xG/shot and set-piece figures based on first 30 matches of Y2; full-season shot-level data pending. Y1-vs-Y2 comparisons are directional signals only; Klopp-vs-Y2 comparisons are statistically confirmed with Bonferroni correction.</p>
  <p><a href="https://github.com/gauravahlawat01goal/football-analytics">Full methodology, code, and processed data →</a></p>
</div>
