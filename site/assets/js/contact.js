/* Formulaire de contact (démonstration) : vérifie les champs, n'envoie rien.
   Erreurs : message précis sous chaque champ + résumé en haut, focus sur le résumé. */
(function () {
  "use strict";
  var form = document.getElementById("form-contact");
  if (!form) return;
  var resume = form.querySelector("[data-resume]");
  var confirmation = document.querySelector("[data-confirmation]");
  var D = form.dataset;

  function libelle(champ) {
    var l = form.querySelector('label[for="' + champ.id + '"]');
    return l ? l.firstChild.textContent.trim() : champ.name;
  }
  function effacer(champ) {
    champ.removeAttribute("aria-invalid");
    var err = document.getElementById(champ.id + "-err");
    if (err) err.remove();
    var aide = champ.id + "-aide";
    if (document.getElementById(aide)) champ.setAttribute("aria-describedby", aide);
    else champ.removeAttribute("aria-describedby");
  }
  function signaler(champ, message) {
    champ.setAttribute("aria-invalid", "true");
    var err = document.createElement("p");
    err.className = "champ__erreur";
    err.id = champ.id + "-err";
    err.innerHTML = '<svg aria-hidden="true"><use href="#i-erreur"/></svg>';
    err.appendChild(document.createTextNode(message));
    var bloc = champ.type === "checkbox" ? champ.closest(".case") : champ;
    bloc.insertAdjacentElement("afterend", err);
    champ.setAttribute("aria-describedby", ((champ.getAttribute("aria-describedby") || "") + " " + err.id).trim());
  }
  function verifier(champ) {
    var v = champ.type === "checkbox" ? champ.checked : champ.value.trim();
    if (champ.type === "checkbox") return v ? "" : D.msgAccord;
    if (champ.required && !v) return D.msgRequis;
    if (champ.type === "email" && v && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) return D.msgEmail;
    if (champ.minLength > 0 && v && v.length < champ.minLength) return D.msgCourt.replace("{n}", champ.minLength);
    return "";
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var erreurs = [];
    form.querySelectorAll("input[required], select[required], textarea[required]").forEach(function (champ) {
      effacer(champ);
      var m = verifier(champ);
      if (m) { signaler(champ, m); erreurs.push({ champ: champ, message: m }); }
    });
    var liste = resume.querySelector("[data-resume-liste]");
    liste.innerHTML = "";
    if (erreurs.length) {
      resume.querySelector("[data-resume-titre]").textContent = D.msgResume.replace("{n}", erreurs.length);
      erreurs.forEach(function (e) {
        var li = document.createElement("li");
        var a = document.createElement("a");
        a.href = "#" + e.champ.id;
        a.textContent = (e.champ.type === "checkbox" ? "" : libelle(e.champ) + " : ") + e.message;
        a.addEventListener("click", function (c) { c.preventDefault(); e.champ.focus(); });
        li.appendChild(a);
        liste.appendChild(li);
      });
      resume.hidden = false;
      resume.focus();
      return;
    }
    resume.hidden = true;
    form.hidden = true;
    confirmation.hidden = false;
    confirmation.focus();
  });

  // Corrige l'erreur d'un champ dès que la saisie devient valide.
  form.addEventListener("input", function (ev) {
    var champ = ev.target;
    if (champ.getAttribute("aria-invalid") === "true" && !verifier(champ)) effacer(champ);
  });
  form.addEventListener("change", function (ev) {
    var champ = ev.target;
    if (champ.getAttribute("aria-invalid") === "true" && !verifier(champ)) effacer(champ);
  });

  // Arrivée depuis un lien « Signaler une erreur » ou « Nous écrire » : ?sujet=erreur&ref=GB-DS-0001
  var params = new URLSearchParams(window.location.search);
  var sujet = form.querySelector("#c-sujet");
  var demande = params.get("sujet");
  if (Array.prototype.some.call(sujet.options, function (o) { return o.value && o.value === demande; })) sujet.value = demande;
  if (/^GB-[A-Z]+-\d{4}$/.test(params.get("ref") || "")) form.querySelector("#c-message").value = params.get("ref") + " : ";

  confirmation.querySelector("[data-recommencer]").addEventListener("click", function () {
    form.reset();
    confirmation.hidden = true;
    form.hidden = false;
    form.querySelector("input, select, textarea").focus();
  });
})();
