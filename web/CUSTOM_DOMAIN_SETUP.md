# Custom Domain Setup

Use this once the final public domain is chosen. The current site can remain on GitHub Pages while the custom domain is configured.

## Recommended Short Path

1. Buy a domain.
2. Decide the canonical host:
   - `https://www.example.com/`, or
   - `https://example.com/`
3. Configure DNS for GitHub Pages or Cloudflare Pages.
4. Update `_config.yml`:

   ```yml
   url: "https://www.example.com"
   baseurl: ""
   ```

5. If using GitHub Pages, add a `CNAME` file containing the chosen domain:

   ```text
   www.example.com
   ```

6. Enable HTTPS.
7. Verify the domain in Google Search Console.
8. Submit `/sitemap.xml`.
9. Test these pages:
   - `/`
   - `/liverpool/`
   - `/liverpool/decline/`
   - `/methodology/`
   - `/analysis/2026/04/18/xg-decline-not-bad-luck/`

## Notes

- GitHub Pages can be indexed by Google. A custom domain is mainly for credibility, brand control, and long-term URL stability.
- Keep old GitHub Pages URLs working until the custom-domain version is verified.
- If the canonical domain changes, update social cards, Search Console, and any pinned X/Threads profile links.
