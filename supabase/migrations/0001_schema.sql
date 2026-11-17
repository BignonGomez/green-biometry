-- =====================================================================
-- Green Biometry — 0001 : schéma de la base (tables, types, contraintes)
-- Conception : docs/conception/02-modele-donnees.md
-- Règle : ce fichier ne se modifie plus une fois appliqué en production ;
-- toute évolution passe par une nouvelle migration numérotée.
-- =====================================================================

create extension if not exists postgis with schema extensions;

-- ---------------------------------------------------------------------
-- Types énumérés (valeurs fermées)
-- ---------------------------------------------------------------------
create type public.role_utilisateur as enum ('contributeur', 'evaluateur', 'administrateur');
create type public.statut_compte as enum ('actif', 'suspendu');
create type public.type_organisation as enum ('ong', 'institution_publique', 'recherche', 'entreprise', 'communaute', 'autre');
create type public.role_organisation as enum ('membre', 'gestionnaire');
create type public.type_territoire as enum ('pays', 'departement', 'commune', 'zone');
create type public.niveau_acces as enum ('public', 'restreint', 'prive');
create type public.statut_publication as enum ('brouillon', 'en_revue', 'publie', 'publie_reserve', 'retire', 'archive');
create type public.statut_version as enum ('en_revue', 'publiee', 'remplacee', 'refusee');
create type public.espace_fichier as enum ('depots', 'publies');
create type public.type_soumission as enum ('nouveau_jeu', 'nouvelle_version', 'correction');
create type public.statut_soumission as enum (
  'brouillon', 'soumis', 'verification_admin', 'controle_technique', 'revue_scientifique',
  'correction_demandee', 'valide', 'publie', 'publie_reserve', 'refuse', 'retire');
create type public.action_revue as enum ('commentaire', 'changement_statut', 'demande_correction', 'decision', 'assignation');
create type public.resultat_controle as enum ('ok', 'avertissement', 'erreur');
create type public.frequence_indicateur as enum ('annuelle', 'mensuelle', 'ponctuelle');
create type public.variation_indicateur as enum ('relative', 'absolue');
create type public.nature_valeur as enum ('observee', 'estimation', 'declaree');
create type public.statut_projet as enum ('en_cours', 'termine');
create type public.niveau_suivi as enum ('activite', 'resultat', 'effet');
create type public.statut_rapport as enum ('manquant', 'soumis', 'valide');

-- ---------------------------------------------------------------------
-- Textes bilingues : JSON {"fr": "…", "en": "…"} (ADR-15)
-- ---------------------------------------------------------------------
create domain public.bilingue as jsonb
  check (value is null or jsonb_typeof(value) = 'object');

-- Vrai si les deux langues sont présentes et non vides.
create function public.bilingue_complet(t jsonb) returns boolean
language sql immutable set search_path = '' as $$
  select t is not null
     and coalesce(btrim(t ->> 'fr'), '') <> ''
     and coalesce(btrim(t ->> 'en'), '') <> ''
$$;

-- Met à jour la colonne maj_le à chaque modification.
create function public.toucher_maj_le() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.maj_le := now();
  return new;
end $$;

-- ---------------------------------------------------------------------
-- Identifiants lisibles, jamais réutilisés (ADR-16)
-- ---------------------------------------------------------------------
create sequence public.seq_jeu;
create sequence public.seq_indicateur;
create sequence public.seq_projet;
create sequence public.seq_soumission;

-- =====================================================================
-- 1. Personnes et organisations
-- =====================================================================
create table public.profils (
  id uuid primary key references auth.users (id) on delete cascade,
  nom_affiche text not null check (btrim(nom_affiche) <> ''),
  role public.role_utilisateur not null default 'contributeur',
  langue text not null default 'fr' check (langue in ('fr', 'en')),
  statut public.statut_compte not null default 'actif',
  specialites text,
  cree_le timestamptz not null default now(),
  maj_le timestamptz not null default now()
);

create table public.organisations (
  id uuid primary key default gen_random_uuid(),
  nom text not null unique check (btrim(nom) <> ''),
  type public.type_organisation not null,
  pays text check (pays ~ '^[A-Z]{2}$'),
  site_web text,
  verifiee boolean not null default false,
  cree_le timestamptz not null default now(),
  maj_le timestamptz not null default now()
);

