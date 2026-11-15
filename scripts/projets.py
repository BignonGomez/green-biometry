"""Pages Projets : liste et fiche de chaque projet (donnees/projets-demo.json).

Règles du cahier des charges appliquées ici :
- chaque indicateur suivi a une valeur de référence (ou l'absence est dite), une cible et un historique ;
- on distingue moyens et activités, résultats, effets écologiques mesurés ;
- on distingue valeur observée, estimation et résultat déclaré ;
- les périodes sans rapport sont montrées, jamais comblées ;
- la plateforme n'attribue jamais automatiquement un changement écologique au projet.
"""
from html import escape
import math
import sys

import catalogue as cat
from indicateurs import fmt, _pas_rond, _segments

NIVEAUX = ("activite", "resultat", "effet")
TYPES = ("observee", "estimation", "declaree")
STATUTS_RAPPORT = {"valide": "badge--valide", "soumis": "badge--soumis", "manquant": "badge--reserve"}


def verifier(projets, jeux, indicateurs, ref):
    slugs_jeux = {j["slug"] for j in jeux}
    slugs_ind = {i["slug"] for i in indicateurs}
    erreurs = []
    for p in projets:
        for s in p["jeux"]:
            if s not in slugs_jeux:
                erreurs.append(f"{p['slug']} : jeu inconnu {s}")
        if len(p["indicateurs"]) < 2:
            erreurs.append(f"{p['slug']} : moins de 2 indicateurs suivis (cahier des charges)")
        for ind in p["indicateurs"]:
            if ind["niveau"] not in NIVEAUX:
                erreurs.append(f"{p['slug']}/{ind['code']} : niveau inconnu {ind['niveau']}")
            if ind.get("indicateur_public") and ind["indicateur_public"] not in slugs_ind:
                erreurs.append(f"{p['slug']}/{ind['code']} : indicateur public inconnu")
            for a, v, typ in ind["serie"]:
                if (v is None) != (typ is None) or (typ and typ not in TYPES):
                    erreurs.append(f"{p['slug']}/{ind['code']} {a} : type de valeur incohérent")
            if not ind.get("cible"):
                erreurs.append(f"{p['slug']}/{ind['code']} : cible absente")
    if erreurs:
        sys.exit("Projets incohérents :\n  " + "\n  ".join(erreurs))


def unite(ind, lang):
    return cat.t(ind["unite"], lang)


def avec_unite(v, ind, lang):
    u = unite(ind, lang)
    colle = u == "%" and lang == "en"
    return f"{fmt(v, lang, ind['decimales'])}{'' if colle else ' '}{escape(u)}"


def derniere(ind):
    connues = [(a, v, t) for a, v, t in ind["serie"] if v is not None]
    return connues[-1] if connues else None


def periode(p):
    return f"{p['debut']}–{p['fin']}"


def lien(p, lang, racine):
    return f"{racine}{lang}/projets/{p['slug']}/"


def badge_statut_projet(p, M):
    classe = "badge--publie" if p["statut"] == "en_cours" else "badge--archive"
    return f'<span class="badge {classe}">{M["projets.statut_" + p["statut"]]}</span>'


def badge_niveau(ind, M):
    return f'<span class="badge badge--niveau badge--niveau-{ind["niveau"]}">{M["projet.niveau_" + ind["niveau"]]}</span>'


def badge_type(typ, M):
    return f'<span class="type-valeur type-valeur--{typ}"><span class="type-valeur__repere" aria-hidden="true"></span>{M["projet.type_" + typ]}</span>'


def avancement(ind):
    """Part du chemin parcouru entre la référence (ou 0) et la cible, bornée à [0, 1]."""
    d = derniere(ind)
    if not d:
        return None
    depart = ind["reference"]["valeur"] if ind["reference"] else 0
    ecart = ind["cible"]["valeur"] - depart
    if not ecart:
        return None
    return max(0.0, min(1.0, (d[1] - depart) / ecart))


def barre(ind, lang, M):
    part = avancement(ind)
    if part is None:
        return ""
    pct = round(part * 100)
    d = derniere(ind)
    texte = (M["projet.avancement"].replace("{valeur}", avec_unite(d[1], ind, lang))
             .replace("{cible}", avec_unite(ind["cible"]["valeur"], ind, lang)).replace("{annee}", ind["cible"]["annee"]))
    return (f'<div class="avancement"><div class="avancement__piste" role="img" aria-label="{escape(texte)}">'
            f'<div class="avancement__jauge" style="width:{pct}%"></div></div>'
            f'<p class="texte-sm texte-doux">{texte}</p></div>')


# ---------------------------------------------------------------- graphique

