"""Construit le site statique dans _site/ (publié sur GitHub Pages).

Rassemble les pages de site/, le logo de design/logo/ et les tokens de design/tokens/.
Les sources restent uniques : rien n'est copié à la main.

Utilisation (depuis la racine du dépôt) :
    python scripts/build_site.py
    python -m http.server 8000 -d _site     # puis ouvrir http://localhost:8000
"""
from pathlib import Path
import shutil

RACINE = Path(__file__).resolve().parent.parent
SORTIE = RACINE / "_site"


def main() -> None:
    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    shutil.copytree(RACINE / "site", SORTIE)

    logos = SORTIE / "assets" / "logo"
    logos.mkdir(parents=True, exist_ok=True)
    for svg in (RACINE / "design" / "logo").glob("*.svg"):
        shutil.copy2(svg, logos / svg.name)

    css = SORTIE / "assets" / "css"
    css.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RACINE / "design" / "tokens" / "tokens.css", css / "tokens.css")

    (SORTIE / ".nojekyll").touch()
    fichiers = [p for p in SORTIE.rglob("*") if p.is_file()]
    taille = sum(p.stat().st_size for p in fichiers)
    print(f"Site construit dans {SORTIE} : {len(fichiers)} fichiers, {taille / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
