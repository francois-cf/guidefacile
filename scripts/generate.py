import csv, os, pathlib, datetime, re, html

BASE = pathlib.Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
DATA = BASE / "data" / "articles.csv"
TPL = (BASE / "templates" / "article.html").read_text(encoding="utf-8")

def sanitize_slug(s):
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9\-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "page"

def render_article(row):
    slug = sanitize_slug(row["slug"])
    title = row["title"].strip()
    meta_desc = row.get("meta_desc","").strip()[:155]
    summary = row.get("summary","").strip()
    html_content = row.get("html_content","").strip()
    affs = row.get("affiliate_links","").strip()
    last_updated = row.get("last_updated") or datetime.date.today().isoformat()

    # Build affiliate list
    items = []
    for part in [p.strip() for p in affs.split(";") if p.strip()]:
        if ":" in part:
            name, url = part.split(":", 1)
            items.append(f"<li><a href='{html.escape(url, quote=True)}' rel='nofollow sponsored noopener' target='_blank'>{html.escape(name)}</a></li>")
        else:
            items.append(f"<li>{html.escape(part)}</li>")
    affiliate_html = "\n        ".join(items) if items else "<li>(À venir)</li>"

    page = (TPL
        .replace("{{TITLE}}", html.escape(title))
        .replace("{{META_DESC}}", html.escape(meta_desc))
        .replace("{{SUMMARY}}", summary)
        .replace("{{HTML_CONTENT}}", html_content)
        .replace("{{AFFILIATE_LINKS}}", affiliate_html)
        .replace("{{DATE}}", html.escape(last_updated))
    )

    outdir = DOCS / slug
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.html").write_text(page, encoding="utf-8")
    return slug, title

def build_index_cards(pages):
    grid_path = DOCS / "index.html"
    html_text = grid_path.read_text(encoding="utf-8")

    # Construire les cartes (une seule fois par slug)
    seen = set()
    cards = []
    for slug, title in pages:
        if slug in seen:
            continue
        seen.add(slug)
        cards.append(f"<div class='card'><a href='./{slug}/index.html'>{html.escape(title)}</a></div>")

    new_block = "<!-- LATEST-START -->\n      " + "\n      ".join(cards) + "\n      <!-- LATEST-END -->"

    # Remplacer précisément entre les repères
    new_html = re.sub(
        r"<!-- LATEST-START -->.*?<!-- LATEST-END -->",
        new_block,
        html_text,
        flags=re.DOTALL
    )

    grid_path.write_text(new_html, encoding="utf-8")


    cards = []
    for slug, title in pages[:24]:
        cards.append(f"<div class='card'><a href='./{slug}/index.html'>{html.escape(title)}</a></div>")
    new_inner = "\n      " + "\n      ".join(cards) + "\n    "
    new_html = before + marker + new_inner + end_marker + rest
    grid_path.write_text(new_html, encoding="utf-8")

def build_sitemap(pages, site_root=None):
    site_root = site_root or os.environ.get("SITE_ROOT", "https://example.github.io/repo")

    # ---- SITEMAP.XML ----
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    # homepage
    lines.append(f"  <url><loc>{site_root}/</loc></url>")
    for slug, _title in pages:
        lines.append(f"  <url><loc>{site_root}/{slug}/</loc></url>")
    lines.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")

    # ---- RSS.XML ----
    rss = [
        '<?xml version="1.0" encoding="UTF-8" ?>',
        '<rss version="2.0"><channel>',
        '<title>GuideFacile</title>',
        f'<link>{site_root}/</link>',
        "<description>Guides d'achat utiles</description>"
    ]
    # date RFC 822
    now_rfc822 = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    for slug, title in pages[:50]:
        rss.append(
            f"<item><title>{html.escape(title)}</title>"
            f"<link>{site_root}/{slug}/</link>"
            f"<pubDate>{now_rfc822}</pubDate></item>"
        )
    rss.append("</channel></rss>")
    (DOCS / "rss.xml").write_text("\n".join(rss), encoding="utf-8")


def main():
    pages = []

    # Vérifie que le CSV existe
    if not DATA.exists():
        raise SystemExit("CSV introuvable: " + str(DATA))

    # Lit le CSV et génère les pages
    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pages.append(render_article(row))

    # Plus récent en premier (tri par slug ici, OK pour commencer)
    pages.sort(key=lambda x: x[0], reverse=True)

    # Debug : combien d'articles lus ?
    print("DEBUG: articles lus =", len(pages))

    # Met à jour l'index et le sitemap
    build_index_cards(pages)
    build_sitemap(pages)


if __name__ == "__main__":
    # Debug : lancement du script
    print("DEBUG: lancement de generate.py…")
    main()
