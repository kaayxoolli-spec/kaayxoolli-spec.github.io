#!/usr/bin/env python3
"""Construit le site Kaay Xool dans _site/ à partir des annonces.

Les annonces viennent du Google Sheets publié en CSV (SHEET_CSV_URL dans config.json),
ou à défaut du fichier data/annonces.csv.
Colonnes : ref, type, categorie, quoi, ou, ville, date, description, photo
"""
import csv
import io
import json
import os
import re
import shutil
import unicodedata
import urllib.request
from datetime import date
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8")) if (ROOT / "config.json").exists() else {}


def setting(name, default=""):
    return (os.environ.get(name) or CONFIG.get(name) or default).strip()


SITE_URL = setting("SITE_URL", "https://kaayxoolli-spec.github.io").rstrip("/")
SHEET_CSV_URL = setting("SHEET_CSV_URL")
GOOGLE_VERIFICATION = setting("GOOGLE_VERIFICATION")
BING_VERIFICATION = setting("BING_VERIFICATION")
INDEXNOW_KEY = setting("INDEXNOW_KEY")

INSTAGRAM = "kaayxoolli"
EMAIL = "kaayxoolli@gmail.com"
CATS = ["Papiers", "Téléphones", "Clés", "Sacs et portefeuilles", "Bijoux", "Animaux", "Personnes", "Véhicules", "Autres"]
VILLES = ["Dakar", "Pikine", "Guédiawaye", "Keur Massar", "Rufisque", "Thiès", "Mbour", "Saint-Louis", "Touba",
          "Kaolack", "Ziguinchor", "Diourbel", "Louga", "Tambacounda", "Kolda", "Fatick", "Kaffrine", "Matam",
          "Kédougou", "Sédhiou", "Autre"]
TYPES = {
    "perdu": ("Perdus", "PERDU", "perdu"),
    "trouve": ("Trouvés", "TROUVÉ", "trouvé"),
    "recherche": ("Personnes recherchées", "RECHERCHÉ", "recherché"),
    "retrouve": ("Retrouvés", "RETROUVÉ", "retrouvé"),
}
QUICK = ["Carte d'identité", "Téléphone", "Clés", "Passeport", "Chat", "Portefeuille"]


def plain(s):
    return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()


def read_rows():
    text = None
    if SHEET_CSV_URL:
        try:
            with urllib.request.urlopen(SHEET_CSV_URL, timeout=30) as r:
                text = r.read().decode("utf-8-sig")
            print("Annonces lues depuis Google Sheets")
        except Exception as err:
            print(f"Google Sheets illisible ({err}), on garde data/annonces.csv")
    if text is None:
        text = (ROOT / "data" / "annonces.csv").read_text(encoding="utf-8-sig")
    rows = []
    for raw in csv.DictReader(io.StringIO(text)):
        row = {plain(k): (v or "").strip() for k, v in raw.items() if k}
        if not row.get("quoi"):
            continue
        t = plain(row.get("type"))
        t = next((k for k in TYPES if t.startswith(k[:5])), "perdu")
        cat = next((c for c in CATS if plain(c) == plain(row.get("categorie"))), "Autres")
        d = row.get("date", "")
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", d)
        if m:
            d = f"{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}"
        rows.append({
            "ref": row.get("ref", "").upper(), "type": t, "cat": cat, "quoi": row["quoi"],
            "ou": row.get("ou", ""), "ville": row.get("ville", ""), "date": d,
            "desc": row.get("description", ""), "photo": row.get("photo", ""),
        })
    for i, r in enumerate(rows, 1):
        if not re.fullmatch(r"[A-Z0-9-]{1,20}", r["ref"]):
            r["ref"] = f"KX-{i:04d}"
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: r["type"] == "retrouve")
    return rows


def fdate(d):
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", d or "")
    return f"{m[3]}/{m[2]}/{m[1]}" if m else d


def place(a):
    return ", ".join(x for x in (a["ou"], a["ville"]) if x)


def headline(a):
    label = {"perdu": "Perdu", "trouve": "Trouvé", "recherche": "Personne recherchée", "retrouve": "Retrouvé"}[a["type"]]
    where = a["ville"] or a["ou"]
    return f"{label} : {a['quoi']}" + (f" à {where}" if where else "")


