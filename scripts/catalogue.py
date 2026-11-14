"""Composants HTML générés à partir de donnees/jeux-demo.json.

Toutes les fonctions reçoivent la langue et les textes traduits (M) :
aucune chaîne visible n'est écrite ici en dur, sauf les noms propres et unités,
qui ne se traduisent pas (cahier des charges, § 14).
"""
from html import escape
import unicodedata

STATUTS = {
    "soumis": ("badge--soumis", "i-horloge"),
    "verification": ("badge--verification", "i-loupe-doc"),
    "controle": ("badge--controle", "i-loupe-doc"),
    "valide": ("badge--valide", "i-ok"),
    "publie": ("badge--publie", "i-ok"),
    "reserve": ("badge--reserve", "i-attention"),
}
ETAPES = ["soumis", "verification", "controle", "valide", "publie"]
MOIS = {
    "fr": ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}


def t(valeur, lang):
    """Texte dans la langue demandée : {"fr": ..., "en": ...} ou chaîne non traduite."""
    if isinstance(valeur, dict):
        return valeur[lang]
    return "" if valeur is None else str(valeur)


def e(valeur, lang):
    return escape(t(valeur, lang))


def date_lisible(iso, lang):
    if not iso:
        return ""
    a, m, j = iso.split("-")
    if lang == "fr":
        return f"{int(j)} {MOIS['fr'][int(m) - 1]} {a}"
    return f"{MOIS['en'][int(m) - 1]} {int(j)}, {a}"


def nombre(n, lang):
    if n is None:
        return ""
    s = f"{n:,}"
    return s.replace(",", " ") if lang == "fr" else s


def periode(jeu):
    return str(jeu["debut"]) if jeu["debut"] == jeu["fin"] else f"{jeu['debut']}–{jeu['fin']}"


def format_local(texte, lang):
    """Nombres et unités écrits en français dans les données -> conventions anglaises."""
    if lang != "en" or not texte:
        return texte
    return (texte.replace(",", ".").replace(" Mo", " MB").replace(" ; ", "; ")
            .replace("° O", "° W"))


def sans_accents(texte):
    return "".join(c for c in unicodedata.normalize("NFD", texte.lower()) if unicodedata.category(c) != "Mn")


def badge_statut(statut, M):
    classe, icone = STATUTS[statut]
    return f'<span class="badge {classe}"><svg aria-hidden="true"><use href="#{icone}"/></svg>{escape(M["commun.statut_" + statut])}</span>'


def badge_demo(M):
    return f'<span class="badge badge--demo">{escape(M["commun.demo"])}</span>'


def nom_licence(jeu, ref, lang):
    return t(ref["licences"][jeu["licence"]]["nom"], lang)


def lien_fiche(jeu, lang, racine):
    return f"{racine}{lang}/catalogue/{jeu['slug']}/"


# ---------------------------------------------------------------- cartes

def carte_jeu(jeu, ref, lang, M, racine, attributs_filtre=False):
    """Carte de résultat (catalogue et accueil)."""
    theme = t(ref["themes"][jeu["theme"]], lang)
    attrs = ""
    if attributs_filtre:
        texte = " ".join([t(jeu["titre"], lang), t(jeu["resume"], lang), t(jeu["source"], lang), theme,
                          t(ref["territoires"][jeu["territoire"]], lang), " ".join(jeu["formats"])])
        attrs = (f' data-recherche="{escape(sans_accents(texte))}" data-theme="{jeu["theme"]}"'
                 f' data-territoire="{jeu["territoire"]}" data-format="{" ".join(f.lower() for f in jeu["formats"])}"'
                 f' data-source="{escape(sans_accents(t(jeu["source"], lang)))}" data-statut="{jeu["statut"]}"'
                 f' data-licence="{jeu["licence"]}" data-debut="{jeu["debut"]}" data-fin="{jeu["fin"]}"'
                 f' data-maj="{jeu["maj"]}" data-titre="{escape(sans_accents(t(jeu["titre"], lang)))}"')
    return f'''<article class="carte carte--lien"{attrs}>
  <div class="carte__badges">{badge_demo(M)}{badge_statut(jeu["statut"], M)}<span class="badge badge--theme">{escape(theme)}</span></div>
  <h3 class="titre-sm carte__titre"><a href="{lien_fiche(jeu, lang, racine)}">{e(jeu["titre"], lang)}</a></h3>
  <p class="texte-sm texte-doux">{e(jeu["resume"], lang)}</p>
  <dl class="meta"><dt>{M["commun.lbl_source"]}</dt><dd>{e(jeu["source"], lang)}</dd><dt>{M["commun.lbl_periode"]}</dt><dd>{periode(jeu)}</dd><dt>{M["commun.lbl_format"]}</dt><dd>{", ".join(jeu["formats"])}</dd><dt>{M["commun.lbl_licence"]}</dt><dd>{escape(nom_licence(jeu, ref, lang))}</dd></dl>
</article>'''


