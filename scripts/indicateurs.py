"""Pages Indicateurs : liste et fiche de chaque indicateur (donnees/indicateurs-demo.json).

Une fiche indicateur donne la définition, l'unité, la méthode, la fréquence, la source
et le niveau de validation, avec un graphique temporel (cahier des charges, fiches indicateurs).
Les valeurs manquantes sont montrées, jamais interpolées (EF-11).
"""
from html import escape
import math
import sys

import catalogue as cat


def verifier(indicateurs, jeux, ref):
    slugs = {j["slug"] for j in jeux}
    erreurs = []
    for ind in indicateurs:
        if ind["jeu"] not in slugs:
            erreurs.append(f"{ind['slug']} : jeu source inconnu {ind['jeu']}")
        if ind["theme"] not in ref["themes"] or ind["territoire"] not in ref["territoires"]:
            erreurs.append(f"{ind['slug']} : thème ou territoire inconnu")
        if not any(v is not None for _, v in ind["serie"]):
            erreurs.append(f"{ind['slug']} : aucune valeur")
    if erreurs:
        sys.exit("Indicateurs incohérents :\n  " + "\n  ".join(erreurs))


def fmt(v, lang, dec=0):
    """Nombre lisible : 22 100 et 0,97 en français ; 22,100 et 0.97 en anglais."""
    s = f"{v:,.{dec}f}"
    if lang == "fr":
        s = s.replace(",", " ").replace(".", ",")
    return s


def valeur_unite(v, ind, lang):
    u = ind["unite"]
    return f"{fmt(v, lang, ind['decimales'])}{'' if u == '%' and lang == 'en' else ' '}{escape(u)}"


def connues(ind):
    return [(a, v) for a, v in ind["serie"] if v is not None]


def manquantes(ind):
    return [a for a, v in ind["serie"] if v is None]


def periode(ind):
    s = ind["serie"]
    return s[0][0] if len(s) == 1 else f"{s[0][0]}–{s[-1][0]}"


def evolution(ind, lang, M, cle="indicateurs.evolution"):
    """Écart entre la première et la dernière valeur connue (texte, ou '' si une seule valeur)."""
    pts = connues(ind)
    if len(pts) < 2:
        return ""
    (a0, v0), (a1, v1) = pts[0], pts[-1]
    if ind["variation"] == "relative" and v0:
        d = (v1 - v0) / v0 * 100
        val = ("+" if d > 0 else "−" if d < 0 else "") + fmt(abs(d), lang, 0) + (" %" if lang == "fr" else "%")
    else:
        d = v1 - v0
        signe = "+" if d > 0 else "−" if d < 0 else ""
        if ind["unite"] == "%":  # écart entre deux pourcentages : en points
            val = signe + fmt(abs(d), lang, ind["decimales"]) + " " + M["indicateurs.points"]
        else:
            val = signe + valeur_unite(abs(d), ind, lang)
    return M[cle].replace("{debut}", a0).replace("{fin}", a1).replace("{valeur}", val)


def lien(ind, lang, racine):
    return f"{racine}{lang}/indicateurs/{ind['slug']}/"


# ---------------------------------------------------------------- graphiques

def _pas_rond(brut):
    if brut <= 0:
        return 1
    p = 10 ** math.floor(math.log10(brut))
    for m in (1, 2, 2.5, 5, 10):
        if brut <= m * p:
            return m * p
    return 10 * p


def _segments(points):
    """Coupe la ligne aux valeurs manquantes : une valeur absente n'est jamais reliée."""
    segs, cour = [], []
    for p in points:
        if p is None:
            if cour:
                segs.append(cour)
            cour = []
        else:
            cour.append(p)
    if cour:
        segs.append(cour)
    return segs


