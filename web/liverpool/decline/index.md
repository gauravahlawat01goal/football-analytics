---
layout: default
title: "Something broke in year two | Liverpool FC Analysis"
description: "Three seasons of data on Liverpool FC's decline - full season, 38 matches. xG fell 29%, PPG fell from 2.16 to 1.58. The numbers show where it broke."
permalink: /liverpool/decline/
social_image: "/assets/figures/xg_per_match_social.png"
---

<header>
  <div class="badge">Liverpool FC · Slot Y2 Analysis</div>
  <h1>Something broke<br>in year two.</h1>
  <p class="hero-sub-headline">The numbers show exactly where the attacking model broke.</p>
  <p class="subtitle">Klopp's final season. Slot's first two. What the data says happened.</p>
</header>

<main>

  <!-- ── The centrepiece number ── -->
  <section>
    <div class="section-label">The number that started this</div>
    <h2>Liverpool's expected goals dropped by nearly a third.</h2>
    <p class="section-intro">
      Slot's first season was efficient - fewer shots, better quality, same output. Year two lost both.
      This is not a finishing slump. The underlying chances themselves got worse.
    </p>

    <div class="hero-stat-block">
      <div class="hero-stat-number">
        <span class="big">1.77</span>
        <span class="unit">xG per match · Slot Y2 2025–26</span>
      </div>
      <div class="hero-stat-text">
        <div class="hero-delta">↓ 29% from Klopp (2.49) · ↓ 28% from Slot Y1 (2.45)</div>
        <h3>Liverpool's attacking xG fell 29% across three seasons</h3>
      </div>
    </div>

    <figure class="mini-chart mini-chart-wide">
      <figcaption>Liverpool's attacking xG held steady last year, then dropped sharply this year.</figcaption>
      <div class="bar-row">
        <span class="bar-label">Klopp 23–24</span>
        <span class="bar-track"><span class="bar-fill" style="width:100%"></span></span>
        <span class="bar-value">2.49</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Last year</span>
        <span class="bar-track"><span class="bar-fill muted" style="width:98%"></span></span>
        <span class="bar-value">2.45</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">This year</span>
        <span class="bar-track"><span class="bar-fill alert" style="width:71%"></span></span>
        <span class="bar-value">1.77</span>
      </div>
      <p>xG per match. Match-level Understat data, full 38-match seasons.</p>
    </figure>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="label">Points per game - Slot Y2</div>
        <div class="value" style="color:var(--red)">1.58</div>
        <div class="delta down">↓ from 2.16 (Klopp) and 2.21 (Slot Y1)</div>
      </div>
      <div class="stat-card">
        <div class="label">Set-piece xG / match</div>
        <div class="value" style="color:var(--red)">0.339</div>
        <div class="delta down">↓ 50% from Klopp era (0.679)</div>
      </div>
      <div class="stat-card">
        <div class="label">Opponent xG / match - Slot Y2</div>
        <div class="value" style="color:var(--red)">1.42</div>
        <div class="delta down">↑ from 1.11 (Slot Y1) - defence declined too</div>
      </div>
    </div>
  </section>

  <!-- ── Season comparison ── -->
  <section>
    <div class="section-label">Three seasons</div>
    <h2>Every number moved in the wrong direction.</h2>
    <p class="section-intro">
      Slot Y1 had a coherent model - fewer shots, higher quality, same goals. Y2 broke that model without replacing it. Look at the Gap column.
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
            <td>2.16</td>
            <td>2.49</td>
            <td>2.26</td>
            <td class="col-gap">−0.23</td>
            <td>0.123</td>
            <td class="highlight">0.679</td>
            <td>1.25</td>
          </tr>
          <tr>
            <td><span class="season-tag y1">Slot Y1 24–25</span></td>
            <td>2.21</td>
            <td>2.45</td>
            <td>2.26</td>
            <td class="col-gap">−0.19</td>
            <td class="highlight">0.146</td>
            <td>0.487</td>
            <td class="highlight">1.11</td>
          </tr>
          <tr class="row-y2">
            <td><span class="season-tag y2">Slot Y2 25–26 †</span></td>
            <td class="text-red">1.58</td>
            <td class="text-red">1.77</td>
            <td class="text-red">1.66</td>
            <td class="col-gap">−0.11</td>
            <td class="text-red">0.118</td>
            <td class="text-red">0.339</td>
            <td class="text-red">1.42</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="gap-insight">
      The Gap column tells the finishing story. For the first 30 matches of Y2 the gap was −0.21 - consistent with Klopp and Slot Y1. Matches 31–37 saw unusual overperformance; then the final match at Brentford (2.99 xG, 1 goal, 1–1) reversed much of it. The full-season gap settled at −0.11 - closer to the historical pattern than the late-season scoring suggested. The underlying xG of 1.77/match, down 29%, is the story.
    </p>
    <p class="table-note">
      Gap = Goals/match minus xG/match; a small negative gap means goals just below xG (normal finishing), a large negative gap is the signature of bad luck. Slot Y2: 38 of 38 matches - season complete.
      xG data: Understat (full seasons). PPG: official PL record (38 matches each). xG/shot and set-piece xG based on first 30 matches of Y2. Highlighted cells are the strongest figure in each column - highest for attacking metrics, lowest for opponent xG.
    </p>

    <div class="mini-chart-grid" aria-label="Attacking output charts">
      <figure class="mini-chart">
        <figcaption>Shot volume fell again this year.</figcaption>
        <div class="bar-row">
          <span class="bar-label">Klopp 23–24</span>
          <span class="bar-track"><span class="bar-fill" style="width:100%"></span></span>
          <span class="bar-value">20.8</span>
        </div>
        <div class="bar-row">
          <span class="bar-label">Last year</span>
          <span class="bar-track"><span class="bar-fill muted" style="width:82%"></span></span>
          <span class="bar-value">17.1</span>
        </div>
        <div class="bar-row">
          <span class="bar-label">This year</span>
          <span class="bar-track"><span class="bar-fill alert" style="width:75%"></span></span>
          <span class="bar-value">15.5</span>
        </div>
        <p>Shots per match. This year used the first 30-match shot-level pull.</p>
      </figure>

      <figure class="mini-chart">
        <figcaption>Set-piece output almost halved.</figcaption>
        <div class="bar-row">
          <span class="bar-label">Klopp 23–24</span>
          <span class="bar-track"><span class="bar-fill" style="width:100%"></span></span>
          <span class="bar-value">0.679</span>
        </div>
        <div class="bar-row">
          <span class="bar-label">Last year</span>
          <span class="bar-track"><span class="bar-fill muted" style="width:72%"></span></span>
          <span class="bar-value">0.487</span>
        </div>
        <div class="bar-row">
          <span class="bar-label">This year</span>
          <span class="bar-track"><span class="bar-fill alert" style="width:50%"></span></span>
          <span class="bar-value">0.339</span>
        </div>
        <p>Set-piece xG per match. This year used the first 30-match shot-level pull.</p>
      </figure>
    </div>
  </section>

  <!-- ── Confirmed findings ── -->
  <section>
    <div class="section-label">What the tests confirm</div>
    <h2>These changes are real, not noise.</h2>
    <p class="section-intro">
      The xG picture above comes from Understat. The following comes from a second dataset -
      SportsMonks match statistics across full Premier League seasons.
    </p>
    <div class="confirmed-grid">
      <div class="confirmed-card">
        <div class="c-label">Ball Safe (secure possession)</div>
        <div class="c-value">−13.9%</div>
        <div class="c-meta">Very large drop</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Shots on target</div>
        <div class="c-value">−36.8%</div>
        <div class="c-meta">Large drop</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Goal attempts</div>
        <div class="c-value">−29.5%</div>
        <div class="c-meta">Large drop</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Tackles / match</div>
        <div class="c-value">−27.0%</div>
        <div class="c-meta">17.8 → 13.0 per match</div>
      </div>
    </div>
    <p class="table-note" style="margin-top: 1rem;">
      <strong>Statistical rigor:</strong> All four metrics passed a Mann-Whitney U test with Bonferroni correction across 44 variables (α/44 ≈ 0.00114) and showed large to very large effect sizes (Cohen's d between 0.89 and 1.06). See the <a href="{{ '/methodology/' | relative_url }}">methodology</a> for full details.
    </p>
  </section>

  <!-- ── Thread series ── -->
  <section>
    <div class="section-label">Read the analysis</div>
    <h2>The investigation into Liverpool's decline.</h2>
    <p class="section-intro">
      The first piece covers the headline xG decline, while subsequent threads explore pressing and set pieces in detail.
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
      Written by Gaurav Ahlawat, a data and AI systems builder trying to make sense of Liverpool through the numbers.
      Built independently in his free time.
    </p>
  </section>

</main>
