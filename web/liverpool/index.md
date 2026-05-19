---
layout: default
title: "Liverpool FC Analysis | Gaurav Ahlawat"
description: "Data-driven analysis of Liverpool FC across three seasons — Klopp 2023–24, Slot Y1 2024–25, Slot Y2 2025–26. xG, pressing, set pieces, game state."
permalink: /liverpool/
---

<header>
  <div class="badge">Liverpool FC · Three Seasons</div>
  <h1>Liverpool FC<br><span style="color:var(--red)">Three seasons of data.</span></h1>
  <p class="hero-sub-headline">Klopp's final year. Slot's first two. What changed, what declined, and what the numbers say.</p>
  <p class="subtitle">An independent statistical analysis using SportsMonks match data, Understat per-shot xG, and FBRef pressing metrics. 101 processed fixtures. 37 Y2 matches tracked.</p>
</header>

<main>

  <!-- ── Featured analysis ── -->
  <section>
    <div class="section-label">Featured analysis</div>
    <h2>Something broke in year two.</h2>
    <p class="section-intro">
      The flagship analysis. Liverpool's Slot Y2 regression examined across xG, shot volume, shot quality,
      set-piece output, and pressing intensity — using two independent datasets.
    </p>
    <div class="featured-card">
      <div class="featured-card-content">
        <div class="featured-eyebrow">Slot Y2 2025–26 · 37 matches</div>
        <h3>The numbers behind Liverpool's decline</h3>
        <p>xG/match fell 30% from Klopp (2.49 → 1.74). Both shot volume and shot quality declined simultaneously. The evidence points upstream of the finishing.</p>
        <div class="featured-stats">
          <span>1.74 xG/match</span>
          <span>1.59 PPG</span>
          <span>−50% set-piece xG</span>
        </div>
      </div>
      <a href="{{ '/liverpool/decline/' | relative_url }}" class="featured-card-link">Read the analysis →</a>
    </div>
  </section>

  <!-- ── Thread series ── -->
  <section>
    <div class="section-label">Published threads</div>
    <h2>The investigation, piece by piece.</h2>
    <div class="thread-list">
      {% assign sorted_posts = site.posts | sort: 'thread_num' %}
      {% for post in sorted_posts %}
      <div class="thread-item {{ post.status }}">
        <div class="thread-num">{{ post.thread_num | prepend: '0' | slice: -2, 2 }}</div>
        <div class="thread-content">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
          <p>{{ post.excerpt | strip_html | truncatewords: 25 }}</p>
        </div>
        <span class="thread-status status-{{ post.status }}">{{ post.status_label }}</span>
      </div>
      {% endfor %}
    </div>
  </section>

  <!-- ── Key findings ── -->
  <section>
    <div class="section-label">Key findings</div>
    <h2>What the data established.</h2>
    <div class="findings-list">
      <div class="finding-item">
        <div class="finding-label">Attacking xG fell 30%</div>
        <div class="finding-detail">2.49 (Klopp) → 2.45 (Y1) → 1.74 (Y2) per match. Observed across 37 matches via Understat.</div>
      </div>
      <div class="finding-item">
        <div class="finding-label">Set-piece xG halved</div>
        <div class="finding-detail">0.679 → 0.487 → 0.339 per match. Consistent with the impact of Trent Alexander-Arnold's departure.</div>
      </div>
      <div class="finding-item">
        <div class="finding-label">Pressing collapsed</div>
        <div class="finding-detail">Tackles/match: 17.9 → 13.3 (−26%). Bonferroni-confirmed across 44 metrics.</div>
      </div>
      <div class="finding-item">
        <div class="finding-label">Defence also declined</div>
        <div class="finding-detail">Opponent xG: 1.25 → 1.11 → 1.42 per match. Attack and defence regressed simultaneously.</div>
      </div>
    </div>
    <p class="table-note" style="margin-top:1.5rem;">
      Confirmatory findings (Klopp vs Slot Y2): Mann-Whitney U with Bonferroni correction across 44 metrics.
      Full statistical framework at <a href="{{ '/methodology/' | relative_url }}">methodology →</a>
    </p>
  </section>

  <!-- ── About ── -->
  <section class="about-section">
    <p class="about-line">
      Analysis by <a href="https://twitter.com/{{ site.twitter_username }}">Gaurav Ahlawat</a> —
      data analyst. Independent project, no affiliation with Liverpool FC.
      Analysis code on <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub</a>.
    </p>
  </section>

</main>
