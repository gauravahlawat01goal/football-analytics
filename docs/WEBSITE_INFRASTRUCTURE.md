# Website Infrastructure & Security Setup

This document outlines the hosting, DNS, and security architecture for the Football Analytics website. The setup is designed to be highly secure, enterprise-grade, SEO-optimized, and **100% free** with no risk of surprise overage bills.

## 1. Hosting (GitHub Pages)
The website is statically hosted on **GitHub Pages** using GitHub Actions.
- **Source:** The site is built from the `/web` directory using Jekyll.
- **Deployment:** A GitHub Action (`deploy-pages.yml`) automatically builds and pushes the site to the `gh-pages` environment every time a change is pushed to the `main` branch.
- **Cost & Limits:** Free tier. GitHub provides 100 GB of bandwidth per month and does not charge overages (no surprise billing).

## 2. Domain & DNS (Cloudflare)
The domain (`thefootballnumbers.com`) is managed via **Cloudflare**, which handles DNS resolution and routing.
- **CNAME Record:** The `www` subdomain is CNAME'd to `gauravahlawat01goal.github.io`.
- **Root Domain Routing:** An `A` record for the root (`@`) points to a dummy IP (`192.0.2.1`).
- **Page Redirect Rule:** A Cloudflare Redirect Rule catches all traffic to the root domain (`thefootballnumbers.com/*`) and issues a **301 Permanent Redirect** to the secure `www` equivalent (`https://www.thefootballnumbers.com/$1`). This prevents duplicate content and boosts SEO.

## 3. Security Architecture
The site is protected by multiple layers of security across Cloudflare and GitHub.
- **Cloudflare Proxy (Orange Cloud):** The `www` DNS record is Proxied. Cloudflare stands between the internet and GitHub, providing global caching, Free DDoS mitigation, and Malicious Bot Protection. This ensures bad actors cannot take down the site or exhaust the GitHub bandwidth limit.
- **SSL/TLS Encryption:** 
  - Cloudflare is set to **Full** (or Full Strict) encryption.
  - GitHub Pages has **Enforce HTTPS** enabled.
  - All traffic from the user $\rightarrow$ Cloudflare $\rightarrow$ GitHub is fully encrypted.
- **Repository Security:**
  - `.gitignore` prevents sensitive data (like `.env` files or raw datasets in `/data`) from being committed to the public repo.
  - **Dependabot** is enabled (`.github/dependabot.yml`) to automatically scan and create pull requests for any vulnerable Ruby (Jekyll), Python, or GitHub Action dependencies.

## 4. Search Engine Optimization (SEO)
The site is explicitly configured for Google and other search engines.
- **Canonical URLs:** The `_config.yml` sets the `url` to `https://www.thefootballnumbers.com` and `baseurl` to `""`. This ensures all internal links and social sharing cards (Open Graph/Twitter) use absolute, canonical paths.
- **Sitemap & Robots:** A dynamic `sitemap.xml` and a `robots.txt` file exist in the root of the site.
- **Google Search Console:** The domain is verified via a Cloudflare TXT record (Domain property), and the `sitemap.xml` has been submitted for crawling and indexing.
