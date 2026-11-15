"""Page Carte : emprises des jeux de données (rectangles englobants) sur fond de carte.

Les emprises sont lues dans le champ texte « emprise » des jeux, par exemple
« 0,77° E – 3,85° E ; 6,23° N – 12,42° N ». Une emprise illisible bloque la construction.
"""
from html import escape
import json
import re
import sys

import catalogue as cat

# Couleur de chaque thème sur la carte (tokens de design/tokens/tokens.css).
COULEURS_THEMES = {
    "forets": "#1F6B2E",
    "restauration": "#7A5600",
    "sols": "#5B3A8C",
    "eau": "#1D5B8C",
    "climat": "#B3261E",
}
RE_COORD = re.compile(r"(\d+(?:,\d+)?)\s*°\s*([EONSW])")


def lire_emprise(jeu):
    """Texte d'emprise -> [ouest, sud, est, nord] en degrés décimaux."""
    valeurs = {"lon": [], "lat": []}
    for nombre, sens in RE_COORD.findall(jeu["emprise"]):
        v = float(nombre.replace(",", "."))
        if sens in "OW":
            valeurs["lon"].append(-v)
        elif sens == "E":
            valeurs["lon"].append(v)
        elif sens == "S":
            valeurs["lat"].append(-v)
        else:
            valeurs["lat"].append(v)
    if len(valeurs["lon"]) != 2 or len(valeurs["lat"]) != 2:
        sys.exit(f"Emprise illisible pour {jeu['slug']} : {jeu['emprise']!r}")
    o, e = sorted(valeurs["lon"])
    s, n = sorted(valeurs["lat"])
    return [o, s, e, n]


def donnees_carte(jeux, ref, lang, M, racine):
    """JSON embarqué dans la page, lu par assets/js/carte.js."""
    items = []
    for j in jeux:
        if j["theme"] not in COULEURS_THEMES:
            sys.exit(f"Thème sans couleur de carte : {j['theme']}")
        items.append({
            "slug": j["slug"],
            "titre": cat.t(j["titre"], lang),
            "theme": j["theme"],
            "themeNom": cat.t(ref["themes"][j["theme"]], lang),
            "territoire": cat.t(ref["territoires"][j["territoire"]], lang),
            "periode": cat.periode(j),
            "lien": cat.lien_fiche(j, lang, racine),
            "emprise": lire_emprise(j),
            "couleur": COULEURS_THEMES[j["theme"]],
        })
    textes = {
        "unJeu": M["carte.popup_un"],
        "plusieurs": M["carte.popup_plusieurs"],
        "aucun": M["carte.popup_aucun"],
        "attribution": M["carte.attribution"],
    }
    brut = json.dumps({"jeux": items, "textes": textes}, ensure_ascii=False)
    return brut.replace("</", "<\\/")


def legende(jeux, ref, lang, M):
    comptes = {}
    for j in jeux:
        comptes[j["theme"]] = comptes.get(j["theme"], 0) + 1
    cases = "".join(
        f'<label class="case"><input type="checkbox" name="theme" value="{k}" checked>'
        f'<span class="carte-legende__pastille" style="--pastille: {COULEURS_THEMES[k]}" aria-hidden="true"></span>'
        f'<span>{escape(cat.t(ref["themes"][k], lang))} <span class="filtre__compte">({n})</span></span></label>'
        for k, n in sorted(comptes.items(), key=lambda x: cat.t(ref["themes"][x[0]], lang)))
    return f'<fieldset class="filtre"><legend class="filtre__legende">{M["carte.legende"]}</legend>{cases}</fieldset>'


def liste(jeux, ref, lang, M, racine):
    """Liste des jeux : fonctionne sans JavaScript (liens vers les fiches)."""
    items = []
    for j in sorted(jeux, key=lambda j: cat.t(j["titre"], lang)):
        items.append(
            f'<li class="carte-liste__item" data-slug="{j["slug"]}" data-theme="{j["theme"]}">'
            f'<span class="carte-legende__pastille" style="--pastille: {COULEURS_THEMES[j["theme"]]}" aria-hidden="true"></span>'
            f'<div><a class="carte-liste__titre" href="{cat.lien_fiche(j, lang, racine)}">{cat.e(j["titre"], lang)}</a>'
            f'<p class="texte-sm texte-doux">{escape(cat.t(ref["territoires"][j["territoire"]], lang))} · {cat.periode(j)}</p>'
            f'<button class="bouton bouton--discret bouton--petit carte-liste__localiser" type="button" data-localiser="{j["slug"]}" hidden>'
            f'<svg aria-hidden="true"><use href="#i-carte"/></svg>{M["carte.localiser"]}'
            f'<span class="sr-only">{M["commun.deux_points"]}{cat.e(j["titre"], lang)}</span></button></div></li>')
    return "\n".join(items)


def variables_carte(jeux, ref, lang, M, racine):
    return {
        "@carte_donnees": donnees_carte(jeux, ref, lang, M, racine),
        "@carte_legende": legende(jeux, ref, lang, M),
        "@carte_liste": liste(jeux, ref, lang, M, racine),
        "@nb_jeux": str(len(jeux)),
    }
