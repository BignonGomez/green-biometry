// Tests du schéma et des règles d'accès de Green Biometry, sur PostgreSQL (PGlite), sans Docker.
// Utilisation : cd supabase/tests && npm install && npm test
//
// Ce qui est simulé (le reste est le vrai SQL des migrations) :
//  - les rôles Supabase anon, authenticated, service_role ;
//  - le schéma auth (table users, fonctions auth.uid() et auth.role()) ;
//  - PostGIS : les colonnes géométriques deviennent du texte (la géographie est testée sur Supabase).
import { PGlite } from "@electric-sql/pglite";
import { readFileSync, readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ici = dirname(fileURLToPath(import.meta.url));
const racine = join(ici, "..");

const SIMULATION_SUPABASE = `
  create role anon nologin;
  create role authenticated nologin;
  create role service_role nologin bypassrls;
  create schema auth;
  create schema extensions;
  create table auth.users (
    id uuid primary key default gen_random_uuid(),
    email text unique,
    raw_user_meta_data jsonb not null default '{}'
  );
  create function auth.uid() returns uuid language sql stable as $$
    select nullif(nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub', '')::uuid $$;
  create function auth.role() returns text language sql stable as $$
    select nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role' $$;
  grant usage on schema auth, extensions to anon, authenticated, service_role;
  grant execute on function auth.uid(), auth.role() to anon, authenticated, service_role;
`;

function adapterPourTest(sql) {
  return sql
    .replace(/^create extension if not exists postgis.*$/m, "-- (PostGIS simulé)")
    .replace(/extensions\.geometry\([^)]*\)/g, "text");
}

// ---------------------------------------------------------------- outils
let reussis = 0;
const echecs = [];
function verifier(nom, condition, detail = "") {
  if (condition) { reussis++; console.log(`  ✓ ${nom}`); }
  else { echecs.push(nom); console.log(`  ✗ ${nom}${detail ? " — " + detail : ""}`); }
}
async function doitEchouer(nom, promesse, motif) {
  try {
    await promesse;
    verifier(nom, false, "aucune erreur alors qu'un refus était attendu");
  } catch (e) {
    const ok = !motif || motif.test(e.message);
    verifier(nom, ok, ok ? "" : `erreur inattendue : ${e.message}`);
  }
}
function section(titre) { console.log(`\n${titre}`); }

const db = new PGlite();

// Exécute une requête « en tant que » quelqu'un : null = visiteur anonyme, "service" = fonction serveur.
async function en(qui, sql, params = []) {
  return db.transaction(async (tx) => {
    if (qui === "service") {
      await tx.exec(`set local role service_role`);
      await tx.query(`select set_config('request.jwt.claims', $1, true)`, [JSON.stringify({ role: "service_role" })]);
    } else if (qui) {
      await tx.exec(`set local role authenticated`);
      await tx.query(`select set_config('request.jwt.claims', $1, true)`, [JSON.stringify({ sub: qui.id, role: "authenticated" })]);
    } else {
      await tx.exec(`set local role anon`);
      await tx.query(`select set_config('request.jwt.claims', $1, true)`, [JSON.stringify({ role: "anon" })]);
    }
    return (await tx.query(sql, params)).rows;
  });
}
const compte = async (qui, sql, params) => (await en(qui, sql, params)).length;

// ---------------------------------------------------------------- installation
section("Installation");
await db.exec(SIMULATION_SUPABASE);
const migrations = readdirSync(join(racine, "migrations")).filter((f) => f.endsWith(".sql")).sort();
for (const f of migrations) {
  try {
    await db.exec(adapterPourTest(readFileSync(join(racine, "migrations", f), "utf8")));
    verifier(`migration ${f} appliquée`, true);
  } catch (e) {
    verifier(`migration ${f} appliquée`, false, e.message);
    console.log(`\n${reussis} réussi(s), ${echecs.length + 1} échec(s) : arrêt.`);
    process.exit(1);
  }
}
await db.exec(readFileSync(join(racine, "seed.sql"), "utf8"));
{
  const [n] = (await db.query(`select (select count(*) from themes)::int t, (select count(*) from licences)::int l,
    (select count(*) from territoires)::int r`)).rows;
  verifier("référentiels chargés (6 thèmes, 5 licences, 15 territoires)", n.t === 6 && n.l === 5 && n.r === 15, JSON.stringify(n));
}

