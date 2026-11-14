# Logo Green Biometry

Logo redessiné en vectoriel le 14 novembre 2026 à partir de `Logo minimaliste Green Biometry.png`.
Le texte est converti en tracés : aucune police n'est nécessaire pour l'afficher.

## Fichiers

| Fichier | Usage |
| --- | --- |
| `logo-horizontal.svg` | Version principale, sur fond clair (blanc, ivoire) |
| `logo-horizontal-blanc.svg` | Sur fond sombre (vert foncé, photo sombre) |
| `logo-horizontal-mono.svg` | Une seule couleur (impression, tampon, document noir et blanc) |
| `symbole.svg` | Symbole seul sur fond clair : en-tête mobile, avatar |
| `symbole-blanc.svg` | Symbole seul sur fond sombre |
| `favicon.svg` | Icône d'onglet du navigateur et d'application |

## Couleurs

| Rôle | Valeur | Règle |
| --- | --- | --- |
| Vert Green Biometry | `#0A4D18` | Couleur principale. Contraste élevé sur blanc, utilisable pour le texte |
| Or Green Biometry | `#F2AC00` | **Accent uniquement.** Jamais pour du texte sur fond clair (contraste d'environ 1,9:1) |

## Règles d'usage

- Zone de protection : laisser autour du logo un espace vide au moins égal à la hauteur de la lettre « e ».
- Taille minimale : 120 px de large pour le logo horizontal ; en dessous, utiliser le symbole seul.
- Ne pas déformer, recolorer, ajouter d'ombre ni poser le logo vert sur un fond vert.

## Régénérer les fichiers

```
python design/logo/source/make_logo.py <chemin>/Montserrat[wght].ttf design/logo
```

La police Montserrat (variable) se télécharge depuis le dépôt `google/fonts` (dossier `ofl/montserrat`).
