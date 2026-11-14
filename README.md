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

**Styleguide en ligne :** https://bignongomez.github.io/green-biometry/

## Contenu du dépôt

```
design/
  logo/               Logo vectoriel (SVG) et ses déclinaisons
    source/           Script de génération du logo et licence de la police
  tokens/tokens.css   Couleurs, polices, espacements : source unique
  maquette-stitch/    Maquette d'origine (export Google Stitch), un dossier par écran
site/                 Pages publiées sur GitHub Pages (styleguide)
scripts/build_site.py Construit _site/ à partir de site/, du logo et des tokens
docs/
  decisions.md        Registre des décisions (ADR)
IDEES.md              Idées hors périmètre, relues seulement au bilan du pilote
```

Les documents privés (cahier des charges, rapports) restent hors du dépôt : voir `.gitignore`.

## Licence

À définir. La police Montserrat utilisée pour le logo est sous licence SIL Open Font License 1.1
(`design/logo/source/OFL-Montserrat.txt`).