create table public.adhesions (
  profil_id uuid not null references public.profils (id) on delete cascade,
  organisation_id uuid not null references public.organisations (id) on delete cascade,
  role_orga public.role_organisation not null default 'membre',
  depuis_le date not null default current_date,
  primary key (profil_id, organisation_id)
);

-- =====================================================================
-- 2. Référentiels
-- =====================================================================
create table public.themes (
  code text primary key check (code ~ '^[a-z][a-z0-9-]*$'),
  libelle public.bilingue not null check (public.bilingue_complet(libelle)),
  ordre int not null default 0
);

create table public.licences (
  code text primary key check (code ~ '^[a-z0-9][a-z0-9-]*$'),
  nom public.bilingue not null check (public.bilingue_complet(nom)),
  url text,
  telechargement_autorise boolean not null,
  ouverte boolean not null
);

create table public.territoires (
  id uuid primary key default gen_random_uuid(),
  code text unique,
  nom public.bilingue not null check (public.bilingue_complet(nom)),
  type public.type_territoire not null,
  pays text check (pays ~ '^[A-Z]{2}$'),
  parent_id uuid references public.territoires (id),
  geom extensions.geometry(MultiPolygon, 4326)
);

create table public.sources (
  id uuid primary key default gen_random_uuid(),
  organisme public.bilingue not null check (public.bilingue_complet(organisme)),
  url text,
  citation text,
  conditions text
);

-- =====================================================================
-- 3. Jeux de données
-- =====================================================================
create table public.jeux (
  id uuid primary key default gen_random_uuid(),
  identifiant text not null unique default ('GB-DS-' || lpad(nextval('public.seq_jeu')::text, 4, '0')),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  titre public.bilingue not null,
  resume public.bilingue,
  theme text not null references public.themes (code),
  territoire_id uuid references public.territoires (id),
  source_id uuid references public.sources (id),
  producteur public.bilingue,
  licence text not null references public.licences (code),
  acces public.niveau_acces not null default 'public',
  statut_publication public.statut_publication not null default 'brouillon',
  periode_debut int check (periode_debut between 1800 and 2200),
  periode_fin int check (periode_fin between 1800 and 2200),
  date_collecte date,
  methode public.bilingue,
  limites public.bilingue,
  resolution text,
  crs text,
  emprise extensions.geometry(Polygon, 4326),
  sensible boolean not null default false,
  organisation_id uuid references public.organisations (id),
  cree_par uuid not null references public.profils (id),
  est_demo boolean not null default false,
  cree_le timestamptz not null default now(),
  maj_le timestamptz not null default now(),
  supprime_le timestamptz,
  constraint periode_ordonnee check (periode_fin is null or periode_debut is null or periode_fin >= periode_debut)
);

create table public.variables (
  id uuid primary key default gen_random_uuid(),
  jeu_id uuid not null references public.jeux (id) on delete cascade,
  ordre int not null default 0,
  nom text not null check (btrim(nom) <> ''),
  unite public.bilingue,
  description public.bilingue not null,
  unique (jeu_id, nom)
);

create table public.versions (
  id uuid primary key default gen_random_uuid(),
  jeu_id uuid not null references public.jeux (id),
  numero text not null check (numero ~ '^[0-9]+(\.[0-9]+)*$'),
  note public.bilingue,
  statut public.statut_version not null default 'en_revue',
  auteur_id uuid not null references public.profils (id),
  cree_le timestamptz not null default now(),
  publiee_le timestamptz,
  unique (jeu_id, numero)
);

create table public.fichiers (
  id uuid primary key default gen_random_uuid(),
  version_id uuid not null references public.versions (id),
  espace public.espace_fichier not null default 'depots',
  chemin text not null unique,
  nom_original text not null,
  format text not null,
  taille bigint not null check (taille >= 0),
  empreinte_sha256 text not null check (empreinte_sha256 ~ '^[0-9a-f]{64}$'),
  depose_par uuid not null references public.profils (id),
  depose_le timestamptz not null default now()
);

