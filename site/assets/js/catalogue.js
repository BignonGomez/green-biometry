/*
 * Green Biometry : filtres du catalogue (amélioration progressive).
 * Sans JavaScript, tous les jeux restent visibles. Avec, la recherche et les filtres
 * s'appliquent en direct et l'adresse de la page garde l'état (?q=…&theme=…), ce qui
 * permet de partager une recherche et de venir de la page d'accueil.
 */
(function () {
  'use strict';
  var form = document.getElementById('catalogue');
  if (!form) return;
  var liste = form.querySelector('[data-liste]');
  var cartes = Array.prototype.slice.call(liste.querySelectorAll('article'));
  var ordreInitial = cartes.slice();
  var compte = form.querySelector('[data-compte]');
  var vide = form.querySelector('[data-vide]');
  var badgeActifs = form.querySelector('[data-filtres-actifs]');
  var panneau = form.querySelector('.filtres');
  var GROUPES = ['theme', 'territoire', 'format', 'source', 'statut', 'licence'];

  function normaliser(texte) {
    return (texte || '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().trim();
  }

  function etat() {
    var e = { q: normaliser(form.q.value), de: parseInt(form.de.value, 10), a: parseInt(form.a.value, 10), tri: form.tri.value };
    GROUPES.forEach(function (g) {
      e[g] = Array.prototype.slice.call(form.querySelectorAll('input[name="' + g + '"]:checked')).map(function (c) { return c.value; });
    });
    return e;
  }

  function correspond(carte, e) {
    var d = carte.dataset;
    if (e.q) {
      var mots = e.q.split(/\s+/);
      for (var i = 0; i < mots.length; i++) if (d.recherche.indexOf(mots[i]) === -1) return false;
    }
    if (e.theme.length && e.theme.indexOf(d.theme) === -1) return false;
    if (e.territoire.length && e.territoire.indexOf(d.territoire) === -1) return false;
    if (e.statut.length && e.statut.indexOf(d.statut) === -1) return false;
    if (e.licence.length && e.licence.indexOf(d.licence) === -1) return false;
    if (e.source.length && e.source.indexOf(d.source) === -1) return false;
    if (e.format.length && !e.format.some(function (f) { return d.format.split(' ').indexOf(f) !== -1; })) return false;
    // Période : le jeu doit couvrir au moins une année de l'intervalle demandé
    if (!isNaN(e.de) && parseInt(d.fin, 10) < e.de) return false;
    if (!isNaN(e.a) && parseInt(d.debut, 10) > e.a) return false;
    return true;
  }

  function trier(cartesVisibles, tri) {
    var copie = tri === 'pertinence' ? ordreInitial.slice() : cartesVisibles.slice();
    if (tri === 'maj') copie.sort(function (x, y) { return y.dataset.maj.localeCompare(x.dataset.maj); });
    if (tri === 'titre') copie.sort(function (x, y) { return x.dataset.titre.localeCompare(y.dataset.titre); });
    copie.forEach(function (c) { liste.appendChild(c); });
  }

  function mettreAJourAdresse(e) {
    var p = new URLSearchParams();
    if (form.q.value.trim()) p.set('q', form.q.value.trim());
    GROUPES.forEach(function (g) { e[g].forEach(function (v) { p.append(g, v); }); });
    if (!isNaN(e.de)) p.set('de', e.de);
    if (!isNaN(e.a)) p.set('a', e.a);
    if (e.tri !== 'pertinence') p.set('tri', e.tri);
    var s = p.toString();
    history.replaceState(null, '', location.pathname + (s ? '?' + s : ''));
  }

  function appliquer() {
    var e = etat();
    var n = 0;
    cartes.forEach(function (c) { var ok = correspond(c, e); c.hidden = !ok; if (ok) n++; });
    trier(cartes, e.tri);
    compte.textContent = n === 1 ? compte.dataset.un : compte.dataset.plusieurs.replace('{n}', n);
    vide.hidden = n !== 0;
    var actifs = GROUPES.reduce(function (s, g) { return s + e[g].length; }, 0) + (!isNaN(e.de) ? 1 : 0) + (!isNaN(e.a) ? 1 : 0);
    badgeActifs.hidden = actifs === 0;
    badgeActifs.textContent = actifs;
    mettreAJourAdresse(e);
  }

  // État initial lu dans l'adresse (?q=…&theme=…)
  var params = new URLSearchParams(location.search);
  if (params.get('q')) form.q.value = params.get('q');
  if (params.get('de')) form.de.value = params.get('de');
  if (params.get('a')) form.a.value = params.get('a');
  if (params.get('tri')) form.tri.value = params.get('tri');
  GROUPES.forEach(function (g) {
    params.getAll(g).forEach(function (v) {
      var c = form.querySelector('input[name="' + g + '"][value="' + CSS.escape(v) + '"]');
      if (c) c.checked = true;
    });
  });

  // Sur mobile, le panneau de filtres démarre fermé
  if (window.matchMedia('(max-width: 1023px)').matches) panneau.open = false;

  var minuteur;
  form.addEventListener('input', function () { clearTimeout(minuteur); minuteur = setTimeout(appliquer, 120); });
  form.addEventListener('change', appliquer);
  form.addEventListener('submit', function (ev) { ev.preventDefault(); appliquer(); });
  form.addEventListener('reset', function () { setTimeout(appliquer, 0); });

  appliquer();
})();
