"""Construit le site statique dans _site/ (publié sur GitHub Pages).

1. Copie les pages statiques de site/ (styleguide, assets, redirection de langue).
2. Ajoute le logo (design/logo/) et les tokens (design/tokens/) : sources uniques.
3. Rend chaque gabarit de gabarits/ dans chaque langue de messages/ :
     gabarits/accueil.html -> _site/fr/index.html et _site/en/index.html
     gabarits/<nom>.html   -> _site/<langue>/<nom>/index.html
4. Vérifie le bilinguisme (EF-14) : la construction échoue si une clé manque
   dans une langue ou si une balise {{...}} reste non remplacée.

Syntaxe des gabarits :
    {{commun.contribuer}}   texte traduit (messages/<langue>.json)
    {{> entete}}            inclut gabarits/partiels/entete.html
    {{@lang}} {{@racine}}   variables de page (langue, chemin vers la racine du site)

Utilisation (depuis la racine du dépôt) :
    python scripts/build_site.py
    python -m http.server 8000 -d _site     # puis ouvrir http://localhost:8000
"""
from pathlib import Path
import json
import re
import shutil
import sys

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "_site"
GABARITS = RACINE / "gabarits"
MESSAGES = RACINE / "messages"
LANGUES = ["fr", "en"]  # la première est la langue de référence

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
        for cle in sorted(reference - cles):
            erreurs.append(f"clé absente en {langue} : {cle}")
        for cle in sorted(cles - reference):
            erreurs.append(f"clé absente en {LANGUES[0]} : {cle}")
    for langue in LANGUES:
        for cle, texte in messages[langue].items():
            if not texte.strip():
                erreurs.append(f"texte vide en {langue} : {cle}")
    if erreurs:
        sys.exit("Traductions incomplètes :\n  " + "\n  ".join(erreurs))
    return messages


def inclure_partiels(texte: str, profondeur: int = 0) -> str:
    if profondeur > 5:
        sys.exit("Inclusions de partiels trop profondes")

    def remplacer(m):
        chemin = GABARITS / "partiels" / f"{m.group(1)}.html"
        if not chemin.exists():
            sys.exit(f"Partiel introuvable : {chemin}")
        return inclure_partiels(chemin.read_text(encoding="utf-8"), profondeur + 1)

    return RE_PARTIEL.sub(remplacer, texte)


def rendre(gabarit: Path, langue: str, textes: dict, racine: str) -> str:
    variables = {
        "@lang": langue,
        "@racine": racine,
        "@courant_fr": 'aria-current="true"' if langue == "fr" else "",
        "@courant_en": 'aria-current="true"' if langue == "en" else "",
    }
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
    pages = 0
    for gabarit in sorted(GABARITS.glob("*.html")):
        for langue in LANGUES:
            if gabarit.stem == "accueil":
                cible, racine = SORTIE / langue / "index.html", "../"
            else:
                cible, racine = SORTIE / langue / gabarit.stem / "index.html", "../../"
            cible.parent.mkdir(parents=True, exist_ok=True)
            cible.write_text(rendre(gabarit, langue, messages[langue], racine), encoding="utf-8")
            pages += 1

    (SORTIE / ".nojekyll").touch()
    fichiers = [p for p in SORTIE.rglob("*") if p.is_file()]
    taille = sum(p.stat().st_size for p in fichiers)
    cles = len(messages[LANGUES[0]])
    print(f"Site construit dans {SORTIE} : {pages} pages rendues ({cles} textes x {len(LANGUES)} langues), "
          f"{len(fichiers)} fichiers, {taille / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
