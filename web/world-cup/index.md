---
layout: default
title: "World Cup 2026 | The Football Numbers"
description: "Previews, tactical analysis and evidence-led features from the 2026 FIFA World Cup."
permalink: /world-cup/
---

<header>
  <div class="badge">World Cup 2026</div>
  <h1>The tournament, explained.</h1>
  <p class="hero-sub-headline">Previews, tactical arguments and evidence-led features from every stage of the knockout rounds.</p>
  <p class="subtitle">These are the final editions first published as X Articles, preserved here as a permanent, readable archive.</p>
</header>

<main>
  <section>
    <div class="section-label">Archive</div>
    <h2>World Cup analysis.</h2>
    <div class="thread-list">
      {% assign world_cup_posts = site.posts | where: 'series', 'World Cup 2026' | sort: 'date' | reverse %}
      {% for post in world_cup_posts %}
      <div class="thread-item {{ post.status }}">
        {% assign item_number = forloop.index %}
        <div class="thread-num">{{ item_number | prepend: '0' | slice: -2, 2 }}</div>
        <div class="thread-content">
          <h3><a href="{{ post.url | relative_url }}">{{ post.title }}</a></h3>
          <p>{{ post.excerpt | strip_html | truncatewords: 28 }}</p>
        </div>
        <time class="thread-status status-live" datetime="{{ post.date | date: '%Y-%m-%d' }}">{{ post.date | date: "%b %-d" }}</time>
      </div>
      {% endfor %}
    </div>
  </section>
</main>