def derniers_jeux(jeux, ref, lang, M, racine, n=3):
    recents = sorted(jeux, key=lambda j: j["maj"], reverse=True)[:n]
    return "\n".join(carte_jeu(j, ref, lang, M, racine) for j in recents)


def liste_catalogue(jeux, ref, lang, M, racine):
    return "\n".join(carte_jeu(j, ref, lang, M, racine, attributs_filtre=True) for j in jeux)


# ---------------------------------------------------------------- filtres

def _groupe(nom, legende, options):
    cases = "".join(
        f'<label class="case"><input type="checkbox" name="{nom}" value="{escape(v)}"> <span>{escape(lib)} <span class="filtre__compte">({n})</span></span></label>'
        for v, lib, n in options)
    return f'<fieldset class="filtre"><legend class="filtre__legende">{escape(legende)}</legend>{cases}</fieldset>'


def facettes(jeux, ref, lang, M):
    def compter(cle, valeurs_jeu):
        comptes = {}
        for j in jeux:
            for v in valeurs_jeu(j):
                comptes[v] = comptes.get(v, 0) + 1
        return comptes

    themes = compter("theme", lambda j: [j["theme"]])
    terr = compter("territoire", lambda j: [j["territoire"]])
    formats = compter("format", lambda j: j["formats"])
    sources = {}
    for j in jeux:
        cle = sans_accents(t(j["source"], lang))
        lib, n = sources.get(cle, (t(j["source"], lang), 0))
        sources[cle] = (lib, n + 1)
    statuts = compter("statut", lambda j: [j["statut"]])
    licences = compter("licence", lambda j: [j["licence"]])
    annees = [j["debut"] for j in jeux] + [j["fin"] for j in jeux]
    amin, amax = min(annees), max(annees)

    groupes = [
        _groupe("theme", M["catalogue.f_theme"], [(k, t(ref["themes"][k], lang), n) for k, n in sorted(themes.items(), key=lambda x: t(ref["themes"][x[0]], lang))]),
        _groupe("territoire", M["catalogue.f_territoire"], [(k, t(ref["territoires"][k], lang), n) for k, n in terr.items()]),
        f'''<fieldset class="filtre"><legend class="filtre__legende">{M["catalogue.f_periode"]}</legend>
<div class="filtre__periode"><label><span>{M["catalogue.f_de"]}</span><input class="saisie" type="number" name="de" inputmode="numeric" min="{amin}" max="{amax}" placeholder="{amin}"></label>
<label><span>{M["catalogue.f_a"]}</span><input class="saisie" type="number" name="a" inputmode="numeric" min="{amin}" max="{amax}" placeholder="{amax}"></label></div></fieldset>''',
        _groupe("format", M["catalogue.f_format"], [(k.lower(), k, n) for k, n in sorted(formats.items())]),
        _groupe("source", M["catalogue.f_source"], [(k, lib, n) for k, (lib, n) in sorted(sources.items())]),
        _groupe("statut", M["catalogue.f_statut"], [(k, M["commun.statut_" + k], n) for k, n in statuts.items()]),
        _groupe("licence", M["catalogue.f_licence"], [(k, nom_licence({"licence": k}, ref, lang), n) for k, n in licences.items()]),
    ]
    return "\n".join(groupes)