-- =====================================================================
-- 4. Contribution et validation
-- =====================================================================
create table public.soumissions (
  id uuid primary key default gen_random_uuid(),
  identifiant text not null unique default ('GB-SUB-' || lpad(nextval('public.seq_soumission')::text, 4, '0')),
  type public.type_soumission not null,
  jeu_id uuid not null references public.jeux (id),
  version_id uuid references public.versions (id),
  contributeur_id uuid not null references public.profils (id),
  evaluateur_id uuid references public.profils (id),
  statut public.statut_soumission not null default 'brouillon',
  droits_declares boolean not null default false,
  declaration text,
  cree_le timestamptz not null default now(),
  soumise_le timestamptz,
  decidee_le timestamptz,
  maj_le timestamptz not null default now()
);

create table public.evenements_revue (
  id bigint generated always as identity primary key,
  soumission_id uuid not null references public.soumissions (id),
  auteur_id uuid references public.profils (id),   -- vide : action automatique
  action public.action_revue not null,
  statut_avant public.statut_soumission,
  statut_apres public.statut_soumission,
  texte text,
  cree_le timestamptz not null default now()
);

create table public.controles_qualite (
  id bigint generated always as identity primary key,
  soumission_id uuid not null references public.soumissions (id),
  fichier_id uuid references public.fichiers (id),
  regle text not null,
  resultat public.resultat_controle not null,
  detail jsonb,
  execute_le timestamptz not null default now()
);

-- =====================================================================
-- 5. Indicateurs
-- =====================================================================
create table public.indicateurs (
  id uuid primary key default gen_random_uuid(),
  identifiant text not null unique default ('GB-IND-' || lpad(nextval('public.seq_indicateur')::text, 4, '0')),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  titre public.bilingue not null,
  resume public.bilingue,
  definition public.bilingue,
  methode public.bilingue,
  limites public.bilingue,
  theme text not null references public.themes (code),
  territoire_id uuid references public.territoires (id),
  unite public.bilingue not null,
  decimales int not null default 0 check (decimales between 0 and 6),
  frequence public.frequence_indicateur not null,
  variation public.variation_indicateur not null default 'relative',
  jeu_source_id uuid references public.jeux (id),
  responsable_id uuid references public.profils (id),
  statut_publication public.statut_publication not null default 'brouillon',
  est_demo boolean not null default false,
  cree_le timestamptz not null default now(),
  maj_le timestamptz not null default now(),
  supprime_le timestamptz
);

create table public.valeurs_indicateur (
  id uuid primary key default gen_random_uuid(),
  indicateur_id uuid not null references public.indicateurs (id) on delete cascade,
  territoire_id uuid references public.territoires (id),
  periode text not null check (periode ~ '^[0-9]{4}(-[0-9]{2})?$'),
  valeur numeric,
  nature public.nature_valeur,
  motif_absence public.bilingue,
  source_id uuid references public.sources (id),
  unique (indicateur_id, territoire_id, periode),
  -- Une valeur manquante est montrée, jamais comblée : elle doit dire pourquoi.
  constraint valeur_ou_motif check (
    (valeur is not null and nature is not null) or (valeur is null and nature is null and motif_absence is not null))
);

-- =====================================================================
-- 6. Projets
-- =====================================================================
create table public.projets (
  id uuid primary key default gen_random_uuid(),
  identifiant text not null unique default ('GB-PRJ-' || lpad(nextval('public.seq_projet')::text, 4, '0')),
  slug text not null unique check (slug ~ '^[a-z0-9]+(-[a-z0-9]+)*$'),
  titre public.bilingue not null,
  resume public.bilingue,
  objectif public.bilingue,
  theme text not null references public.themes (code),
  territoire_id uuid references public.territoires (id),
  statut public.statut_projet not null default 'en_cours',
  debut int not null check (debut between 1900 and 2200),
  fin int check (fin between 1900 and 2200),
  porteur_organisation_id uuid references public.organisations (id),
  visibilite public.niveau_acces not null default 'public',
  statut_publication public.statut_publication not null default 'brouillon',
  gestionnaire_id uuid not null references public.profils (id),
  est_demo boolean not null default false,
  cree_le timestamptz not null default now(),
  maj_le timestamptz not null default now(),
  supprime_le timestamptz,
  constraint projet_dates check (fin is null or fin >= debut)
);

