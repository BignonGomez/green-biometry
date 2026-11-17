-- =====================================================================
-- Green Biometry — 0002 : sécurité (droits, règles par ligne, circuit de validation)
-- Conception : docs/conception/02-modele-donnees.md, § 4 à 6. ADR-13.
-- Principe : on retire tout, puis on accorde explicitement table par table.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 1. Fonctions d'aide utilisées par les règles
--    SECURITY DEFINER : elles lisent profils et adhésions sans être
--    bloquées par leurs propres règles. search_path vide : pas de détournement.
-- ---------------------------------------------------------------------
create function public.mon_role() returns public.role_utilisateur
language sql stable security definer set search_path = '' as $$
  select p.role from public.profils p where p.id = auth.uid() and p.statut = 'actif'
$$;

create function public.est_admin() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce(public.mon_role() = 'administrateur', false)
$$;

create function public.est_evaluateur() returns boolean
language sql stable security definer set search_path = '' as $$
  select coalesce(public.mon_role() in ('evaluateur', 'administrateur'), false)
$$;

create function public.membre_de(p_organisation uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.adhesions a
    join public.profils p on p.id = a.profil_id
    where a.organisation_id = p_organisation and a.profil_id = auth.uid() and p.statut = 'actif')
$$;

-- L'évaluateur assigné à une soumission (envoyée) de ce jeu.
create function public.evalue_le_jeu(p_jeu uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.soumissions s
    where s.jeu_id = p_jeu and s.evaluateur_id = auth.uid() and s.statut <> 'brouillon')
$$;

-- Le contributeur peut modifier la fiche tant qu'elle n'est pas publiée
-- et qu'aucune soumission de ce jeu n'est en cours d'examen.
create function public.jeu_modifiable(p_jeu uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.jeux j
    where j.id = p_jeu and j.supprime_le is null
      and j.statut_publication in ('brouillon', 'en_revue')
      and not exists (
        select 1 from public.soumissions s
        where s.jeu_id = j.id
          and s.statut in ('soumis', 'verification_admin', 'controle_technique', 'revue_scientifique', 'valide')))
$$;