def graphe(ind, p, lang, M):
    """Valeurs dans le temps, référence et cible ; périodes manquantes hachurées, jamais reliées."""
    ref = ind["reference"]
    cible = ind["cible"]
    serie = [(a, v, t) for a, v, t in ind["serie"]]
    annees = ([ref["annee"]] if ref else []) + [a for a, _, _ in serie]
    if cible["annee"] not in annees:
        annees.append(cible["annee"])
    vals = [v for _, v, _ in serie if v is not None] + [cible["valeur"]] + ([ref["valeur"]] if ref else [])
    bas = min(0, min(vals))
    pas = _pas_rond((max(vals) - bas) / 4)
    haut = math.ceil(max(vals) / pas) * pas
    if haut == max(vals):
        haut += pas
    W, H, g, d, h0, b = 720, 280, 64, 24, 24, 40
    lw = (W - g - d) / len(annees)
    x = lambda a: g + lw * (annees.index(a) + 0.5)
    y = lambda v: h0 + (H - h0 - b) * (1 - (v - bas) / (haut - bas))
    u = escape(unite(ind, lang))

    parts = []
    k = 0
    while bas + k * pas <= haut + 1e-9:
        val = bas + k * pas
        parts.append(f'<line x1="{g}" x2="{W - d}" y1="{y(val):.1f}" y2="{y(val):.1f}" class="graphe__grille"/>'
                     f'<text x="{g - 8}" y="{y(val) + 4:.1f}" text-anchor="end" class="graphe__axe">{fmt(val, lang)}</text>')
        k += 1
    for a, v, _ in serie:
        if v is None:
            parts.append(f'<rect x="{x(a) - lw / 2 + 2:.1f}" y="{h0}" width="{lw - 4:.1f}" height="{H - h0 - b}" class="graphe__manque"/>'
                         f'<text x="{x(a):.1f}" y="{h0 + 16}" text-anchor="middle" class="graphe__nd">{M["projet.sans_rapport"]}</text>')
    for a in annees:
        parts.append(f'<text x="{x(a):.1f}" y="{H - b + 20}" text-anchor="middle" class="graphe__axe">{escape(a)}</text>')
    # Cible : ligne pointillée sur toute la largeur, étiquetée.
    yc = y(cible["valeur"])
    parts.append(f'<line x1="{g}" x2="{W - d}" y1="{yc:.1f}" y2="{yc:.1f}" class="graphe__cible"/>'
                 f'<text x="{W - d}" y="{yc - 8:.1f}" text-anchor="end" class="graphe__cible-texte">'
                 f'{M["projet.cible"]} {cible["annee"]}{M["commun.deux_points"]}{fmt(cible["valeur"], lang, ind["decimales"])}</text>')
    # Ligne : référence puis valeurs connues, coupée aux périodes manquantes.
    pts = ([(x(ref["annee"]), y(ref["valeur"]))] if ref else []) + [None if v is None else (x(a), y(v)) for a, v, _ in serie]
    for seg in _segments(pts):
        if len(seg) > 1:
            parts.append('<polyline class="graphe__ligne" points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py in seg) + '"/>')
    if ref:
        parts.append(f'<rect x="{x(ref["annee"]) - 5:.1f}" y="{y(ref["valeur"]) - 5:.1f}" width="10" height="10" class="graphe__reference">'
                     f'<title>{M["projet.reference"]} {ref["annee"]}{M["commun.deux_points"]}{avec_unite(ref["valeur"], ind, lang)}</title></rect>')
    for a, v, t in serie:
        if v is not None:
            parts.append(f'<circle cx="{x(a):.1f}" cy="{y(v):.1f}" r="5" class="graphe__point graphe__point--{t}">'
                         f'<title>{escape(a)}{M["commun.deux_points"]}{avec_unite(v, ind, lang)} ({M["projet.type_" + t]})</title></circle>')
    titre = cat.t(ind["titre"], lang)
    svg = (f'<svg class="graphe" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(titre)} ({u}), {M["projet.cible"]} {cible["annee"]}">'
           f'<defs><pattern id="hachures-{ind["code"]}" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
           f'<line x1="0" y1="0" x2="0" y2="8" class="graphe__hachure"/></pattern></defs>'
           f'<text x="{g}" y="12" class="graphe__unite">{u}</text>{"".join(parts)}</svg>')
    svg = svg.replace('class="graphe__manque"/>', f'class="graphe__manque" style="fill:url(#hachures-{ind["code"]})"/>')
    return svg


def tableau(ind, lang, M):
    lignes = []
    if ind["reference"]:
        r = ind["reference"]
        lignes.append(f'<tr><td>{r["annee"]}</td><td class="nombre">{fmt(r["valeur"], lang, ind["decimales"])}</td><td>{M["projet.reference"]}</td></tr>')
    for a, v, t in ind["serie"]:
        if v is None:
            lignes.append(f'<tr class="ligne-manque"><td>{a}</td><td class="nombre">—</td><td>{M["projet.sans_rapport_long"]}</td></tr>')
        else:
            lignes.append(f'<tr><td>{a}</td><td class="nombre">{fmt(v, lang, ind["decimales"])}</td><td>{badge_type(t, M)}</td></tr>')
    c = ind["cible"]
    lignes.append(f'<tr><td>{c["annee"]}</td><td class="nombre">{fmt(c["valeur"], lang, ind["decimales"])}</td><td>{M["projet.cible"]}</td></tr>')
    return (f'<details class="graphe__donnees"><summary>{M["fiche.apercu_tableau"]}</summary><div class="tableau-defilant">'
            f'<table class="tableau"><thead><tr><th scope="col">{M["indicateur.annee"]}</th>'
            f'<th scope="col" class="nombre">{escape(unite(ind, lang))}</th><th scope="col">{M["projet.nature"]}</th></tr></thead>'
            f'<tbody>{"".join(lignes)}</tbody></table></div></details>')


def bloc_indicateur(ind, p, indicateurs, lang, M, racine):
    ref = ind["reference"]
    d = derniere(ind)
    ref_txt = (f'{avec_unite(ref["valeur"], ind, lang)} <span class="texte-doux">({ref["annee"]})</span>' if ref
               else f'<span class="texte-doux">{M["projet.sans_reference"]}</span>')
    der_txt = (f'{avec_unite(d[1], ind, lang)} <span class="texte-doux">({d[0]})</span><br>{badge_type(d[2], M)}' if d else "—")
    lien_public = ""
    if ind.get("indicateur_public"):
        pub = next(i for i in indicateurs if i["slug"] == ind["indicateur_public"])
        lien_public = (f'<p class="texte-sm"><svg class="icone-texte" aria-hidden="true"><use href="#i-courbe"/></svg>'
                       f'{M["projet.indicateur_public"]} <a href="{racine}{lang}/indicateurs/{pub["slug"]}/">{cat.e(pub["titre"], lang)}</a></p>')
    return f'''<article class="suivi" aria-labelledby="t-{ind["code"]}">
  <div class="suivi__tete">
    {badge_niveau(ind, M)}
    <h3 class="titre-sm" id="t-{ind["code"]}">{cat.e(ind["titre"], lang)}</h3>
  </div>
  <dl class="suivi__valeurs">
    <div><dt>{M["projet.reference"]}</dt><dd>{ref_txt}</dd></div>
    <div><dt>{M["projet.derniere"]}</dt><dd>{der_txt}</dd></div>
    <div><dt>{M["projet.cible"]}</dt><dd>{avec_unite(ind["cible"]["valeur"], ind, lang)} <span class="texte-doux">({ind["cible"]["annee"]})</span></dd></div>
  </dl>
  {barre(ind, lang, M)}
  <figure class="graphe__cadre">{graphe(ind, p, lang, M)}</figure>
  <p class="texte-sm texte-doux suivi__note">{cat.e(ind["note"], lang)}</p>
  {lien_public}
  {tableau(ind, lang, M)}
</article>'''


def legende(M):
    items = "".join(f'<li>{badge_type(t, M)}<span class="texte-sm texte-doux">{M["projet.type_" + t + "_aide"]}</span></li>' for t in TYPES)
    return (f'<ul class="legende-types">{items}'
            f'<li><span class="type-valeur type-valeur--reference"><span class="type-valeur__repere" aria-hidden="true"></span>{M["projet.reference"]}</span>'
            f'<span class="texte-sm texte-doux">{M["projet.reference_aide"]}</span></li>'
            f'<li><span class="type-valeur type-valeur--cible"><span class="type-valeur__repere" aria-hidden="true"></span>{M["projet.cible"]}</span>'
            f'<span class="texte-sm texte-doux">{M["projet.cible_aide"]}</span></li></ul>')


def activites(p, lang, M):
    lignes = "".join(f'<tr><td>{cat.e(a["libelle"], lang)}</td><td class="nombre">{fmt(a["valeur"], lang)}</td><td>{cat.e(a["unite"], lang)}</td></tr>'
                     for a in p["activites"])
    return (f'<div class="tableau-defilant"><table class="tableau"><thead><tr><th scope="col">{M["projet.activite"]}</th>'
            f'<th scope="col" class="nombre">{M["projet.quantite"]}</th><th scope="col">{M["indicateur.unite"]}</th></tr></thead>'
            f'<tbody>{lignes}</tbody></table></div>')


def rapports(p, lang, M):
    lignes = []
    for r in p["rapports"]:
        badge = f'<span class="badge {STATUTS_RAPPORT[r["statut"]]}">{M["projet.rapport_" + r["statut"]]}</span>'
        date = f'<time datetime="{r["date"]}">{cat.date_lisible(r["date"], lang)}</time>' if r["date"] else "—"
        lignes.append(f'<tr><td><strong>{r["periode"]}</strong></td><td>{date}</td><td>{badge}</td></tr>')
    return (f'<div class="tableau-defilant"><table class="tableau"><thead><tr><th scope="col">{M["projet.rapport_periode"]}</th>'
            f'<th scope="col">{M["projet.rapport_date"]}</th><th scope="col">{M["projet.rapport_statut"]}</th></tr></thead>'
            f'<tbody>{"".join(lignes)}</tbody></table></div>')


# ---------------------------------------------------------------- pages

def badges(p, ref, lang, M):
    return (cat.badge_demo(M) + badge_statut_projet(p, M)
            + f'<span class="badge badge--theme">{escape(cat.t(ref["themes"][p["theme"]], lang))}</span>')


def carte_projet(p, ref, lang, M, racine):
    suivis = "".join(
        f'<li><span class="texte-sm">{cat.e(i["titre"], lang)}</span>{barre(i, lang, M)}</li>' for i in p["indicateurs"])
    return f'''<article class="carte carte--lien projet-carte">
  <div class="carte__badges">{badges(p, ref, lang, M)}</div>
  <h3 class="titre-sm carte__titre"><a href="{lien(p, lang, racine)}">{cat.e(p["titre"], lang)}</a></h3>
  <p class="texte-sm texte-doux">{cat.e(p["resume"], lang)}</p>
  <dl class="meta"><dt>{M["projets.porteur"]}</dt><dd>{cat.e(p["porteur"], lang)}</dd><dt>{M["commun.lbl_territoire"]}</dt><dd>{escape(cat.t(ref["territoires"][p["territoire"]], lang))}</dd><dt>{M["commun.lbl_periode"]}</dt><dd>{periode(p)}</dd></dl>
  <ul class="projet-carte__suivis">{suivis}</ul>
</article>'''


def variables_liste(projets, ref, lang, M, racine):
    return {"@liste_projets": "\n".join(carte_projet(p, ref, lang, M, racine) for p in projets),
            "@nb_projets": str(len(projets))}


def variables_fiche(p, jeux, indicateurs, ref, lang, M, racine):
    jeux_lies = [j for j in jeux if j["slug"] in p["jeux"]]
    manquants = [r["periode"] for r in p["rapports"] if r["statut"] == "manquant"]
    deposes = [r for r in p["rapports"] if r["date"]]
    dernier = max(deposes, key=lambda r: r["date"]) if deposes else None
    alerte_manque = ""
    if manquants:
        alerte_manque = (f'<div class="alerte alerte--avert" role="note"><svg aria-hidden="true"><use href="#i-attention"/></svg><div>'
                         f'<p class="alerte__titre">{M["projet.manque_titre"].replace("{liste}", ", ".join(manquants))}</p>'
                         f'<p class="texte-sm">{M["projet.manque_texte"]}</p></div></div>')
    liste_jeux = "".join(f'<li><a href="{cat.lien_fiche(j, lang, racine)}">{cat.e(j["titre"], lang)}</a></li>' for j in jeux_lies)
    partenaires = "".join(f"<li>{cat.e(x, lang)}</li>" for x in p["partenaires"])
    return {
        "@prj_titre": cat.e(p["titre"], lang),
        "@prj_resume": cat.e(p["resume"], lang),
        "@prj_identifiant": p["identifiant"],
        "@prj_badges": badges(p, ref, lang, M),
        "@prj_porteur": cat.e(p["porteur"], lang),
        "@prj_periode": periode(p),
        "@prj_territoire": escape(cat.t(ref["territoires"][p["territoire"]], lang)),
        "@prj_objectif": cat.e(p["objectif"], lang),
        "@prj_nb_indicateurs": str(len(p["indicateurs"])),
        "@prj_dernier_rapport": (f'{dernier["periode"]} <span class="texte-sm texte-doux">({cat.date_lisible(dernier["date"], lang)})</span>'
                                 if dernier else "—"),
        "@prj_nb_manquants": str(len(manquants)),
        "@prj_alerte_manque": alerte_manque,
        "@prj_legende": legende(M),
        "@prj_suivis": "\n".join(bloc_indicateur(i, p, indicateurs, lang, M, racine) for i in p["indicateurs"]),
        "@prj_activites": activites(p, lang, M),
        "@prj_rapports": rapports(p, lang, M),
        "@prj_partenaires": partenaires,
        "@prj_jeux": liste_jeux,
        "@prj_jeu_carte": p["jeux"][0],
        "@meta_description": cat.e(p["resume"], lang),
    }
