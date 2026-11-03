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
# Compteur de visites GoatCounter (gratuit, sans cookies) : le nom choisi sur goatcounter.com, ex. "kaayxool"
GOATCOUNTER_CODE = setting("GOATCOUNTER_CODE")

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
LIEUX = {
    "Dakar": "le Plateau, la Médina, Sandaga, Colobane, les Parcelles Assainies, Liberté, Yoff ou Ouakam",
    "Pikine": "Thiaroye, le marché Zinc ou Icotaf",
    "Guédiawaye": "Golf Sud, Sam Notaire ou Wakhinane",
    "Keur Massar": "le marché de Keur Massar, Jaxaay ou Malika",
    "Rufisque": "le marché de Rufisque, la gare ou Bargny",
    "Thiès": "la gare routière, le marché Central ou Grand Thiès",
    "Mbour": "Saly, la gare routière ou le marché de Mbour",
    "Saint-Louis": "l'Île, Sor ou Guet Ndar",
    "Touba": "les alentours de la Grande Mosquée ou le marché Ocass",
    "Kaolack": "le marché central ou Médina Baye",
    "Ziguinchor": "le port ou le marché Saint-Maur",
}
QUICK = ["Carte d'identité", "Téléphone", "Clés", "Passeport", "Chat", "Portefeuille"]

# Découvrir le Sénégal : rubriques et fiches de la vitrine Kaay Xool
DCATS = [("lieux", "Lieux"), ("religieux", "Lieux saints"), ("cuisine", "Gastronomie"), ("events", "Événements"),
         ("culture", "Culture et wolof"), ("boutiques", "Boutiques")]
PHOTO_CRED = {
    "goree": "Adjoajo · CC BY-SA 4.0", "lacrose": "Arnault · CC BY-SA 2.0", "ngor": "Olha Pererva · CC BY-SA 4.0",
    "corniche": "Issiaga_Photography · CC BY-SA 4.0", "saly": "DJIBSSON · CC BY-SA 4.0", "thieb": "Alweaver2 · CC BY-SA 4.0",
    "bissap": "Kalamuh 045 · CC BY-SA 4.0", "attaya": "Ajocom · CC BY-SA 4.0",
}
FICHES = [
    ("lieux", "Île de Gorée", "goree", "", "Île historique au large de Dakar, inscrite au patrimoine mondial de l'UNESCO. Maison des Esclaves, ruelles colorées, sans voitures.", ["Dakar", "20 min de chaloupe"]),
    ("lieux", "Lac Rose (Retba)", "lacrose", "", "Lac aux reflets roses selon la lumière, où l'on récolte le sel à la main. Balades en pirogue et dunes autour.", ["Rufisque", "≈ 35 km de Dakar"]),
    ("lieux", "Île de Ngor", "ngor", "", "Petite île face à la pointe des Almadies : plages calmes, eau claire et restaurants de poisson.", ["Dakar", "Pirogue depuis Ngor"]),
    ("lieux", "Corniche de Dakar", "corniche", "", "Route côtière pour marcher, courir ou faire du sport face à l'océan, surtout en fin de journée.", ["Dakar", "Gratuit"]),
    ("lieux", "Saly et la Petite Côte", "saly", "", "Station balnéaire de la Petite Côte : plages, hôtels, pêche et sorties en mer.", ["Mbour", "≈ 80 km de Dakar"]),
    ("religieux", "Touba et la Grande Mosquée", "", "Touba", "Ville sainte du mouridisme, fondée par Cheikh Ahmadou Bamba. Sa Grande Mosquée est l'une des plus grandes d'Afrique de l'Ouest.", ["Diourbel", "Tenue correcte exigée"]),
    ("religieux", "Grand Magal de Touba", "", "Magal", "Grand pèlerinage annuel qui commémore le départ en exil de Cheikh Ahmadou Bamba. Des millions de fidèles convergent vers Touba.", ["Touba", "18 Safar, chaque année"]),
    ("religieux", "Gamou de Tivaouane", "", "Gamou", "Célébration de la naissance du Prophète (Maouloud), grand rendez-vous de la confrérie tidiane à Tivaouane.", ["Thiès", "Nuit du Maouloud"]),
    ("religieux", "Pèlerinage marial de Popenguine", "", "Popenguine", "Pèlerinage catholique au sanctuaire Notre-Dame de la Délivrande, sur la Petite Côte.", ["Thiès", "Week-end de Pentecôte"]),
    ("cuisine", "Thiéboudienne", "thieb", "", "Le plat national : riz cuit dans un bouillon de poisson et de légumes. Se partage autour du bol.", ["Plat", "Midi"]),
    ("cuisine", "Bissap", "bissap", "", "Boisson à base de fleurs d'hibiscus, servie bien fraîche, parfois avec menthe ou fleur d'oranger.", ["Boisson", "Rafraîchissant"]),
    ("cuisine", "Attaya", "attaya", "", "Le thé à la menthe en trois verres, préparé lentement : un moment de discussion et de teranga.", ["Boisson", "Trois verres"]),
    ("events", "JOJ Dakar 2026", "", "JOJ", "Jeux Olympiques de la Jeunesse, premiers Jeux olympiques organisés en Afrique, à Dakar, Diamniadio et Saly.", ["31 oct. – 13 nov. 2026", "Dakar · Diamniadio · Saly"]),
    ("culture", "Mots de wolof utiles", "", "Salaam", "Nanga def ? (Comment ça va ?) · Maa ngi fi (Ça va) · Jërëjëf (Merci) · Ba beneen (À la prochaine).", ["Langue", "Pour bien accueillir"]),
    ("culture", "La teranga", "", "Teranga", "L'hospitalité sénégalaise : accueillir, partager le repas, offrir l'attaya. Le cœur de l'esprit Kaay Xool.", ["Valeur", "Partout au Sénégal"]),
    ("boutiques", "Ta boutique ici", "", "+", f"Mode, cosmétique, parfumerie, artisanat, services… Une fiche avec photos et contact. Écris à Kaay Xool sur Instagram @{INSTAGRAM}.", ["Pour les commerçants"]),
]