# ---------------------------------------------------------------- fiche

def tableau_variables(jeu, lang, M):
    lignes = "".join(
        f'<tr><td><code>{escape(v["nom"])}</code></td><td>{e(v["unite"], lang)}</td><td>{e(v["description"], lang)}</td></tr>'
        for v in jeu["variables"])
    return (f'<div class="tableau-defilant"><table class="tableau"><thead><tr><th scope="col">{M["fiche.v_nom"]}</th>'
            f'<th scope="col">{M["fiche.v_unite"]}</th><th scope="col">{M["fiche.v_description"]}</th></tr></thead><tbody>{lignes}</tbody></table></div>')


def tableau_versions(jeu, lang, M):
    lignes = []
    for i, v in enumerate(jeu["versions"]):
        emp = f'<code title="{M["fiche.empreinte_aide"]}">{v["empreinte"][:16]}…</code>' if v["empreinte"] else "—"
        actuelle = f' <span class="badge badge--valide">{M["fiche.version_actuelle"]}</span>' if i == 0 else ""
        lignes.append(f'<tr><td><strong>{escape(v["version"])}</strong>{actuelle}</td><td>{date_lisible(v["date"], lang)}</td><td>{e(v["note"], lang)}</td><td>{emp}</td></tr>')
    return (f'<div class="tableau-defilant"><table class="tableau"><thead><tr><th scope="col">{M["fiche.versions_version"]}</th>'
            f'<th scope="col">{M["fiche.versions_date"]}</th><th scope="col">{M["fiche.versions_note"]}</th>'
            f'<th scope="col">{M["fiche.versions_empreinte"]}</th></tr></thead><tbody>{"".join(lignes)}</tbody></table></div>')


def parcours_validation(jeu, lang, M):
    v = jeu["validation"]
    items = []
    for etape in ETAPES:
        date = v.get(etape, "")
        if not date and etape == "valide" and jeu["statut"] == "reserve":
            items.append(f'<li class="parcours__etape parcours__etape--attente"><span class="parcours__point" aria-hidden="true"></span>'
                         f'<span class="parcours__libelle">{M["commun.statut_valide"]}</span>'
                         f'<span class="parcours__date">{M["fiche.validation_en_cours"]}</span></li>')
            continue
        libelle = M["commun.statut_reserve"] if (etape == "publie" and jeu["statut"] == "reserve") else M["commun.statut_" + etape]
        items.append(f'<li class="parcours__etape"><span class="parcours__point" aria-hidden="true"></span>'
                     f'<span class="parcours__libelle">{escape(libelle)}</span>'
                     f'<time class="parcours__date" datetime="{date}">{date_lisible(date, lang)}</time></li>')
    return f'<ol class="parcours">{"".join(items)}</ol>'


