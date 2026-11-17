"""Photos d'en-tête des pages de rubrique (catalogue, carte, indicateurs, projets, à propos, contact).

Chaque photo est déclarée ici avec son crédit et sa licence, et listée dans design/photos/REGISTRE.md.
Une rubrique sans photo garde l'en-tête uni. Fichiers : site/assets/img/hero-<rubrique>-1600.webp et -800.webp.
"""
from html import escape
from pathlib import Path

IMG = Path(__file__).resolve().parent.parent / "site" / "assets" / "img"

CC_BY_SA = ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/deed.fr")
HEROS = {
    "catalogue": {
        "auteur": "Kulttuurinavigaattori",
        "titre": "Forêt sacrée de Ouidah",
        "titre_en": "Sacred forest of Ouidah",
        "source": "https://commons.wikimedia.org/wiki/File:Sacred_Forest_Ouidah_Benin_Jan_2018.jpg",
        "licence": CC_BY_SA,
    },
    "carte": {
        "auteur": "Marie-Michaire LIMA",
        "titre": "Parc national de la Pendjari vu du ciel",
        "titre_en": "Pendjari National Park from the air",
        "source": "https://commons.wikimedia.org/wiki/File:Parc_National_de_la_Pendjari,_vu_du_ciel.jpg",
        "licence": CC_BY_SA,
    },
    "projets": {
        "auteur": "Kijoe",
        "titre": "Germination d'une mangrove au Bénin",
        "titre_en": "Mangrove seedlings in Benin",
        "source": "https://commons.wikimedia.org/wiki/File:Racine_et_de_ut_de_germination_d%27une_mangrove_au_B%C3%A9nin.jpg",
        "licence": CC_BY_SA,
    },
    "apropos": {
        "auteur": "Farid AMADOU BAHLEMAN",
        "titre": "Cobes defassa au parc national de la Pendjari",
        "titre_en": "Waterbuck in Pendjari National Park",
        "source": "https://commons.wikimedia.org/wiki/File:Waterbuck_ou_Cobe_defassa_au_Parc_National_de_la_Pendjari.jpg",
        "licence": CC_BY_SA,
    },
    "indicateurs": {
        "auteur": "Asabiyya",
        "titre": "Lac Nokoué, Ganvié",
        "titre_en": "Lake Nokoué, Ganvié",
        "source": "https://commons.wikimedia.org/wiki/File:Ganvie,_Lake_Village,_Lake_Nokou%C3%A9,_Benin_02.jpg",
        "licence": CC_BY_SA,
    },
    "contact": {
        "auteur": "Ji-Elle",
        "titre": "Chutes de Tanougou",
        "titre_en": "Tanougou Falls",
        "source": "https://commons.wikimedia.org/wiki/File:Chutes_de_Tanougou_(3).jpg",
        "licence": CC_BY_SA,
    },
}


def variables(rubrique, lang, M, racine):
    """Variables d'en-tête ; vides (en-tête uni) si la rubrique n'a pas de photo disponible."""
    h = HEROS.get(rubrique)
    if not h or not (IMG / f"hero-{rubrique}-1600.webp").exists():
        return {"@entete_classe": "", "@hero_photo": "", "@hero_credit": ""}
    base = f"{racine}assets/img/hero-{rubrique}"
    # Photo décorative (alt vide) : le titre de la page porte le sens ; la légende est dans le crédit.
    photo = (f'<img class="entete-page__photo" src="{base}-1600.webp" '
             f'srcset="{base}-800.webp 800w, {base}-1600.webp 1600w" sizes="100vw" alt="" '
             f'width="1600" height="560" fetchpriority="high" decoding="async">')
    titre = h["titre"] if lang == "fr" else h["titre_en"]
    nom_lic, url_lic = h["licence"]
    credit = (f'<p class="entete-page__credit">{M["commun.photo"]}{M["commun.deux_points"]}'
              f'<a href="{h["source"]}">{escape(titre)}</a>, {escape(h["auteur"])}, '
              f'<a href="{url_lic}" rel="license">{nom_lic}</a></p>')
    return {"@entete_classe": "entete-page--photo", "@hero_photo": photo, "@hero_credit": credit}