// Comptes de test (créés comme le ferait Supabase Auth)
async function creerCompte(email, nom) {
  const r = await db.query(`insert into auth.users (email, raw_user_meta_data) values ($1, $2) returning id`,
    [email, JSON.stringify({ nom_affiche: nom })]);
  return { id: r.rows[0].id, email };
}
const admin = await creerCompte("admin@example.org", "Admin");
const eva = await creerCompte("eva@example.org", "Éva Évaluatrice");
const eva2 = await creerCompte("eva2@example.org", "Second évaluateur");
const alice = await creerCompte("alice@example.org", "Alice Contributrice");
const bob = await creerCompte("bob@example.org", "Bob Contributeur");
const mona = await creerCompte("mona@example.org", "Mona, membre ONG");
// Premier administrateur : posé directement en base par le propriétaire (voir supabase/README.md).
await db.query(`update profils set role = 'administrateur' where id = $1`, [admin.id]);
await db.query(`update profils set role = 'evaluateur' where id in ($1, $2)`, [eva.id, eva2.id]);
const ong = (await db.query(`insert into organisations (nom, type, pays, verifiee) values ('ONG Mangroves (test)', 'ong', 'BJ', true) returning id`)).rows[0].id;
await db.query(`insert into adhesions (profil_id, organisation_id) values ($1, $2)`, [mona.id, ong]);
const territoire = (await db.query(`select id from territoires where code = 'BJ-AQ-ABC'`)).rows[0].id;

// ---------------------------------------------------------------- 1. Comptes et profils
section("1. Comptes et profils");
verifier("le profil est créé automatiquement à l'inscription",
  (await compte(alice, `select 1 from profils where id = auth.uid() and nom_affiche = 'Alice Contributrice' and role = 'contributeur'`)) === 1);
verifier("un contributeur ne voit que son propre profil", (await compte(alice, `select 1 from profils`)) === 1);
verifier("un administrateur voit tous les profils", (await compte(admin, `select 1 from profils`)) === 6);
await doitEchouer("un contributeur ne peut pas se donner le rôle administrateur",
  en(alice, `update profils set role = 'administrateur' where id = auth.uid()`), /permission denied/);
await doitEchouer("definir_role est refusé à un non-administrateur",
  en(alice, `select definir_role($1, 'administrateur')`, [bob.id]), /Réservé aux administrateurs/);
await doitEchouer("un administrateur ne peut pas changer son propre rôle",
  en(admin, `select definir_role($1, 'contributeur')`, [admin.id]), /propre rôle/);
await en(admin, `select definir_role($1, 'contributeur')`, [bob.id]);
verifier("un administrateur peut changer le rôle d'un autre compte (et c'est journalisé)",
  (await db.query(`select 1 from journal_audit where action = 'definir_role'`)).rows.length === 1);
await doitEchouer("un visiteur ne peut pas lire les profils", en(null, `select * from profils`), /permission denied/);

// ---------------------------------------------------------------- 2. Brouillon d'un jeu
section("2. Dépôt d'un jeu de données (brouillon)");
const [jeu] = await en(alice, `insert into jeux (slug, titre, theme, licence, cree_par)
  values ('plantations-test', '{"fr": "Plantations (test)", "en": "Plantings (test)"}', 'restauration', 'cc-by-4', auth.uid())
  returning id, identifiant, statut_publication`);
verifier("le jeu reçoit un identifiant lisible GB-DS-0001", jeu.identifiant === "GB-DS-0001", jeu.identifiant);
verifier("un nouveau jeu est en brouillon", jeu.statut_publication === "brouillon");
verifier("un visiteur ne voit pas un brouillon", (await compte(null, `select 1 from jeux`)) === 0);
verifier("un autre contributeur ne voit pas ce brouillon", (await compte(bob, `select 1 from jeux`)) === 0);
verifier("son auteur le voit", (await compte(alice, `select 1 from jeux`)) === 1);
await doitEchouer("le contributeur ne peut pas se publier lui-même",
  en(alice, `update jeux set statut_publication = 'publie' where id = $1`, [jeu.id]), /permission denied/);
await doitEchouer("on ne peut pas créer un jeu au nom de quelqu'un d'autre",
  en(bob, `insert into jeux (slug, titre, theme, licence, cree_par) values ('x', '{"fr":"x","en":"x"}', 'eau', 'cc0', $1)`, [alice.id]),
  /row-level security/);
await doitEchouer("on ne peut pas rattacher un jeu à une organisation dont on n'est pas membre",
  en(bob, `insert into jeux (slug, titre, theme, licence, cree_par, organisation_id) values ('y', '{"fr":"y","en":"y"}', 'eau', 'cc0', auth.uid(), $1)`, [ong]),
  /row-level security/);

