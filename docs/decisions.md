# Registre des décisions (ADR)

Chaque décision structurante est notée ici : date, statut, raison et conséquence à surveiller.
Statuts : Proposé, Décidé, Remplacé.

| Réf. | Date | Décision | Statut | Conséquence à surveiller |
| --- | --- | --- | --- | --- |
| ADR-01 | 2026-11-11 | Application unique plutôt que services séparés pour le MVP | Proposé | Couplage à gérer par une bonne structure de code |
| ADR-02 | 2026-11-11 | PostgreSQL et PostGIS managés (Supabase) | Proposé | Dépendance au fournisseur : export de la base chaque nuit |
| ADR-03 | 2026-11-11 | Traitements R ou Python hors de l'application | Proposé | Scripts versionnés et documentés |
| ADR-04 | 2026-11-11 | Pas d'IA dans le MVP | Décidé | Réévaluer après le pilote |
| ADR-05 | 2026-11-11 | Collecte terrain via un outil existant (KoboToolbox, ODK) | Proposé | Format d'import à standardiser |
| ADR-06 | 2026-11-14 | Stack : Next.js (TypeScript) + Supabase ; plan B Django | Proposé | À confirmer avant le 29 nov. 2026 selon le niveau en React |
| ADR-07 | 2026-11-14 | Hébergement gratuit : GitHub (code), GitHub Pages (maquette), Vercel et Supabase (application) | Proposé | Limites des offres gratuites, usage non commercial de Vercel Hobby |
| ADR-08 | 2026-11-14 | Logo redessiné en SVG ; couleurs de marque #0A4D18 (vert) et #F2AC00 (or, accent seulement) | Remplacé par ADR-11 (couleurs) | Harmoniser la palette de la maquette avec ces couleurs |
| ADR-09 | 2026-11-14 | Thème clair seulement au MVP, fond ivoire #FBF9F5, titres Playfair Display, texte Inter | Remplacé par ADR-11 (fond), polices conservées | Thème sombre reporté en V2 |
| ADR-10 | 2026-11-16 | Carte publique : Leaflet (hébergé avec le site) et fond OpenStreetMap, désaturé en CSS | Proposé | Politique d'usage des tuiles OSM : prévoir un fournisseur de tuiles (ou nos propres tuiles) avant la mise en production. Le fond CARTO exige désormais une clé |
| ADR-11 | 2026-11-16 | Palette « Eau claire » : bleu #0E6BA8 (actions), bleu clair #7CC6EE (accent seulement), marine #0B3550 (fonds sombres), fond #F8FBFD. Plus de vert dans la marque ; le vert reste seulement la couleur du thème Forêts dans les données. Logo : même forme, recoloré | Décidé | Bleu clair jamais en texte sur fond clair (1,9:1). Le nom « Green Biometry » reste un nom de travail |