def graphe(ind, lang, M):
    serie = ind["serie"]
    vals = [v for _, v in serie if v is not None]
    vmin, vmax = min(vals), max(vals)
    bas = 0 if vmin >= 0 else vmin
    pas = _pas_rond((vmax - bas) / 4)
    bas = math.floor(bas / pas) * pas
    haut = math.ceil(vmax / pas) * pas
    if haut == vmax:
        haut += pas
    W, H, g, d, h0, b = 720, 300, 64, 24, 24, 40
    n = len(serie)
    lw = (W - g - d) / n
    x = lambda i: g + lw * (i + 0.5)
    y = lambda v: h0 + (H - h0 - b) * (1 - (v - bas) / (haut - bas))
    dec_axe = ind["decimales"] if pas < 1 else 0

    parts = []
    k = 0
    while bas + k * pas <= haut + 1e-9:
        val = bas + k * pas
        yy = y(val)
        parts.append(f'<line x1="{g}" x2="{W - d}" y1="{yy:.1f}" y2="{yy:.1f}" class="graphe__grille"/>'
                     f'<text x="{g - 8}" y="{yy + 4:.1f}" text-anchor="end" class="graphe__axe">{fmt(val, lang, dec_axe)}</text>')
        k += 1
    for i, (a, v) in enumerate(serie):
        if v is None:
            parts.append(f'<rect x="{x(i) - lw / 2 + 2:.1f}" y="{h0}" width="{lw - 4:.1f}" height="{H - h0 - b}" class="graphe__manque"/>'
                         f'<text x="{x(i):.1f}" y="{h0 + 16}" text-anchor="middle" class="graphe__nd">{M["fiche.apercu_nd"]}</text>')
        parts.append(f'<text x="{x(i):.1f}" y="{H - b + 20}" text-anchor="middle" class="graphe__axe">{escape(a)}</text>')
    pts = [None if v is None else (x(i), y(v)) for i, (_, v) in enumerate(serie)]
    for seg in _segments(pts):
        if len(seg) > 1:
            parts.append('<polyline class="graphe__ligne" points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py in seg) + '"/>')
    for i, (a, v) in enumerate(serie):
        if v is not None:
            parts.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="4.5" class="graphe__point">'
                         f'<title>{escape(a)}{M["commun.deux_points"]}{valeur_unite(v, ind, lang)}</title></circle>')
    a_der, v_der = connues(ind)[-1]
    i_der = [a for a, _ in serie].index(a_der)
    parts.append(f'<text x="{x(i_der):.1f}" y="{y(v_der) - 12:.1f}" text-anchor="middle" class="graphe__etiquette">{fmt(v_der, lang, ind["decimales"])}</text>')

    titre = cat.t(ind["titre"], lang)
    aria = f'{titre} ({ind["unite"]}), {periode(ind)}'
    svg = (f'<svg class="graphe" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(aria)}">'
           f'<defs><pattern id="hachures" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           f'<line x1="0" y1="0" x2="0" y2="8" class="graphe__hachure"/></pattern></defs>'
           f'<text x="{g}" y="12" class="graphe__unite">{escape(ind["unite"])}</text>{"".join(parts)}</svg>')
    lignes = "".join(
        f'<tr><td>{escape(a)}</td><td class="nombre">{fmt(v, lang, ind["decimales"]) if v is not None else M["fiche.apercu_nd"]}</td></tr>'
        for a, v in serie)
    tableau = (f'<details class="graphe__donnees"><summary>{M["fiche.apercu_tableau"]}</summary><div class="tableau-defilant">'
               f'<table class="tableau"><thead><tr><th scope="col">{M["indicateur.annee"]}</th><th scope="col" class="nombre">{escape(ind["unite"])}</th></tr></thead>'
               f'<tbody>{lignes}</tbody></table></div></details>')
    alerte = ""
    if manquantes(ind):
        alerte = (f'<div class="alerte alerte--avert" role="note"><svg aria-hidden="true"><use href="#i-attention"/></svg><div>'
                  f'<p class="alerte__titre">{M["fiche.apercu_alerte_titre"].replace("{liste}", ", ".join(manquantes(ind)))}</p>'
                  f'<p class="texte-sm">{M["indicateur.manque_texte"]}</p></div></div>')
    return (f'<figure class="graphe__cadre"><figcaption><strong>{escape(titre)}</strong> · {escape(ind["unite"])} · {periode(ind)} {cat.badge_demo(M)}</figcaption>'
            f'{svg}</figure>{alerte}{tableau}')


def mini_graphe(ind):
    """Courbe d'aperçu des cartes de la liste (décorative : la valeur est écrite à côté)."""
    serie = ind["serie"]
    vals = [v for _, v in serie if v is not None]
    vmin, vmax = min(vals), max(vals)
    etendue = (vmax - vmin) or 1
    W, H, m = 160, 44, 5
    n = len(serie)
    x = lambda i: m + (W - 2 * m) * (i / (n - 1) if n > 1 else 0.5)
    y = lambda v: m + (H - 2 * m) * (1 - (v - vmin) / etendue)
    pts = [None if v is None else (x(i), y(v)) for i, (_, v) in enumerate(serie)]
    traits = "".join('<polyline points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py in s) + '"/>'
                     for s in _segments(pts) if len(s) > 1)
    der = [p for p in pts if p][-1]
    return (f'<svg class="mini-graphe" viewBox="0 0 {W} {H}" aria-hidden="true" focusable="false">{traits}'
            f'<circle cx="{der[0]:.1f}" cy="{der[1]:.1f}" r="3.5"/></svg>')