const [version] = await en(alice, `insert into versions (jeu_id, numero, note, auteur_id) values ($1, '1.0', '{"fr": "Première version", "en": "First version"}', auth.uid()) returning id`, [jeu.id]);
const [soum] = await en(alice, `insert into soumissions (type, jeu_id, version_id, contributeur_id) values ('nouveau_jeu', $1, $2, auth.uid()) returning id, identifiant`, [jeu.id, version.id]);
verifier("la soumission reçoit un identifiant GB-SUB-0001", soum.identifiant === "GB-SUB-0001");

// ---------------------------------------------------------------- 3. Envoi
section("3. Envoi de la soumission (EF-05)");
await doitEchouer("envoi refusé sans déclaration des droits",
  en(alice, `select changer_statut($1, 'soumis')`, [soum.id]), /droit de partager/);
await en(alice, `update soumissions set droits_declares = true, declaration = 'Je déclare avoir le droit de partager ces données.' where id = $1`, [soum.id]);
await doitEchouer("envoi refusé sans fichier",
  en(alice, `select changer_statut($1, 'soumis')`, [soum.id]), /au moins un fichier/);
await en(alice, `insert into fichiers (version_id, chemin, nom_original, format, taille, empreinte_sha256, depose_par)
  values ($1, 'depots/test/plantations.csv', 'plantations.csv', 'CSV', 1200, $2, auth.uid())`, [version.id, "a".repeat(64)]);
await en(alice, `select changer_statut($1, 'soumis')`, [soum.id]);
verifier("la soumission est envoyée et le jeu passe en revue",
  (await db.query(`select s.statut, j.statut_publication from soumissions s join jeux j on j.id = s.jeu_id where s.id = $1`, [soum.id]))
    .rows[0].statut_publication === "en_revue");
await doitEchouer("pendant l'examen, le contributeur ne peut plus modifier la fiche",
  en(alice, `update jeux set titre = '{"fr": "Autre", "en": "Other"}' where id = $1 returning id`, [jeu.id]).then((r) => { if (!r.length) throw new Error("aucune ligne modifiée"); }),
  /aucune ligne modifiée/);
await doitEchouer("pendant l'examen, le contributeur ne peut plus modifier la version",
  en(alice, `update versions set numero = '9.9' where id = $1 returning id`, [version.id]).then((r) => { if (!r.length) throw new Error("aucune ligne modifiée"); }),
  /aucune ligne modifiée/);
await doitEchouer("le contributeur ne peut pas faire avancer sa propre soumission",
  en(alice, `select changer_statut($1, 'verification_admin')`, [soum.id]), /Transition non autorisée/);

// ---------------------------------------------------------------- 4. Revue
section("4. Vérification, contrôle et revue (EF-07)");
await en(admin, `select changer_statut($1, 'verification_admin')`, [soum.id]);
await en(admin, `select changer_statut($1, 'controle_technique')`, [soum.id]);
await en("service", `select changer_statut($1, 'revue_scientifique')`, [soum.id]);
verifier("la fonction de contrôle automatique (rôle service) fait passer en revue scientifique",
  (await db.query(`select statut from soumissions where id = $1`, [soum.id])).rows[0].statut === "revue_scientifique");
await doitEchouer("un évaluateur non assigné ne peut pas valider",
  en(eva, `select changer_statut($1, 'valide')`, [soum.id]), /Transition non autorisée/);
await doitEchouer("un contributeur ne peut pas être désigné évaluateur",
  en(admin, `select assigner_evaluateur($1, $2)`, [soum.id, bob.id]), /pas évaluatrice/);
await en(admin, `select assigner_evaluateur($1, $2)`, [soum.id, eva.id]);
verifier("l'évaluatrice assignée voit la soumission", (await compte(eva, `select 1 from soumissions`)) === 1);
verifier("l'évaluatrice assignée voit le jeu en revue", (await compte(eva, `select 1 from jeux`)) === 1);
verifier("un autre évaluateur ne voit ni la soumission ni le jeu",
  (await compte(eva2, `select 1 from soumissions`)) === 0 && (await compte(eva2, `select 1 from jeux`)) === 0);
await en(alice, `insert into evenements_revue (soumission_id, auteur_id, action, texte) values ($1, auth.uid(), 'commentaire', 'Les relevés de 2025 sont complets.')`, [soum.id]);
verifier("le contributeur peut commenter sa soumission", true);
await doitEchouer("le contributeur ne peut pas écrire une décision dans l'historique",
  en(alice, `insert into evenements_revue (soumission_id, auteur_id, action, texte) values ($1, auth.uid(), 'decision', 'Validé !')`, [soum.id]),
  /row-level security/);
