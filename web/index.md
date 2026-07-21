---
layout: default
title: "Football Analytics | Gaurav Ahlawat"
description: "Independent, evidence-led football analysis covering the 2026 World Cup, Liverpool and the tactical stories behind the numbers."
social_image: "/assets/figures/xg_per_match_social.png"
---

<header>
  <div class="badge">Football Analytics</div>
  <h1>Football analysis.</h1>
  <p class="hero-sub-headline">Independent analysis of the 2026 World Cup, Liverpool and the game behind the numbers.</p>
  <p class="subtitle">Tactical writing grounded in match data, reporting and what happened on the pitch.</p>
</header>

<main>

  <!-- ── Featured project ── -->
  <section>
    <div class="section-label">Featured project</div>
    <h2>Liverpool FC - three seasons of data.</h2>
    <p class="section-intro">
      How did the reigning champions regress so sharply? The analysis spans Slot's title-winning first season, his troubled second, and Klopp's final year as the baseline - using SportsMonks match statistics and Understat per-shot xG across 114 fixtures.
    </p>

    <div class="featured-card">
      <div class="featured-card-content">
        <div class="featured-eyebrow">Slot Y2 2025–26 · Season complete</div>
        <h3>Something broke in year two.</h3>
        <p>xG/match fell 29% from Klopp (2.49 → 1.77). Shot volume, shot quality, and set-piece output all declined. Two datasets point to the same conclusion.</p>
        <div class="featured-stats">
          <span>1.77 xG / match</span>
          <span>1.58 PPG</span>
          <span>−29% from Klopp</span>
        </div>
      </div>
      <a href="{{ '/liverpool/decline/' | relative_url }}" class="featured-card-link">Read the analysis →</a>
    </div>
  </section>

  <!-- ── Published analysis ── -->
  <section>
    <div class="section-label">Latest</div>
    <h2>Latest analysis.</h2>
    <p class="section-intro">World Cup previews and features, plus longer-running club projects. Browse the full <a href="{{ '/world-cup/' | relative_url }}">World Cup 2026 archive</a>.</p>
    <div class="thread-list">
      {% assign sorted_posts = site.posts | sort: 'date' | reverse %}
      {% for post in sorted_posts limit: 6 %}
      <div class="thread-item {{ post.status }}">
        {% assign item_number = forloop.index %}
        <div class="thread-num">{{ item_number | prepend: '0' | slice: -2, 2 }}</div>
        <div class="thread-content">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
          <p>{{ post.excerpt | strip_html | truncatewords: 25 }}</p>
        </div>
        <span class="thread-status status-{{ post.status }}">{{ post.series | default: post.status_label }}</span>
      </div>
      {% endfor %}
    </div>
    <p class="archive-link"><a href="{{ '/world-cup/' | relative_url }}">View all 12 World Cup articles →</a></p>
  </section>

  <!-- ── About ── -->
  <section class="about-section">
    <p class="about-line">
      Analysis by Gaurav Ahlawat. Independent football writing built from match data,
      reporting and tactical context.
      Analysis code on <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub</a>.
    </p>
  </section>

</main>
