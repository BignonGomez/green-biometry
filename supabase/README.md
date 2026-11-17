# Base de données (Supabase)

Schéma, règles d'accès et tests de la plateforme. Conception : [`docs/conception/02-modele-donnees.md`](../docs/conception/02-modele-donnees.md).

```
migrations/0001_schema.sql    Tables, types, contraintes, identifiants lisibles
migrations/0002_securite.sql  Droits, règles par ligne (RLS), circuit de validation, fonctions d'administration
seed.sql                      Référentiels : thèmes, licences, territoires du Bénin (rejouable)
tests/lancer.mjs              Tests : un scénario par règle d'accès
```

## Lancer les tests (sans Docker, sans compte Supabase)

```
cd supabase/tests
npm install        # une seule fois : installe PGlite (PostgreSQL pour Node.js), version figée
npm test
```

Les tests appliquent les migrations sur un vrai PostgreSQL (PGlite), créent des comptes de chaque rôle
(visiteur, contributeur, évaluateur, administrateur, membre d'une organisation, fonction serveur)
et vérifient chaque case de la matrice « qui voit quoi ». Ils tournent aussi sur GitHub à chaque modification
de `supabase/` (`.github/workflows/tests-base.yml`).

**Ce qui est simulé localement :** les rôles et le schéma `auth` de Supabase, et PostGIS (les colonnes
géométriques deviennent du texte). La géographie et le stockage des fichiers se testent sur le projet Supabase « gb-dev ».

## Règles

- **Une migration appliquée en production ne se modifie plus** : toute évolution est une nouvelle migration numérotée.
- **Toute nouvelle table** reçoit dans la même migration : `enable row level security`, ses règles, ses `grant` explicites, et ses tests.
- **Le statut d'une soumission ne se modifie jamais directement** : uniquement par `changer_statut()`.

## Premier administrateur

Aucun compte ne peut se donner lui-même le rôle d'administrateur. Après la première inscription,
le propriétaire du projet l'attribue une fois, dans l'éditeur SQL de Supabase :

```sql
update public.profils set role = 'administrateur'
where id = (select id from auth.users where email = 'ADRESSE-DU-PREMIER-ADMIN');
```

Ensuite, les rôles se gèrent avec `definir_role()` (journalisé, jamais sur soi-même).