def plain(s):
    return unicodedata.normalize("NFD", str(s or "")).encode("ascii", "ignore").decode().lower().strip()


def read_rows():
    # Les annonces gérées par Claude (data/annonces.csv) et celles du Google Sheets s'additionnent.
    texts = [(ROOT / "data" / "annonces.csv").read_text(encoding="utf-8-sig")]
    if SHEET_CSV_URL:
        try:
            with urllib.request.urlopen(SHEET_CSV_URL, timeout=30) as r:
                texts.append(r.read().decode("utf-8-sig"))
            print("Annonces lues aussi depuis Google Sheets")
        except Exception as err:
            print(f"Google Sheets illisible ({err}), seulement data/annonces.csv")
    rows, seen = [], set()
    raws = [raw for text in texts for raw in csv.DictReader(io.StringIO(text))]
    for raw in raws:
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
        ref = row.get("ref", "").upper()
        if ref and ref in seen:
            continue
        seen.add(ref)
        rows.append({
            "ref": ref, "type": t, "cat": cat, "quoi": row["quoi"],
            "ou": row.get("ou", ""), "ville": row.get("ville", ""), "date": d,
            "desc": row.get("description", ""), "photo": row.get("photo", ""),
        })
    for i, r in enumerate(rows, 1):
        if not re.fullmatch(r"[A-Z0-9-]{1,20}", r["ref"]):
            r["ref"] = f"KX-{i:04d}"
    rows.sort(key=lambda r: r["date"], reverse=True)
    rows.sort(key=lambda r: r["type"] == "retrouve")
    return rows


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", plain(s)).strip("-")


def city_links(current=None):
    return "".join(
        f'<a class="chip" href="{SITE_URL}/objets-perdus/{slug(v)}.html"{" aria-current=\"page\"" if v == current else ""}>{e(v)}</a>'
        for v in VILLES if v != "Autre")


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
    if GOATCOUNTER_CODE:
        verif += (f'<script data-goatcounter="https://{e(GOATCOUNTER_CODE)}.goatcounter.com/count" '
                  'async src="https://gc.zgo.at/count.js"></script>\n')
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
<meta property="og:image" content="{SITE_URL}/assets/affiche.jpg">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1440">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE_URL}/assets/affiche.jpg">
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


NAV = (f'<nav class="nav" aria-label="Rubriques"><a href="{SITE_URL}/decouvrir.html">Découvrir le Sénégal</a>'
       f'<a href="{SITE_URL}/#t-annonces">Objets perdus et trouvés</a><a href="{SITE_URL}/#declarer">Déclarer</a>'
       f'<a href="{SITE_URL}/xamtabax.html">XAMTABAX Ingénierie</a></nav>')


