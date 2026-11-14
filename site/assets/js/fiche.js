/* Green Biometry : fiche jeu de données (copie de la citation, téléchargement de démonstration). */
(function () {
  'use strict';
  document.querySelectorAll('[data-copier]').forEach(function (bouton) {
    bouton.addEventListener('click', function () {
      var texte = document.getElementById(bouton.dataset.copier).textContent.trim();
      var libelle = bouton.querySelector('span');
      var initial = libelle.textContent;
      function confirmer() {
        libelle.textContent = bouton.dataset.copieOk;
        setTimeout(function () { libelle.textContent = initial; }, 2500);
      }
      if (navigator.clipboard) navigator.clipboard.writeText(texte).then(confirmer, function () {});
    });
  });
  document.querySelectorAll('[data-demo-telechargement]').forEach(function (bouton) {
    bouton.addEventListener('click', function () {
      var message = bouton.closest('section').querySelector('[data-demo-message]');
      if (message) message.hidden = false;
    });
  });
})();
