---
layout: post
title: "Liverpool's xG decline isn't bad luck"
date: 2026-04-18
updated: 2026-05-24
thread_num: 1
status: live
status_label: "Live"
description: "Three seasons of data show Liverpool's attacking xG fell 29% in Slot Y2 — from 2.49 to 1.77 per match. Full season, 38 matches. The decline is visible before the finishing, not in it."
excerpt: "Liverpool's attacking xG fell from 2.49 (Klopp) to 1.77 (Slot Y2) — a 29% drop across the full 38-match season. Shot volume declined, shot quality declined, set-piece output halved. The problem starts before finishing."
---

Ask most Liverpool fans what went wrong in Slot's second season and they'll tell you the same thing: bad luck, near misses, posts, goalkeepers. The results didn't reflect the performances, the story goes. Things will turn.

Three seasons of data say something different. The decline wasn't in the finishing. It was in the chances themselves — and it was there long before the goals dried up.

## The numbers tell a different story

Expected goals gives us a clean test. If Liverpool were simply unlucky, xG would stay high while goals lagged behind. If xG itself falls, the problem starts before the finishing: in chance creation.

Here is the full picture across all three seasons:

| Season | xG / match | Goals / match | Gap |
|--------|-----------|---------------|-----|
| Klopp 2023–24 | 2.49 | 2.26 | −0.23 |
| Slot Y1 2024–25 | 2.45 | 2.26 | −0.19 |
| Slot Y2 2025–26 | **1.77** | **1.66** | −0.11 |

*Source: Understat. Slot Y2: full 38-match season.*

<figure class="post-figure">
  <img src="{{ '/assets/figures/xg_per_match.png' | relative_url }}" alt="xG per match by season: Klopp 2.49, Slot Y1 2.45, Slot Y2 1.77" />
  <figcaption>xG per match across three seasons. The Y2 drop is the sharpest single-season change of the three.</figcaption>
</figure>

The xG/match column is the headline: 2.49 to 1.77, the steepest single-season fall of the three. But the column that settles the bad-luck argument is the one beside it — the gap between expected and actual goals.

## The finishing was never the problem

If Liverpool were simply unlucky, the gap would blow out: lots of xG, far fewer goals. It didn't. A bad-luck season would show a much larger negative gap — goals far below xG. Instead the gap held steady. Klopp finished 0.23 below his xG, Slot Y1 sat at −0.19, and for the first 30 matches of Y2 the figure was −0.21 — squarely in line with both previous seasons.

<div class="insight-callout">
  <div class="insight-label">The key insight</div>
  <p>Through 30 matches, Liverpool finished their chances exactly as well as they had in the two previous seasons. The drop was upstream — fewer chances, and worse ones — not in front of goal.</p>
</div>

The full-season gap of −0.11 is flattered by a short late run of overperformance across matches 31–37, then partly corrected on the final day at Brentford, where Liverpool generated 2.99 xG, scored once, and drew 1–1. The late scoring was variance. The xG itself — 1.77 per match, down 29% from Klopp's 2.49 — was the season in miniature.

## Both levers broke simultaneously

So where did the chances go? To answer that, the next two tables draw on a separate, earlier data pull. *Note: shot volume and xG/shot figures are based on the first 30 matches of Y2 from a shot-level data pull; match-level xG reflects the complete 38-match season throughout.*

Slot's first season made sense as a model:

| Season | Shots / match | xG / shot |
|--------|--------------|-----------|
| Klopp 2023–24 | 20.8 | 0.123 |
| Slot Y1 2024–25 | 17.1 | **0.146** |
| Slot Y2 2025–26 | **15.5** | 0.118 |

Slot Y1 took fewer shots but made them count, at 0.146 xG per shot against Klopp's 0.123. Total xG barely moved, goals were identical, and the season ended with a Premier League title. The trade-off — volume for quality — held the output steady.

Y2 broke that logic. Volume fell again, to 15.5 shots per match — but this time quality didn't compensate. At 0.118 xG per shot, the chances were worse than Klopp's, not better. Volume and quality moved the wrong way together, and there was nothing left to cushion the fall.

## Set pieces: a specific tactical fingerprint

One slice of the decline is easier to isolate than the rest:

| Season | Set-piece xG / match |
|--------|---------------------|
| Klopp 2023–24 | 0.679 |
| Slot Y1 2024–25 | 0.487 |
| Slot Y2 2025–26 | 0.339 |

Set-piece expected goals halved from the Klopp era to Y2 — roughly a third of a goal per match in expected value, gone. And it did not happen all at once: the drop from Klopp to Slot Y1 was already −28% (while Trent Alexander-Arnold was still at the club), and it continued after his departure (−30% Y1→Y2).

## The defence held until it didn't

One mitigating factor from Slot's first season deserves credit: the defence. Liverpool conceded an opponent xG of just 1.11 in Y1, the best of the three seasons, which cushioned the attacking efficiency shift. That buffer was gone in Y2.

Opponent xG/match: 1.25 (Klopp) → 1.11 (Slot Y1) → **1.42** (Slot Y2).

Attack and defence regressed simultaneously. The 1.58 PPG — roughly 60 points across a 38-match season, down from 2.16 under Klopp and 2.21 in Y1 — is not a cluster of near misses. It was the predictable arithmetic of creating fewer, worse chances, while allowing more of them at the other end.

## What independent data confirms

So far the case rests on Understat. A second, independent dataset tells the same story: SportsMonks match statistics across full Premier League seasons, tested with Mann-Whitney U and Bonferroni correction over 44 metrics (α/44 ≈ 0.00114). Comparing Klopp's 2023–24 to Slot Y2, four findings cleared that threshold:

- **Ball Safe (secure possession): −13.9%** (Cohen's d = 1.06 — very large effect)
- **Shots on target: −36.8%** (Cohen's d = 0.90 — large effect)
- **Goal attempts: −29.5%** (Cohen's d = 0.89 — large effect)
- **Tackles per match: −27.0%** (17.8 → 13.0 per match, Cohen's d = 0.93 — large effect)

These are not marginal signals. They are large, consistent, and robust to correction. The press is less intense. The shots are fewer. The quality is lower. The results follow.

What you watched in 2025–26 — the listless phases, the inability to break teams down, the sense that the old danger had drained away — is documented across three years of data from two independent sources.

## What this does not prove

This analysis shows association, not causation. It cannot isolate Slot's tactical choices from squad changes, Trent Alexander-Arnold's departure, injuries, or fixture difficulty; it does not adjust for opponent strength, so a tackle count of 13.0 per match means different things against different opposition; and it makes no claim about next season. What it does show is that the decline appears in attacking xG, shot volume, shot quality, set-piece output, and independent match-stat signals — consistently, across two datasets.

You weren't imagining it.

---

<div class="post-footer-note">
  <p><strong>Data:</strong> Understat (xG) and SportsMonks API v3 (match statistics). Match-level xG covers the full 38-match Y2 season; xG/shot and set-piece figures are from the first 30 matches.</p>
  <p><strong>Statistics:</strong> Klopp-vs-Y2 comparisons are Bonferroni-confirmed; Y1-vs-Y2 comparisons are directional signals only.</p>
  <p><a href="https://github.com/gauravahlawat01goal/football-analytics">Full methodology and analysis code →</a></p>
</div>