def apercu(jeu, lang, M):
    """Graphique en barres SVG + tableau des valeurs. Unité et période toujours affichées (EF-11)."""
    a = jeu.get("apercu")
    if not a:
        return ""
    pts = a["points"]
    unite = a["unite"]
    valeurs = [v for _, v in pts if v is not None]
    vmax = max(valeurs)
    pas = 10 ** (len(str(int(vmax))) - 1)
    haut = ((int(vmax) // pas) + 1) * pas
    W, H, g, d, h0, b = 640, 260, 56, 16, 16, 48
    lw = (W - g - d) / len(pts)
    bw = lw * 0.62
    y = lambda val: h0 + (H - h0 - b) * (1 - val / haut)
    grille = []
    for i in range(5):
        val = haut * i / 4
        yy = y(val)
        grille.append(f'<line x1="{g}" x2="{W - d}" y1="{yy:.1f}" y2="{yy:.1f}" class="graphe__grille"/>'
                      f'<text x="{g - 8}" y="{yy + 4:.1f}" text-anchor="end" class="graphe__axe">{nombre(int(val), lang)}</text>')
    barres, manquants = [], []
    for i, (cat, val) in enumerate(pts):
        x = g + i * lw + (lw - bw) / 2
        cx = x + bw / 2
        etiquette = cat.split(" / ")[0 if lang == "fr" else -1]
        if val is None:
            manquants.append(etiquette)
            barres.append(f'<rect x="{x:.1f}" y="{h0}" width="{bw:.1f}" height="{H - h0 - b}" class="graphe__manque"/>'
                          f'<text x="{cx:.1f}" y="{H - b - 8}" text-anchor="middle" class="graphe__nd">{M["fiche.apercu_nd"]}</text>')
        else:
            yy = y(val)
            barres.append(f'<rect x="{x:.1f}" y="{yy:.1f}" width="{bw:.1f}" height="{H - b - yy:.1f}" rx="2" class="graphe__barre"><title>{escape(etiquette)}{M["commun.deux_points"]}{nombre(val, lang)} {escape(unite)}</title></rect>')
        barres.append(f'<text x="{cx:.1f}" y="{H - b + 18}" text-anchor="middle" class="graphe__axe">{escape(etiquette if len(etiquette) <= 11 else etiquette[:10] + "…")}</text>')
    titre = t(a["titre"], lang)
    svg = (f'<svg class="graphe" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(titre)} ({escape(unite)}), {periode(jeu)}">'
           f'<defs><pattern id="hachures" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           f'<line x1="0" y1="0" x2="0" y2="8" class="graphe__hachure"/></pattern></defs>'
           f'{"".join(grille)}<text x="{g}" y="10" class="graphe__unite">{escape(unite)}</text>{"".join(barres)}</svg>')
    alerte = ""
    if manquants:
        alerte = (f'<div class="alerte alerte--avert" role="note"><svg aria-hidden="true"><use href="#i-attention"/></svg><div>'
                  f'<p class="alerte__titre">{M["fiche.apercu_alerte_titre"].replace("{liste}", ", ".join(manquants))}</p>'
                  f'<p class="texte-sm">{M["fiche.apercu_alerte_texte"]}</p></div></div>')
    lignes = "".join(
        f'<tr><td>{escape(c.split(" / ")[0 if lang == "fr" else -1])}</td><td class="nombre">{nombre(v, lang) if v is not None else M["fiche.apercu_nd"]}</td></tr>'
        for c, v in pts)
    tableau = (f'<details class="graphe__donnees"><summary>{M["fiche.apercu_tableau"]}</summary><div class="tableau-defilant">'
               f'<table class="tableau"><thead><tr><th scope="col">{M["fiche.apercu_categorie"]}</th><th scope="col" class="nombre">{escape(unite)}</th></tr></thead>'
               f'<tbody>{lignes}</tbody></table></div></details>')
    return (f'<section class="fiche__bloc" aria-labelledby="t-apercu"><h2 class="titre-md" id="t-apercu">{M["fiche.sec_apercu"]}</h2>'
            f'<figure class="graphe__cadre"><figcaption><strong>{escape(titre)}</strong> · {escape(unite)} · {periode(jeu)} {badge_demo(M)}</figcaption>'
            f'{svg}</figure>{alerte}<p class="texte-sm texte-doux">{M["fiche.apercu_demo_note"]}</p>{tableau}</section>')


def bloc_telechargement(jeu, ref, lang, M):
    lic = ref["licences"][jeu["licence"]]
    if not lic["telechargement"]:
        lien = (f'<a class="bouton bouton--secondaire" href="{escape(jeu["source_url"])}">{M["fiche.source_lien"]}</a>'
                if jeu.get("source_url") else "")
        return (f'<div class="alerte alerte--info" role="note"><svg aria-hidden="true"><use href="#i-cadenas"/></svg><div>'
                f'<p class="alerte__titre">{M["fiche.telechargement_refuse_titre"]}</p>'
                f'<p class="texte-sm">{M["fiche.telechargement_refuse_texte"]}</p></div></div>{lien}')
    boutons = "".join(
        f'<button class="bouton bouton--primaire" type="button" data-demo-telechargement><svg aria-hidden="true"><use href="#i-telecharger"/></svg>'
        f'{M["fiche.telecharger"]} {escape(f)}</button>' for f in jeu["formats"])
    lic_lien = f'<a href="{lic["url"]}" rel="license">{escape(t(lic["nom"], lang))}</a>'
    return (f'<div class="pile">{boutons}</div><p class="texte-sm texte-doux">{M["fiche.m_taille"]}{M["commun.deux_points"]}{escape(format_local(jeu["taille"], lang))}</p>'
            f'<p class="texte-sm">{M["fiche.telechargement_note"].replace("{licence}", lic_lien)}</p>'
            f'<p class="texte-sm texte-doux" data-demo-message hidden>{M["fiche.telechargement_demo"]}</p>')


def citation(jeu, lang, M):
    producteur = t(jeu["producteur"], lang)
    annee = jeu["maj"][:4]
    version = jeu["versions"][0]["version"]
    return f'{producteur} ({annee}). {t(jeu["titre"], lang)}, version {version}. Green Biometry, {jeu["identifiant"]}.'


def variables_fiche(jeu, ref, lang, M, racine):
    lic = ref["licences"][jeu["licence"]]
    lic_nom = escape(t(lic["nom"], lang))
    lic_html = f'<a href="{lic["url"]}" rel="license">{lic_nom}</a>' if lic["url"] else lic_nom
    source = e(jeu["source"], lang)
    if jeu.get("source_url"):
        source = f'<a href="{escape(jeu["source_url"])}">{source}</a>'
    return {
        "@jeu_titre": e(jeu["titre"], lang),
        "@jeu_resume": e(jeu["resume"], lang),
        "@jeu_identifiant": jeu["identifiant"],
        "@jeu_badges": badge_demo(M) + badge_statut(jeu["statut"], M)
                       + f'<span class="badge badge--theme">{escape(t(ref["themes"][jeu["theme"]], lang))}</span>',
        "@jeu_methode": e(jeu["methode"], lang),
        "@jeu_limites": e(jeu["limites"], lang),
        "@jeu_producteur": e(jeu["producteur"], lang),
        "@jeu_source": source,
        "@jeu_periode": periode(jeu),
        "@jeu_maj": f'<time datetime="{jeu["maj"]}">{date_lisible(jeu["maj"], lang)}</time>',
        "@jeu_territoire": escape(t(ref["territoires"][jeu["territoire"]], lang)),
        "@jeu_emprise": escape(format_local(jeu["emprise"], lang)),
        "@jeu_resolution": e(jeu["resolution"], lang),
        "@jeu_crs": escape(jeu["crs"]),
        "@jeu_formats": ", ".join(jeu["formats"]),
        "@jeu_theme": escape(t(ref["themes"][jeu["theme"]], lang)),
        "@jeu_licence": lic_html,
        "@jeu_acces": M["fiche.acces_public"],
        "@jeu_variables": tableau_variables(jeu, lang, M),
        "@jeu_versions": tableau_versions(jeu, lang, M),
        "@jeu_validation": parcours_validation(jeu, lang, M),
        "@jeu_apercu": apercu(jeu, lang, M),
        "@jeu_telechargement": bloc_telechargement(jeu, ref, lang, M),
        "@jeu_citation": escape(citation(jeu, lang, M)),
        "@jeu_reserve": (f'<div class="alerte alerte--avert" role="note"><svg aria-hidden="true"><use href="#i-attention"/></svg><div>'
                         f'<p class="alerte__titre">{M["fiche.reserve_titre"]}</p><p class="texte-sm">{M["fiche.reserve_texte"]}</p></div></div>')
                        if jeu["statut"] == "reserve" else "",
        "@meta_description": e(jeu["resume"], lang),
    }
