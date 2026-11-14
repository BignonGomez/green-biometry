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
| ADR-08 | 2026-11-14 | Logo redessiné en SVG ; couleurs de marque #0A4D18 (vert) et #F2AC00 (or, accent seulement) | Proposé | Harmoniser la palette de la maquette avec ces couleurs |
| ADR-09 | 2026-11-14 | Thème clair seulement au MVP, fond ivoire #FBF9F5, titres Playfair Display, texte Inter | Proposé | Thème sombre reporté en V2 |