# ---------------------------------------------------------------- pages

def badges(ind, ref, lang, M):
    return (cat.badge_demo(M) + cat.badge_statut(ind["statut"], M)
            + f'<span class="badge badge--theme">{escape(cat.t(ref["themes"][ind["theme"]], lang))}</span>')


def carte_indicateur(ind, ref, lang, M, racine):
    a, v = connues(ind)[-1]
    evo = evolution(ind, lang, M)
    return f'''<article class="carte carte--lien indicateur-carte">
  <div class="carte__badges">{badges(ind, ref, lang, M)}</div>
  <h3 class="titre-sm carte__titre"><a href="{lien(ind, lang, racine)}">{cat.e(ind["titre"], lang)}</a></h3>
  <p class="texte-sm texte-doux">{escape(cat.t(ref["territoires"][ind["territoire"]], lang))} · {periode(ind)}</p>
  <div class="indicateur-carte__chiffre">
    <p><span class="indicateur__valeur">{fmt(v, lang, ind["decimales"])}</span> <span class="indicateur__unite">{escape(ind["unite"])}</span><br><span class="texte-sm texte-doux">{M["indicateurs.en"]} {a}</span></p>
    {mini_graphe(ind)}
  </div>
  {f'<p class="texte-sm">{evo}</p>' if evo else f'<p class="texte-sm texte-doux">{M["indicateurs.une_valeur"]}</p>'}
</article>'''


def variables_liste(indicateurs, ref, lang, M, racine):
    return {
        "@liste_indicateurs": "\n".join(carte_indicateur(i, ref, lang, M, racine) for i in indicateurs),
        "@nb_indicateurs": str(len(indicateurs)),
    }


def variables_fiche(ind, jeux, ref, lang, M, racine):
    jeu = next(j for j in jeux if j["slug"] == ind["jeu"])
    a, v = connues(ind)[-1]
    evo = evolution(ind, lang, M)
    reserve = ""
    if ind["statut"] == "reserve":
        reserve = (f'<div class="alerte alerte--avert" role="note"><svg aria-hidden="true"><use href="#i-attention"/></svg><div>'
                   f'<p class="alerte__titre">{M["fiche.reserve_titre"]}</p><p class="texte-sm">{M["fiche.reserve_texte"]}</p></div></div>')
    return {
        "@ind_titre": cat.e(ind["titre"], lang),
        "@ind_resume": cat.e(ind["resume"], lang),
        "@ind_slug": ind["slug"],
        "@ind_identifiant": ind["identifiant"],
        "@ind_badges": badges(ind, ref, lang, M),
        "@ind_valeur": fmt(v, lang, ind["decimales"]),
        "@ind_unite": escape(ind["unite"]),
        "@ind_annee": a,
        "@ind_evolution": evolution(ind, lang, M, "indicateur.evolution_court") or M["indicateurs.une_valeur"],
        "@ind_periode": periode(ind),
        "@ind_frequence": M["indicateur.frequence_" + ind["frequence"]],
        "@ind_graphe": graphe(ind, lang, M),
        "@ind_definition": cat.e(ind["definition"], lang),
        "@ind_methode": cat.e(ind["methode"], lang),
        "@ind_limites": cat.e(ind["limites"], lang),
        "@ind_territoire": escape(cat.t(ref["territoires"][ind["territoire"]], lang)),
        "@ind_theme": escape(cat.t(ref["themes"][ind["theme"]], lang)),
        "@ind_validation": cat.badge_statut(ind["statut"], M),
        "@ind_maj": f'<time datetime="{ind["maj"]}">{cat.date_lisible(ind["maj"], lang)}</time>',
        "@ind_reserve": reserve,
        "@ind_source_titre": cat.e(jeu["titre"], lang),
        "@ind_source_lien": cat.lien_fiche(jeu, lang, racine),
        "@ind_source_producteur": cat.e(jeu["source"], lang),
        "@ind_source_licence": escape(cat.nom_licence(jeu, ref, lang)),
        "@ind_jeu_slug": jeu["slug"],
        "@meta_description": cat.e(ind["resume"], lang),
    }
