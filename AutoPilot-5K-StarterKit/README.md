# AutoPilot-5K Starter Kit

A lean, free-to-run system to launch an AI‑assisted, programmatic SEO site with a quiz funnel, email capture, and affiliate/digital‑product monetization. It’s designed to run on autopilot after setup using free tiers.

## What you’ll build
- **Static site** served by **GitHub Pages** from `/docs` (free).
- **Programmatic pages** generated daily by **GitHub Actions** (free).
- **Lead capture** via **Brevo** (free tier) or **Substack** (free).
- **Quiz recommender** via **Tally** (free) -> personalized results page with affiliate links.
- **Content generation** using free **Hugging Face Inference API** (you’ll add your key) or any LLM you prefer; orchestrated via **Make.com** (free tier).
- **Analytics**: Cloudflare Web Analytics (free) or Plausible trial + Google Search Console.
- **Monetization**: Affiliate links + a simple digital product (Notion/Google Sheet template) delivered via **Gumroad** (free-to-start).

> ⚠️ Replace placeholder URLs, IDs, and tokens marked like `YOUR_*` before going live.

---

## Quick start (15 steps)

1) **Create repo** on GitHub and upload this folder. Enable **GitHub Pages** to serve from the `/docs` folder.
2) In your repo, go to **Settings → Pages** and set Source = `Deploy from a branch`, Branch = `main`, Folder = `/docs`.
3) In **Settings → Secrets and variables → Actions**, add these (if you’ll fetch from Notion/HF):
   - `NOTION_TOKEN` = secret token for your Notion integration
   - `NOTION_DATABASE_ID` = the database ID for your Content DB (optional if using CSV)
   - `HF_API_TOKEN` = Hugging Face Inference token (optional)
4) Open `/templates/article.html` to customize branding (colors, logo, copy).
5) Edit `/docs/index.html` (hero section + lead magnet) and `/legal/privacy.md`.
6) Put a few seed rows into `/data/articles.csv` (use the provided example). Each row = a page.
7) Commit & push. Pages will be live at `https://<your-username>.github.io/<repo>/`.
8) **Automation**: In `.github/workflows/build.yml`, a nightly cron runs `/scripts/generate.py` which:
   - reads `/data/articles.csv`
   - renders new pages into `/docs/<slug>/index.html`
   - rebuilds `sitemap.xml` and the index listing
   - commits changes
9) **Lead capture**: Create a Brevo or Substack form. Paste its HTML embed into `/docs/index.html` where indicated.
10) **Quiz funnel**: Build a free **Tally** form with the fields listed in `growth/quiz-questions.txt`. Set its thank-you redirect to `/result/?q=<encoded-answers>` or to a custom result page you generate.
11) **Affiliate**: Replace `YOUR_AFFILIATE_LINK_*` placeholders in `/data/articles.csv`. Start with Amazon FR / Awin / CJ merchants relevant to your niche.
12) **Digital product**: Create a Notion or Google Sheet template. List it in `/docs/index.html` (CTA). Sell via Gumroad. Add delivery link in Gumroad settings (auto-fulfillment).
13) **Make.com orchestration**: Use `growth/make-scenario-outline.md` to set a scenario that, each day, (a) generates 5–20 article drafts via HF Inference or your LLM, (b) appends rows to `/data/articles.csv` via GitHub API, and (c) posts titles to Buffer/Twitter.
14) **Analytics**: Add your Cloudflare or Plausible snippet to `/templates/article.html` and `/docs/index.html` in the `<!-- ANALYTICS -->` slot.
15) **SEO**: Submit `https://<your-domain>/sitemap.xml` to Google Search Console.

---

## Files of note
- `scripts/generate.py` — page generator and sitemap builder.
- `automation/build.yml` — GitHub Actions nightly cron.
- `data/articles.csv` — your content “CMS” (replace with Notion later if desired).
- `prompts/article_prompt.txt` — copyable LLM prompt for consistent articles.
- `prompts/product_selector_prompt.txt` — prompt to generate quiz-based recommendations.
- `growth/quiz-questions.txt` — questions to create in Tally for your quiz.
- `growth/email-sequences.txt` — welcome, referral, and upsell copy.
- `legal/privacy.md` — GDPR-friendly privacy template (edit for your case).

---

## Upgrade path (optional)
- Replace CSV with Notion: point `scripts/generate.py` to your Notion DB (code path included but commented).
- Add Pinterest/Twitter autoposts with Buffer (free tier) reading `docs/rss.xml`.
- Add a basic referral system with a Tally form + Make.com counting referrals in a Notion table, then emailing unlock codes via Brevo.

Good luck — ship fast, iterate weekly, and keep pages helpful and compliant.
