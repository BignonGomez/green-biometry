"""Construit le site statique dans _site/ (publié sur GitHub Pages).

1. Copie les pages statiques de site/ (styleguide, assets, redirection de langue).
2. Ajoute le logo (design/logo/) et les tokens (design/tokens/) : sources uniques.
3. Rend chaque page dans chaque langue de messages/ :
     accueil   -> _site/<langue>/index.html
     catalogue -> _site/<langue>/catalogue/index.html
     carte     -> _site/<langue>/carte/index.html
     indicateurs -> _site/<langue>/indicateurs/index.html, plus une fiche par indicateur
     projets   -> _site/<langue>/projets/index.html, plus une fiche par projet
     apropos   -> _site/<langue>/a-propos/index.html
     contact   -> _site/<langue>/contact/index.html
     texte     -> _site/<langue>/conditions/ et /confidentialite/ (sections lues dans les messages)
     fiche     -> _site/<langue>/catalogue/<slug>/index.html (une par jeu de donnees/jeux-demo.json)
4. Vérifie le bilinguisme (EF-14) : la construction échoue si une clé manque
   dans une langue ou si une balise {{...}} reste non remplacée.

Syntaxe des gabarits :
    {{commun.contribuer}}   texte traduit (messages/<langue>.json)
    {{> entete}}            inclut gabarits/partiels/entete.html
    {{@lang}} {{@racine}}   variables de page (langue, chemin vers la racine du site, données…)

Utilisation (depuis la racine du dépôt) :
    python scripts/build_site.py
    python -m http.server 8000 -d _site     # puis ouvrir http://localhost:8000
"""
from pathlib import Path
import json
import re
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalogue as cat  # noqa: E402
import carte  # noqa: E402
import indicateurs as ind  # noqa: E402
import projets as prj  # noqa: E402
import pages_texte  # noqa: E402
import photos  # noqa: E402

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "_site"
GABARITS = RACINE / "gabarits"
MESSAGES = RACINE / "messages"
DONNEES = RACINE / "donnees" / "jeux-demo.json"
INDICATEURS = RACINE / "donnees" / "indicateurs-demo.json"
PROJETS = RACINE / "donnees" / "projets-demo.json"
LANGUES = ["fr", "en"]  # la première est la langue de référence
# Chemin du site sur le serveur (GitHub Pages de projet). À changer avec un nom de domaine propre.
BASE_URL = "/green-biometry/"
NAV = ["catalogue", "carte", "indicateurs", "projets", "apropos"]
# Pages de rubrique qui ont une photo d'en-tête (voir scripts/photos.py).
HEROS = {"catalogue/": "catalogue", "carte/": "carte", "indicateurs/": "indicateurs",
         "projets/": "projets", "a-propos/": "apropos", "contact/": "contact"}

RE_PARTIEL = re.compile(r"\{\{>\s*([\w-]+)\s*\}\}")
RE_BALISE = re.compile(r"\{\{\s*(@?[\w.]+)\s*\}\}")


def aplatir(dico: dict, prefixe: str = "") -> dict:
    plat = {}
    for cle, valeur in dico.items():
        chemin = f"{prefixe}{cle}"
        if isinstance(valeur, dict):
            plat.update(aplatir(valeur, chemin + "."))
        else:
            plat[chemin] = str(valeur)
    return plat


def charger_messages() -> dict:
    messages = {}
    for langue in LANGUES:
        with open(MESSAGES / f"{langue}.json", encoding="utf-8") as f:
            messages[langue] = aplatir(json.load(f))
    reference = set(messages[LANGUES[0]])
    erreurs = []
    for langue in LANGUES[1:]:
        cles = set(messages[langue])
        erreurs += [f"clé absente en {langue} : {c}" for c in sorted(reference - cles)]
        erreurs += [f"clé absente en {LANGUES[0]} : {c}" for c in sorted(cles - reference)]
    for langue in LANGUES:
        erreurs += [f"texte vide en {langue} : {c}" for c, v in messages[langue].items() if not v.strip()]
    if erreurs:
        sys.exit("Traductions incomplètes :\n  " + "\n  ".join(erreurs))
    return messages


def verifier_donnees(donnees: dict) -> None:
    """Chaque texte traduisible des jeux doit exister en FR et en EN."""
    erreurs = []

    def parcourir(valeur, chemin):
        if isinstance(valeur, dict):
            if set(valeur) & set(LANGUES):
                erreurs.extend(f"{chemin} : langue {l} manquante" for l in LANGUES if not str(valeur.get(l, "")).strip())
                return
            for k, v in valeur.items():
                parcourir(v, f"{chemin}.{k}")
        elif isinstance(valeur, list):
            for i, v in enumerate(valeur):
                parcourir(v, f"{chemin}[{i}]")

    parcourir(donnees["jeux"], "jeux")
    parcourir(donnees.get("indicateurs", []), "indicateurs")
    parcourir(donnees.get("projets", []), "projets")
    if erreurs:
        sys.exit("Données incomplètes :\n  " + "\n  ".join(erreurs))


def inclure_partiels(texte: str, profondeur: int = 0) -> str:
    if profondeur > 5:
        sys.exit("Inclusions de partiels trop profondes")

    def remplacer(m):
        chemin = GABARITS / "partiels" / f"{m.group(1)}.html"
        if not chemin.exists():
            sys.exit(f"Partiel introuvable : {chemin}")
        return inclure_partiels(chemin.read_text(encoding="utf-8"), profondeur + 1)

    return RE_PARTIEL.sub(remplacer, texte)


