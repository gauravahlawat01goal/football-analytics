---
layout: default
title: "Something broke in year two | Liverpool FC Analysis"
description: "Three seasons of data on Liverpool FC's decline — 37 matches, 1,924 shots. xG fell 30%, PPG fell from 2.14 to 1.59. The numbers show where it broke."
permalink: /liverpool/decline/
---

<header>
  <div class="badge">Liverpool FC · Slot Y2 Analysis</div>
  <h1>Something broke<br>in year two.</h1>
  <p class="hero-sub-headline">The data says so. Let's show you where.</p>
  <p class="subtitle">Klopp's final season. Slot's first two. What the data says happened.</p>
</header>

<main>

  <!-- ── The centrepiece number ── -->
  <section>
    <div class="section-label">The number that started this</div>
    <h2>Liverpool's expected goals fell off a cliff.</h2>
    <p class="section-intro">
      Slot's first season was efficient — fewer shots, better quality, same output. Year two lost both.
      This is not a finishing slump. The underlying chances themselves got worse.
    </p>

    <div class="hero-stat-block">
      <div class="hero-stat-number">
        <span class="big">1.74</span>
        <span class="unit">xG per match · Slot Y2 2025–26</span>
      </div>
      <div class="hero-stat-text">
        <div class="hero-delta">↓ 30% from Klopp (2.49) · ↓ 29% from Slot Y1 (2.45)</div>
        <h3>Liverpool's attacking xG fell 30% — observed across 37 matches</h3>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">Points per game — Slot Y2</div>
        <div class="value" style="color:var(--red)">1.59</div>
        <div class="delta down">↓ from 2.14 (Klopp) and 2.12 (Slot Y1)</div>
      </div>
      <div class="stat-card">
        <div class="label">Set-piece xG / match</div>
        <div class="value" style="color:var(--red)">0.339</div>
        <div class="delta down">↓ 50% from Klopp era (0.679)</div>
      </div>
      <div class="stat-card">
        <div class="label">Opponent xG / match — Slot Y2</div>
        <div class="value" style="color:var(--red)">1.42</div>
        <div class="delta down">↑ from 1.11 (Slot Y1) — defence declined too</div>
      </div>
    </div>
  </section>

  <!-- ── Season comparison ── -->
  <section>
    <div class="section-label">Three seasons</div>
    <h2>Every number moved in the wrong direction.</h2>
    <p class="section-intro">
      Slot Y1 had a coherent model — fewer shots, higher quality, same goals. Y2 broke that model without replacing it. Look at the Gap column.
    </p>
    <div style="overflow-x: auto;">
      <table class="comparison-table">
        <thead>
          <tr>
            <th>Season</th>
            <th>PPG</th>
            <th>xG / match</th>
            <th>Goals / match</th>
            <th class="col-gap">Gap</th>
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
            <td class="col-gap">−0.23</td>
            <td>0.123</td>
            <td class="highlight">0.679</td>
            <td>1.25</td>
          </tr>
          <tr>
            <td><span class="season-tag y1">Slot Y1 24–25</span></td>
            <td>2.12</td>
            <td>2.45</td>
            <td>2.26</td>
            <td class="col-gap">−0.19</td>
            <td class="highlight">0.146</td>
            <td>0.487</td>
            <td class="highlight">1.11</td>
          </tr>
          <tr class="row-y2">
            <td><span class="season-tag y2">Slot Y2 25–26 †</span></td>
            <td class="text-red">1.59</td>
            <td class="text-red">1.74</td>
            <td class="text-red">1.68</td>
            <td class="col-gap">−0.06</td>
            <td class="text-red">0.118</td>
            <td class="text-red">0.339</td>
            <td class="text-red">1.42</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="gap-insight">
      The Gap column tells the finishing story. For the first 30 matches of Y2 the gap was −0.21 — consistent with Klopp and Slot Y1. The final seven games saw unusual overperformance (+0.57), pulling the full-season gap to −0.06. Those late goals were real; the chance quality that produced them (1.74 xG/match, down 30% from Klopp) was not.
    </p>
    <p class="table-note">
      Gap = Goals/match minus xG/match. † Slot Y2: 37 of 38 matches played (one match remaining).
      xG data: Understat. PPG: SportsMonks. xG/shot and set-piece xG based on first 30 matches of Y2. Highlighted cells are the best figure in each column.
    </p>
  </section>

  <!-- ── Confirmed findings ── -->
  <section>
    <div class="section-label">What the tests confirm</div>
    <h2>These changes are real, not noise.</h2>
    <p class="section-intro">
      The xG picture above comes from Understat. The following comes from a second, independent dataset —
      SportsMonks match statistics across 101 fixtures. Tested with Mann-Whitney U and Bonferroni correction
      across all 44 metrics. Everything below survived the most conservative multiple-comparison threshold.
    </p>
    <div class="confirmed-grid">
      <div class="confirmed-card">
        <div class="c-label">Ball Safe</div>
        <div class="c-value">−13.5%</div>
        <div class="c-meta">Cohen's d = 1.11 — very large effect</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Shots on target</div>
        <div class="c-value">−37.2%</div>
        <div class="c-meta">Cohen's d = 0.88 — large effect</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Goal attempts</div>
        <div class="c-value">−29.3%</div>
        <div class="c-meta">Cohen's d = 0.87 — large effect</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Tackles / match</div>
        <div class="c-value">−25.7%</div>
        <div class="c-meta">17.9 → 13.3 per match</div>
      </div>
    </div>
  </section>

  <!-- ── Thread series ── -->
  <section>
    <div class="section-label">Read the analysis</div>
    <h2>The investigation into Liverpool's decline.</h2>
    <p class="section-intro">
      Each piece stands alone. Start with the first — it's the foundation everything else builds on.
    </p>
    <div class="thread-list">
      {% assign sorted_posts = site.posts | sort: 'thread_num' %}
      {% for post in sorted_posts %}
      <div class="thread-item {{ post.status }}">
        <div class="thread-num">{{ post.thread_num | prepend: '0' | slice: -2, 2 }}</div>
        <div class="thread-content">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
          <p>{{ post.excerpt | strip_html | truncatewords: 30 }}</p>
        </div>
        <span class="thread-status status-{{ post.status }}">{{ post.status_label }}</span>
      </div>
      {% endfor %}
    </div>
  </section>

  <!-- ── About ── -->
  <section class="about-section">
    <p class="about-line">
      Analysis by <a href="https://twitter.com/{{ site.twitter_username }}">Gaurav Ahlawat</a> —
      data analyst. Independent project, no affiliation with Liverpool FC or any data provider.
      Full methodology at <a href="{{ '/methodology/' | relative_url }}">methodology →</a> ·
      Analysis code on <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub</a>.
    </p>
  </section>

</main>
