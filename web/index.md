---
layout: default
title: "Football Analytics | Gaurav Ahlawat"
description: "Data-driven football analysis. Liverpool FC three-season study — xG, pressing, set pieces, game state."
---

<header>
  <div class="badge">Football Analytics</div>
  <h1>Data-driven analysis<br>of the game.</h1>
  <p class="hero-sub-headline">Independent football research. Starting with Liverpool FC.</p>
  <p class="subtitle">Statistical analysis combining match data, per-shot xG, and pressing metrics. Built to answer specific questions — not just describe what happened.</p>
</header>

<main>

  <!-- ── Featured project ── -->
  <section>
    <div class="section-label">Featured project</div>
    <h2>Liverpool FC — three seasons of data.</h2>
    <p class="section-intro">
      How did the reigning champions regress so sharply? The analysis spans Slot's title-winning first season, his troubled second, and Klopp's final year as the baseline — using SportsMonks match statistics and Understat per-shot xG across 114 fixtures.
    </p>

    <div class="featured-card">
      <div class="featured-card-content">
        <div class="featured-eyebrow">Slot Y2 2025–26 · Season complete</div>
        <h3>Something broke in year two.</h3>
        <p>xG/match fell 29% from Klopp (2.49 → 1.77). Shot volume declined. Shot quality declined. Set-piece xG halved. Two independent datasets point to the same conclusion.</p>
        <div class="featured-stats">
          <span>1.77 xG / match</span>
          <span>1.58 PPG</span>
          <span>−29% from Klopp</span>
        </div>
      </div>
      <a href="{{ '/liverpool/decline/' | relative_url }}" class="featured-card-link">Read the analysis →</a>
    </div>
  </section>

  <!-- ── Published threads ── -->
  <section>
    <div class="section-label">Published</div>
    <h2>Published analysis.</h2>
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

  <!-- ── About ── -->
  <section class="about-section">
    <p class="about-line">
      Analysis by <a href="https://twitter.com/{{ site.twitter_username }}">Gaurav Ahlawat</a>,
      data analyst. Liverpool FC is the first project in an ongoing series covering the Premier League,
      Bundesliga, La Liga, and Serie A.
      Analysis code on <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub</a>.
    </p>
  </section>

</main>