await doitEchouer("l'historique ne se modifie pas",
  en(admin, `update evenements_revue set texte = 'modifié'`), /permission denied/);
await doitEchouer("une demande de correction exige un motif",
  en(eva, `select changer_statut($1, 'correction_demandee')`, [soum.id]), /motif/);
await en(eva, `select changer_statut($1, 'valide')`, [soum.id]);
verifier("l'évaluatrice assignée valide", (await db.query(`select statut from soumissions where id = $1`, [soum.id])).rows[0].statut === "valide");
await doitEchouer("l'évaluatrice ne peut pas publier",
  en(eva, `select changer_statut($1, 'publie')`, [soum.id]), /Transition non autorisée/);

// ---------------------------------------------------------------- 5. Publication
section("5. Publication (EF-04)");
await doitEchouer("publication refusée tant que la fiche est incomplète",
  en(admin, `select changer_statut($1, 'publie')`, [soum.id]), /Fiche incomplète/);
await en(admin, `update jeux set resume = '{"fr": "Résumé", "en": "Summary"}', producteur = '{"fr": "ONG", "en": "NGO"}',
  methode = '{"fr": "Comptage", "en": "Count"}', limites = '{"fr": "Échantillon limité", "en": "Small sample"}',
  periode_debut = 2024, periode_fin = 2025, territoire_id = $2, emprise = 'POLYGON((2.31 6.42, 2.40 6.42, 2.40 6.51, 2.31 6.51, 2.31 6.42))',
  resolution = 'Arbre', crs = 'EPSG:4326' where id = $1`, [jeu.id, territoire]);
await en(admin, `insert into variables (jeu_id, nom, description) values ($1, 'survie', '{"fr": "Taux de survie", "en": "Survival rate"}')`, [jeu.id]);
await en(admin, `select changer_statut($1, 'publie')`, [soum.id]);
verifier("le jeu complet est publié, sa version aussi",
  (await db.query(`select j.statut_publication, v.statut from jeux j join versions v on v.jeu_id = j.id where j.id = $1`, [jeu.id]))
    .rows.every((r) => r.statut_publication === "publie" && r.statut === "publiee"));
verifier("un visiteur voit désormais le jeu, sa version, ses variables et son fichier",
  (await compte(null, `select 1 from jeux`)) === 1 && (await compte(null, `select 1 from versions`)) === 1
  && (await compte(null, `select 1 from variables`)) === 1 && (await compte(null, `select 1 from fichiers`)) === 1);
await doitEchouer("un visiteur ne voit pas les soumissions", en(null, `select * from soumissions`), /permission denied/);
verifier("le journal d'audit est invisible pour un contributeur", (await compte(alice, `select 1 from journal_audit`)) === 0);
verifier("chaque décision est horodatée et attribuée dans l'historique",
  (await db.query(`select count(*)::int n from evenements_revue where soumission_id = $1 and action = 'decision' and auteur_id is not null`, [soum.id])).rows[0].n === 2);
verifier("le délai de décision est mesurable (soumise_le et decidee_le remplis)",
  (await db.query(`select soumise_le is not null and decidee_le is not null ok from soumissions where id = $1`, [soum.id])).rows[0].ok);
await doitEchouer("un retrait exige un motif", en(admin, `select changer_statut($1, 'retire')`, [soum.id]), /motif/);

// ---------------------------------------------------------------- 6. Accès restreint
section("6. Jeu restreint (EF-09)");
const [jeuR] = await db.query(`insert into jeux (slug, titre, theme, licence, cree_par, organisation_id, acces, statut_publication)
  values ('inventaire-restreint', '{"fr": "Inventaire restreint", "en": "Restricted inventory"}', 'forets', 'conditions-source', $1, $2, 'restreint', 'publie')
  returning id`, [mona.id, ong]).then((r) => r.rows);
verifier("un visiteur ne voit pas un jeu restreint publié", (await compte(null, `select 1 from jeux where id = $1`, [jeuR.id])) === 0);
verifier("un contributeur extérieur ne le voit pas", (await compte(bob, `select 1 from jeux where id = $1`, [jeuR.id])) === 0);
verifier("un membre de l'organisation détentrice le voit", (await compte(mona, `select 1 from jeux where id = $1`, [jeuR.id])) === 1);
verifier("un évaluateur le voit (accès restreint, pas privé)", (await compte(eva2, `select 1 from jeux where id = $1`, [jeuR.id])) === 1);
await db.query(`update jeux set acces = 'prive' where id = $1`, [jeuR.id]);
verifier("un jeu privé est invisible pour un évaluateur non assigné", (await compte(eva2, `select 1 from jeux where id = $1`, [jeuR.id])) === 0);