def head(title, desc, path, extra=""):
    url = SITE_URL + path
    verif = ""
    if GOOGLE_VERIFICATION:
        verif += f'<meta name="google-site-verification" content="{e(GOOGLE_VERIFICATION)}">\n'
    if BING_VERIFICATION:
        verif += f'<meta name="msvalidate.01" content="{e(BING_VERIFICATION)}">\n'
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{e(url)}">
{verif}<meta property="og:type" content="website">
<meta property="og:site_name" content="Kaay Xool">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(url)}">
<meta property="og:image" content="{SITE_URL}/assets/logo.png">
<meta property="og:locale" content="fr_SN">
<meta name="theme-color" content="#13124A">
<link rel="icon" href="{SITE_URL}/assets/logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@700;800&family=Poppins:wght@400;500;600&display=swap">
<link rel="stylesheet" href="{SITE_URL}/assets/style.css">
{extra}</head>
<body>
"""


FOOTER = f"""<footer>
  <div class="wrap">
    <p>Kaay Xool met en relation les personnes qui ont perdu et celles qui ont trouvé. Nous ne gardons aucun objet et ne servons pas d'intermédiaire pour un paiement.</p>
    <p>Contact : Instagram <a href="https://www.instagram.com/{INSTAGRAM}/" rel="noopener">@{INSTAGRAM}</a> · <strong>{EMAIL}</strong></p>
  </div>
</footer>
<script src="{SITE_URL}/assets/app.js" defer></script>
</body>
</html>
"""


def contact_block(a):
    lost = a["type"] in ("perdu", "recherche")
    label = "Je l'ai vu(e)" if a["type"] == "recherche" else ("Je l'ai vu ou trouvé" if lost else "C'est à moi")
    msg = (f"Bonjour Kaay Xool, je vous écris pour l'annonce {a['ref']} ({a['quoi']}). "
           + ("Je l'ai vu. Où et quand : " if lost else "Je pense que c'est à moi. Détail que seul le propriétaire connaît : "))
    hint = "et l'endroit où vous l'avez vu" if lost else "et un détail que seul le propriétaire connaît"
    return f"""<details class="contact">
  <summary class="btn {'dark' if lost else 'lime'}">{label}</summary>
  <div class="contact-box">
    <span>Écrivez à <strong>@{INSTAGRAM}</strong> sur Instagram avec la référence <strong>{e(a['ref'])}</strong> {hint}.</span>
    <span>Ou par e-mail : <strong>{EMAIL}</strong></span>
    <span class="actions"><a class="btn lime small" href="https://ig.me/m/{INSTAGRAM}" rel="noopener">Ouvrir Instagram</a><button class="btn small" type="button" data-copy="{e(msg)}">Copier un message</button></span>
  </div>
</details>"""


def card(a):
    badge = TYPES[a["type"]][1]
    photo = f'<img class="photo" src="{e(a["photo"])}" alt="{e(a["quoi"])}" loading="lazy">' if a["photo"] else ""
    when = f"<span>{fdate(a['date'])}</span>" if a["date"] else ""
    desc = f'<p class="desc">{e(a["desc"])}</p>' if a["desc"] else ""
    act = "" if a["type"] == "retrouve" else f'<div class="act">{contact_block(a)}</div>'
    return f"""<article class="card" data-type="{a['type']}" data-cat="{e(a['cat'])}">
  {photo}<div class="in">
    <div class="top"><span class="badge {a['type']}">{badge}</span><span class="ref">Réf. {e(a['ref'])}</span></div>
    <h3><a href="{SITE_URL}/annonce/{e(a['ref'])}.html">{e(a['quoi'])}</a></h3>
    <div class="meta"><span>{e(a['cat'])}</span><span>{e(place(a))}</span>{when}</div>
    {desc}
    {act}
  </div>
