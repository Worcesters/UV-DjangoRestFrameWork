/**
 * UML Dispatcher — analyse d'un PlantUML et aperçu éditable de l'arborescence
 * de rangement (regroupement par lien d'héritage / réalisation).
 *
 * Idempotent : le script est ré-exécuté à chaque swap HTMX du panneau outil ;
 * les écouteurs sont attachés une seule fois par nœud (garde `dataset.bound`).
 */
(function () {
  "use strict";

  function getCsrfToken(form) {
    var input = form && form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : "";
  }

  function textNode(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text != null) el.textContent = text;
    return el;
  }

  function renderGroups(container, data) {
    container.innerHTML = "";
    if (!data.groups || data.groups.length === 0) {
      container.appendChild(
        textNode("p", "uml-dispatch-empty", "Aucun lien détecté : tous les fichiers iront dans _divers.")
      );
    }
    data.groups.forEach(function (group) {
      container.appendChild(buildGroupCard(group));
    });
    if (data.unlinked && data.unlinked.length > 0) {
      container.appendChild(buildUnlinkedCard(data.unlinked));
    }
  }

  function buildGroupCard(group) {
    var card = textNode("div", "uml-dispatch-group");

    var head = textNode("div", "uml-dispatch-group__head");
    head.appendChild(textNode("span", "uml-dispatch-group__target", group.target));
    head.appendChild(textNode("span", "uml-dispatch-group__count", group.count + " fichier(s)"));
    card.appendChild(head);

    var input = document.createElement("input");
    input.type = "text";
    input.className = "uml-dispatch-folder-input";
    input.value = group.folder;
    input.setAttribute("data-target", group.target);
    input.setAttribute("aria-label", "Nom du dossier pour " + group.target);
    card.appendChild(input);

    var chips = textNode("div", "uml-dispatch-chips");
    group.members.forEach(function (member) {
      chips.appendChild(textNode("span", "uml-dispatch-chip", member));
    });
    card.appendChild(chips);
    return card;
  }

  function buildUnlinkedCard(unlinked) {
    var card = textNode("div", "uml-dispatch-group uml-dispatch-group--misc");
    var head = textNode("div", "uml-dispatch-group__head");
    head.appendChild(textNode("span", "uml-dispatch-group__target", "_divers"));
    head.appendChild(textNode("span", "uml-dispatch-group__count", unlinked.length + " fichier(s)"));
    card.appendChild(head);
    var chips = textNode("div", "uml-dispatch-chips");
    unlinked.forEach(function (member) {
      chips.appendChild(textNode("span", "uml-dispatch-chip uml-dispatch-chip--muted", member));
    });
    card.appendChild(chips);
    return card;
  }

  function analyze(config, form, resultBox, summary) {
    var textarea = form.querySelector("#id_dispatch_uml");
    var umlText = textarea ? textarea.value.trim() : "";
    if (!umlText) {
      summary.textContent = "Colle d'abord un PlantUML.";
      return;
    }
    summary.textContent = "Analyse…";
    var body = new URLSearchParams();
    body.set("plantuml_text", umlText);
    fetch(config.getAttribute("data-analyze-url"), {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(form),
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: body.toString(),
    })
      .then(function (res) {
        return res.json().then(function (json) {
          return { ok: res.ok, json: json };
        });
      })
      .then(function (result) {
        if (!result.ok) {
          summary.textContent = result.json.error || "Erreur d'analyse.";
          return;
        }
        renderGroups(resultBox, result.json);
        summary.textContent =
          result.json.groups.length +
          " groupe(s) · " +
          result.json.total_classes +
          " classe(s) détectée(s).";
      })
      .catch(function () {
        summary.textContent = "Erreur réseau lors de l'analyse.";
      });
  }

  function syncFolderMap(form, resultBox) {
    var map = {};
    resultBox.querySelectorAll(".uml-dispatch-folder-input").forEach(function (input) {
      var target = input.getAttribute("data-target");
      if (target) map[target] = input.value;
    });
    var hidden = form.querySelector("#id_folder_map");
    if (hidden) hidden.value = JSON.stringify(map);
  }

  function init() {
    var config = document.getElementById("umlDispatchConfig");
    var form = document.getElementById("umlDispatchForm");
    if (!config || !form || config.dataset.bound === "1") return;
    config.dataset.bound = "1";

    var resultBox = document.getElementById("umlDispatchResult");
    var summary = document.getElementById("umlDispatchSummary");
    var analyzeBtn = document.getElementById("umlDispatchAnalyzeBtn");

    if (analyzeBtn) {
      analyzeBtn.addEventListener("click", function () {
        analyze(config, form, resultBox, summary);
      });
    }
    form.addEventListener("submit", function () {
      syncFolderMap(form, resultBox);
    });

    var textarea = form.querySelector("#id_dispatch_uml");
    if (textarea && textarea.value.trim()) {
      analyze(config, form, resultBox, summary);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
  document.body.addEventListener("htmx:afterSwap", function (evt) {
    if (evt.detail && evt.detail.target && evt.detail.target.id === "gen-tool-panel") {
      init();
    }
  });
})();
