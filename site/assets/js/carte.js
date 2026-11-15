/* Carte des emprises : Leaflet + données embarquées (#donnees-carte).
   Sans JavaScript, la liste des jeux reste utilisable (liens vers les fiches). */
(function () {
  "use strict";
  var source = document.getElementById("donnees-carte");
  var conteneur = document.getElementById("carte");
  if (!source || !conteneur || typeof L === "undefined") return;

  var donnees = JSON.parse(source.textContent);
  var T = donnees.textes;
  var jeux = donnees.jeux;
  var parSlug = {};
  var legende = document.querySelector("[data-legende]");
  var compte = document.querySelector("[data-compte]");
  var actif = null;

  var carte = L.map(conteneur, { scrollWheelZoom: false, zoomSnap: 0.5, worldCopyJump: true });
  carte.attributionControl.setPrefix(false);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: T.attribution, maxZoom: 19
  }).addTo(carte);
  // Molette active seulement après un clic dans la carte : le défilement de la page reste libre.
  carte.on("click", function () { carte.scrollWheelZoom.enable(); });
  conteneur.addEventListener("mouseleave", function () { carte.scrollWheelZoom.disable(); });

  function bornes(j) {
    var e = j.emprise; // [ouest, sud, est, nord]
    return L.latLngBounds([e[1], e[0]], [e[3], e[2]]);
  }
  function surface(j) {
    var e = j.emprise;
    return (e[2] - e[0]) * (e[3] - e[1]);
  }
  function styleDe(j, enAvant) {
    return {
      color: j.couleur, weight: enAvant ? 3.5 : 2,
      fillColor: j.couleur, fillOpacity: enAvant ? 0.28 : 0.08,
      dashArray: enAvant ? null : "6 4"
    };
  }

  // Les plus grandes emprises d'abord : les petites restent visibles par-dessus.
  jeux.slice().sort(function (a, b) { return surface(b) - surface(a); }).forEach(function (j) {
    j.calque = L.rectangle(bornes(j), Object.assign({ interactive: false }, styleDe(j, false))).addTo(carte);
    // Repère au centre : les très petites zones restent visibles à petite échelle.
    j.repere = L.circleMarker(bornes(j).getCenter(), {
      radius: 5, color: "#fff", weight: 2, fillColor: j.couleur, fillOpacity: 1, interactive: false
    }).addTo(carte);
    parSlug[j.slug] = j;
  });

  function themesCoches() {
    var coches = {};
    legende.querySelectorAll("input[name=theme]").forEach(function (c) { coches[c.value] = c.checked; });
    return coches;
  }
  function visibles() {
    var coches = themesCoches();
    return jeux.filter(function (j) { return coches[j.theme]; });
  }

  function echapper(s) {
    return String(s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
  }
  function contenuPopup(liste) {
    if (!liste.length) return '<p class="popup-jeux">' + echapper(T.aucun) + "</p>";
    var titre = liste.length === 1 ? T.unJeu : T.plusieurs.replace("{n}", liste.length);
    return '<div class="popup-jeux"><p class="popup-jeux__titre">' + echapper(titre) + "</p><ul>" +
      liste.map(function (j) {
        return '<li><span class="carte-legende__pastille" style="--pastille:' + j.couleur + '" aria-hidden="true"></span><div>' +
          '<a href="' + echapper(j.lien) + '">' + echapper(j.titre) + "</a>" +
          "<p>" + echapper(j.themeNom) + " · " + echapper(j.territoire) + " · " + echapper(j.periode) + "</p></div></li>";
      }).join("") + "</ul></div>";
  }

  function mettreEnAvant(slug) {
    actif = slug;
    jeux.forEach(function (j) { j.calque.setStyle(styleDe(j, j.slug === slug)); });
    if (slug) parSlug[slug].calque.bringToFront();
    document.querySelectorAll(".carte-liste__item").forEach(function (li) {
      li.classList.toggle("est-actif", li.dataset.slug === slug);
    });
  }

  // Clic sur la carte : tous les jeux dont l'emprise contient ce point.
  carte.on("click", function (ev) {
    var touches = visibles().filter(function (j) { return bornes(j).contains(ev.latlng); })
      .sort(function (a, b) { return surface(a) - surface(b); });
    // openOn ferme l'infobulle précédente (popupclose) : mise en avant après l'ouverture.
    L.popup({ maxWidth: 320 }).setLatLng(ev.latlng).setContent(contenuPopup(touches)).openOn(carte);
    mettreEnAvant(touches.length ? touches[0].slug : null);
  });
  carte.on("popupclose", function () { mettreEnAvant(null); });

  function localiser(slug) {
    var j = parSlug[slug];
    carte.fitBounds(bornes(j), { padding: [32, 32], maxZoom: 12 });
    L.popup({ maxWidth: 320, autoPan: true }).setLatLng(bornes(j).getCenter()).setContent(contenuPopup([j])).openOn(carte);
    mettreEnAvant(slug);
    if (window.matchMedia("(max-width: 1023px)").matches) conteneur.scrollIntoView({ behavior: "smooth", block: "start" });
  }
  document.querySelectorAll("[data-localiser]").forEach(function (b) {
    b.hidden = false;
    b.addEventListener("click", function () { localiser(b.dataset.localiser); });
  });

  function appliquerFiltres() {
    var coches = themesCoches();
    var n = 0;
    jeux.forEach(function (j) {
      var ok = coches[j.theme];
      if (ok) { n++; j.calque.addTo(carte); j.repere.addTo(carte); }
      else { j.calque.remove(); j.repere.remove(); }
    });
    // Les petites emprises repassent au-dessus après un réaffichage.
    jeux.slice().sort(function (a, b) { return surface(a) - surface(b); }).forEach(function (j) {
      if (coches[j.theme]) j.calque.bringToBack();
    });
    document.querySelectorAll(".carte-liste__item").forEach(function (li) { li.hidden = !coches[li.dataset.theme]; });
    compte.textContent = n + " " + (n === 1 ? compte.dataset.un : compte.dataset.plusieurs);
    carte.closePopup();
  }
  legende.addEventListener("change", appliquerFiltres);

  // Vue de départ : le Bénin (pays pilote).
  carte.fitBounds([[6.2, 0.7], [12.45, 3.9]], { padding: [16, 16] });

  // Arrivée depuis une fiche (« Voir sur la carte ») : ?jeu=<slug>
  var demande = new URLSearchParams(window.location.search).get("jeu");
  if (demande && parSlug[demande]) {
    var j = parSlug[demande];
    carte.fitBounds(bornes(j), { padding: [32, 32], maxZoom: 12 });
    L.popup({ maxWidth: 320 }).setLatLng(bornes(j).getCenter()).setContent(contenuPopup([j])).openOn(carte);
    mettreEnAvant(demande);
  }
})();