def rendre(gabarit: Path, langue: str, textes: dict, variables: dict) -> str:
    source = inclure_partiels(gabarit.read_text(encoding="utf-8"))
    manquantes = set()

    def remplacer(m):
        cle = m.group(1)
        if cle in variables:
            return variables[cle]
        if cle in textes:
            return textes[cle]
        manquantes.add(cle)
        return m.group(0)

    html = RE_BALISE.sub(remplacer, source)
    if manquantes:
        sys.exit(f"{gabarit.name} ({langue}) : clés inconnues : {', '.join(sorted(manquantes))}")
    return html


def pages(donnees):
    """(gabarit, chemin sous /<langue>/, rubrique active, fonction -> variables propres à la page)."""
    jeux, ref = donnees["jeux"], donnees["referentiels"]
    yield "accueil.html", "", None, lambda l, M, r: {
        "@derniers_jeux": cat.derniers_jeux(jeux, ref, l, M, r)}
    yield "catalogue.html", "catalogue/", "catalogue", lambda l, M, r: {
        "@liste_jeux": cat.liste_catalogue(jeux, ref, l, M, r),
        "@facettes": cat.facettes(jeux, ref, l, M),
        "@nb_jeux": str(len(jeux))}
    yield "carte.html", "carte/", "carte", lambda l, M, r: carte.variables_carte(jeux, ref, l, M, r)
    inds = donnees["indicateurs"]
    yield "indicateurs.html", "indicateurs/", "indicateurs", lambda l, M, r: ind.variables_liste(inds, ref, l, M, r)
    for i in inds:
        yield "indicateur.html", f"indicateurs/{i['slug']}/", "indicateurs", (
            lambda l, M, r, i=i: ind.variables_fiche(i, jeux, ref, l, M, r))
    yield "apropos.html", "a-propos/", "apropos", lambda l, M, r: {}
    yield "contact.html", "contact/", None, lambda l, M, r: {}
    yield "bientot.html", "bientot/", None, lambda l, M, r: {}
    for page in ("conditions", "confidentialite"):
        yield "texte.html", f"{page}/", None, lambda l, M, r, page=page: pages_texte.variables(page, M)
    prjs = donnees["projets"]
    yield "projets.html", "projets/", "projets", lambda l, M, r: prj.variables_liste(prjs, ref, l, M, r)
    for p in prjs:
        yield "projet.html", f"projets/{p['slug']}/", "projets", (
            lambda l, M, r, p=p: prj.variables_fiche(p, jeux, inds, ref, l, M, r))
    for jeu in jeux:
        yield "fiche.html", f"catalogue/{jeu['slug']}/", "catalogue", (
            lambda l, M, r, jeu=jeu: cat.variables_fiche(jeu, ref, l, M, r))


def main() -> None:
    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    shutil.copytree(RACINE / "site", SORTIE)

    logos = SORTIE / "assets" / "logo"
    logos.mkdir(parents=True, exist_ok=True)
    for svg in (RACINE / "design" / "logo").glob("*.svg"):
        shutil.copy2(svg, logos / svg.name)
    shutil.copy2(RACINE / "design" / "tokens" / "tokens.css", SORTIE / "assets" / "css" / "tokens.css")

    messages = charger_messages()
    donnees = json.loads(DONNEES.read_text(encoding="utf-8"))
    donnees["indicateurs"] = json.loads(INDICATEURS.read_text(encoding="utf-8"))["indicateurs"]
    donnees["projets"] = json.loads(PROJETS.read_text(encoding="utf-8"))["projets"]
    verifier_donnees(donnees)
    ind.verifier(donnees["indicateurs"], donnees["jeux"], donnees["referentiels"])
    prj.verifier(donnees["projets"], donnees["jeux"], donnees["indicateurs"], donnees["referentiels"])

    n = 0
    for gabarit, chemin, rubrique, variables_page in pages(donnees):
        for langue in LANGUES:
            racine = "../" * (1 + chemin.count("/"))
            variables = {
                "@lang": langue,
                "@racine": racine,
                "@chemin_fr": f"{racine}fr/{chemin}",
                "@chemin_en": f"{racine}en/{chemin}",
                "@courant_fr": 'aria-current="true"' if langue == "fr" else "",
                "@courant_en": 'aria-current="true"' if langue == "en" else "",
            }
            for nav in NAV:
                variables[f"@actif_{nav}"] = 'aria-current="page"' if nav == rubrique else ""
            variables.update(photos.variables(HEROS.get(chemin), langue, messages[langue], racine))
            variables.update(variables_page(langue, messages[langue], racine))
            cible = SORTIE / langue / chemin / "index.html"
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(rendre(GABARITS / gabarit, langue, messages[langue], variables), encoding="utf-8")
            n += 1

    # Page 404 bilingue : servie par GitHub Pages à n'importe quelle profondeur, donc chemins absolus.
    (SORTIE / "404.html").write_text(
        rendre(GABARITS / "404.html", LANGUES[0], messages[LANGUES[0]], {"@racine": BASE_URL}), encoding="utf-8")
    (SORTIE / ".nojekyll").touch()
    fichiers = [p for p in SORTIE.rglob("*") if p.is_file()]
    taille = sum(p.stat().st_size for p in fichiers)
    print(f"Site construit dans {SORTIE} : {n} pages ({len(donnees['jeux'])} fiches x {len(LANGUES)} langues incluses), "
          f"{len(messages[LANGUES[0]])} textes, {len(fichiers)} fichiers, {taille / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