def fiche_card(f):
    cat, titre, img, glyph, desc, meta = f
    label = dict(DCATS)[cat]
    if img:
        visual = (f'<div class="fiche-ph"><img src="{SITE_URL}/assets/decouvrir/{img}.jpg" alt="{e(titre)}" loading="lazy" width="640" height="400">'
                  f'<span class="cred">Photo : {e(PHOTO_CRED[img])} · Wikimedia Commons</span></div>')
    else:
        visual = f'<div class="fiche-ph glyph" aria-hidden="true">{e(glyph)}</div>'
    pills = "".join(f"<span>{e(m)}</span>" for m in meta)
    return f"""<article class="card fiche" data-dc="{cat}">
  {visual}<div class="in">
    <span class="dcat">{e(label)}</span>
    <h3>{e(titre)}</h3>
    <p class="desc">{e(desc)}</p>
    <div class="meta">{pills}</div>
  </div>
</article>"""


def decouvrir_page():
    title = "Découvrir le Sénégal – lieux, lieux saints, cuisine | Kaay Xool"
    desc = ("Île de Gorée, Lac Rose, Touba et le Grand Magal, thiéboudienne, bissap, mots de wolof : "
            "la vitrine du Sénégal par Kaay Xool, pour les visiteurs, la diaspora et les Sénégalais.")
    chips = '<button type="button" class="chip" data-dc="" aria-pressed="true">Tout</button>' + "".join(
        f'<button type="button" class="chip" data-dc="{k}" aria-pressed="false">{e(v)}</button>' for k, v in DCATS)
    cards = "\n".join(fiche_card(f) for f in FICHES)
    return head(title, desc, "/decouvrir.html") + f"""<header class="hero">
  <div class="wrap">
    <div class="hero-top">
      <a href="{SITE_URL}/"><img class="logo" src="{SITE_URL}/assets/logo.png" alt="Kaay Xool" width="520" height="332"></a>
      <a class="ig" href="https://www.instagram.com/{INSTAGRAM}/" rel="noopener">@{INSTAGRAM}</a>
    </div>
    <h1>Découvre le Sénégal. <em>Kaay xool</em>, viens voir.</h1>
    <p>Lieux à visiter, lieux saints, cuisine, culture et boutiques, au même endroit. <span class="free">100 % gratuit</span></p>
    <form class="search" id="dsearch" role="search" action="{SITE_URL}/decouvrir.html">
      <input id="dq" name="q" type="search" placeholder="Plage, Touba, thiéb, wolof…" aria-label="Chercher dans la vitrine" autocomplete="off">
      <button class="btn lime" type="submit">Chercher</button>
    </form>
    {NAV}
  </div>
</header>

<main class="wrap">
  <p class="crumb"><a href="{SITE_URL}/">← Objets perdus et trouvés</a></p>
  <section aria-labelledby="t-vitrine">
    <h2 id="t-vitrine">Découvrir le Sénégal</h2>
    <div class="filters"><div class="chips" id="dcats" role="group" aria-label="Rubrique">{chips}</div></div>
    <p class="count" id="dcount" aria-live="polite"></p>
    <div class="grid" id="dlist">
{cards}
    </div>
    <div class="empty" id="dnone" hidden><b>Aucune fiche ne correspond</b>Essayez un autre mot ou choisissez « Tout ».</div>
  </section>
  <section class="block" aria-labelledby="t-boutique">
    <h2 id="t-boutique">Ta boutique dans la vitrine</h2>
    <div class="panel"><p>Commerçant, artisan, restaurant, agence ou entreprise ? Kaay Xool présente ton activité avec photos, description et contact. Écris-nous sur Instagram <a href="https://ig.me/m/{INSTAGRAM}" rel="noopener">@{INSTAGRAM}</a> ou à <strong>{EMAIL}</strong>.</p></div>
  </section>
</main>
""" + FOOTER


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
    <h1>Perdu ? Trouvé ? <em>Kaay xool</em>, viens voir.</h1>
    <p>Kaay Xool vous aide à retrouver vos téléphones, papiers, clés, sacs et animaux, à Dakar et partout au Sénégal. <span class="free">100 % gratuit</span></p>
    <form class="search" id="search-form" role="search" action="{SITE_URL}/">
      <input id="q" name="q" type="search" placeholder="Téléphone, carte d'identité, Keur Massar…" aria-label="Rechercher une annonce" autocomplete="off">
      <button class="btn lime" type="submit">Chercher</button>
    </form>
    <div class="quick" id="quick"><span>Recherches fréquentes :</span>{quick}</div>
    {NAV}
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
          <a class="btn dark" id="mail" href="mailto:{EMAIL}">Envoyer par e-mail</a>
          <a class="btn" href="https://ig.me/m/{INSTAGRAM}" rel="noopener">Ouvrir Instagram @{INSTAGRAM}</a>
        </div>
        <p class="hint">Le plus rapide : <strong>Envoyer par e-mail</strong>, ajoutez une photo si possible, puis envoyez. Ou copiez le message et collez-le dans nos messages privés Instagram. Adresse : <strong>{EMAIL}</strong>.</p>
      </div>
    </div>
  </section>

  <section class="block" aria-labelledby="t-decouvrir">
    <h2 id="t-decouvrir">Découvrir le Sénégal</h2>
    <p class="lead">Lieux à visiter, lieux saints, cuisine, culture et boutiques : la vitrine du Sénégal par Kaay Xool.</p>
    <div class="grid">{"".join(fiche_card(f) for f in [x for x in FICHES if x[2]][:3])}</div>
    <p class="actions" style="margin-top:14px"><a class="btn lime" href="{SITE_URL}/decouvrir.html">Voir toute la vitrine</a></p>
  </section>

  <section class="block" aria-labelledby="t-comment">
    <h2 id="t-comment">Comment ça marche</h2>
    <div class="how">
      <div class="steps">
        <div class="step"><b>1. Déclarez en 1 minute</b>Quoi, où, quand, et une photo si possible, par le formulaire ou en message privé sur Instagram.</div>
        <div class="step"><b>2. On publie et on partage</b>Votre annonce arrive ici et sur notre page Instagram, puis circule dans tout le quartier.</div>
        <div class="step"><b>3. Vous retrouvez</b>On met en relation celui qui a perdu et celui qui a trouvé. Votre numéro n'est jamais publié.</div>
      </div>
      <a class="poster" href="{SITE_URL}/assets/affiche.jpg"><img src="{SITE_URL}/assets/affiche.jpg" alt="Affiche Kaay Xool : Perdu ? Trouvé ? Kaay Xool vous aide à le retrouver, partout au Sénégal. 100 % gratuit. Déclarez en 1 minute, on publie et on partage, vous retrouvez. Votre numéro n'est jamais publié. Ne payez jamais pour récupérer un objet." width="1080" height="1440" loading="lazy"></a>
    </div>
  </section>

  <section class="block" aria-labelledby="t-villes">
    <h2 id="t-villes">Objets perdus par ville</h2>
    <nav class="chips wraps" aria-label="Villes">{city_links()}</nav>
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