</article>"""


def opts(items):
    return "".join(f"<option>{e(x)}</option>" for x in items)


def index_page(rows):
    title = "Kaay Xool – Objets perdus et trouvés au Sénégal"
    desc = ("Téléphone, carte d'identité, clés, animal ou personne recherchée : cherchez parmi les annonces "
            "d'objets perdus et trouvés à Dakar et partout au Sénégal, ou déclarez gratuitement ce que vous avez perdu.")
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "name": "Kaay Xool", "url": SITE_URL + "/", "logo": SITE_URL + "/assets/logo.png",
             "email": EMAIL, "sameAs": [f"https://www.instagram.com/{INSTAGRAM}/"]},
            {"@type": "WebSite", "name": "Kaay Xool", "url": SITE_URL + "/", "inLanguage": "fr",
             "potentialAction": {"@type": "SearchAction", "target": SITE_URL + "/?q={search_term_string}",
                                 "query-input": "required name=search_term_string"}},
        ],
    }
    extra = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>\n'
    counts = {k: sum(1 for r in rows if r["type"] == k) for k in TYPES}
    types = f'<button type="button" class="chip" data-t="" aria-pressed="true">Toutes les annonces</button>' + "".join(
        f'<button type="button" class="chip" data-t="{k}" aria-pressed="false">{v[0]} ({counts[k]})</button>' for k, v in TYPES.items())
    cats = '<button type="button" class="chip" data-c="" aria-pressed="true">Toutes catégories</button>' + "".join(
        f'<button type="button" class="chip" data-c="{e(c)}" aria-pressed="false">{e(c)}</button>' for c in CATS)
    if rows:
        cards = "\n".join(card(a) for a in rows)
        empty = ('<div class="empty" id="none" hidden><b>Aucune annonce ne correspond</b>Essayez un autre mot ou retirez un filtre. '
                 'Sinon, déclarez-le : on publie et on partage pour vous.<span class="actions">'
                 '<button class="btn small" type="button" id="reset">Effacer la recherche</button>'
                 '<a class="btn lime small" href="#declarer">Déclarer</a></span></div>')
    else:
        cards = ""
        empty = ('<div class="empty"><b>Les annonces arrivent bientôt</b>Les objets, papiers, animaux et personnes signalés à '
                 'Kaay Xool apparaîtront ici. Vous avez perdu ou trouvé quelque chose ?'
                 '<a class="btn lime" href="#declarer">Déclarer maintenant</a></div><span id="none" hidden></span>')
    quick = "".join(f'<button type="button" data-q="{e(q)}">{e(q)}</button>' for q in QUICK)
    return head(title, desc, "/", extra) + f"""<header class="hero">
  <div class="wrap">
    <div class="hero-top">
      <a href="{SITE_URL}/"><img class="logo" src="{SITE_URL}/assets/logo.png" alt="Kaay Xool" width="520" height="332"></a>
      <a class="ig" href="https://www.instagram.com/{INSTAGRAM}/" rel="noopener">@{INSTAGRAM}</a>
    </div>
    <h1>Objets perdus et trouvés au Sénégal. <em>Kaay xool</em>, viens voir.</h1>
    <p>Le moteur de recherche des objets perdus et trouvés, des papiers, des animaux et des personnes recherchées, à Dakar et dans tout le Sénégal.</p>
    <form class="search" id="search-form" role="search" action="{SITE_URL}/">
      <input id="q" name="q" type="search" placeholder="Téléphone, carte d'identité, Keur Massar…" aria-label="Rechercher une annonce" autocomplete="off">
      <button class="btn lime" type="submit">Chercher</button>
    </form>
    <div class="quick" id="quick"><span>Recherches fréquentes :</span>{quick}</div>
  </div>
</header>

