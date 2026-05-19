---
layout: default
title: "Methodology | Liverpool FC Analysis"
description: "Data sources, statistical framework, and caveats for the Liverpool FC three-season analysis. SportsMonks, Understat, Mann-Whitney U, Bonferroni correction."
permalink: /methodology/
---

<header>
  <div class="badge">Liverpool FC · Three Seasons of Data</div>
  <h1>Methodology.</h1>
  <p class="hero-sub-headline">What was measured, how, and what it can and cannot prove.</p>
</header>

<main>

  <!-- ── Data sources ── -->
  <section>
    <div class="section-label">Data sources</div>
    <h2>Three tiers of data.</h2>
    <div class="source-grid">
      <div class="source-card">
        <div class="tier">Tier 1 · Match data</div>
        <h4>SportsMonks API v3</h4>
        <p>101 processed fixtures across three seasons. 44 match statistics per team per match — shots, tackles, passes, possession, interceptions, key passes, big chances, and more. Also: lineups, formations, ball coordinates, goals, and scores.</p>
      </div>
      <div class="source-card">
        <div class="tier">Tier 2 · xG enrichment</div>
        <h4>Understat</h4>
        <p>107 matches, 1,924 per-shot xG records with coordinates. Enables xG/match, xG/shot, and open-play vs set-piece breakdown. Shot-level data covers the first 30 Y2 matches; match-level xG updated to 37 matches.</p>
      </div>
      <div class="source-card">
        <div class="tier">Tier 3 · Pressing metrics</div>
        <h4>FBRef</h4>
        <p>PPDA (passes allowed per defensive action) per match — a more precise pressing intensity proxy than tackle counts. Integration in progress; current pressing analysis uses SportsMonks tackle and interception data.</p>
      </div>
    </div>
    <p class="table-note" style="margin-top:0.85rem;">
      Raw data is not published. Analysis code is available in the
      <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub repository</a>.
      All data used under respective providers' terms.
    </p>
  </section>

  <!-- ── Statistical framework ── -->
  <section>
    <div class="section-label">Statistical framework</div>
    <h2>How findings are tested and labelled.</h2>
    <div class="method-box">
      <p>
        <strong>Confirmatory analysis</strong> (Klopp 2023–24 vs Slot Y2 2025–26): Mann-Whitney U tests
        with Bonferroni correction across all 44 statistical metrics. Mann-Whitney U is a non-parametric
        rank-based test — appropriate for match statistics, which are bounded and often skewed.
        The Bonferroni threshold (α/44 ≈ 0.00114) is the most conservative multiple-comparison
        correction available. Only findings that survive this threshold are reported as
        <strong>confirmed</strong>.
      </p>
      <p>
        <strong>Exploratory analysis</strong> (Slot Y1 vs Y2): Y2 is a near-complete season — 37 of 38
        matches at time of publication. Y1-vs-Y2 comparisons report effect sizes and directional signals
        only. These are clearly labelled as <strong>directional</strong>. Nominal p-values are noted
        but not treated as sufficient on their own.
      </p>
      <p>
        <strong>Effect sizes</strong>: All findings include Cohen's d (standardised mean difference).
        d = 0.2 is small, d = 0.5 is medium, d = 0.8 is large. The confirmed findings range from
        d = 0.86 to d = 1.11 — large to very large effects.
      </p>
      <p>
        <strong>House style</strong>: <em>Observed</em> = descriptive data trend from a single source.
        <em>Confirmed</em> = survived Bonferroni-corrected statistical testing.
        <em>Directional</em> = suggestive, exploratory, or not corrected for multiple comparisons.
      </p>
    </div>
  </section>

  <!-- ── Confirmed findings ── -->
  <section>
    <div class="section-label">Confirmed findings</div>
    <h2>What survived the strictest test.</h2>
    <p class="section-intro">
      Klopp 2023–24 vs Slot Y2 2025–26. Mann-Whitney U, Bonferroni-corrected across 44 metrics.
    </p>
    <div class="confirmed-grid">
      <div class="confirmed-card">
        <div class="c-label">Ball Safe</div>
        <div class="c-value">−13.5%</div>
        <div class="c-meta">Cohen's d = 1.11 — very large effect</div>
      </div>
      <div class="confirmed-card">
        <div class="c-label">Shots outside box</div>
        <div class="c-value">−38.6%</div>
        <div class="c-meta">Cohen's d = 0.93 — large effect</div>
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
        <div class="c-meta">17.9 → 13.3 per match · d = 0.86</div>
      </div>
    </div>
  </section>

  <!-- ── Scope and caveats ── -->
  <section>
    <div class="section-label">Scope and caveats</div>
    <h2>What this analysis cannot claim.</h2>
    <div class="method-box">
      <p>
        <strong>No causation.</strong> This analysis documents associations between seasons — it does not
        establish that any specific change (manager tactics, player departures, injuries, fixture difficulty)
        caused the observed declines. Where timing is noted (e.g. set-piece xG and Trent Alexander-Arnold's
        departure), it is presented as consistent with the data, not proven by it.
      </p>
      <p>
        <strong>No opponent adjustment.</strong> All metrics are raw — they do not adjust for opponent
        strength. A tackles-per-match average of 13.3 means different things against different opposition.
        Opponent-adjusted metrics are planned but not yet complete.
      </p>
      <p>
        <strong>Y2 sample.</strong> Slot Y2 figures are based on 37 of 38 matches (one fixture remaining —
        Brentford away, May 24). xG/shot and set-piece xG are from the original 30-match Understat pull;
        match-level xG has been updated to 37 matches. All Y2 figures will be refreshed after the season
        concludes.
      </p>
      <p>
        <strong>Mixed shot-level sample.</strong> The shot volume (15.5/match) and xG/shot (0.118) figures
        come from the first 30 matches of Y2. The final seven matches showed higher goals-per-match (2.0)
        through significant finishing overperformance (+0.57 gap) — not an improvement in underlying chance
        quality. These two samples are clearly distinguished throughout the analysis.
      </p>
    </div>
    <div class="caveat-box">
      Slot Y2: 37 of 38 matches played. Match-level xG updated to 37 matches via Understat.
      Shot-level breakdowns (xG/shot, set-piece xG) based on first 30-match pull and labelled accordingly.
    </div>
  </section>

  <!-- ── Reproducibility ── -->
  <section>
    <div class="section-label">Reproducibility</div>
    <h2>Running the analysis.</h2>
    <div class="method-box">
      <p>
        The full pipeline — data collection, processing, and analysis — is available in the
        <a href="https://github.com/{{ site.github_username }}/football-analytics">GitHub repository</a>.
        Requires Python 3.11+, Poetry, and a SportsMonks API key.
      </p>
      <p>
        Analysis scripts in <code>scripts/analysis/</code> run end-to-end and reproduce all 26 charts.
        Statistical helpers (Mann-Whitney U, Cohen's d, Bonferroni correction) are in
        <code>src/liverpool_strategy/analysis/notebook_helpers.py</code>.
      </p>
      <p>
        Raw and processed data are not published in the repository. Aggregate outputs and methodology
        are fully documented in the code.
      </p>
    </div>
  </section>

  <!-- ── Back link ── -->
  <section class="about-section">
    <p class="about-line">
      ← <a href="{{ '/liverpool/decline/' | relative_url }}">Back to the analysis</a> ·
      <a href="{{ '/liverpool/' | relative_url }}">Liverpool FC project</a> ·
      <a href="{{ '/' | relative_url }}">Home</a>
    </p>
  </section>

</main>
