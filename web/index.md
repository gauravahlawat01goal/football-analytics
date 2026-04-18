---
layout: default
title: "Liverpool FC: Three Seasons of Data | Gaurav Ahlawat"
description: "Data-driven tactical analysis of Liverpool FC across three seasons."
---

<header>
  <div class="badge">Data Analysis Project</div>
  <h1>Liverpool FC:<br><span>Three Seasons of Data</span></h1>
  <p class="subtitle">
    Statistical analysis of Liverpool's tactical evolution across Klopp's final season (2023–24)
    and Arne Slot's first two years (2024–25, 2025–26).
  </p>
  <div class="header-meta">
    <span>101 processed fixtures</span>
    <span>·</span>
    <span>1,924 tracked shots</span>
    <span>·</span>
    <span>44 statistical metrics</span>
    <span>·</span>
    <span>3 data sources</span>
  </div>
</header>

<main>

  <!-- ── Headline numbers ── -->
  <section>
    <h2>Headline Numbers</h2>
    <div class="stats-grid">

      <div class="stat-card">
        <div class="label">xG / match — Slot Y2</div>
        <div class="value">1.81</div>
        <div class="delta down">↓ 27% from Klopp (2.49) · 1,924 shots</div>
      </div>

      <div class="stat-card">
        <div class="label">Points per game — Slot Y2</div>
        <div class="value">1.63</div>
        <div class="delta down">↓ from 2.14 (Klopp) and 2.12 (Y1)</div>
      </div>

      <div class="stat-card">
        <div class="label">Set-piece xG / match</div>
        <div class="value">0.339</div>
        <div class="delta down">↓ 50% from Klopp era (0.679)</div>
      </div>

      <div class="stat-card">
        <div class="label">xG overperformance (all 3 seasons)</div>
        <div class="value">≈ −0.20</div>
        <div class="delta neutral">Consistent across all seasons · not finishing luck</div>
      </div>

    </div>
  </section>

  <!-- ── Season comparison ── -->
  <section>
    <h2>Season Comparison</h2>
    <div style="overflow-x: auto;">
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Season</th>
            <th>PPG</th>
            <th>xG / match</th>
            <th>Goals / match</th>
            <th>xG / shot</th>
            <th>Set-piece xG</th>
            <th>Opp xG</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><span class="season-tag klopp">Klopp 23–24</span></td>
            <td>2.14</td>
            <td>2.49</td>
            <td>2.26</td>
            <td>0.123</td>
            <td>0.679</td>
            <td>1.25</td>
          </tr>
          <tr>
            <td><span class="season-tag y1">Slot Y1 24–25</span></td>
            <td>2.12</td>
            <td>2.45</td>
            <td>2.26</td>
            <td class="highlight">0.146</td>
            <td>0.487</td>
            <td class="highlight">1.11</td>
          </tr>
          <tr>
            <td><span class="season-tag y2">Slot Y2 25–26 †</span></td>
            <td style="color:#f44336">1.63</td>
            <td style="color:#f44336">1.81</td>
            <td style="color:#f44336">1.61</td>
            <td style="color:#f44336">0.118</td>
            <td style="color:#f44336">0.339</td>
            <td style="color:#f44336">1.34</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p style="font-size:0.75rem; color:var(--text-muted); margin-top:0.6rem;">
      † Slot Y2 based on 31 of 38 matches played (season ongoing). Figures may update.
      xG data: Understat (107 matches, 1,924 shots). PPG data: SportsMonks (101 processed fixtures).
      Highlighted values are the best figure in that column.
    </p>
  </section>

  <!-- ── Confirmed findings ── -->
  <section>
    <h2>Statistically Confirmed Findings</h2>
    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:1.2rem;">
      The following changes are confirmed using Mann-Whitney U tests with Bonferroni correction
      across 44 metrics (Klopp 2023–24 vs Slot Y2 2025–26). These are not directional signals —
      they survive the most conservative multiple-comparison threshold.
    </p>
    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">Shots on target</div>
        <div class="value" style="color:#f44336">−37.2%</div>
        <div class="delta down">Cohen's d = 0.88 (large)</div>
      </div>
      <div class="stat-card">
        <div class="label">Goal attempts</div>
        <div class="value" style="color:#f44336">−29.3%</div>
        <div class="delta down">Cohen's d = 0.87 (large)</div>
      </div>
      <div class="stat-card">
        <div class="label">Tackles / match</div>
        <div class="value" style="color:#f44336">−25.7%</div>
        <div class="delta down">17.9 → 13.3 / match</div>
      </div>
      <div class="stat-card">
        <div class="label">Ball Safe</div>
        <div class="value" style="color:#f44336">−13.5%</div>
        <div class="delta down">Cohen's d = 1.11 (very large)</div>
      </div>
    </div>
  </section>

  <!-- ── Thread series ── -->
  <section>
    <h2>Thread Series</h2>
    <div class="thread-list">
      {% for post in site.posts %}
      <div class="thread-item {{ post.status }}">
        <div class="thread-num">{{ post.thread_num | prepend: '0' | slice: -2, 2 }}</div>
        <div class="thread-content">
          <h3><a href="{{ post.url | relative_url }}" style="color:inherit">{{ post.title }}</a></h3>
          <p>{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        </div>
        <span class="thread-status status-{{ post.status }}">{{ post.status_label }}</span>
      </div>
      {% endfor %}
    </div>
  </section>

  <!-- ── Methodology ── -->
  <section>
    <h2>Methodology</h2>
    <div class="method-box">
      <p>
        <strong>Confirmatory analysis</strong> (Klopp 2023–24 vs Slot era): Mann-Whitney U tests
        with Bonferroni correction across all 44 statistical metrics. The Bonferroni threshold
        is conservative (α/44 per comparison). Only findings that survive this threshold are
        reported as "confirmed."
      </p>
      <p>
        <strong>Exploratory analysis</strong> (Slot Y1 vs Y2): Y2 is a partial season (31 of 38 matches
        at time of analysis). Y1-vs-Y2 comparisons report effect sizes and directional signals only —
        not confirmed statistical significance. These are clearly labelled as "directional" in all
        published content.
      </p>
      <p>
        <strong>xG data</strong>: Understat per-shot expected goals (107 matches, 1,924 shots).
        Per-shot xG enables both quality analysis (xG/shot) and source breakdown (open play vs set piece).
        The consistent ~0.2 goals/match underperformance across all three seasons is the methodological
        basis for concluding Y2's decline is quality-driven, not finishing-luck.
      </p>
    </div>
    <div class="caveat-box">
      ⚠ Slot Y2 data is mid-season (31 of 38 matches). All Y2 figures — including xG/match, PPG,
      and percentage changes — are snapshots and will be updated as the season concludes.
    </div>
  </section>

  <!-- ── Data sources ── -->
  <section>
    <h2>Data Sources</h2>
    <div class="source-grid">
      <div class="source-card">
        <div class="tier">Tier 1 · Match data</div>
        <h4>SportsMonks API v3</h4>
        <p>101 processed fixtures. Goals, lineups, formations, 44 match statistics per team, ball coordinates.</p>
      </div>
      <div class="source-card">
        <div class="tier">Tier 2 · xG enrichment</div>
        <h4>Understat</h4>
        <p>107 matches, 1,924 per-shot xG records with coordinates. Open-play and set-piece breakdown.</p>
      </div>
      <div class="source-card">
        <div class="tier">Tier 3 · Tactical metrics</div>
        <h4>FBRef</h4>
        <p>PPDA (passes allowed per defensive action) per match. Integration in progress.</p>
      </div>
    </div>
    <p style="font-size:0.78rem; color:var(--text-muted); margin-top:0.85rem;">
      Raw data is not published. Analysis code, processed outputs, and methodology are available
      in the GitHub repository. All data used under respective providers' terms.
    </p>
  </section>

</main>