<main class="wrap">
  <section aria-labelledby="t-annonces">
    <h2 id="t-annonces">Les annonces</h2>
    <div class="filters">
      <div class="chips" id="types" role="group" aria-label="Type d'annonce">{types}</div>
      <div class="chips" id="cats" role="group" aria-label="Catégorie">{cats}</div>
    </div>
    <p class="count" id="count" aria-live="polite"></p>
    <div class="grid" id="list">
{cards}
    </div>
    {empty}
  </section>

  <section class="block" id="declarer" aria-labelledby="t-declarer">
    <h2 id="t-declarer">Déclarer un objet perdu ou trouvé</h2>
    <div class="panel">
      <form id="form" class="form" novalidate>
        <label>Type<select id="f-type"><option>Perdu</option><option>Trouvé</option><option>Personne recherchée</option></select></label>
        <label>Catégorie<select id="f-cat">{opts(CATS)}</select></label>
        <label class="full">Quoi ?<input id="f-quoi" maxlength="80" placeholder="Ex. Téléphone noir, coque rouge"></label>
        <label>Où ?<input id="f-ou" maxlength="80" placeholder="Ex. Marché de Keur Massar"></label>
        <label>Ville<select id="f-ville">{opts(VILLES)}</select></label>
        <label>Quand ?<input id="f-quand" type="date"></label>
        <label>Votre prénom<input id="f-nom" maxlength="40" placeholder="Ex. Awa"></label>
        <label class="full">Signe distinctif<textarea id="f-signe" maxlength="300" placeholder="Ex. Autocollant sur l'arrière, fissure en haut de l'écran"></textarea></label>
        <div class="full actions"><button class="btn dark" type="submit">Préparer mon message</button></div>
      </form>
      <p class="err" id="err" hidden></p>
      <div id="result" hidden>
        <div class="out" id="out"></div>
        <div class="actions">
          <button class="btn lime" type="button" id="copy" data-copy="">Copier le message</button>
          <a class="btn" href="https://ig.me/m/{INSTAGRAM}" rel="noopener">Ouvrir Instagram @{INSTAGRAM}</a>
        </div>
        <p class="hint">Copiez le message, puis collez-le dans nos messages privés Instagram, avec une photo si possible. Vous pouvez aussi l'envoyer à <strong>{EMAIL}</strong>.</p>
      </div>
    </div>
  </section>

  <section class="block" aria-labelledby="t-comment">
    <h2 id="t-comment">Comment ça marche</h2>
    <div class="steps">
      <div class="step"><b>1. Vous nous écrivez</b>Quoi, où, quand, et une photo si possible.</div>
      <div class="step"><b>2. On publie</b>Votre annonce arrive ici et sur notre page Instagram.</div>
      <div class="step"><b>3. On partage</b>Les abonnés partagent, l'annonce circule dans tout le quartier.</div>
      <div class="step"><b>4. Vous retrouvez</b>On met en relation celui qui a perdu et celui qui a trouvé.</div>
    </div>
  </section>

  <section class="block" aria-labelledby="t-securite">
    <h2 id="t-securite">Nos règles de sécurité</h2>
    <div class="panel">
      <ul class="rules">
        <li>Ne payez jamais pour récupérer un objet.</li>
        <li>Faites la remise dans un lieu public, de jour, si possible accompagné.</li>
        <li>Avant de rendre un objet, posez une question de contrôle au propriétaire (fond d'écran, contenu du sac, détail caché).</li>
        <li>Nous floutons les numéros des papiers d'identité et ne publions pas votre téléphone : les contacts passent par Kaay Xool.</li>
      </ul>
      <div class="alert"><strong>Personne disparue :</strong> prévenez d'abord la police ou la gendarmerie. Nous publions un avis de recherche uniquement avec l'accord de la famille.</div>
    </div>
  </section>
</main>
""" + FOOTER


def annonce_page(a):
    title = f"{headline(a)} – Réf. {a['ref']} | Kaay Xool"
    desc = " ".join(x for x in [
        f"{TYPES[a['type']][1].capitalize()} : {a['quoi']}.",
        f"Lieu : {place(a)}." if place(a) else "",
        f"Le {fdate(a['date'])}." if a["date"] else "",
        a["desc"],
        f"Contactez Kaay Xool avec la référence {a['ref']}.",
    ] if x)[:300]
    photo = f'<img class="photo" src="{e(a["photo"])}" alt="{e(a["quoi"])}">' if a["photo"] else ""
    act = ('<p class="alert">Cette annonce est close : l\'objet ou la personne a été retrouvé.</p>'
           if a["type"] == "retrouve" else contact_block(a))
    return head(title, desc, f"/annonce/{a['ref']}.html") + f"""<header class="hero">
  <div class="wrap">
    <div class="hero-top">
      <a href="{SITE_URL}/"><img class="logo" src="{SITE_URL}/assets/logo.png" alt="Kaay Xool" width="520" height="332"></a>
      <a class="ig" href="https://www.instagram.com/{INSTAGRAM}/" rel="noopener">@{INSTAGRAM}</a>
    </div>
  </div>
</header>
<main class="wrap">
  <p class="crumb"><a href="{SITE_URL}/">← Toutes les annonces</a></p>
  <article class="detail">
    <div class="top"><span class="badge {a['type']}">{TYPES[a['type']][1]}</span><span class="ref">Réf. {e(a['ref'])}</span></div>
    <h1>{e(headline(a))}</h1>
    {photo}
    {f'<p style="margin:0;white-space:pre-wrap">{e(a["desc"])}</p>' if a["desc"] else ""}
    <dl class="kv">
      <dt>Catégorie</dt><dd>{e(a['cat'])}</dd>
      <dt>Lieu</dt><dd>{e(place(a)) or "Non précisé"}</dd>
      <dt>Date</dt><dd>{fdate(a['date']) or "Non précisée"}</dd>
    </dl>
    {act}
    <p class="hint">Ne payez jamais pour récupérer un objet. Faites la remise dans un lieu public, de jour.</p>
  </article>
</main>
""" + FOOTER


def main():
    rows = read_rows()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "annonce").mkdir(parents=True)
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / "index.html").write_text(index_page(rows), encoding="utf-8")
    for a in rows:
        (OUT / "annonce" / f"{a['ref']}.html").write_text(annonce_page(a), encoding="utf-8")
    (OUT / "404.html").write_text(head("Page introuvable | Kaay Xool", "Cette page n'existe pas.", "/404.html")
                                  + f'<main class="wrap"><h1>Page introuvable</h1><p><a href="{SITE_URL}/">Retour aux annonces</a></p></main>' + FOOTER,
                                  encoding="utf-8")
    today = date.today().isoformat()
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>"] + [
        f"  <url><loc>{SITE_URL}/annonce/{e(a['ref'])}.html</loc></url>" for a in rows]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "\n".join(urls) + "\n</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8")
    (OUT / ".nojekyll").write_text("")
    if INDEXNOW_KEY:
        (OUT / f"{INDEXNOW_KEY}.txt").write_text(INDEXNOW_KEY, encoding="utf-8")
    print(f"{len(rows)} annonce(s) -> {OUT}")


if __name__ == "__main__":
    main()
