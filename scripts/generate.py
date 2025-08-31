import csv, os, pathlib, datetime, re, html

# Chemins
BASE = pathlib.Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
DATA = BASE / "data" / "articles.csv"

# S'assure que docs/ existe et contient .nojekyll
DOCS.mkdir(parents=True, exist_ok=True)
(DOCS / ".nojekyll").write_text("", encoding="utf-8")

def _read_csv():
    if not DATA.exists():
        raise SystemExit("CSV introuvable: " + str(DATA))
    pages = []
    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalise les champs
            slug = (row.get("slug") or "").strip()
            title = (row.get("title") or "").strip()
            meta_desc = (row.get("meta_desc") or "").strip()
            summary = (row.get("summary") or "").strip()
            affiliate_links = (row.get("affiliate_links") or "").strip()
            html_content = (row.get("html_content") or "").strip()
            last_updated = (row.get("last_updated") or "").strip()
            if not slug or not title:
                # Ignore les lignes incomplètes
                continue
            pages.append({
                "slug": slug,
                "title": title,
                "meta_desc": meta_desc,
                "summary": summary,
                "affiliate_links": affiliate_links,
                "html_content": html_content,
                "last_updated": last_updated or datetime.date.today().isoformat(),
            })
    return pages

def _render_affiliate_buttons(links_str: str) -> str:
    if not links_str:
        return ""
    buttons = []
    # format attendu: "Amazon:https://...;Decathlon:https://..."
    for part in links_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            name, url = part.split(":", 1)
        else:
            name, url = "Acheter", part
        name = html.escape(name.strip())
        url = html.escape(url.strip())
        buttons.append(f"<a class='btn' href='{url}' rel='nofollow sponsored'>Voir sur {name}</a>")
    if not buttons:
        return ""
    return "<div class='buy-block'>" + " ".join(buttons) + "</div>"

def build_page(page):
    slug = page["slug"]
    title = page["title"]
    meta_desc = page["meta_desc"]
    summary = page["summary"]
    html_content = page["html_content"]
    buy = _render_affiliate_buttons(page["affiliate_links"])

    # Répertoire de la page
    outdir = DOCS / slug
    outdir.mkdir(parents=True, exist_ok=True)

    # Template minimal autonome (utilise le style global de l'index si présent)
    body = f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <title>{html.escape(title)} — GuideFacile</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="canonical" href="./">
  <link rel="stylesheet" href="../style.css" onerror="this.remove()">
  <style>
    body{{font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu;max-width:860px;margin:0 auto;padding:16px}}
    .btn{{display:inline-block;padding:.6rem .9rem;border-radius:.6rem;border:1px solid #ddd;text-decoration:none}}
    .buy-block{{margin:1rem 0;display:flex;gap:.5rem;flex-wrap:wrap}}
    .muted{{color:#666;font-size:.95rem}}
    .back{{margin:1rem 0;display:inline-block}}
    table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #eee;padding:.5rem;text-align:left}}
  </style>
</head>
<body>
  <a class="back" href="../">← Retour</a>
  <h1>{html.escape(title)}</h1>
  <p class="muted">{html.escape(summary)}</p>
  {buy}
  <article>
    {html_content}
  </article>
  {buy}
  <p class="muted">Dernière mise à jour : {html.escape(page["last_updated"])}</p>
</body>
</html>"""
    (outdir / "index.html").write_text(body, encoding="utf-8")

def build_index_cards(pages):
    """Remplit la zone entre <!-- LATEST-START --> et <!-- LATEST-END --> dans docs/index.html"""
    grid_path = DOCS / "index.html"
    html_text = grid_path.read_text(encoding="utf-8")

    seen = set()
    cards = []
    for p in pages:
        slug, title = p["slug"], p["title"]
        if slug in seen:
            continue
        seen.add(slug)
        cards.append(f"<div class='card'><a href='./{slug}/index.html'>{html.escape(title)}</a></div>")

    new_block = "<!-- LATEST-START -->\n    " + "\n    ".join(cards) + "\n    <!-- LATEST-END -->"

    new_html = re.sub(
        r"<!-- LATEST-START -->.*?<!-- LATEST-END -->",
        new_block,
        html_text,
        flags=re.DOTALL
    )
    grid_path.write_text(new_html, encoding="utf-8")

def build_sitemap_and_rss(pages, site_root=None):
    site_root = site_root or os.environ.get("SITE_ROOT", "https://example.github.io/repo")

    # SITEMAP
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f"  <url><loc>{site_root}/</loc></url>")
    for p in pages:
        sm.append(f"  <url><loc>{site_root}/{p['slug']}/</loc></url>")
    sm.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # RSS (50 derniers)
    rss = ['<?xml version="1.0" encoding="UTF-8" ?>',
           '<rss version="2.0"><channel>',
           '<title>GuideFacile</title>',
           f'<link>{site_root}/</link>',
           "<description>Guides d'achat utiles</description>"]
    now_rfc822 = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    for p in pages[:50]:
        rss.append(
            f"<item><title>{html.escape(p['title'])}</title>"
            f"<link>{site_root}/{p['slug']}/</link>"
            f"<pubDate>{now_rfc822}</pubDate></item>"
        )
    rss.append("</channel></rss>")
    (DOCS / "rss.xml").write_text("\n".join(rss), encoding="utf-8")

def main():
    print("DEBUG: lancement de generate.py…")
    pages = _read_csv()
    print("DEBUG: articles lus =", len(pages))

    # Génère chaque page
    for p in pages:
        build_page(p)

    # Met à jour l'accueil + sitemap/rss
    build_index_cards(pages)
  # Utilise d'abord la variable d'env SITE_ROOT (build.yml), sinon fallback github.io
site_root = os.environ.get("SITE_ROOT")
if not site_root:
    user, repo = os.environ.get("GITHUB_REPOSITORY", "user/repo").split("/")
    site_root = f"https://{user}.github.io/{repo}"

print("DEBUG: SITE_ROOT utilisé =", site_root)
build_sitemap_and_rss(pages, site_root=site_root)

if __name__ == "__main__":
    main()
