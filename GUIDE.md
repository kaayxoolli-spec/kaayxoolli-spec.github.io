# Mettre Kaay Xool en ligne, gratuitement

Le site est prêt. Il reste 3 actions à faire de ton côté (environ 10 minutes, depuis ton téléphone). Ensuite, Claude envoie le site et s'occupe du reste.

## Ce que tu fais (une seule fois)

### 1. Créer un compte GitHub
1. Va sur **https://github.com/signup**.
2. Utilise ton e-mail **kaayxoolli@gmail.com**.
3. Choisis le nom d'utilisateur **kaayxool** (ou **kaayxoolli** s'il est pris).
   Ce nom donnera l'adresse du site : **https://kaayxool.github.io**.

### 2. Créer l'espace du site
1. Va sur **https://github.com/new**.
2. Dans **Repository name**, écris exactement ton nom d'utilisateur suivi de `.github.io`
   (exemple : `kaayxool.github.io`).
3. Laisse **Public** coché. Ne coche rien d'autre.
4. Appuie sur **Create repository**.

### 3. Donner l'accès à Claude
1. Va sur **https://claude.ai/connect-github** et connecte ton compte GitHub.
2. Quand GitHub te le demande, installe l'application Claude sur le dépôt `kaayxool.github.io`.
3. Reviens dans cette conversation et écris : **« c'est fait, mon nom GitHub est … »**.

## Ce que Claude fait ensuite
- Il envoie tout le site sur ton dépôt.
- Il te dit où appuyer pour allumer la publication : **Settings → Pages → Source : GitHub Actions** (un seul réglage).
- Le site est en ligne en 2 minutes à l'adresse **https://kaayxool.github.io**.

## Ajouter des annonces (sans Claude, depuis ton téléphone)

1. Crée un Google Sheets nommé **Annonces Kaay Xool**.
2. Écris cette première ligne, une colonne par mot :
   `ref | type | categorie | quoi | ou | ville | date | description | photo`
3. Une ligne par annonce. Exemple :
   `KX-0001 | Perdu | Téléphones | Téléphone noir, coque rouge | Marché | Keur Massar | 04/10/2026 | Perdu près des tissus |`
   - **type** : Perdu, Trouvé, Recherché ou Retrouvé
   - **categorie** : Papiers, Téléphones, Clés, Sacs et portefeuilles, Bijoux, Animaux, Personnes, Véhicules, Autres
   - **photo** : facultatif, un lien vers une image
   - Ne mets jamais de numéro de téléphone ni de numéro de pièce d'identité.
4. Menu **Fichier → Partager → Publier sur le web** → choisis la feuille et **CSV** → **Publier**. Copie le lien.
5. Envoie ce lien à Claude une fois : il le branche au site.

Ensuite, le site relit ton tableau **toutes les heures**. Une nouvelle ligne devient une annonce en ligne, avec sa propre page que Google peut trouver. Pour clore une annonce, remplace le type par **Retrouvé**.

## Être trouvé sur Google (gratuit)

1. **Google Search Console** : https://search.google.com/search-console
   - « Ajouter une propriété » → **Préfixe de l'URL** → `https://kaayxool.github.io/`
   - Choisis la méthode **Balise HTML**, copie seulement le code entre `content="` et `"`, et envoie-le à Claude.
   - Une fois la balise en ligne, appuie sur **Valider**, puis dans **Sitemaps** ajoute `sitemap.xml`.
2. **Bing Webmaster Tools** (Bing, Yahoo, DuckDuckGo) : https://www.bing.com/webmasters
   → « Importer depuis Google Search Console », c'est automatique.
3. **Google Business Profile** : https://business.google.com → crée la fiche **Kaay Xool** avec le lien du site.
4. **Mets le lien partout** : la bio Instagram @kaayxoolli, chaque annonce publiée sur Instagram, ton statut WhatsApp, une page Facebook, les groupes de quartier.

Google met en général quelques jours à quelques semaines pour afficher un nouveau site.
