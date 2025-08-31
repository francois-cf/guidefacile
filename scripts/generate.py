import csv, os, pathlib, datetime, html

BASE = pathlib.Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
DATA = BASE / "data" / "articles.csv"

def safe_slug(slug):
    return slug.strip().replace(" ", "-").lower()

def render_article(row):
    slug = safe_slug(row["slug"])
    title = row["title"]
    meta_desc = row["meta_desc"]
    summary = row["summary"]
    affiliate_links = row["affiliate_links"].split(";") if row["affiliate_links"] else []
    html_content = row["html_content"]

    outdir = DOCS / slug
    outdir.mkdir(parents=True, exist_ok=True)
    outf = outdir / "index.html"

    links_html = ""
    for link in affiliate_links:
        if ":" in link:
            label, url = link.split(":", 1)
            links_html += f'<a class="btn" href="{html.escape(url.strip())}" target="_blank" rel="nofollow noopener">{html.escape(label.strip())}</a> '

    with open(outf, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(meta_desc)}">
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <h1>{html.escape(title)}</h1>
  <p>{summary}</p>
  <div>{links_html}</div>
  <article>{html_content}</article>
  <p><a href="../index.html">⬅ Retour à l'accueil</a></p>
</body>
</html>""")

    return (row["last_updated"], slug, title, summary)

def build_index_cards(pages):
    indexf = DOCS / "index.html"
    with open(indexf, encoding="utf-8") as f:
        index_html = f.read()

    start = index_html.find("<!-- LATEST-START -->")
    end = index_html.find("<!-- LATEST-END -->")

    if start == -1 or end == -1:
        print("⚠️ Impossible de trouver les marqueurs dans index.html")
        return

    marker = "<!-- LATEST-START -->"
    end_marker = "<!-- LATEST-END -->"

    before = index_html[: start + len(marker)]
    rest = index_html[end:]
    new_inner = "\n" + "\n".join(
        f'<div class="card"><a href="./{slug}/index.html">{title}</a><p>{summary}</p></div>'
        for (_, slug, title, summary) in pages
    ) + "\n"

    new_html = before + new_inner + end_marker + rest

    with open(indexf, "w", encoding="utf-8") as f:
        f.write(new_html)

def build_sitemap_and_rss(pages, site_root):
    # Générer sitemap.xml
    sitemapf = DOCS / "sitemap.xml"
    with open(sitemapf, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f"<url><loc>{site_root}/</loc></url>\n")
        for (_, slug, _, _) in pages:
            f.write(f"<url><loc>{site_root}/{slug}/</loc></url>\n")
        f.write("</urlset>")

    # Générer rss.xml
    rssf = DOCS / "rss.xml"
    with open(rssf, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<rss version="2.0"><channel>\n')
        f.write(f"<title>Guides - {site_root}</title>\n")
        f.write(f"<link>{site_root}/</link>\n")
        for (_, slug, title, summary) in pages:
            f.write("<item>\n")
            f.write(f"<title>{html.escape(title)}</title>\n")
            f.write(f"<link>{site_root}/{slug}/</link>\n")
            f.write(f"<description>{html.escape(summary)}</description>\n")
            f.write("</item>\n")
        f.write("</channel></rss>")

def main():
    pages = []
    if DATA.exists():
        with open(DATA, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                pages.append(render_article(row))

    # newest first
    pages.sort(key=lambda x: x[0], reverse=True)
    build_index_cards(pages)

    # Choisir le site_root : variable d'env (SITE_ROOT) ou fallback github.io
    site_root = os.environ.get("SITE_ROOT")
    if not site_root:
        user, repo = os.environ.get("GITHUB_REPOSITORY", "user/repo").split("/")
        site_root = f"https://{user}.github.io/{repo}"

    print("DEBUG: SITE_ROOT utilisé =", site_root)
    build_sitemap_and_rss(pages, site_root=site_root)

if not DATA.exists():
    raise SystemExit("CSV introuvable: " + str(DATA))

if __name__ == "__main__":
    print("DEBUG: lancement de generate.py…")
    main()
