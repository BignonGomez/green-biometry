# Green Biometry

Plateforme internationale de données et de suivi environnemental, bilingue FR/EN :
catalogue de données, contribution, validation, cartographie, indicateurs et suivi de projets.

> « Green Biometry » est un **nom de travail**. Le nom définitif sera décidé le 14 février 2027
> (cahier des charges v2.0, § 14 et § 22).

## État du projet

**Phase : conception** (novembre 2026 – mars 2027). Aucune fonctionnalité n'est encore développée.
La maquette n'est pas un produit opérationnel, et ses chiffres sont fictifs.

| Jalon | Date visée |
| --- | --- |
| Conception validée (maquette testée, modèle de données) | 7 mars 2027 |
| Démonstrateur public (catalogue en lecture, FR/EN) | 1er août 2027 |
| MVP (parcours complet soumission → validation → publication) | mars 2028 |
| Pilote en ligne | juillet 2028 |

**En ligne :** https://bignongomez.github.io/green-biometry/ (FR et EN) : accueil, catalogue et fiches,
carte, indicateurs, projets, à propos, contact, conditions d'utilisation, confidentialité ·
styleguide https://bignongomez.github.io/green-biometry/styleguide/

## Contenu du dépôt

```
design/
  logo/               Logo vectoriel (SVG) et ses déclinaisons
    source/           Script de génération du logo et licence de la police
  tokens/tokens.css   Couleurs, polices, espacements : source unique
  photos/REGISTRE.md  Source, auteur et licence de chaque photo publiée
  maquette-stitch/    Maquette d'origine (export Google Stitch), un dossier par écran
gabarits/             Pages bilingues (un gabarit par page) et partiels communs (en-tête, pied)
messages/fr.json      Textes français (langue de référence)
messages/en.json      Textes anglais : mêmes clés, sinon la construction échoue
donnees/jeux-demo.json Jeux de démonstration (DÉMO) : source unique du catalogue, des fiches et de l'accueil
donnees/indicateurs-demo.json, donnees/projets-demo.json  Indicateurs et projets de démonstration (DÉMO)
site/                 Fichiers statiques publiés tels quels (styleguide, CSS, polices)
scripts/build_site.py Construit _site/ : rend les gabarits dans chaque langue, ajoute logo et tokens
scripts/catalogue.py  Composants générés à partir des données (cartes, filtres, fiche, graphique)
scripts/carte.py, indicateurs.py, projets.py, pages_texte.py  Pages Carte, Indicateurs, Projets, textes légaux
docs/
  decisions.md        Registre des décisions (ADR)
IDEES.md              Idées hors périmètre, relues seulement au bilan du pilote
```

Les documents privés (cahier des charges, rapports) restent hors du dépôt : voir `.gitignore`.

## Licence

À définir. La police Montserrat utilisée pour le logo est sous licence SIL Open Font License 1.1
(`design/logo/source/OFL-Montserrat.txt`).
