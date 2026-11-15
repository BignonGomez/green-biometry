"""Pages de texte (conditions d'utilisation, confidentialité).

Les sections viennent des messages : <page>.s1_titre, <page>.s1_texte, <page>.s2_titre…
Le texte peut contenir du HTML simple (<p>, <ul>, <a>, <strong>), écrit dans les messages.
"""
import re


def variables(page, M):
    numeros = sorted({int(m.group(1)) for k in M if (m := re.fullmatch(rf"{page}\.s(\d+)_titre", k))})
    sommaire, sections = [], []
    for n in numeros:
        ancre = f"s{n}"
        titre = M[f"{page}.s{n}_titre"]
        sommaire.append(f'<li><a href="#{ancre}">{titre}</a></li>')
        sections.append(f'      <section id="{ancre}" aria-labelledby="t-{ancre}"><h2 class="titre-md" id="t-{ancre}">{titre}</h2>'
                        f'{M[f"{page}.s{n}_texte"]}</section>')
    intro = M[f"{page}.intro"]
    return {
        "@page_titre": M[f"{page}.titre"],
        "@page_intro": intro,
        "@page_intro_meta": re.sub(r"<[^>]+>", "", intro),
        "@sommaire": "".join(sommaire),
        "@sections": "\n".join(sections),
    }