-- Le contributeur peut déposer pour ce jeu : il l'a créé, ou il est membre de l'organisation détentrice.
create function public.peut_contribuer(p_jeu uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  select exists (
    select 1 from public.jeux j
    where j.id = p_jeu and j.supprime_le is null
      and (j.cree_par = auth.uid() or (j.organisation_id is not null and public.membre_de(j.organisation_id))))
$$;

-- Écriture dans le journal d'audit : uniquement depuis les fonctions de la base.
create function public.ecrire_audit(p_action text, p_objet_type text, p_objet_id text, p_details jsonb default null)
returns void language sql security definer set search_path = '' as $$
  insert into public.journal_audit (acteur_id, action, objet_type, objet_id, details)
  values (auth.uid(), p_action, p_objet_type, p_objet_id, p_details)
$$;

-- Champs obligatoires manquants pour publier un jeu (EF-04, ADR-15). Tableau vide = complet.
create function public.jeu_manquants(p_jeu uuid) returns text[]
language plpgsql stable security definer set search_path = '' as $$
declare
  j public.jeux%rowtype;
  manque text[] := '{}';
begin
  select * into j from public.jeux where id = p_jeu;
  if not found then
    return array['jeu'];
  end if;
  if not public.bilingue_complet(j.titre) then manque := array_append(manque, 'titre'); end if;
  if not public.bilingue_complet(j.resume) then manque := array_append(manque, 'resume'); end if;
  if not public.bilingue_complet(j.producteur) then manque := array_append(manque, 'producteur'); end if;
  if not public.bilingue_complet(j.methode) then manque := array_append(manque, 'methode'); end if;
  if not public.bilingue_complet(j.limites) then manque := array_append(manque, 'limites'); end if;
  if j.periode_debut is null or j.periode_fin is null then manque := array_append(manque, 'periode'); end if;
  if j.territoire_id is null then manque := array_append(manque, 'territoire'); end if;
  if j.emprise is null then manque := array_append(manque, 'emprise'); end if;
  if coalesce(btrim(j.resolution), '') = '' then manque := array_append(manque, 'resolution'); end if;
  if coalesce(btrim(j.crs), '') = '' then manque := array_append(manque, 'crs'); end if;
  if not exists (select 1 from public.variables v where v.jeu_id = p_jeu) then
    manque := array_append(manque, 'variables');
  elsif exists (select 1 from public.variables v where v.jeu_id = p_jeu and not public.bilingue_complet(v.description)) then
    manque := array_append(manque, 'description_variables');
  end if;
  return manque;
end $$;

-- ---------------------------------------------------------------------
-- 2. Création automatique du profil à l'inscription
-- ---------------------------------------------------------------------
create function public.creer_profil() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profils (id, nom_affiche, langue)
  values (
    new.id,
    coalesce(nullif(btrim(new.raw_user_meta_data ->> 'nom_affiche'), ''), split_part(new.email, '@', 1)),
    case when new.raw_user_meta_data ->> 'langue' = 'en' then 'en' else 'fr' end);
  return new;
end $$;

create trigger creer_profil after insert on auth.users
  for each row execute function public.creer_profil();

-- ---------------------------------------------------------------------
-- 3. Circuit de validation : seule façon de changer le statut d'une soumission
-- ---------------------------------------------------------------------
create function public.changer_statut(
  p_soumission uuid,
  p_statut public.statut_soumission,
  p_texte text default null
) returns public.statut_soumission
language plpgsql security definer set search_path = '' as $$
declare
  s public.soumissions%rowtype;
  r public.role_utilisateur := public.mon_role();
  systeme boolean := coalesce(auth.role() = 'service_role', false);
  admin boolean := coalesce(r = 'administrateur', false);
  evaluateur_assigne boolean;
  autorise boolean := false;
  manque text[];
  action public.action_revue;
begin
  select * into s from public.soumissions where id = p_soumission for update;
  if not found then
    raise exception 'Soumission introuvable.' using errcode = 'P0002';
  end if;
  evaluateur_assigne := coalesce(r = 'evaluateur' and s.evaluateur_id = auth.uid(), false);

  -- Transitions autorisées et qui peut les faire (conception, § 4)
  autorise := case
    when s.statut in ('brouillon', 'correction_demandee') and p_statut = 'soumis'
      then s.contributeur_id = auth.uid()
    when s.statut = 'soumis' and p_statut = 'verification_admin'
      then admin
    when s.statut = 'verification_admin' and p_statut in ('controle_technique', 'correction_demandee', 'refuse')
      then admin
    when s.statut = 'controle_technique' and p_statut in ('revue_scientifique', 'correction_demandee')
      then admin or systeme
    when s.statut = 'revue_scientifique' and p_statut in ('valide', 'correction_demandee', 'refuse')
      then admin or evaluateur_assigne
    when s.statut = 'revue_scientifique' and p_statut = 'publie_reserve'
      then admin
    when s.statut = 'valide' and p_statut = 'publie'
      then admin
    when s.statut = 'publie_reserve' and p_statut = 'publie'
      then admin or evaluateur_assigne
    when s.statut in ('publie', 'publie_reserve') and p_statut = 'retire'
      then admin
    else false
  end;
  if not autorise then
    raise exception 'Transition non autorisée : % → %.', s.statut, p_statut using errcode = '42501';
  end if;

  -- Conditions de chaque transition
  if p_statut = 'soumis' then
    if not s.droits_declares then
      raise exception 'Déclarez que vous avez le droit de partager ces données avant d''envoyer.' using errcode = '23514';
    end if;
    if s.version_id is null or not exists (select 1 from public.fichiers f where f.version_id = s.version_id) then
      raise exception 'Ajoutez au moins un fichier avant d''envoyer.' using errcode = '23514';
    end if;
  end if;
  if p_statut in ('correction_demandee', 'refuse', 'retire') and coalesce(btrim(p_texte), '') = '' then
    raise exception 'Indiquez le motif : il sera envoyé au contributeur.' using errcode = '23514';
  end if;
  if p_statut in ('publie', 'publie_reserve') then
    manque := public.jeu_manquants(s.jeu_id);
    if cardinality(manque) > 0 then
      raise exception 'Fiche incomplète, champs manquants : %.', array_to_string(manque, ', ') using errcode = '23514';
    end if;
  end if;

  -- Effets
  update public.soumissions set
    statut = p_statut,
    soumise_le = case when p_statut = 'soumis' then now() else soumise_le end,
    decidee_le = case when p_statut in ('valide', 'publie', 'publie_reserve', 'refuse')
                      then coalesce(decidee_le, now()) else decidee_le end
  where id = s.id;

  if p_statut = 'soumis' then
    update public.jeux set statut_publication = 'en_revue' where id = s.jeu_id and statut_publication = 'brouillon';
  elsif p_statut in ('publie', 'publie_reserve') then
    update public.versions set statut = 'remplacee'
      where jeu_id = s.jeu_id and statut = 'publiee' and id <> s.version_id;
    update public.versions set statut = 'publiee', publiee_le = coalesce(publiee_le, now()) where id = s.version_id;
    update public.jeux set statut_publication = p_statut::text::public.statut_publication where id = s.jeu_id;
  elsif p_statut = 'refuse' then
    update public.versions set statut = 'refusee' where id = s.version_id;
    update public.jeux set statut_publication = 'brouillon'
      where id = s.jeu_id and statut_publication = 'en_revue'
        and not exists (select 1 from public.versions v where v.jeu_id = s.jeu_id and v.statut = 'publiee');
  elsif p_statut = 'retire' then
    update public.jeux set statut_publication = 'retire' where id = s.jeu_id;
  end if;

  action := case
    when p_statut = 'correction_demandee' then 'demande_correction'
    when p_statut in ('valide', 'publie', 'publie_reserve', 'refuse', 'retire') then 'decision'
    else 'changement_statut' end;
  insert into public.evenements_revue (soumission_id, auteur_id, action, statut_avant, statut_apres, texte)
  values (s.id, auth.uid(), action, s.statut, p_statut, nullif(btrim(p_texte), ''));
  perform public.ecrire_audit('changer_statut', 'soumission', s.id::text,
    jsonb_build_object('de', s.statut, 'vers', p_statut, 'systeme', systeme));
  return p_statut;
end $$;

-- L'administrateur désigne l'évaluateur (décision du 17 novembre 2026).
create function public.assigner_evaluateur(p_soumission uuid, p_evaluateur uuid) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.est_admin() then
    raise exception 'Réservé aux administrateurs.' using errcode = '42501';
  end if;
  if not exists (select 1 from public.profils p where p.id = p_evaluateur and p.role in ('evaluateur', 'administrateur') and p.statut = 'actif') then
    raise exception 'Cette personne n''est pas évaluatrice.' using errcode = '23514';
  end if;
  if exists (select 1 from public.soumissions s where s.id = p_soumission and s.contributeur_id = p_evaluateur) then
    raise exception 'Un contributeur ne peut pas évaluer sa propre soumission.' using errcode = '23514';
  end if;
  update public.soumissions set evaluateur_id = p_evaluateur where id = p_soumission;
  if not found then
    raise exception 'Soumission introuvable.' using errcode = 'P0002';
  end if;
  insert into public.evenements_revue (soumission_id, auteur_id, action, texte)
  values (p_soumission, auth.uid(), 'assignation', null);
  perform public.ecrire_audit('assigner_evaluateur', 'soumission', p_soumission::text, jsonb_build_object('evaluateur', p_evaluateur));
end $$;

-- Changement de rôle : administrateurs seulement, et jamais sur soi-même.
create function public.definir_role(p_profil uuid, p_role public.role_utilisateur) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.est_admin() then
    raise exception 'Réservé aux administrateurs.' using errcode = '42501';
  end if;
  if p_profil = auth.uid() then
    raise exception 'Un administrateur ne peut pas changer son propre rôle.' using errcode = '42501';
  end if;
  update public.profils set role = p_role where id = p_profil;
  perform public.ecrire_audit('definir_role', 'profil', p_profil::text, jsonb_build_object('role', p_role));
end $$;

-- Publication d'un indicateur ou d'un projet (administrateurs).
create function public.definir_publication(p_objet text, p_id uuid, p_statut public.statut_publication) returns void
language plpgsql security definer set search_path = '' as $$
begin
  if not public.est_admin() then
    raise exception 'Réservé aux administrateurs.' using errcode = '42501';
  end if;
  if p_objet = 'indicateur' then
    if p_statut in ('publie', 'publie_reserve') and exists (
      select 1 from public.indicateurs i where i.id = p_id
        and not (public.bilingue_complet(i.titre) and public.bilingue_complet(i.definition)
                 and public.bilingue_complet(i.methode) and public.bilingue_complet(i.limites)
                 and public.bilingue_complet(i.unite))) then
      raise exception 'Fiche indicateur incomplète (titre, définition, méthode, limites, unité dans les deux langues).' using errcode = '23514';
    end if;
    update public.indicateurs set statut_publication = p_statut where id = p_id;
  elsif p_objet = 'projet' then
    if p_statut in ('publie', 'publie_reserve') and (
      exists (select 1 from public.projets p where p.id = p_id
                and not (public.bilingue_complet(p.titre) and public.bilingue_complet(p.resume) and public.bilingue_complet(p.objectif)))
      or (select count(*) from public.suivis_projet s where s.projet_id = p_id) < 2) then
      raise exception 'Fiche projet incomplète : titre, résumé, objectif dans les deux langues et au moins 2 indicateurs suivis.' using errcode = '23514';
    end if;
    update public.projets set statut_publication = p_statut where id = p_id;
  else
    raise exception 'Objet inconnu : %.', p_objet using errcode = '22023';
  end if;
  if not found then
    raise exception 'Introuvable.' using errcode = 'P0002';
  end if;
  perform public.ecrire_audit('definir_publication', p_objet, p_id::text, jsonb_build_object('statut', p_statut));
end $$;

-- ---------------------------------------------------------------------
-- 4. Droits d'accès : on retire tout, puis on accorde explicitement
--    (les projets Supabase récents n'exposent plus les tables par défaut).
-- ---------------------------------------------------------------------
grant usage on schema public to anon, authenticated, service_role;
revoke all on all tables in schema public from anon, authenticated;
revoke all on all sequences in schema public from anon, authenticated;
revoke execute on all functions in schema public from public, anon, authenticated;

grant all on all tables in schema public to service_role;
grant all on all sequences in schema public to service_role;
grant execute on all functions in schema public to service_role;

-- Fonctions utilisées dans les règles (évaluées avec les droits de la personne)
grant execute on function public.bilingue_complet(jsonb), public.mon_role(), public.est_admin(),
  public.est_evaluateur(), public.membre_de(uuid), public.evalue_le_jeu(uuid), public.jeu_modifiable(uuid),
  public.peut_contribuer(uuid) to anon, authenticated;
-- Actions ouvertes aux personnes connectées (chacune vérifie le rôle elle-même)
grant execute on function public.changer_statut(uuid, public.statut_soumission, text),
  public.assigner_evaluateur(uuid, uuid), public.definir_role(uuid, public.role_utilisateur),
  public.definir_publication(text, uuid, public.statut_publication), public.jeu_manquants(uuid) to authenticated;

-- Identifiants lisibles : les valeurs par défaut lisent les séquences
grant usage on sequence public.seq_jeu, public.seq_soumission, public.seq_projet, public.seq_indicateur to authenticated;

-- Lecture publique (les règles filtrent ensuite ligne par ligne)
grant select on public.themes, public.licences, public.territoires, public.sources, public.organisations,
  public.jeux, public.variables, public.versions, public.fichiers,
  public.indicateurs, public.valeurs_indicateur,
  public.projets, public.projets_partenaires, public.projets_jeux, public.suivis_projet,
  public.rapports_projet, public.mesures_projet, public.activites_projet
  to anon, authenticated;
grant select on public.profils, public.adhesions, public.soumissions, public.evenements_revue,
  public.controles_qualite, public.journal_audit, public.telechargements to authenticated;

-- Écritures (colonnes protégées exclues : statut, identifiant, auteur, démonstration, suppression)
grant insert, update on public.themes, public.licences, public.territoires, public.sources,
  public.organisations, public.adhesions to authenticated;
grant update (nom_affiche, langue, specialites) on public.profils to authenticated;
grant insert (slug, titre, resume, theme, territoire_id, source_id, producteur, licence, acces, periode_debut,
  periode_fin, date_collecte, methode, limites, resolution, crs, emprise, sensible, organisation_id, cree_par)
  on public.jeux to authenticated;
grant update (slug, titre, resume, theme, territoire_id, source_id, producteur, licence, acces, periode_debut,
  periode_fin, date_collecte, methode, limites, resolution, crs, emprise, sensible, organisation_id)
  on public.jeux to authenticated;
grant insert, update, delete on public.variables to authenticated;
grant insert (jeu_id, numero, note, auteur_id) on public.versions to authenticated;
grant update (numero, note) on public.versions to authenticated;
grant insert (version_id, chemin, nom_original, format, taille, empreinte_sha256, depose_par) on public.fichiers to authenticated;
grant insert (type, jeu_id, version_id, contributeur_id, droits_declares, declaration) on public.soumissions to authenticated;
grant update (version_id, droits_declares, declaration) on public.soumissions to authenticated;
grant insert (soumission_id, auteur_id, action, texte) on public.evenements_revue to authenticated;
grant insert (slug, titre, resume, definition, methode, limites, theme, territoire_id, unite, decimales, frequence,
  variation, jeu_source_id, responsable_id) on public.indicateurs to authenticated;
grant update (slug, titre, resume, definition, methode, limites, theme, territoire_id, unite, decimales, frequence,
  variation, jeu_source_id, responsable_id) on public.indicateurs to authenticated;
grant insert, update, delete on public.valeurs_indicateur to authenticated;
grant insert (slug, titre, resume, objectif, theme, territoire_id, statut, debut, fin, porteur_organisation_id,
  visibilite, gestionnaire_id) on public.projets to authenticated;
grant update (slug, titre, resume, objectif, theme, territoire_id, statut, debut, fin, porteur_organisation_id,
  visibilite) on public.projets to authenticated;
grant insert, update, delete on public.projets_partenaires, public.projets_jeux, public.suivis_projet,
  public.rapports_projet, public.mesures_projet, public.activites_projet to authenticated;

-- ---------------------------------------------------------------------
-- 5. Règles par ligne (toutes les tables)
-- ---------------------------------------------------------------------
alter table public.profils enable row level security;
alter table public.organisations enable row level security;
alter table public.adhesions enable row level security;
alter table public.themes enable row level security;
alter table public.licences enable row level security;
alter table public.territoires enable row level security;
alter table public.sources enable row level security;
alter table public.jeux enable row level security;
alter table public.variables enable row level security;
alter table public.versions enable row level security;
alter table public.fichiers enable row level security;
alter table public.soumissions enable row level security;
alter table public.evenements_revue enable row level security;
alter table public.controles_qualite enable row level security;
alter table public.indicateurs enable row level security;
alter table public.valeurs_indicateur enable row level security;
alter table public.projets enable row level security;
alter table public.projets_partenaires enable row level security;
alter table public.projets_jeux enable row level security;
alter table public.suivis_projet enable row level security;
alter table public.rapports_projet enable row level security;
alter table public.mesures_projet enable row level security;
alter table public.activites_projet enable row level security;
alter table public.journal_audit enable row level security;
alter table public.telechargements enable row level security;

-- Personnes et organisations
create policy profils_lecture on public.profils for select to authenticated
  using (id = auth.uid() or public.est_admin());
create policy profils_modif on public.profils for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid());

create policy organisations_lecture on public.organisations for select to anon, authenticated using (true);
create policy organisations_ajout on public.organisations for insert to authenticated with check (public.est_admin());
create policy organisations_modif on public.organisations for update to authenticated
  using (public.est_admin()) with check (public.est_admin());

create policy adhesions_lecture on public.adhesions for select to authenticated
  using (profil_id = auth.uid() or public.est_admin());
create policy adhesions_ajout on public.adhesions for insert to authenticated with check (public.est_admin());
create policy adhesions_modif on public.adhesions for update to authenticated
  using (public.est_admin()) with check (public.est_admin());

-- Référentiels : lecture libre, écriture par les administrateurs
create policy themes_lecture on public.themes for select to anon, authenticated using (true);
create policy themes_ajout on public.themes for insert to authenticated with check (public.est_admin());
create policy themes_modif on public.themes for update to authenticated using (public.est_admin()) with check (public.est_admin());
create policy licences_lecture on public.licences for select to anon, authenticated using (true);
create policy licences_ajout on public.licences for insert to authenticated with check (public.est_admin());
create policy licences_modif on public.licences for update to authenticated using (public.est_admin()) with check (public.est_admin());
create policy territoires_lecture on public.territoires for select to anon, authenticated using (true);
create policy territoires_ajout on public.territoires for insert to authenticated with check (public.est_admin());
create policy territoires_modif on public.territoires for update to authenticated using (public.est_admin()) with check (public.est_admin());
create policy sources_lecture on public.sources for select to anon, authenticated using (true);
create policy sources_ajout on public.sources for insert to authenticated with check (public.est_admin());
create policy sources_modif on public.sources for update to authenticated using (public.est_admin()) with check (public.est_admin());

-- Jeux de données (conception, § 5)
create policy jeux_lecture on public.jeux for select to anon, authenticated using (
  (supprime_le is null and statut_publication in ('publie', 'publie_reserve') and acces = 'public')
  or (auth.uid() is not null and (
       cree_par = auth.uid()
    or public.est_admin()
    or public.evalue_le_jeu(id)
    or (supprime_le is null and statut_publication in ('publie', 'publie_reserve') and (
          (organisation_id is not null and public.membre_de(organisation_id))
       or (acces = 'restreint' and public.est_evaluateur()))))));
create policy jeux_ajout on public.jeux for insert to authenticated with check (
  cree_par = auth.uid()
  and (organisation_id is null or public.membre_de(organisation_id) or public.est_admin()));
create policy jeux_modif on public.jeux for update to authenticated
  using (public.est_admin() or (cree_par = auth.uid() and public.jeu_modifiable(id)))
  with check (public.est_admin() or (cree_par = auth.uid() and (organisation_id is null or public.membre_de(organisation_id))));

-- Les éléments d'un jeu suivent la visibilité du jeu (la sous-requête applique la règle de jeux)
create policy variables_lecture on public.variables for select to anon, authenticated
  using (exists (select 1 from public.jeux j where j.id = jeu_id));
create policy variables_ecriture on public.variables for all to authenticated
  using (public.est_admin() or (public.peut_contribuer(jeu_id) and public.jeu_modifiable(jeu_id)))
  with check (public.est_admin() or (public.peut_contribuer(jeu_id) and public.jeu_modifiable(jeu_id)));

create policy versions_lecture on public.versions for select to anon, authenticated using (
  exists (select 1 from public.jeux j where j.id = jeu_id)
  and (statut = 'publiee' or auteur_id = auth.uid() or public.est_admin()
       or public.evalue_le_jeu(jeu_id) or public.peut_contribuer(jeu_id)));
create policy versions_ajout on public.versions for insert to authenticated
  with check (auteur_id = auth.uid() and public.peut_contribuer(jeu_id));
create policy versions_modif on public.versions for update to authenticated
  using (auteur_id = auth.uid() and statut = 'en_revue' and public.jeu_modifiable(jeu_id))
  with check (auteur_id = auth.uid() and statut = 'en_revue');

create policy fichiers_lecture on public.fichiers for select to anon, authenticated
  using (exists (select 1 from public.versions v where v.id = version_id));
create policy fichiers_ajout on public.fichiers for insert to authenticated with check (
  depose_par = auth.uid()
  and exists (select 1 from public.versions v where v.id = version_id and v.auteur_id = auth.uid() and v.statut = 'en_revue'));

-- Soumissions et revue
create policy soumissions_lecture on public.soumissions for select to authenticated
  using (contributeur_id = auth.uid() or evaluateur_id = auth.uid() or public.est_admin());
create policy soumissions_ajout on public.soumissions for insert to authenticated
  with check (contributeur_id = auth.uid() and public.peut_contribuer(jeu_id));
create policy soumissions_modif on public.soumissions for update to authenticated
  using (contributeur_id = auth.uid() and statut in ('brouillon', 'correction_demandee'))
  with check (contributeur_id = auth.uid() and statut in ('brouillon', 'correction_demandee'));

create policy evenements_lecture on public.evenements_revue for select to authenticated
  using (exists (select 1 from public.soumissions s where s.id = soumission_id));
create policy evenements_commentaire on public.evenements_revue for insert to authenticated
  with check (auteur_id = auth.uid() and action = 'commentaire'
              and exists (select 1 from public.soumissions s where s.id = soumission_id));

create policy controles_lecture on public.controles_qualite for select to authenticated
  using (exists (select 1 from public.soumissions s where s.id = soumission_id));

-- Indicateurs
create policy indicateurs_lecture on public.indicateurs for select to anon, authenticated using (
  (supprime_le is null and statut_publication in ('publie', 'publie_reserve'))
  or (auth.uid() is not null and (public.est_admin() or responsable_id = auth.uid())));
create policy indicateurs_ajout on public.indicateurs for insert to authenticated with check (public.est_admin());
create policy indicateurs_modif on public.indicateurs for update to authenticated
  using (public.est_admin() or responsable_id = auth.uid())
  with check (public.est_admin() or responsable_id = auth.uid());

create policy valeurs_lecture on public.valeurs_indicateur for select to anon, authenticated
  using (exists (select 1 from public.indicateurs i where i.id = indicateur_id));
create policy valeurs_ecriture on public.valeurs_indicateur for all to authenticated
  using (exists (select 1 from public.indicateurs i where i.id = indicateur_id
                 and (public.est_admin() or i.responsable_id = auth.uid())))
  with check (exists (select 1 from public.indicateurs i where i.id = indicateur_id
                      and (public.est_admin() or i.responsable_id = auth.uid())));

-- Projets
create policy projets_lecture on public.projets for select to anon, authenticated using (
  (supprime_le is null and statut_publication in ('publie', 'publie_reserve') and visibilite = 'public')
  or (auth.uid() is not null and (
       gestionnaire_id = auth.uid()
    or public.est_admin()
    or (supprime_le is null and statut_publication in ('publie', 'publie_reserve') and (
          (porteur_organisation_id is not null and public.membre_de(porteur_organisation_id))
       or (visibilite = 'restreint' and public.est_evaluateur()))))));
create policy projets_ajout on public.projets for insert to authenticated
  with check (gestionnaire_id = auth.uid()
              and (porteur_organisation_id is null or public.membre_de(porteur_organisation_id) or public.est_admin()));
create policy projets_modif on public.projets for update to authenticated
  using (public.est_admin() or gestionnaire_id = auth.uid())
  with check (public.est_admin() or gestionnaire_id = auth.uid());

-- Éléments d'un projet : visibles si le projet l'est ; modifiables par son gestionnaire ou un administrateur
create policy partenaires_lecture on public.projets_partenaires for select to anon, authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id));
create policy partenaires_ecriture on public.projets_partenaires for all to authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));
create policy projets_jeux_lecture on public.projets_jeux for select to anon, authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id) and exists (select 1 from public.jeux j where j.id = jeu_id));
create policy projets_jeux_ecriture on public.projets_jeux for all to authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));
create policy suivis_lecture on public.suivis_projet for select to anon, authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id));
create policy suivis_ecriture on public.suivis_projet for all to authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));
create policy rapports_lecture on public.rapports_projet for select to anon, authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id));
create policy rapports_ecriture on public.rapports_projet for all to authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));
create policy activites_lecture on public.activites_projet for select to anon, authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id));
create policy activites_ecriture on public.activites_projet for all to authenticated
  using (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.projets p where p.id = projet_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));
create policy mesures_lecture on public.mesures_projet for select to anon, authenticated
  using (exists (select 1 from public.suivis_projet s where s.id = suivi_id));
create policy mesures_ecriture on public.mesures_projet for all to authenticated
  using (exists (select 1 from public.suivis_projet s join public.projets p on p.id = s.projet_id
                 where s.id = suivi_id and (p.gestionnaire_id = auth.uid() or public.est_admin())))
  with check (exists (select 1 from public.suivis_projet s join public.projets p on p.id = s.projet_id
                      where s.id = suivi_id and (p.gestionnaire_id = auth.uid() or public.est_admin())));

-- Journal et téléchargements : lecture par les administrateurs ; écriture par les fonctions seulement
create policy audit_lecture on public.journal_audit for select to authenticated using (public.est_admin());
create policy telechargements_lecture on public.telechargements for select to authenticated using (public.est_admin());
