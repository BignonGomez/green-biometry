-- =====================================================================
-- Green Biometry — référentiels de départ (thèmes, licences, territoires)
-- Rejouable : chaque insertion ignore les lignes déjà présentes.
-- Les géométries des territoires seront importées à part (fichiers officiels).
-- =====================================================================

insert into public.themes (code, libelle, ordre) values
  ('forets',       '{"fr": "Forêts", "en": "Forests"}', 1),
  ('restauration', '{"fr": "Restauration", "en": "Restoration"}', 2),
  ('sols',         '{"fr": "Occupation des sols", "en": "Land cover"}', 3),
  ('eau',          '{"fr": "Eau", "en": "Water"}', 4),
  ('climat',       '{"fr": "Climat", "en": "Climate"}', 5),
  ('biodiversite', '{"fr": "Biodiversité", "en": "Biodiversity"}', 6)
on conflict (code) do nothing;

insert into public.licences (code, nom, url, telechargement_autorise, ouverte) values
  ('cc-by-4',    '{"fr": "CC BY 4.0", "en": "CC BY 4.0"}', 'https://creativecommons.org/licenses/by/4.0/', true, true),
  ('cc-by-sa-4', '{"fr": "CC BY-SA 4.0", "en": "CC BY-SA 4.0"}', 'https://creativecommons.org/licenses/by-sa/4.0/', true, true),
  ('cc0',        '{"fr": "CC0 (domaine public)", "en": "CC0 (public domain)"}', 'https://creativecommons.org/publicdomain/zero/1.0/', true, true),
  ('odbl',       '{"fr": "ODbL 1.0", "en": "ODbL 1.0"}', 'https://opendatacommons.org/licenses/odbl/1-0/', true, true),
  ('conditions-source', '{"fr": "Conditions de la source", "en": "Source terms"}', null, false, false)
on conflict (code) do nothing;

-- Territoires : Bénin, ses 12 départements (codes ISO 3166-2:BJ), la commune pilote, l'Afrique de l'Ouest.
insert into public.territoires (code, nom, type, pays) values
  ('BJ', '{"fr": "Bénin", "en": "Benin"}', 'pays', 'BJ'),
  ('WA', '{"fr": "Afrique de l''Ouest", "en": "West Africa"}', 'zone', null)
on conflict (code) do nothing;

insert into public.territoires (code, nom, type, pays, parent_id)
select d.code, d.nom::jsonb, 'departement', 'BJ', (select id from public.territoires where code = 'BJ')
from (values
  ('BJ-AL', '{"fr": "Alibori", "en": "Alibori"}'),
  ('BJ-AK', '{"fr": "Atacora", "en": "Atakora"}'),
  ('BJ-AQ', '{"fr": "Atlantique", "en": "Atlantique"}'),
  ('BJ-BO', '{"fr": "Borgou", "en": "Borgou"}'),
  ('BJ-CO', '{"fr": "Collines", "en": "Collines"}'),
  ('BJ-KO', '{"fr": "Couffo", "en": "Kouffo"}'),
  ('BJ-DO', '{"fr": "Donga", "en": "Donga"}'),
  ('BJ-LI', '{"fr": "Littoral", "en": "Littoral"}'),
  ('BJ-MO', '{"fr": "Mono", "en": "Mono"}'),
  ('BJ-OU', '{"fr": "Ouémé", "en": "Ouémé"}'),
  ('BJ-PL', '{"fr": "Plateau", "en": "Plateau"}'),
  ('BJ-ZO', '{"fr": "Zou", "en": "Zou"}')
) as d(code, nom)
on conflict (code) do nothing;

insert into public.territoires (code, nom, type, pays, parent_id)
select 'BJ-AQ-ABC', '{"fr": "Abomey-Calavi", "en": "Abomey-Calavi"}', 'commune', 'BJ',
       (select id from public.territoires where code = 'BJ-AQ')
on conflict (code) do nothing;
