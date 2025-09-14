import os, pathlib, datetime, html, re, csv

# Chemins de base
BASE = pathlib.Path(__file__).resolve().parents[1]
DOCS = BASE / "docs"
DATA = BASE / "data" / "articles.csv"

# -------- CSV robuste (tolère les lignes "cassées") --------
def _normalize_row(row, lineno=None):
    """Nettoie une ligne CSV et aplatit les listes accidentelles pour éviter les plantages."""
    norm = {}
    for k, v in row.items():
        key = (k or "").strip().lower()

        # Certaines lignes mal collées transforment un champ en liste -> on join proprement
        if isinstance(v, list):
            print(f"DEBUG: valeur liste détectée ligne {lineno}, key={key} -> {v}")
            v = ",".join(str(x) for x in v)

        # Cast en str + suppression des retours à la ligne internes
        if v is None:
            val = ""
        else:
            val = str(v)
        val = val.replace("\r", " ").replace("\n", " ").strip()
        norm[key] = val
    return norm


def _read_csv():
    pages = []
    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(
            f,
            delimiter=",",
            quotechar='"',
            skipinitialspace=True
        )
        for i, row in enumerate(reader, start=2):  # i=2 = première ligne après l'en-tête
            try:
                p = _normalize_row(row, lineno=i)

                # sécurité : on vérifie qu'il y a bien un slug et un title
                if not p.get("slug") or not p.get("title"):
                    print(f"ERROR: ligne {i} ignorée (slug/title manquant). Contenu={p}")
                    continue

                pages.append(p)   # <-- on stocke le dict tel quel (PAS de render_article)
            except Exception as e:
                print(f"ERROR: ligne {i} ignorée ({e}). Contenu brut={row}")
                continue
    return pages


# -------- Boutons d’affiliation --------
def _affiliate_buttons(links_str: str) -> str:
    """Transforme 'Label:url;Label2:url2' en boutons HTML. Amazon -> .btn-amazon, sinon .btn."""
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
        url_str = (url or "").strip()
        is_amazon = ("amzn.to" in url_str.lower()) or ("amazon." in url_str.lower())
        css_class = "btn-amazon" if is_amazon else "btn"
        buttons.append(
            f"<a class='{css_class}' href='{html.escape(url_str)}' target='_blank' rel='nofollow sponsored noopener'>{html.escape(label.strip())}</a>"
        )
    if not buttons:
        return ""
    return "<div class='buy-block' style='margin:16px 0;display:flex;gap:10px;flex-wrap:wrap;justify-content:center'>" + " ".join(buttons) + "</div>"


# -------- Page article (même design que l’accueil) --------
def build_page(p: dict) -> None:
    """Génère la page HTML d’un article dans l’ordre: hero -> bouton (haut) -> description -> photo -> bouton (bas)."""
    slug = p["slug"]
    title = p["title"]
    summary = p["summary"]
    meta_desc = p["meta_desc"]

    # Boutons affiliés (haut/bas identiques)
    buy_html = _affiliate_buttons(p.get("affiliate_links") or p.get("liens_affiliés") or "")

    # Image (pas de lien cliquable)
    image_url = (p.get("image_url") or p.get("image") or "").strip()
    image_html = ""
    if image_url:
        image_html = f"""
        <figure class="product-figure">
          <img class="product-img" src="{html.escape(image_url)}" alt="{html.escape(title)}" loading="lazy" />
        </figure>
        """

    html_content = p["html_content"]

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

  <!-- Hero -->
  <div class="container">
    <div class="hero">
      <h1>{html.escape(title)}</h1>
      <p>{html.escape(summary)}</p>
      <div class="cta">
        <a class="btn" href="../index.html#guides">Voir les derniers guides</a>
      </div>
    </div>
  </div>

  <!-- Bouton Amazon (haut, centré) -->
  <div class="container">
    <div class="buy-block buy-top">
      {buy_html}
    </div>
  </div>

  <!-- Description / contenu -->
  <div class="container">
    <article>{html_content}</article>
  </div>

  <!-- Photo (non cliquable) -->
  <div class="container">
    {image_html}
  </div>

  <!-- Bouton Amazon (bas, identique) -->
  <div class="container">
    <div class="buy-block buy-bottom">
      {buy_html}
    </div>
  </div>

  <!-- Métadonnée de mise à jour -->
  <div class="container">
    <div class="updated">
      <small><span class="dot"></span> Mis à jour le 
        <time datetime="{html.escape(p['last_updated'])}">{html.escape(p['last_updated'])}</time>
      </small>
    </div>
  </div>

  <!-- Footer -->
  <footer class="container">
    <p>© <span id="y"></span> GuideFacile • 
      <a href="../legal/privacy.md">Vie privée</a> • 
      Certains liens sont affiliés. Nous pouvons recevoir une commission sans coût supplémentaire pour vous.
    </p>
  </footer>
  <script>document.getElementById('y').textContent = new Date().getFullYear()</script>

</body>
</html>"""

    outf.write_text(page_html, encoding="utf-8")



# -------- Accueil : injection des cartes --------
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
        slug, title, summary = p["slug"], p["title"], p.get("summary", "")
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


# -------- Sitemap + RSS --------
def build_sitemap_and_rss(pages: list, site_root: str) -> None:
    # SITEMAP
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm.append(f"<url><loc>{site_root}/</loc></url>")
    for p in pages:
        sm.append(f"<url><loc>{site_root}/{p['slug']}/</loc></url>")
    sm.append("</urlset>")
    (DOCS / "sitemap.xml").write_text("\n".join(sm), encoding="utf-8")

    # RSS (très simple)
    rss = ['<?xml version="1.0" encoding="UTF-8"?>', '<rss version="2.0"><channel>']
    rss.append(f"<title>GuideFacile</title>")
    rss.append(f"<link>{site_root}/</link>")
    for p in pages:
        rss.append("<item>")
        rss.append(f"<title>{html.escape(p['title'])}</title>")
        rss.append(f"<link>{site_root}/{p['slug']}/</link>")
        rss.append(f"<description>{html.escape(p.get('summary',''))}</description>")
        rss.append("</item>")
    rss.append("</channel></rss>")
    (DOCS / "rss.xml").write_text("\n".join(rss), encoding="utf-8")


def _sort_key(p: dict):
    """Tri par date (du plus récent au plus ancien), tolérant aux formats."""
    try:
        return datetime.date.fromisoformat(p.get("last_updated",""))
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