create table public.projets_partenaires (
  projet_id uuid not null references public.projets (id) on delete cascade,
  organisation_id uuid not null references public.organisations (id),
  primary key (projet_id, organisation_id)
);

create table public.projets_jeux (
  projet_id uuid not null references public.projets (id) on delete cascade,
  jeu_id uuid not null references public.jeux (id),
  primary key (projet_id, jeu_id)
);

create table public.suivis_projet (
  id uuid primary key default gen_random_uuid(),
  projet_id uuid not null references public.projets (id) on delete cascade,
  titre public.bilingue not null,
  niveau public.niveau_suivi not null,
  unite public.bilingue not null,
  decimales int not null default 0 check (decimales between 0 and 6),
  indicateur_id uuid references public.indicateurs (id),
  reference_valeur numeric,
  reference_periode text check (reference_periode ~ '^[0-9]{4}(-[0-9]{2})?$'),
  cible_valeur numeric not null,
  cible_periode text not null check (cible_periode ~ '^[0-9]{4}(-[0-9]{2})?$'),
  note public.bilingue,
  ordre int not null default 0,
  constraint reference_complete check ((reference_valeur is null) = (reference_periode is null))
);

create table public.rapports_projet (
  id uuid primary key default gen_random_uuid(),
  projet_id uuid not null references public.projets (id) on delete cascade,
  periode text not null check (periode ~ '^[0-9]{4}(-[0-9]{2})?$'),
  statut public.statut_rapport not null default 'manquant',
  depose_le timestamptz,
  fichier_id uuid references public.fichiers (id),
  unique (projet_id, periode)
);

create table public.mesures_projet (
  id uuid primary key default gen_random_uuid(),
  suivi_id uuid not null references public.suivis_projet (id) on delete cascade,
  periode text not null check (periode ~ '^[0-9]{4}(-[0-9]{2})?$'),
  valeur numeric,
  nature public.nature_valeur,
  rapport_id uuid references public.rapports_projet (id),
  unique (suivi_id, periode),
  constraint mesure_coherente check ((valeur is null) = (nature is null))
);

create table public.activites_projet (
  id uuid primary key default gen_random_uuid(),
  projet_id uuid not null references public.projets (id) on delete cascade,
  libelle public.bilingue not null,
  valeur numeric not null,
  unite public.bilingue not null,
  ordre int not null default 0
);

-- =====================================================================
-- 7. Suivi et audit
-- =====================================================================
create table public.journal_audit (
  id bigint generated always as identity primary key,
  acteur_id uuid,
  action text not null,
  objet_type text not null,
  objet_id text not null,
  details jsonb,
  resultat text not null default 'ok',
  cree_le timestamptz not null default now()
);

create table public.telechargements (
  id bigint generated always as identity primary key,
  jeu_id uuid not null references public.jeux (id),
  version_id uuid not null references public.versions (id),
  profil_id uuid references public.profils (id),
  cree_le timestamptz not null default now()
);

-- ---------------------------------------------------------------------
-- Index utiles aux règles d'accès et aux pages
-- ---------------------------------------------------------------------
create index on public.jeux (statut_publication, acces) where supprime_le is null;
create index on public.jeux (organisation_id);
create index on public.jeux (cree_par);
create index on public.versions (jeu_id);
create index on public.fichiers (version_id);
create index on public.soumissions (contributeur_id);
create index on public.soumissions (evaluateur_id);
create index on public.soumissions (jeu_id);
create index on public.evenements_revue (soumission_id);
create index on public.controles_qualite (soumission_id);
create index on public.valeurs_indicateur (indicateur_id);
create index on public.suivis_projet (projet_id);
create index on public.adhesions (organisation_id);

-- maj_le automatique
create trigger maj_le before update on public.profils for each row execute function public.toucher_maj_le();
create trigger maj_le before update on public.organisations for each row execute function public.toucher_maj_le();
create trigger maj_le before update on public.jeux for each row execute function public.toucher_maj_le();
create trigger maj_le before update on public.soumissions for each row execute function public.toucher_maj_le();
create trigger maj_le before update on public.indicateurs for each row execute function public.toucher_maj_le();
create trigger maj_le before update on public.projets for each row execute function public.toucher_maj_le();