def city_page(ville, rows):
    mine = [a for a in rows if plain(a["ville"]) == plain(ville)]
    open_ = [a for a in mine if a["type"] != "retrouve"]
    lieux = LIEUX.get(ville)
    title = f"Objets perdus et trouvés à {ville} | Kaay Xool"
    desc = (f"Téléphone, carte d'identité, clés ou animal perdu à {ville} ? Consultez les annonces d'objets perdus "
            f"et trouvés à {ville} et déclarez gratuitement ce que vous avez perdu ou trouvé avec Kaay Xool.")
    intro = (f"Vous avez perdu ou trouvé quelque chose à {ville}"
             + (f", par exemple vers {lieux}" if lieux else "")
             + " ? Kaay Xool publie votre annonce, la partage sur Instagram et met en relation celui qui a perdu "
               "et celui qui a trouvé. C'est gratuit, et votre numéro n'est jamais publié.")
    if mine:
        listing = f'<p class="count">{len(open_)} annonce{"s" if len(open_) > 1 else ""} en cours à {e(ville)}</p><div class="grid">' + "\n".join(card(a) for a in mine) + "</div>"
    else:
        listing = (f'<div class="empty"><b>Aucune annonce à {e(ville)} pour le moment</b>'
                   f'Vous avez perdu ou trouvé quelque chose à {e(ville)} ? Déclarez-le, on publie et on partage pour vous.'
                   f'<a class="btn lime" href="{SITE_URL}/#declarer">Déclarer gratuitement</a></div>')
    return head(title, desc, f"/objets-perdus/{slug(ville)}.html") + f"""<header class="hero">
  <div class="wrap">
    <div class="hero-top">
      <a href="{SITE_URL}/"><img class="logo" src="{SITE_URL}/assets/logo.png" alt="Kaay Xool" width="520" height="332"></a>
      <a class="ig" href="https://www.instagram.com/{INSTAGRAM}/" rel="noopener">@{INSTAGRAM}</a>
    </div>
    <h1>Objets perdus et trouvés à <em>{e(ville)}</em></h1>
    <p>{e(intro)}</p>
    <form class="search" role="search" action="{SITE_URL}/">
      <input name="q" type="search" placeholder="Rechercher partout au Sénégal…" aria-label="Rechercher une annonce" autocomplete="off">
      <button class="btn lime" type="submit">Chercher</button>
    </form>
  </div>
</header>
<main class="wrap">
  <p class="crumb"><a href="{SITE_URL}/">← Toutes les annonces du Sénégal</a></p>
  <section aria-labelledby="t-ville">
    <h2 id="t-ville">Annonces à {e(ville)}</h2>
    {listing}
  </section>
  <section class="block" aria-labelledby="t-comment">
    <h2 id="t-comment">Perdu quelque chose à {e(ville)} ?</h2>
    <div class="steps">
      <div class="step"><b>1. Déclarez en 1 minute</b>Quoi, où, quand, et une photo si possible, par le <a href="{SITE_URL}/#declarer">formulaire</a> ou en message privé sur Instagram <a href="https://ig.me/m/{INSTAGRAM}" rel="noopener">@{INSTAGRAM}</a>.</div>
      <div class="step"><b>2. On publie et on partage</b>Votre annonce arrive sur Kaay Xool et sur notre Instagram, puis circule à {e(ville)}.</div>
      <div class="step"><b>3. Vous retrouvez</b>On met en relation celui qui a perdu et celui qui a trouvé. Ne payez jamais pour récupérer un objet.</div>
    </div>
  </section>
  <section class="block" aria-labelledby="t-villes">
    <h2 id="t-villes">Autres villes</h2>
    <nav class="chips wraps" aria-label="Villes">{city_links(ville)}</nav>
  </section>
</main>
""" + FOOTER



