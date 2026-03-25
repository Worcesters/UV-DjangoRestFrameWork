/**
 * Générateur de pipeline : containers dynamiques, branches API, copie config.
 */
(function () {
    "use strict";

    var cfg = document.getElementById("pipelineGeneratorConfig");
    var branchesApiUrl = cfg && cfg.dataset.branchesApiUrl ? cfg.dataset.branchesApiUrl : "";

    function readInitialContainers() {
        var el = document.getElementById("pipeline-initial-containers");
        if (!el) return [];
        try {
            var data = JSON.parse(el.textContent.trim());
            return Array.isArray(data) ? data : [];
        } catch (_e) {
            return [];
        }
    }

    var initialContainers = readInitialContainers();

    var containersSection = document.getElementById("containersSection");
    var sshSection = document.getElementById("sshSection");
    var containersList = document.getElementById("containersList");
    var addContainerBtn = document.getElementById("addContainerBtn");
    var pipelineForm = document.getElementById("pipelineForm");
    var containersJsonInput = document.getElementById("id_containers_json");
    var useContainersInputs = document.querySelectorAll("input[name='use_containers']");
    var useSshInputs = document.querySelectorAll("input[name='use_ssh']");
    var repoUrlInput = document.getElementById("id_repo_url");
    var deployBranchInput = document.getElementById("id_deploy_branch");
    var branchDatalist = document.getElementById("deploy-branch-options");
    var loadBranchesBtn = document.getElementById("loadBranchesBtn");
    var branchesStatus = document.getElementById("branchesStatus");

    var copyBtn = document.getElementById("copyPipelineBtn");
    var output = document.getElementById("id_generated_config");

    if (!containersSection || !containersList || !addContainerBtn || !pipelineForm || !containersJsonInput || !sshSection) {
        return;
    }

    function escAttr(v) {
        if (v == null) return "";
        return String(v)
            .replace(/&/g, "&amp;")
            .replace(/"/g, "&quot;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
    }

    function createContainerRow(container) {
        container = container || {};
        var row = document.createElement("div");
        row.className = "rounded-xl border border-cyan-200 bg-white p-3";
        row.innerHTML =
            '<div class="grid sm:grid-cols-2 gap-3">' +
            '<input type="text" data-key="service_name" placeholder="Nom du service (ex: api)" value="' +
            escAttr(container.service_name) +
            '" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">' +
            '<input type="text" data-key="docker_image" placeholder="Image docker (ex: myapp:latest)" value="' +
            escAttr(container.docker_image) +
            '" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">' +
            '<input type="text" data-key="dockerfile_path" placeholder="Dockerfile path (ex: Dockerfile)" value="' +
            escAttr(container.dockerfile_path || "Dockerfile") +
            '" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">' +
            '<input type="text" data-key="ports" placeholder="Ports (ex: 8000:8000)" value="' +
            escAttr(container.ports) +
            '" class="w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">' +
            "</div>" +
            '<input type="text" data-key="environment" placeholder="Env container (ex: APP_ENV=prod,DEBUG=0)" value="' +
            escAttr(container.environment) +
            '" class="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700">' +
            '<div class="mt-3 flex justify-end">' +
            '<button type="button" class="remove-container text-xs px-3 py-1.5 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-700 font-semibold">Supprimer</button>' +
            "</div>";

        var removeBtn = row.querySelector(".remove-container");
        if (removeBtn) {
            removeBtn.addEventListener("click", function () {
                row.remove();
            });
        }
        containersList.appendChild(row);
    }

    function isContainersEnabled() {
        var selected = document.querySelector("input[name='use_containers']:checked");
        return selected && selected.value === "yes";
    }

    function syncContainersVisibility() {
        if (isContainersEnabled()) {
            containersSection.classList.remove("hidden");
        } else {
            containersSection.classList.add("hidden");
        }
    }

    function syncSshVisibility() {
        var selected = document.querySelector("input[name='use_ssh']:checked");
        if (selected && selected.value === "yes") {
            sshSection.classList.remove("hidden");
        } else {
            sshSection.classList.add("hidden");
        }
    }

    function setBranchesStatus(message, isError) {
        if (!branchesStatus) return;
        branchesStatus.textContent = message;
        branchesStatus.classList.remove("text-slate-500", "text-rose-600", "text-emerald-600");
        if (isError) {
            branchesStatus.classList.add("text-rose-600");
            return;
        }
        if (message) {
            branchesStatus.classList.add("text-emerald-600");
            return;
        }
        branchesStatus.classList.add("text-slate-500");
    }

    function loadBranches() {
        if (!repoUrlInput || !deployBranchInput || !branchDatalist || !loadBranchesBtn || !branchesApiUrl) {
            return;
        }
        var repoUrl = repoUrlInput.value.trim();
        if (!repoUrl) {
            setBranchesStatus("Renseigne une URL repository.", true);
            return;
        }

        loadBranchesBtn.disabled = true;
        setBranchesStatus("Chargement...", false);

        fetch(branchesApiUrl + "?repo_url=" + encodeURIComponent(repoUrl))
            .then(function (r) {
                return r.json().then(function (payload) {
                    return { ok: r.ok, payload: payload };
                });
            })
            .then(function (result) {
                if (!result.ok) {
                    setBranchesStatus(result.payload.error || "Erreur de recuperation.", true);
                    return;
                }
                var branches = Array.isArray(result.payload.branches) ? result.payload.branches : [];
                branchDatalist.innerHTML = "";
                branches.forEach(function (branch) {
                    var option = document.createElement("option");
                    option.value = branch;
                    branchDatalist.appendChild(option);
                });
                if (branches.length > 0) {
                    setBranchesStatus(
                        branches.length + " branche(s) disponibles — choisis la branche cible.",
                        false
                    );
                } else {
                    setBranchesStatus("Aucune branche trouvee.", true);
                }
            })
            .catch(function () {
                setBranchesStatus("Erreur reseau pendant la recuperation.", true);
            })
            .finally(function () {
                loadBranchesBtn.disabled = false;
            });
    }

    function serializeContainers() {
        var rows = containersList.querySelectorAll("div.rounded-xl");
        var payload = [];
        rows.forEach(function (row) {
            var item = {};
            row.querySelectorAll("input[data-key]").forEach(function (input) {
                item[input.dataset.key] = input.value.trim();
            });
            payload.push(item);
        });
        containersJsonInput.value = JSON.stringify(payload);
    }

    addContainerBtn.addEventListener("click", function () {
        createContainerRow({});
    });

    useContainersInputs.forEach(function (input) {
        input.addEventListener("change", syncContainersVisibility);
    });
    useSshInputs.forEach(function (input) {
        input.addEventListener("change", syncSshVisibility);
    });

    pipelineForm.addEventListener("submit", function () {
        serializeContainers();
    });

    initialContainers.forEach(function (container) {
        createContainerRow(container || {});
    });

    syncContainersVisibility();
    syncSshVisibility();

    if (loadBranchesBtn) {
        loadBranchesBtn.addEventListener("click", loadBranches);
    }

    if (!copyBtn || !output) {
        return;
    }

    var defaultLabel = copyBtn.textContent;
    function resetCopyState() {
        copyBtn.textContent = defaultLabel;
        copyBtn.classList.remove("bg-emerald-100", "text-emerald-700", "scale-105");
        copyBtn.classList.add("bg-slate-100", "text-slate-700");
    }

    copyBtn.addEventListener("click", function () {
        navigator.clipboard.writeText(output.value || "").then(
            function () {
                copyBtn.textContent = "Copie !";
                copyBtn.classList.remove("bg-slate-100", "text-slate-700");
                copyBtn.classList.add("bg-emerald-100", "text-emerald-700", "scale-105");
                setTimeout(resetCopyState, 900);
            },
            function (error) {
                if (typeof console !== "undefined" && console.warn) {
                    console.warn("Clipboard copy failed:", error);
                }
                copyBtn.textContent = "Erreur";
                copyBtn.classList.remove("bg-slate-100", "text-slate-700", "scale-105");
                copyBtn.classList.add("bg-rose-100", "text-rose-700");
                setTimeout(resetCopyState, 900);
            }
        );
    });
})();
