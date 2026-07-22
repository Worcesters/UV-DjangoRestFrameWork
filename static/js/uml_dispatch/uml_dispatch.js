/**
 * UML Dispatcher — analyse d'un PlantUML et aperçu éditable de l'arborescence
 * de rangement (regroupement par lien d'héritage / réalisation).
 *
 * Le téléchargement ZIP passe par fetch + blob pour éviter la navigation vers
 * une page blanche (réponse binaire sur POST classique).
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

  function showError(message) {
    var box = document.getElementById("umlDispatchError");
    if (!box) return;
    if (message) {
      box.textContent = message;
      box.classList.remove("hidden");
    } else {
      box.textContent = "";
      box.classList.add("hidden");
    }
  }

  function setGenerating(isGenerating) {
    var btn = document.getElementById("umlDispatchGenerateBtn");
    if (!btn) return;
    btn.disabled = isGenerating;
    btn.textContent = isGenerating ? "Génération en cours…" : "Générer & télécharger le ZIP";
  }

  function parseFilename(contentDisposition) {
    if (!contentDisposition) return "reorganise.zip";
    var match = /filename="([^"]+)"/i.exec(contentDisposition);
    return match && match[1] ? match[1] : "reorganise.zip";
  }

  function triggerDownload(blob, filename) {
    var url = URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
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

  function generateZip(form, resultBox) {
    var archive = form.querySelector("#id_archive");
    if (!archive || !archive.files || archive.files.length === 0) {
      showError("Sélectionne d'abord une archive ZIP.");
      return;
    }

    showError("");
    setGenerating(true);
    syncFolderMap(form, resultBox);

    var formData = new FormData(form);
    fetch(form.action, {
      method: "POST",
      headers: {
        "X-CSRFToken": getCsrfToken(form),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: formData,
    })
      .then(function (res) {
        var contentType = res.headers.get("Content-Type") || "";
        if (res.ok && contentType.indexOf("application/zip") !== -1) {
          return res.blob().then(function (blob) {
            return {
              ok: true,
              blob: blob,
              filename: parseFilename(res.headers.get("Content-Disposition")),
            };
          });
        }
        return res
          .json()
          .catch(function () {
            return { error: "Réponse serveur inattendue (code " + res.status + ")." };
          })
          .then(function (json) {
            return { ok: false, error: (json && json.error) || "Erreur lors de la génération." };
          });
      })
      .then(function (result) {
        if (result.ok && result.blob) {
          triggerDownload(result.blob, result.filename);
          return;
        }
        showError(result.error || "Erreur lors de la génération.");
      })
      .catch(function () {
        showError("Erreur réseau lors de la génération du ZIP.");
      })
      .finally(function () {
        setGenerating(false);
      });
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
    form.addEventListener("submit", function (evt) {
      evt.preventDefault();
      generateZip(form, resultBox);
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