XT_SERVICES = [
    ("📐", "Études", "Plans et DAO (AutoCAD), métrés, devis quantitatifs et estimatifs, dossiers d'appel d'offres."),
    ("👷", "Suivi des travaux", "Surveillance de chantier, contrôle des quantités et de la qualité, validation des attachements et décomptes, réception."),
    ("🤝", "Assistance au maître d'ouvrage", "Choix de l'entreprise, analyse des offres, contrats, planning et suivi du budget."),
    ("🌍", "Suivi de chantier diaspora", "Tu construis au pays depuis l'étranger ? Visite chaque semaine, photos, rapport et vérification des factures."),
]
XT_DOMAINES = ["Routes et VRD", "Hydraulique", "Assainissement", "Bâtiment", "Électricité",
               "Télécommunications", "Énergie solaire", "Topographie et géotechnique"]
XT_REFS = ["VDN Section 3 : 15 km, 3 autoponts (conducteur de travaux)",
           "PROMOVILLES lots 1 et 2, Dakar et Rufisque (chef de projet)",
           "VRD Senelec Hann : réseaux, voiries, bassins",
           "Châteaux d'eau et forages : Louga, Nguidilé, Boulal",
           "Campus social UGB, Saint-Louis : bâtiments R+4",
           "15 ans de chantiers routes, VRD, hydraulique et bâtiment"]


