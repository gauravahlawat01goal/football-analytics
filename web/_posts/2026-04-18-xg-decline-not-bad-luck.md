---
layout: post
title: "Liverpool's xG decline is real, not bad luck"
date: 2026-04-18
thread_num: 1
status: live
status_label: "Live"
data_source: "Understat · 1,924 shots · 107 matches"
description: "Three seasons of shot data show Liverpool's Y2 regression is genuine chance quality decline — not finishing variance. All three seasons underperform xG by the same ~0.2/match margin."
excerpt: "All three seasons underperform xG by ~0.2 goals/match consistently. Y2's drop to 1.81 xG/match is not bad luck — the chances themselves got worse."
---

## The question Liverpool fans have been asking

Is this season bad luck, or are we actually worse?

The answer is uncomfortable — but three seasons of data make it clear. Liverpool are not unlucky in front of goal. They are generating genuinely worse chances than at any point in the Klopp or Slot Y1 era.

## The core finding: xG itself collapsed

Expected goals per match — a measure of chance quality, not finishing — across the three seasons:

| Season | xG / match | Goals / match | Gap |
|--------|-----------|---------------|-----|
| Klopp 2023–24 | 2.49 | 2.26 | −0.23 |
| Slot Y1 2024–25 | 2.45 | 2.26 | −0.19 |
| Slot Y2 2025–26 | **1.81** | **1.61** | −0.20 |

*Source: Understat, 107 matches, 1,924 shots. Slot Y2 based on 31 of 38 matches (season ongoing).*

Klopp's final season and Slot's first were effectively identical in chance quality. This season dropped 27%.

## Why this is not finishing bad luck

The most important number in the table above is the **gap** column — how much Liverpool underperform their xG each season.

Klopp: −0.23. Slot Y1: −0.19. Slot Y2: −0.20.

**The underperformance is the same in all three seasons.** Liverpool have consistently scored about 0.2 goals per match fewer than their xG predicts — regardless of who was managing, who was playing, and how the season was going.

This matters because if the Y2 goal drought were a finishing slump, you would expect the Y2 gap to be significantly larger than previous seasons. It isn't. The finishing is no worse than it was under Klopp. The *xG itself* fell.

## Both levers broke simultaneously

| Season | Shots / match | xG / shot |
|--------|--------------|-----------|
| Klopp 2023–24 | 20.8 | 0.123 |
| Slot Y1 2024–25 | 17.1 | **0.146** |
| Slot Y2 2025–26 | **15.5** | 0.118 |

Slot Y1 was actually the most efficient season of the three — fewer shots than Klopp, but meaningfully better quality per shot (0.146 vs 0.123 xG/shot). The goals-per-match output was identical (2.26) because the quality made up for the volume.

Y2 broke both at once: volume declined further (15.5 shots/match), and quality per shot dropped below even Klopp levels (0.118). There was no compensating factor.

## The set-piece picture

| Season | Set-piece xG / match | Open-play xG / match |
|--------|---------------------|---------------------|
| Klopp 2023–24 | 0.679 | — |
| Slot Y1 2024–25 | 0.487 | — |
| Slot Y2 2025–26 | 0.339 | — |

Set-piece xG halved from the Klopp era to Y2. The decline started under Slot Y1 (−28%) while Trent Alexander-Arnold was still at the club, and continued after his departure (−30% Y1→Y2). The full picture is addressed in Thread 2: The Trent Effect, Part 1 (coming soon).

## What you've been feeling is real

Liverpool are conceding more chances too — opponent xG/match rose from 1.11 (Slot Y1, the best defensive season) to 1.34 in Y2. Attack and defence both declined simultaneously.

The table reflects the xG before the table does. The 1.63 PPG (down from 2.14 under Klopp and 2.12 in Y1) is not a run of bad luck. It is the predictable result of creating fewer and worse chances, while conceding more.

## Confirmed findings

The shot volume and quality decline is reinforced by SportsMonks match statistics across 101 processed fixtures. Compared to Klopp's final season, Slot Y2 shows — confirmed with Bonferroni-corrected Mann-Whitney U tests across 44 metrics:

- **Shots on target: −37.2%** (Cohen's d = 0.88, large effect)
- **Goal attempts: −29.3%** (Cohen's d = 0.87)
- **Tackles: −25.7%** (Cohen's d = 0.86)

These are not borderline results. They survive the most conservative multiple-comparison correction.

---

*Data: Understat (107 matches, 1,924 per-shot xG records) and SportsMonks API v3 (101 processed fixtures, 44 match statistics per team). Slot Y2 figures based on 31 of 38 matches — partial season, figures subject to update. Y1-vs-Y2 comparisons are directional signals only; the Klopp-vs-Y2 comparisons above are statistically confirmed.*

*[Full methodology and code →](https://github.com/gauravahlawat01goal/football-analytics)*
