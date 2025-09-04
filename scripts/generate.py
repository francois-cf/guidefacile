import csv, os, pathlib, datetime, html, re

# Chemins de base
BASE = pathlib.Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
DATA = BASE / "data" / "articles.csv"

def _normalize_row(row: dict) -> dict:
    """Normalise les clés et sécurise les champs manquants."""
    lower = { (k or "").strip().lower(): (v or "").strip() for k, v in row.items() }
    slug = (lower.get("slug", "") or "").replace(" ", "-").lower()
    title = lower.get("title", "")
    meta_desc = lower.get("meta_desc", "") or lower.get("meta desc", "") or lower.get("metadesc", "")
    summary = lower.get("summary", "")
    affiliate_links = lower.get("affiliate_links", "") or lower.get("affiliate links", "")
    html_content = lower.get("html_content", "") or lower.get("html content", "") or lower.get("content", "")
    last_updated = lower.get("last_updated", "") or datetime.date.today().isoformat()

    return {
        "slug": slug,
        "title": title,
        "meta_desc": meta_desc,
        "summary": summary,
        "affiliate_links": affiliate_links,
        "html_content": html_content,
        "last_updated": last_updated,
    }

def _read_csv() -> list:
    """Lit le CSV et retourne une liste de pages prêtes à générer."""
    if not DATA.exists():
        raise SystemExit("CSV introuvable: " + str(DATA))
    pages = []
    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = _normalize_row(row)
            if p["slug"] and p["title"]:
                pages.append(p)
    return pages

def _affiliate_buttons(links_str: str) -> str:
    """Transforme 'Label:url;Label2:url2' en boutons HTML .btn dans un .buy-block."""
    if not links_str:
        return ""
    buttons = []
    for part in links_str.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" in part:
            label, url = part.split(":", 1)
        else:
            label, url = "Voir le produit", part
        buttons.append(
            f"<a class='btn' href='{html.escape(url.strip())}' target='_blank' rel='nofollow sponsored noopener'>{html.escape(label.strip())}</a>"
        )
    if not buttons:
        return ""
    return "<div class='buy-block' style='margin:16px 0;display:flex;gap:10px;flex-wrap:wrap;justify-content:center'>" + " ".join(buttons) + "</div>"

def build_page(p: dict) -> None:
    """Génère la page HTML d’un article avec le même design que l’accueil."""
    slug = p["slug"]
    title = p["title"]
    summary = p["summary"]
    meta_desc = p["meta_desc"]
    html_content = p["html_content"]
    buy = _affiliate_buttons(p["affiliate_links"])

    outdir = DOCS / slug
    outdir.mkdir(parents=True, exist_ok=True)
    outf = outdir / "index.html"

    page_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)} • GuideFacile</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(meta_desc)}">
  <link rel="stylesheet" href="../assets/style.css">
  <link rel="icon" href="/favicon.ico?v=3" sizes="any" type="image/x-icon">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png?v=3">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png?v=3">
<link rel="apple-touch-icon" sizes="180x180" href="/favicon-180x180.png?v=3">
<meta name="theme-color" content="#A4193D">


</head>
<body>

  <!-- Hero Crimson -->
  <div class="container">
    <div class="hero">
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(summary)}</p>
      <div class="cta">
        <a class="btn" href="../index.html#guides">Voir les derniers guides</a>
      </div>
    </div>
  </div>

  <!-- Contenu de l’article -->
  <div class="container">
    <article>{html_content}</article>
    {buy}
    <p class="muted">Dernière mise à jour : {html.escape(p["last_updated"])}</p>
  </div>

  <!-- Footer -->
  <footer class="container">
    <p>© <span id="y"></span> GuideFacile • 
      <a href="../legal/privacy.md">Vie privée</a> • 
      Contient des liens d’affiliation. En tant que Partenaire Amazon, GuideFacile réalise un bénéfice sur les achats remplissant les conditions requises.
    </p>
  </footer>
  <script>document.getElementById('y').textContent = new Date().getFullYear()</script>

</body>
</html>"""

    outf.write_text(page_html, encoding="utf-8")

def build_index_cards(pages: list) -> None:
    """Injecte les cartes d’articles entre <!-- LATEST-START --> et <!-- LATEST-END --> dans docs/index.html."""
    indexf = DOCS / "index.html"
    if not indexf.exists():
        print("⚠️ docs/index.html introuvable, saut de la mise à jour de l'accueil.")
        return
    html_text = indexf.read_text(encoding="utf-8")

    seen = set()
    cards = []
    for p in pages:
        slug, title, summary = p["slug"], p["title"], p["summary"]
        if slug in seen:
            continue
        seen.add(slug)
        cards.append(f"<div class='card'><a href='./{slug}/index.html'>{html.escape(title)}</a></div>")

    block = "<!-- LATEST-START -->\n  " + "\n  ".join(cards) + "\n  <!-- LATEST-END -->"

    new_html = re.sub(
        r"<!-- LATEST-START -->.*?<!-- LATEST-END -->",
        block,
        html_text,
        flags=re.DOTALL
    )
    indexf.write_text(new_html, encoding="utf-8")

def build_sitemap_and_rss(pages: list, site_root: str) -> None:
    """Génère sitemap.xml et rss.xml dans docs/ avec la bonne racine d’URL."""
    # SITEMAP
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f"<url><loc>{site_root}/</loc></url>")
    for p in pages:
        sm.append(f"<url><loc>{site_root}/{p['slug']}/</loc></url>")
    sm.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # RSS simple
    rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>']
    rss.append(f"<title>GuideFacile</title>")
    rss.append(f"<link>{site_root}/</link>")
    for p in pages:
        rss.append("<item>")
        rss.append(f"<title>{html.escape(p['title'])}</title>")
        rss.append(f"<link>{site_root}/{p['slug']}/</link>")
        rss.append(f"<description>{html.escape(p['summary'])}</description>")
        rss.append("</item>")
    rss.append("</channel></rss>")
    (DOCS / "rss.xml").write_text("\n".join(rss), encoding="utf-8")

def _sort_key(p: dict):
    """Tri par date (du plus récent au plus ancien), tolérant aux formats."""
    try:
        return datetime.date.fromisoformat(p["last_updated"])
    except Exception:
        return datetime.date.today()

def main():
    print("DEBUG: lancement de generate.py…")

    pages = _read_csv()
    print("DEBUG: articles lus =", len(pages))
    print("DEBUG: slugs =", ", ".join([p["slug"] for p in pages]))

    # Génère chaque page produit
    for p in pages:
        build_page(p)

    # Accueil : cartes automatiques
    pages.sort(key=_sort_key, reverse=True)
    build_index_cards(pages)

    # Détermine la racine de site
    site_root = os.environ.get("SITE_ROOT")
    if not site_root:
        user_repo = os.environ.get("GITHUB_REPOSITORY", "")
        if "/" in user_repo:
            user, repo = user_repo.split("/", 1)
            site_root = f"https://{user}.github.io/{repo}"
        else:
            site_root = "https://example.github.io/repo"
    print("DEBUG: SITE_ROOT utilisé =", site_root)

    # Sitemap + RSS
    build_sitemap_and_rss(pages, site_root=site_root)

if __name__ == "__main__":
    if not DATA.exists():
        raise SystemExit("CSV introuvable: " + str(DATA))
    main()