def xamtabax_page():
    title = "XAMTABAX Ingénierie – bureau d'études, suivi et contrôle des travaux à Dakar"
    desc = ("Études, suivi de chantier, assistance au maître d'ouvrage et suivi de chantier pour la diaspora. "
            "Routes, hydraulique, bâtiment, électricité, télécoms, solaire. Dakar, Sénégal.")
    wa = "https://wa.me/221773703014?text=" + "Bonjour%20XAMTABAX%2C%20j%27ai%20un%20projet%20de%20construction"
    css = """<style>
.xt-hero{background:#14324F;color:#fff;padding:40px 0 34px}
.xt-hero h1{font-family:Montserrat,sans-serif;font-size:clamp(34px,8vw,60px);margin:0;letter-spacing:1px}
.xt-hero h1 span{color:#E9B949}
.xt-hero .sub{letter-spacing:6px;color:#cfe3d6;font-weight:600;margin:4px 0 16px}
.xt-hero p{max-width:720px}
.xt-hero .slg{color:#E9B949;font-weight:600}
.xt-btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.xt-btns a{display:inline-block;padding:12px 18px;border-radius:10px;font-weight:600;text-decoration:none}
.xt-wa{background:#25D366;color:#06301a}.xt-mail{background:#E9B949;color:#14324F}.xt-pdf{background:#fff;color:#14324F}
.xt-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:14px;margin:14px 0 28px}
.xt-card{background:#F3F7F4;border-left:6px solid #1E7B3A;border-radius:12px;padding:16px 18px}
.xt-card h3{margin:0 0 6px;color:#14324F}
.xt-card.hl{background:#FFF6DD;border-left-color:#E9B949}
.xt-dom{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0 28px;padding:0;list-style:none}
.xt-dom li{background:#14324F;color:#fff;border-radius:999px;padding:8px 14px;font-weight:600}
.xt-refs li{margin-bottom:6px}
.xt-note{font-size:.9em;color:#6b7a87;font-style:italic}
.xt-img{max-width:100%;height:auto;border-radius:12px;box-shadow:0 4px 18px rgba(0,0,0,.12);margin-top:10px}
</style>"""
    cards = "".join(f'<article class="xt-card{" hl" if "diaspora" in t else ""}"><h3>{i} {e(t)}</h3><p>{e(d)}</p></article>'
                    for i, t, d in XT_SERVICES)
    doms = "".join(f"<li>{e(d)}</li>" for d in XT_DOMAINES)
    refs = "".join(f"<li>{e(r)}</li>" for r in XT_REFS)
    return head(title, desc, "/xamtabax.html", css) + f"""<header class="xt-hero">
  <div class="wrap">
    <p class="crumb"><a href="{SITE_URL}/" style="color:#cfe3d6">← Kaay Xool</a></p>
    <h1>XAM<span>TABAX</span></h1>
    <div class="sub">INGÉNIERIE</div>
    <p><span class="slg">« Xam-xam ci sa tabax »</span> : le savoir au service de ta construction.<br>
    Bureau d'études, suivi et contrôle des travaux, à Dakar et dans tout le Sénégal.</p>
    <div class="xt-btns">
      <a class="xt-wa" href="{wa}" rel="noopener">💬 WhatsApp : 77 370 30 14</a>
      <a class="xt-mail" href="mailto:gueyejob@gmail.com?subject=Projet%20XAMTABAX">✉️ gueyejob@gmail.com</a>
      <a class="xt-pdf" href="{SITE_URL}/assets/xamtabax/XAMTABAX_Ingenierie_plaquette.pdf">📄 Télécharger la plaquette</a>
    </div>
  </div>
</header>
<main class="wrap">
  <h2>Nos services</h2>
  <div class="xt-grid">{cards}</div>
  <h2>Nos domaines d'intervention</h2>
  <ul class="xt-dom">{doms}</ul>
  <h2>L'expérience de notre ingénieur fondateur</h2>
  <p><strong>Matsarr GUEYE</strong>, ingénieur génie civil, spécialité routes et ouvrages d'art.</p>
  <ul class="xt-refs">{refs}</ul>
  <p class="xt-note">Références acquises par Matsarr GUEYE au sein des entreprises où il a exercé.</p>
  <h2>La plaquette</h2>
  <img class="xt-img" src="{SITE_URL}/assets/xamtabax/plaquette.jpg" alt="Plaquette XAMTABAX Ingénierie" width="1240" height="1754" loading="lazy">
</main>
""" + FOOTER


def main():
    rows = read_rows()
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "annonce").mkdir(parents=True)
    (OUT / "objets-perdus").mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / "index.html").write_text(index_page(rows), encoding="utf-8")
    (OUT / "decouvrir.html").write_text(decouvrir_page(), encoding="utf-8")
    (OUT / "xamtabax.html").write_text(xamtabax_page(), encoding="utf-8")
    for a in rows:
        (OUT / "annonce" / f"{a['ref']}.html").write_text(annonce_page(a), encoding="utf-8")
    villes = [v for v in VILLES if v != "Autre"]
    for v in villes:
        (OUT / "objets-perdus" / f"{slug(v)}.html").write_text(city_page(v, rows), encoding="utf-8")
    (OUT / "404.html").write_text(head("Page introuvable | Kaay Xool", "Cette page n'existe pas.", "/404.html")
                                  + f'<main class="wrap"><h1>Page introuvable</h1><p><a href="{SITE_URL}/">Retour aux annonces</a></p></main>' + FOOTER,
                                  encoding="utf-8")
    today = date.today().isoformat()
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{today}</lastmod></url>",
            f"  <url><loc>{SITE_URL}/decouvrir.html</loc></url>",
            f"  <url><loc>{SITE_URL}/xamtabax.html</loc></url>"] + [
        f"  <url><loc>{SITE_URL}/objets-perdus/{slug(v)}.html</loc></url>" for v in villes] + [
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