// ---------------------------------------------------------------- 7. Référentiels, indicateurs, projets
section("7. Référentiels, indicateurs et projets");
await doitEchouer("un contributeur ne peut pas ajouter de thème",
  en(alice, `insert into themes (code, libelle) values ('test', '{"fr": "T", "en": "T"}')`), /row-level security/);
await en(admin, `insert into themes (code, libelle) values ('test', '{"fr": "Test", "en": "Test"}')`);
verifier("un administrateur peut ajouter un thème", (await compte(null, `select 1 from themes where code = 'test'`)) === 1);
await doitEchouer("un libellé de thème doit exister dans les deux langues",
  en(admin, `insert into themes (code, libelle) values ('test2', '{"fr": "Seulement français"}')`), /check constraint/);

const [ind] = await en(admin, `insert into indicateurs (slug, titre, theme, unite, frequence)
  values ('pluie-test', '{"fr": "Pluie", "en": "Rain"}', 'eau', '{"fr": "mm", "en": "mm"}', 'annuelle') returning id, identifiant`);
verifier("l'indicateur reçoit un identifiant GB-IND-0001", ind.identifiant === "GB-IND-0001");
await doitEchouer("une valeur manquante doit dire pourquoi",
  en(admin, `insert into valeurs_indicateur (indicateur_id, periode) values ($1, '2019')`, [ind.id]), /valeur_ou_motif/);
await en(admin, `insert into valeurs_indicateur (indicateur_id, periode, motif_absence) values ($1, '2019', '{"fr": "Stations incomplètes", "en": "Incomplete stations"}')`, [ind.id]);
verifier("un indicateur non publié est invisible pour un visiteur", (await compte(null, `select 1 from indicateurs`)) === 0);
await doitEchouer("publication d'un indicateur incomplet refusée",
  en(admin, `select definir_publication('indicateur', $1, 'publie')`, [ind.id]), /incomplète/);

const [prj] = await en(alice, `insert into projets (slug, titre, theme, debut, gestionnaire_id)
  values ('projet-test', '{"fr": "Projet", "en": "Project"}', 'restauration', 2024, auth.uid()) returning id, identifiant`);
verifier("le projet reçoit un identifiant GB-PRJ-0001", prj.identifiant === "GB-PRJ-0001");
await en(alice, `insert into suivis_projet (projet_id, titre, niveau, unite, cible_valeur, cible_periode)
  values ($1, '{"fr": "Survie", "en": "Survival"}', 'effet', '{"fr": "%", "en": "%"}', 80, '2027')`, [prj.id]);
verifier("le gestionnaire ajoute un indicateur suivi à son projet", true);
await doitEchouer("un autre contributeur ne peut pas modifier ce projet",
  en(bob, `insert into suivis_projet (projet_id, titre, niveau, unite, cible_valeur, cible_periode)
    values ($1, '{"fr": "X", "en": "X"}', 'activite', '{"fr": "u", "en": "u"}', 1, '2027')`, [prj.id]), /row-level security/);
await doitEchouer("le gestionnaire ne peut pas publier son projet lui-même",
  en(alice, `update projets set statut_publication = 'publie' where id = $1`, [prj.id]), /permission denied/);
await doitEchouer("publication refusée avec moins de 2 indicateurs suivis",
  en(admin, `select definir_publication('projet', $1, 'publie')`, [prj.id]), /au moins 2 indicateurs/);
await doitEchouer("une référence sans période est refusée",
  en(alice, `insert into suivis_projet (projet_id, titre, niveau, unite, reference_valeur, cible_valeur, cible_periode)
    values ($1, '{"fr": "Y", "en": "Y"}', 'resultat', '{"fr": "ha", "en": "ha"}', 0, 40, '2026')`, [prj.id]), /reference_complete/);
verifier("un projet en brouillon est invisible pour un visiteur", (await compte(null, `select 1 from projets`)) === 0);

// ---------------------------------------------------------------- bilan
console.log(`\n${reussis} réussi(s), ${echecs.length} échec(s).`);
if (echecs.length) {
  console.log("Échecs :\n- " + echecs.join("\n- "));
  process.exit(1);
}
