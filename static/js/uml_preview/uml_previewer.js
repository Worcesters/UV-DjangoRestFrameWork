/**
 * UML Previewer : preview API, aide modale, UML Builder (drag & drop + modale).
 */
(function () {
    "use strict";

    var cfgEl = document.getElementById("umlPreviewerConfig");
    var apiUrl = cfgEl && cfgEl.dataset.apiUrl ? cfgEl.dataset.apiUrl : "";

    function getCsrfToken() {
        var input = document.querySelector("input[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function isValidIdentifier(name) {
        return /^[A-Za-z_][A-Za-z0-9_]*$/.test(name);
    }

    /** Rend un nom utilisable comme extrémité PlantUML (quote si besoin). */
    function toPlantUmlToken(name) {
        return isValidIdentifier(name) ? name : '"' + name + '"';
    }

    function ensureStartEnd(uml) {
        var text = String(uml ?? "");
        if (!text.includes("@startuml")) {
            text = "@startuml\n" + text;
        }
        if (!text.includes("@enduml")) {
            text = text.trimEnd() + "\n@enduml";
        }
        return text;
    }

    function insertBeforeEnduml(uml, block) {
        var text = ensureStartEnd(uml);
        var idx = text.indexOf("@enduml");
        if (idx === -1) {
            return text.trimEnd() + "\n" + block + "\n@enduml";
        }
        var before = text.slice(0, idx).replace(/\s*$/, "");
        return before + "\n\n" + block + "\n" + text.slice(idx);
    }

    function escapeRegExp(s) {
        return String(s).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    }

    /**
     * Insère une ligne de membre (attribut / méthode) dans le corps `{ }`
     * d'une classe / classe abstraite / interface existante.
     * Si le type est déclaré sans corps (ex. `class User`), le corps est créé.
     */
    function insertMemberIntoType(uml, typeName, memberLine) {
        var text = ensureStartEnd(uml);
        var declRe = new RegExp(
            "^([ \\t]*)(abstract[ \\t]+)?(class|interface)[ \\t]+" +
                escapeRegExp(typeName) +
                "\\b.*$",
            "m"
        );
        var m = declRe.exec(text);
        if (!m) {
            return insertBeforeEnduml(uml, typeName + " : " + memberLine);
        }
        var indent = m[1] || "";
        var memberIndent = indent + "  ";
        var declEnd = m.index + m[0].length;

        if (m[0].indexOf("{") === -1) {
            var insertion = " {\n" + memberIndent + memberLine + "\n" + indent + "}";
            return text.slice(0, declEnd) + insertion + text.slice(declEnd);
        }

        var firstBrace = text.indexOf("{", m.index);
        var depth = 0;
        var closeIdx = -1;
        for (var i = firstBrace; i < text.length; i++) {
            var ch = text[i];
            if (ch === "{") {
                depth++;
            } else if (ch === "}") {
                depth--;
                if (depth === 0) {
                    closeIdx = i;
                    break;
                }
            }
        }
        if (closeIdx === -1) {
            return insertBeforeEnduml(uml, typeName + " : " + memberLine);
        }
        var before = text.slice(0, closeIdx).replace(/[ \t]*$/, "");
        if (!before.endsWith("\n")) before += "\n";
        return before + memberIndent + memberLine + "\n" + indent + text.slice(closeIdx);
    }

    /** Couples de cardinalités PlantUML pour chaque préréglage de multiplicité. */
    function multiplicityCards(v) {
        switch (v) {
            case "one_to_one":
                return ["1", "1"];
            case "one_to_many":
                return ["1", "*"];
            case "many_to_one":
                return ["*", "1"];
            case "many_to_many":
                return ["*", "*"];
            default:
                return ["", ""];
        }
    }

    function extractClasses(uml) {
        var names = new Set();
        var re = /^\s*(abstract\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b/gm;
        var m;
        while ((m = re.exec(uml)) !== null) {
            names.add(m[2]);
        }
        return Array.from(names);
    }

    function extractInterfaces(uml) {
        var names = new Set();
        var re = /^\s*interface\s+([A-Za-z_][A-Za-z0-9_]*)\b/gm;
        var m;
        while ((m = re.exec(uml)) !== null) {
            names.add(m[1]);
        }
        return Array.from(names);
    }

    function extractEnums(uml) {
        var names = new Set();
        var re = /^\s*enum\s+([A-Za-z_][A-Za-z0-9_]*)\b/gm;
        var m;
        while ((m = re.exec(uml)) !== null) {
            names.add(m[1]);
        }
        return Array.from(names);
    }

    /**
     * Conteneurs déclarés (package / namespace / zones : database, folder, etc.).
     * Renvoie l'alias (`as X`) si présent, sinon le nom (entre guillemets ou identifiant),
     * afin d'obtenir une extrémité de lien exploitable en PlantUML.
     */
    function extractPackages(uml) {
        var names = new Set();
        var re =
            /^\s*(?:package|namespace|database|folder|frame|node|cloud|component|rectangle|artifact|storage|queue|card)\s+(?:"([^"]+)"|([A-Za-z_][A-Za-z0-9_.]*))(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?/gm;
        var m;
        while ((m = re.exec(uml)) !== null) {
            var name = m[3] || m[1] || m[2];
            if (name) names.add(name);
        }
        return Array.from(names).sort();
    }

    /** Noms utilisables comme extrémités de liens (classes, interfaces, enums). */
    function extractTypeNames(uml) {
        var s = new Set();
        extractClasses(uml).forEach(function (n) {
            s.add(n);
        });
        extractInterfaces(uml).forEach(function (n) {
            s.add(n);
        });
        extractEnums(uml).forEach(function (n) {
            s.add(n);
        });
        return Array.from(s).sort();
    }

    /** Lit l’orientation du lien (PlantUML : -up-, -down-, -left-, -right-). */
    function getBuilderLinkDirection() {
        var s = document.getElementById("umlBuilderLinkDirection");
        if (!s || !s.value) return "";
        var v = String(s.value).toLowerCase();
        if (["up", "down", "left", "right"].indexOf(v) === -1) return "";
        return v;
    }

    /**
     * Remplit un &lt;select&gt;. exclude : nom à omettre, ou tableau de noms (ex. l’autre liste).
     */
    function fillSelect(selectEl, options, placeholder, exclude) {
        selectEl.innerHTML = "";
        var opt0 = document.createElement("option");
        opt0.value = "";
        opt0.textContent = placeholder;
        selectEl.appendChild(opt0);
        var skip = new Set();
        if (exclude != null && exclude !== "") {
            if (Array.isArray(exclude)) {
                exclude.forEach(function (x) {
                    if (x) skip.add(x);
                });
            } else {
                skip.add(exclude);
            }
        }
        options.forEach(function (name) {
            if (skip.has(name)) return;
            var o = document.createElement("option");
            o.value = name;
            o.textContent = name;
            selectEl.appendChild(o);
        });
    }

    function setSelectValueIfPresent(selectEl, value) {
        if (!value) return;
        var ok = Array.prototype.some.call(selectEl.options, function (opt) {
            return opt.value === value;
        });
        if (ok) selectEl.value = value;
    }

    /**
     * Peuple un select avec des noms « simples » puis, dans un optgroup,
     * les packages sélectionnables. `exclude` : nom à omettre (dans les deux groupes).
     */
    function fillSelectWithPackages(selectEl, names, packages, placeholder, exclude) {
        selectEl.innerHTML = "";
        var opt0 = document.createElement("option");
        opt0.value = "";
        opt0.textContent = placeholder;
        selectEl.appendChild(opt0);
        names.forEach(function (name) {
            if (exclude && name === exclude) return;
            var o = document.createElement("option");
            o.value = name;
            o.textContent = name;
            selectEl.appendChild(o);
        });
        if (packages.length) {
            var group = document.createElement("optgroup");
            group.label = "Zones & packages";
            packages.forEach(function (name) {
                if (exclude && name === exclude) return;
                var o = document.createElement("option");
                o.value = name;
                o.textContent = name;
                o.setAttribute("data-uml-package", "1");
                group.appendChild(o);
            });
            if (group.childNodes.length) selectEl.appendChild(group);
        }
    }

    function isPackageOptionSelected(selectEl) {
        var opt = selectEl.options[selectEl.selectedIndex];
        return Boolean(opt && opt.getAttribute("data-uml-package") === "1");
    }

    /** Valeur du select prête pour PlantUML (quote si c'est un package). */
    function selectedEndpointToken(selectEl) {
        return isPackageOptionSelected(selectEl)
            ? toPlantUmlToken(selectEl.value)
            : selectEl.value;
    }

    /**
     * Enfant (classe) / parent (classe ou package) mutuellement exclusifs :
     * une classe ne peut pas être son propre parent.
     */
    function wireExtendsSelects(selChild, selParent, classes, packages) {
        function sync() {
            var childVal = selChild.value;
            var parentVal = selParent.value;
            fillSelectWithPackages(selParent, classes, packages, "— Choisir —", childVal || null);
            setSelectValueIfPresent(selParent, parentVal);
            var parentIsClass = classes.indexOf(selParent.value) !== -1;
            fillSelect(selChild, classes, "— Choisir —", parentIsClass ? selParent.value : null);
            setSelectValueIfPresent(selChild, childVal);
        }
        selChild.addEventListener("change", sync);
        selParent.addEventListener("change", sync);
        sync();
    }

    /**
     * Source / cible d'une relation, mutuellement exclusives, avec packages
     * sélectionnables dans les deux extrémités.
     */
    function wirePackageAwareExclusiveSelects(selA, selB, names, packages) {
        function sync() {
            var a = selA.value;
            var b = selB.value;
            fillSelectWithPackages(selB, names, packages, "— Choisir —", a || null);
            setSelectValueIfPresent(selB, b);
            fillSelectWithPackages(selA, names, packages, "— Choisir —", selB.value || null);
            setSelectValueIfPresent(selA, a);
        }
        selA.addEventListener("change", sync);
        selB.addEventListener("change", sync);
        sync();
    }

    /**
     * Implements : cible = interface ou package, réalisée par une classe.
     * Exclusions symétriques si un nom apparaît dans les deux pools.
     */
    function wireImplementsSelectsPkg(selI, interfaces, packages, selC, classes) {
        function sync() {
            var iface = selI.value;
            var cls = selC.value;
            fillSelectWithPackages(
                selI,
                interfaces,
                packages,
                "— Choisir —",
                cls && interfaces.indexOf(cls) !== -1 ? cls : null
            );
            setSelectValueIfPresent(selI, iface);
            fillSelect(
                selC,
                classes,
                "— Choisir —",
                selI.value && classes.indexOf(selI.value) !== -1 ? selI.value : null
            );
            setSelectValueIfPresent(selC, cls);
        }
        selI.addEventListener("change", sync);
        selC.addEventListener("change", sync);
        sync();
    }

    function init() {
        var textarea = document.getElementById("id_uml_text");
        if (!textarea) return;
        if (textarea.dataset.umlPreviewBound === "1") return;
        textarea.dataset.umlPreviewBound = "1";

        var form = textarea.closest("form");
        if (!form) return;

        var csrfToken = getCsrfToken();
        var debounceTimer = null;

        var previewLoading = document.getElementById("umlPreviewLoading");
        var previewFetchError = document.getElementById("umlPreviewFetchError");
        var previewImageWrap = document.getElementById("umlPreviewImageWrap");
        var previewImage = document.getElementById("umlPreviewImage");
        var previewEmpty = document.getElementById("umlPreviewEmpty");

        function setPreviewLoading(on) {
            if (previewLoading) previewLoading.classList.toggle("hidden", !on);
        }

        function setPreviewError(msg) {
            if (!previewFetchError) return;
            if (msg) {
                previewFetchError.textContent = msg;
                previewFetchError.classList.remove("hidden");
            } else {
                previewFetchError.textContent = "";
                previewFetchError.classList.add("hidden");
            }
        }

        function syncPanZoom() {
            if (!previewImageWrap || !window.GenPreviewPanZoom) return;
            GenPreviewPanZoom.init(previewImageWrap);
            GenPreviewPanZoom.reset(previewImageWrap);
        }

        function applyPreviewUrl(url) {
            if (!previewImageWrap || !previewImage) return;

            if (!url) {
                form.setAttribute("data-preview-url", "");
                previewImageWrap.classList.add("hidden");
                if (previewEmpty) previewEmpty.classList.remove("hidden");
                previewImage.removeAttribute("src");
                return;
            }

            form.setAttribute("data-preview-url", url);
            setPreviewError("");
            if (previewEmpty) previewEmpty.classList.add("hidden");
            previewImageWrap.classList.add("hidden");

            previewImage.onload = function () {
                previewImage.onload = null;
                previewImage.onerror = null;
                previewImageWrap.classList.remove("hidden");
                syncPanZoom();
            };

            previewImage.onerror = function () {
                previewImage.onload = null;
                previewImage.onerror = null;
                setPreviewError("Impossible de charger l'aperçu PlantUML.");
                previewImageWrap.classList.add("hidden");
                if (previewEmpty) previewEmpty.classList.remove("hidden");
                previewImage.removeAttribute("src");
            };

            if (previewImage.src !== url) {
                previewImage.src = url;
            } else if (previewImage.complete && previewImage.naturalWidth) {
                previewImage.onload();
            } else {
                previewImage.src = url;
            }
        }

        function updateUml(newUml) {
            textarea.value = String(newUml ?? "");
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }

        function refreshPreviewFromApi() {
            var value = textarea.value.trim();
            setPreviewError("");

            if (!value) {
                applyPreviewUrl("");
                return;
            }

            if (!apiUrl || !csrfToken) {
                setPreviewError("Configuration preview manquante.");
                return;
            }

            setPreviewLoading(true);
            var body = new FormData();
            body.append("uml_text", ensureStartEnd(value));
            body.append("csrfmiddlewaretoken", csrfToken);
            fetch(apiUrl, {
                method: "POST",
                body: body,
                headers: { "X-Requested-With": "XMLHttpRequest" },
            })
                .then(function (r) {
                    return r.json();
                })
                .then(function (data) {
                    setPreviewLoading(false);
                    if (data.preview_url) {
                        applyPreviewUrl(data.preview_url);
                    } else {
                        setPreviewError(data.error || "Impossible de générer l'aperçu.");
                    }
                })
                .catch(function () {
                    setPreviewLoading(false);
                    setPreviewError("Erreur réseau lors de l'aperçu.");
                });
        }

        textarea.addEventListener("input", function () {
            if (debounceTimer) clearTimeout(debounceTimer);
            debounceTimer = setTimeout(refreshPreviewFromApi, 2000);
        });

        var initialUrl = form.getAttribute("data-preview-url") || "";
        if (initialUrl) {
            applyPreviewUrl(initialUrl);
        } else if (textarea.value.trim()) {
            refreshPreviewFromApi();
        }

        /* ---------- Modale principale (aperçu user + aide) ---------- */
        var mainModal = document.getElementById("umlPreviewModal");
        var mainBackdrop = document.getElementById("umlPreviewBackdrop");
        var userBlock = document.getElementById("umlUserDiagramBlock");
        var helpBlock = document.getElementById("umlHelpBlock");
        var userDiagramImg = document.getElementById("umlUserDiagramImage");
        var openModalBtn = document.getElementById("openUmlPreviewModal");

        function closeMainModal() {
            if (!mainModal) return;
            mainModal.classList.add("hidden");
            document.body.classList.remove("overflow-hidden");
            if (userBlock) userBlock.classList.add("hidden");
            if (helpBlock) helpBlock.classList.add("hidden");
        }

        function openUserDiagram() {
            if (!mainModal || !userBlock || !helpBlock) return;
            var url = form.getAttribute("data-preview-url") || "";
            if (!url) return;
            if (userDiagramImg) userDiagramImg.src = url;
            helpBlock.classList.add("hidden");
            userBlock.classList.remove("hidden");
            mainModal.classList.remove("hidden");
            document.body.classList.add("overflow-hidden");
            if (window.GenPreviewPanZoom) {
                var modalCanvas = document.getElementById("umlUserDiagramCanvas");
                GenPreviewPanZoom.init(userBlock);
                if (modalCanvas) {
                    userDiagramImg.onload = function () {
                        userDiagramImg.onload = null;
                        GenPreviewPanZoom.reset(modalCanvas);
                    };
                    if (userDiagramImg.complete) {
                        GenPreviewPanZoom.reset(modalCanvas);
                    }
                }
            }
        }

        if (openModalBtn) openModalBtn.addEventListener("click", openUserDiagram);
        document.querySelectorAll(".closeUmlModalBtn").forEach(function (btn) {
            btn.addEventListener("click", closeMainModal);
        });
        if (mainBackdrop) {
            mainBackdrop.addEventListener("click", closeMainModal);
        }

        /* ---------- Modale UML Builder ---------- */
        var builderModal = document.getElementById("umlBuilderModal");
        var builderBackdrop = document.getElementById("umlBuilderModalBackdrop");
        var builderTitle = document.getElementById("umlBuilderModalTitle");
        var builderBody = document.getElementById("umlBuilderModalBody");
        var builderCancel = document.getElementById("umlBuilderModalCancel");
        var builderApply = document.getElementById("umlBuilderModalApply");
        var builderAction = null;

        function closeBuilderModal() {
            if (!builderModal) return;
            builderModal.classList.add("hidden");
            builderAction = null;
            if (builderBody) builderBody.innerHTML = "";
        }

        function openBuilderModal(action, uml) {
            if (!builderModal || !builderBody || !builderTitle) return;
            builderAction = action;
            if (builderApply) builderApply.classList.remove("hidden");
            var classes = extractClasses(uml);
            var interfaces = extractInterfaces(uml);
            var enums = extractEnums(uml);
            var packages = extractPackages(uml);
            builderBody.innerHTML = "";

            var labelClass =
                "block text-xs font-bold text-slate-600 mb-1.5 tracking-wide uppercase";
            var selectClass =
                "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-300";
            var inputClass =
                "w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-violet-400 focus:border-violet-300";

            /** Encadré pédagogique en tête de modale (citation + détail HTML). */
            function appendBuilderDesc(parent, o) {
                var el = document.createElement("div");
                el.className =
                    "rounded-xl border p-3 mb-4 text-[11px] leading-relaxed shadow-sm " +
                    (o.boxClass || "border-violet-200 bg-violet-50/90");
                var h = "";
                if (o.title) {
                    h +=
                        '<p class="font-bold uppercase tracking-[0.1em] text-[10px] mb-2 ' +
                        (o.titleClass || "text-violet-800") +
                        '">' +
                        o.title +
                        "</p>";
                }
                if (o.quote) {
                    h +=
                        '<p class="mb-2"><q class="text-[12px] font-semibold not-italic ' +
                        (o.quoteClass || "text-violet-900") +
                        '">' +
                        o.quote +
                        "</q></p>";
                }
                if (o.detailHtml) {
                    h +=
                        '<div class="' +
                        (o.detailClass || "text-slate-700") +
                        '">' +
                        o.detailHtml +
                        "</div>";
                }
                el.innerHTML = h;
                parent.appendChild(el);
            }

            /**
             * Bloc « direction d'affichage » : boussole (valeur stockée dans champ caché).
             */
            function appendLinkDirectionSelect(parent) {
                var box = document.createElement("div");
                box.className =
                    "mt-4 rounded-xl border border-violet-200/90 bg-gradient-to-br from-violet-50/90 to-fuchsia-50/40 p-3 shadow-sm";

                var title = document.createElement("p");
                title.className =
                    "text-xs font-black uppercase tracking-[0.1em] text-violet-800 mb-1";
                title.textContent = "Direction d'affichage du lien";
                box.appendChild(title);

                var sub = document.createElement("p");
                sub.className = "text-[10px] text-slate-600 mb-3 leading-snug";
                sub.innerHTML =
                    "Orientation <strong>précise</strong> du segment entre les deux éléments (PlantUML : <code class=\"text-[9px] bg-white/70 px-0.5 rounded\">-up-</code>, <code class=\"text-[9px] bg-white/70 px-0.5 rounded\">-right-</code>, etc.). Laisse <strong>Auto</strong> pour le placement automatique.";
                box.appendChild(sub);

                var hiddenDir = document.createElement("input");
                hiddenDir.type = "hidden";
                hiddenDir.id = "umlBuilderLinkDirection";
                hiddenDir.value = "";
                hiddenDir.setAttribute("aria-hidden", "true");
                box.appendChild(hiddenDir);

                var compass = document.createElement("div");
                compass.className = "flex flex-col items-center gap-1.5";
                var btnBase =
                    "uml-dir-btn min-w-[5.5rem] px-2 py-2 text-[11px] font-bold rounded-xl border transition-all shadow-sm ";
                var btnIdle =
                    "border-slate-200 bg-white text-slate-700 hover:bg-violet-100 hover:border-violet-200";
                var btnActive =
                    "ring-2 ring-violet-500 ring-offset-1 border-violet-400 bg-violet-100 text-violet-900";

                function makeDirButton(label, dirValue) {
                    var b = document.createElement("button");
                    b.type = "button";
                    b.setAttribute("data-uml-dir", dirValue);
                    b.setAttribute("aria-pressed", dirValue === "" ? "true" : "false");
                    b.className = btnBase + (dirValue === "" ? btnActive : btnIdle);
                    b.textContent = label;
                    return b;
                }

                var rowUp = document.createElement("div");
                rowUp.appendChild(makeDirButton("↑ Haut", "up"));
                compass.appendChild(rowUp);

                var rowMid = document.createElement("div");
                rowMid.className = "flex flex-wrap items-center justify-center gap-1.5";
                rowMid.appendChild(makeDirButton("← Gauche", "left"));
                rowMid.appendChild(makeDirButton("◎ Auto", ""));
                rowMid.appendChild(makeDirButton("Droite →", "right"));
                compass.appendChild(rowMid);

                var rowDown = document.createElement("div");
                rowDown.appendChild(makeDirButton("↓ Bas", "down"));
                compass.appendChild(rowDown);

                box.appendChild(compass);

                var allDirBtns = compass.querySelectorAll(".uml-dir-btn");

                function syncUiFromValue(val) {
                    hiddenDir.value = val;
                    allDirBtns.forEach(function (btn) {
                        var v = btn.getAttribute("data-uml-dir");
                        if (v === null) v = "";
                        var on = v === val;
                        btn.setAttribute("aria-pressed", on ? "true" : "false");
                        btn.className = btnBase + (on ? btnActive : btnIdle);
                    });
                }

                allDirBtns.forEach(function (btn) {
                    btn.addEventListener("click", function () {
                        var v = btn.getAttribute("data-uml-dir");
                        if (v === null) v = "";
                        syncUiFromValue(v);
                    });
                });

                syncUiFromValue("");

                parent.appendChild(box);
            }

            /**
             * Position de la note (note left|right|top|bottom of X) — boussole + champ caché.
             */
            function appendNotePositionCompass(parent) {
                var box = document.createElement("div");
                box.className =
                    "mt-4 rounded-xl border border-teal-200/90 bg-gradient-to-br from-teal-50/90 to-cyan-50/40 p-3 shadow-sm";

                var title = document.createElement("p");
                title.className =
                    "text-xs font-black uppercase tracking-[0.1em] text-teal-800 mb-1";
                title.textContent = "Position de la note";
                box.appendChild(title);

                var sub = document.createElement("p");
                sub.className = "text-[10px] text-slate-600 mb-3 leading-snug";
                sub.innerHTML =
                    "Comme pour les liens : <strong>Auto</strong> laisse PlantUML choisir le placement (<code class=\"text-[9px] bg-white/70 px-0.5 rounded\">note of MaClasse</code>), sinon une position précise (<code class=\"text-[9px] bg-white/70 px-0.5 rounded\">note right of …</code>).";
                box.appendChild(sub);

                var hiddenSide = document.createElement("input");
                hiddenSide.type = "hidden";
                hiddenSide.id = "umlBuilderNoteSide";
                hiddenSide.value = "";
                hiddenSide.setAttribute("aria-hidden", "true");
                box.appendChild(hiddenSide);

                var compass = document.createElement("div");
                compass.className = "flex flex-col items-center gap-1.5";
                var btnBase =
                    "uml-note-side-btn min-w-[5.5rem] px-2 py-2 text-[11px] font-bold rounded-xl border transition-all shadow-sm ";
                var btnIdle =
                    "border-slate-200 bg-white text-slate-700 hover:bg-teal-100 hover:border-teal-200";
                var btnActive =
                    "ring-2 ring-teal-500 ring-offset-1 border-teal-400 bg-teal-100 text-teal-900";

                function makeSideButton(label, sideValue) {
                    var b = document.createElement("button");
                    b.type = "button";
                    b.setAttribute("data-note-side", sideValue);
                    b.setAttribute(
                        "aria-pressed",
                        sideValue === "" ? "true" : "false"
                    );
                    b.className =
                        btnBase + (sideValue === "" ? btnActive : btnIdle);
                    b.textContent = label;
                    return b;
                }

                var rowUp = document.createElement("div");
                rowUp.appendChild(makeSideButton("↑ Haut", "top"));
                compass.appendChild(rowUp);

                var rowMid = document.createElement("div");
                rowMid.className = "flex flex-wrap items-center justify-center gap-1.5";
                rowMid.appendChild(makeSideButton("← Gauche", "left"));
                rowMid.appendChild(makeSideButton("◎ Auto", ""));
                rowMid.appendChild(makeSideButton("Droite →", "right"));
                compass.appendChild(rowMid);

                var rowDown = document.createElement("div");
                rowDown.appendChild(makeSideButton("↓ Bas", "bottom"));
                compass.appendChild(rowDown);

                box.appendChild(compass);

                var allBtns = compass.querySelectorAll(".uml-note-side-btn");

                function syncNoteSide(val) {
                    hiddenSide.value = val;
                    allBtns.forEach(function (btn) {
                        var v = btn.getAttribute("data-note-side");
                        if (v === null) v = "";
                        var on = v === val;
                        btn.setAttribute("aria-pressed", on ? "true" : "false");
                        btn.className = btnBase + (on ? btnActive : btnIdle);
                    });
                }

                allBtns.forEach(function (btn) {
                    btn.addEventListener("click", function () {
                        var v = btn.getAttribute("data-note-side");
                        if (v === null) v = "";
                        syncNoteSide(v);
                    });
                });

                syncNoteSide("");

                parent.appendChild(box);
            }

            /**
             * Sélecteur d'icône native OpenIconic (grille curée + recherche + suggestion).
             * Stocke le glyphe choisi dans un input caché `opts.hiddenId`.
             * Retourne { setSuggestion(glyph) } pour proposer une icône selon la saisie.
             */
            function appendIconPicker(parent, opts) {
                var box = document.createElement("div");
                box.className = "uml-icon-picker";

                var hidden = document.createElement("input");
                hidden.type = "hidden";
                hidden.id = opts.hiddenId;
                hidden.value = "";
                box.appendChild(hidden);

                var icons = window.UmlIcons;
                if (!icons || !Array.isArray(icons.groups)) {
                    parent.appendChild(box);
                    return { setSuggestion: function () {} };
                }

                var head = document.createElement("div");
                head.className = "uml-icon-picker__head";
                var current = document.createElement("div");
                current.className = "uml-icon-picker__current";
                var preview = document.createElement("span");
                var nameEl = document.createElement("span");
                nameEl.className = "uml-icon-picker__name";
                current.appendChild(preview);
                current.appendChild(nameEl);
                var clearBtn = document.createElement("button");
                clearBtn.type = "button";
                clearBtn.className = "uml-icon-picker__clear";
                clearBtn.textContent = "Aucune";
                head.appendChild(current);
                head.appendChild(clearBtn);
                box.appendChild(head);

                var search = document.createElement("input");
                search.type = "text";
                search.className = "uml-icon-picker__search";
                search.placeholder = "Rechercher une icône…";
                box.appendChild(search);

                var scroll = document.createElement("div");
                scroll.className = "uml-icon-picker__scroll";
                box.appendChild(scroll);
                parent.appendChild(box);

                var userLocked = false;

                function renderPreview(glyph) {
                    preview.innerHTML = "";
                    if (glyph) {
                        preview.className = "uml-icon-picker__preview";
                        var oi = document.createElement("span");
                        oi.className = "oi";
                        oi.setAttribute("data-glyph", glyph);
                        oi.setAttribute("aria-hidden", "true");
                        preview.appendChild(oi);
                        nameEl.textContent = "<&" + glyph + ">";
                    } else {
                        preview.className =
                            "uml-icon-picker__preview uml-icon-picker__preview--empty";
                        preview.textContent = "∅";
                        nameEl.textContent = "Aucune icône";
                    }
                }

                function markActive(glyph) {
                    scroll.querySelectorAll(".uml-icon-btn").forEach(function (b) {
                        b.classList.toggle(
                            "uml-icon-btn--active",
                            b.getAttribute("data-glyph") === glyph
                        );
                    });
                }

                function select(glyph, fromUser) {
                    hidden.value = glyph || "";
                    if (fromUser) userLocked = true;
                    renderPreview(glyph);
                    markActive(glyph);
                }

                function makeIconButton(glyph) {
                    var b = document.createElement("button");
                    b.type = "button";
                    b.className = "uml-icon-btn";
                    b.setAttribute("data-glyph", glyph);
                    b.title = glyph;
                    var oi = document.createElement("span");
                    oi.className = "oi";
                    oi.setAttribute("data-glyph", glyph);
                    oi.setAttribute("aria-hidden", "true");
                    b.appendChild(oi);
                    b.addEventListener("click", function () {
                        select(hidden.value === glyph ? "" : glyph, true);
                    });
                    return b;
                }

                function renderGrouped() {
                    scroll.innerHTML = "";
                    icons.groups.forEach(function (g) {
                        var lbl = document.createElement("p");
                        lbl.className = "uml-icon-group__label";
                        lbl.textContent = g.label;
                        scroll.appendChild(lbl);
                        var grid = document.createElement("div");
                        grid.className = "uml-icon-grid";
                        g.icons.forEach(function (gl) {
                            grid.appendChild(makeIconButton(gl));
                        });
                        scroll.appendChild(grid);
                    });
                    markActive(hidden.value);
                }

                function renderSearch(q) {
                    scroll.innerHTML = "";
                    var matches = icons.all.filter(function (n) {
                        return n.indexOf(q) !== -1;
                    });
                    if (!matches.length) {
                        var e = document.createElement("p");
                        e.className = "uml-icon-picker__empty";
                        e.textContent = "Aucune icône trouvée.";
                        scroll.appendChild(e);
                        return;
                    }
                    var grid = document.createElement("div");
                    grid.className = "uml-icon-grid";
                    matches.forEach(function (gl) {
                        grid.appendChild(makeIconButton(gl));
                    });
                    scroll.appendChild(grid);
                    markActive(hidden.value);
                }

                clearBtn.addEventListener("click", function () {
                    select("", true);
                });
                search.addEventListener("input", function () {
                    var q = search.value.trim().toLowerCase();
                    if (q) renderSearch(q);
                    else renderGrouped();
                });

                renderGrouped();
                if (opts.suggested && icons.has(opts.suggested)) {
                    select(opts.suggested, false);
                } else {
                    renderPreview("");
                }

                return {
                    setSuggestion: function (glyph) {
                        if (userLocked) return;
                        select(glyph && icons.has(glyph) ? glyph : "", false);
                    },
                };
            }

            if (action === "extends") {
                builderTitle.textContent = "Héritage (extends)";
                var canExtend =
                    classes.length >= 1 && (classes.length >= 2 || packages.length >= 1);
                if (!canExtend) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>une classe enfant</strong> et une cible parent (<strong>autre classe</strong> ou <strong>package</strong>) avant d’utiliser Extends.</p>';
                    builderApply.classList.add("hidden");
                } else {
                    builderApply.classList.remove("hidden");
                    appendBuilderDesc(builderBody, {
                        boxClass: "border-orange-200 bg-orange-50/95 text-orange-950",
                        title: "Héritage (extends)",
                        titleClass: "text-orange-900",
                        quote: "EST UN",
                        quoteClass: "text-orange-950",
                        detailHtml:
                            "La classe <strong>enfant</strong> est une sorte de <strong>parent</strong> (spécialisation / généralisation). Exemple : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-orange-200/80 font-mono\">Enfant --|&gt; Parent</code>. Le parent peut aussi être un <strong>package</strong>.",
                        detailClass: "text-orange-900/95",
                    });
                    var row1 = document.createElement("div");
                    row1.innerHTML =
                        '<label class="' +
                        labelClass +
                        '">Classe enfant</label>';
                    var selChild = document.createElement("select");
                    selChild.id = "umlBuilderExtendsChild";
                    selChild.className = selectClass;
                    fillSelect(selChild, classes, "— Choisir —");
                    row1.appendChild(selChild);
                    builderBody.appendChild(row1);

                    var row2 = document.createElement("div");
                    row2.className = "mt-4";
                    row2.innerHTML =
                        '<label class="' +
                        labelClass +
                        '">Classe ou package parent</label>';
                    var selParent = document.createElement("select");
                    selParent.id = "umlBuilderExtendsParent";
                    selParent.className = selectClass;
                    fillSelectWithPackages(selParent, classes, packages, "— Choisir —");
                    row2.appendChild(selParent);
                    builderBody.appendChild(row2);
                    wireExtendsSelects(selChild, selParent, classes, packages);
                    appendLinkDirectionSelect(builderBody);
                }
            } else if (action === "implements") {
                builderTitle.textContent = "Implémentation (interface)";
                var canImplement =
                    classes.length >= 1 && interfaces.length + packages.length >= 1;
                if (!canImplement) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>une classe</strong> et une cible (<strong>interface</strong> ou <strong>package</strong>) avant Implements.</p>';
                    builderApply.classList.add("hidden");
                } else {
                    builderApply.classList.remove("hidden");
                    appendBuilderDesc(builderBody, {
                        boxClass: "border-cyan-200 bg-cyan-50/95 text-cyan-950",
                        title: "Repère",
                        titleClass: "text-cyan-900",
                        quote: "La classe réalise le contrat de l’interface",
                        quoteClass: "text-cyan-950",
                        detailHtml:
                            "Choisis d’abord l’<strong>interface</strong> (ou un <strong>package</strong>), puis la <strong>classe</strong> qui l’implémente. Syntaxe : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-cyan-200/80 font-mono\">Interface &lt;|.. Classe</code>.",
                        detailClass: "text-cyan-900/95",
                    });
                    var r1 = document.createElement("div");
                    r1.innerHTML =
                        '<label class="' + labelClass + '">Interface ou package</label>';
                    var selI = document.createElement("select");
                    selI.id = "umlBuilderImplementsInterface";
                    selI.className = selectClass;
                    fillSelectWithPackages(selI, interfaces, packages, "— Choisir —");
                    r1.appendChild(selI);
                    builderBody.appendChild(r1);

                    var r2 = document.createElement("div");
                    r2.className = "mt-4";
                    r2.innerHTML =
                        '<label class="' + labelClass + '">Classe</label>';
                    var selC = document.createElement("select");
                    selC.id = "umlBuilderImplementsClass";
                    selC.className = selectClass;
                    fillSelect(selC, classes, "— Choisir —");
                    r2.appendChild(selC);
                    builderBody.appendChild(r2);
                    wireImplementsSelectsPkg(selI, interfaces, packages, selC, classes);
                    appendLinkDirectionSelect(builderBody);
                }
            } else if (
                action === "rel_aggregate" ||
                action === "rel_compose" ||
                action === "rel_depend" ||
                action === "rel_associate"
            ) {
                var relTitles = {
                    rel_aggregate: "Agrégation (o--)",
                    rel_compose: "Composition (*--)",
                    rel_depend: "Dépendance (..>)",
                    rel_associate: "Association (→)",
                };
                var relDescBlocks = {
                    rel_aggregate: {
                        boxClass: "border-amber-200 bg-amber-50/95 text-amber-950",
                        title: "Agrégation (o--)",
                        titleClass: "text-amber-900",
                        quote: "Je possède (mais tu es libre)",
                        quoteClass: "text-amber-950",
                        detailHtml:
                            "Côté <strong>contenant</strong> (agrégat) puis <strong>partie</strong> : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-amber-200/80 font-mono\">Contenant o-- Partie</code>.",
                        detailClass: "text-amber-900/95",
                    },
                    rel_compose: {
                        boxClass: "border-emerald-200 bg-emerald-50/95 text-emerald-950",
                        title: "Composition (*--)",
                        titleClass: "text-emerald-900",
                        quote: "A UN",
                        quoteClass: "text-emerald-950",
                        detailHtml:
                            "La relation <strong>« A UN »</strong> (forte) : côté <strong>composite</strong> puis <strong>composant</strong>. Exemple : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-emerald-200/80 font-mono\">Composite *-- Composant</code>.",
                        detailClass: "text-emerald-900/95",
                    },
                    rel_depend: {
                        boxClass: "border-sky-200 bg-sky-50/95 text-sky-950",
                        title: "Dépendance (..>)",
                        titleClass: "text-sky-900",
                        quote: "J'utilise ponctuellement",
                        quoteClass: "text-sky-950",
                        detailHtml:
                            "La <strong>source</strong> dépend de la <strong>cible</strong> (usage faible, souvent temporaire). Exemple : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-sky-200/80 font-mono\">A ..&gt; B</code>.",
                        detailClass: "text-sky-900/95",
                    },
                    rel_associate: {
                        boxClass: "border-purple-200 bg-purple-50/95 text-purple-950",
                        title: "Association (→)",
                        titleClass: "text-purple-900",
                        quote: "Je connais",
                        quoteClass: "text-purple-950",
                        detailHtml:
                            "Lien structurel avec <strong>sens</strong> de la flèche (référence durable). Exemple : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-purple-200/80 font-mono\">A --&gt; B</code>.",
                        detailClass: "text-purple-900/95",
                    },
                };
                builderTitle.textContent = relTitles[action] || "Relation";
                var typeNames = extractTypeNames(uml);
                if (typeNames.length + packages.length < 2) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>deux</strong> éléments (classe, interface, enum ou package) avant d’ajouter une relation.</p>';
                    builderApply.classList.add("hidden");
                } else {
                    builderApply.classList.remove("hidden");
                    var rd = relDescBlocks[action];
                    if (rd) appendBuilderDesc(builderBody, rd);

                    var rf = document.createElement("div");
                    rf.innerHTML =
                        '<label class="' + labelClass + '">Source (départ)</label>';
                    var selFrom = document.createElement("select");
                    selFrom.id = "umlBuilderRelFrom";
                    selFrom.className = selectClass;
                    fillSelectWithPackages(selFrom, typeNames, packages, "— Choisir —");
                    rf.appendChild(selFrom);
                    builderBody.appendChild(rf);

                    var rt = document.createElement("div");
                    rt.className = "mt-4";
                    rt.innerHTML =
                        '<label class="' + labelClass + '">Cible (arrivée)</label>';
                    var selTo = document.createElement("select");
                    selTo.id = "umlBuilderRelTo";
                    selTo.className = selectClass;
                    fillSelectWithPackages(selTo, typeNames, packages, "— Choisir —");
                    rt.appendChild(selTo);
                    builderBody.appendChild(rt);

                    wirePackageAwareExclusiveSelects(selFrom, selTo, typeNames, packages);
                    appendLinkDirectionSelect(builderBody);

                    var rl = document.createElement("div");
                    rl.className = "mt-4";
                    rl.innerHTML =
                        '<label class="' +
                        labelClass +
                        '">Libellé sur la flèche (optionnel)</label>';
                    var inpLbl = document.createElement("input");
                    inpLbl.type = "text";
                    inpLbl.id = "umlBuilderLinkLabel";
                    inpLbl.className = inputClass;
                    inpLbl.placeholder = "ex. utilise, possède, contient…";
                    rl.appendChild(inpLbl);
                    builderBody.appendChild(rl);

                    var rm = document.createElement("div");
                    rm.className = "mt-4";
                    rm.innerHTML =
                        '<label class="' +
                        labelClass +
                        '">Multiplicité (cardinalité)</label>' +
                        '<p class="text-[10px] text-slate-500 mb-1.5 leading-snug">Cardinalité Source → Cible, posée aux deux extrémités (PlantUML : <code class="text-[9px] bg-slate-100 px-0.5 rounded">A "1" --&gt; "*" B</code>).</p>';
                    var selMult = document.createElement("select");
                    selMult.id = "umlBuilderRelMultiplicity";
                    selMult.className = selectClass;
                    [
                        ["", "Auto / aucune"],
                        ["one_to_one", "1 → 1  (OneToOne)"],
                        ["one_to_many", "1 → n  (OneToMany)"],
                        ["many_to_one", "n → 1  (ManyToOne)"],
                        ["many_to_many", "n → n  (ManyToMany)"],
                    ].forEach(function (pair) {
                        var o = document.createElement("option");
                        o.value = pair[0];
                        o.textContent = pair[1];
                        selMult.appendChild(o);
                    });
                    rm.appendChild(selMult);
                    builderBody.appendChild(rm);
                }
            } else if (
                action === "add_class" ||
                action === "add_abstract_class" ||
                action === "add_interface" ||
                action === "add_enum"
            ) {
                var titles = {
                    add_class: "Ajouter une classe",
                    add_abstract_class: "Ajouter une classe abstraite",
                    add_interface: "Ajouter une interface",
                    add_enum: "Ajouter une énumération",
                };
                builderTitle.textContent = titles[action] || "UML Builder";
                builderApply.classList.remove("hidden");
                var typeHints = {
                    add_class: {
                        boxClass: "border-blue-200 bg-blue-50/95 text-blue-950",
                        title: "Classe concrète",
                        titleClass: "text-blue-900",
                        quote: "Type métier avec état et comportement",
                        quoteClass: "text-blue-950",
                        detailHtml:
                            "Identifiant PlantUML sans espace (ex. <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">OrderService</code>).",
                        detailClass: "text-blue-900/90",
                    },
                    add_abstract_class: {
                        boxClass: "border-indigo-200 bg-indigo-50/95 text-indigo-950",
                        title: "Classe abstraite",
                        titleClass: "text-indigo-900",
                        quote: "Modèle à spécialiser",
                        quoteClass: "text-indigo-950",
                        detailHtml:
                            "Ne peut pas être instanciée seule ; sert de base à des sous-classes concrètes.",
                        detailClass: "text-indigo-900/90",
                    },
                    add_interface: {
                        boxClass: "border-fuchsia-200 bg-fuchsia-50/95 text-fuchsia-950",
                        title: "Interface",
                        titleClass: "text-fuchsia-900",
                        quote: "Contrat : signatures sans implémentation",
                        quoteClass: "text-fuchsia-950",
                        detailHtml:
                            "Les classes <strong>implémentent</strong> l’interface (tuile Implements ou <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">&lt;|..</code>).",
                        detailClass: "text-fuchsia-900/90",
                    },
                    add_enum: {
                        boxClass: "border-lime-200 bg-lime-50/95 text-lime-950",
                        title: "Énumération",
                        titleClass: "text-lime-900",
                        quote: "Liste fermée de valeurs",
                        quoteClass: "text-lime-950",
                        detailHtml:
                            "Utile pour états, codes, statuts. Une valeur par défaut <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">VALUE</code> est insérée, à adapter.",
                        detailClass: "text-lime-900/90",
                    },
                };
                var th = typeHints[action];
                if (th) appendBuilderDesc(builderBody, th);

                var wrap = document.createElement("div");
                wrap.innerHTML =
                    '<label class="' +
                    labelClass +
                    '">Nom</label>';
                var inp = document.createElement("input");
                inp.type = "text";
                inp.id = "umlBuilderNameInput";
                inp.className = inputClass;
                inp.placeholder = "ex. UserRepository";
                wrap.appendChild(inp);
                builderBody.appendChild(wrap);

                var typeIconPicker = appendIconPicker(builderBody, {
                    hiddenId: "umlBuilderTypeIcon",
                    suggested: "",
                });
                if (window.UmlIcons) {
                    inp.addEventListener("input", function () {
                        var v = inp.value.trim();
                        typeIconPicker.setSuggestion(
                            v ? window.UmlIcons.suggestForClass(v) : ""
                        );
                    });
                }
            } else if (action === "add_attribute" || action === "add_method") {
                var isMethod = action === "add_method";
                builderTitle.textContent = isMethod
                    ? "Ajouter une méthode"
                    : "Ajouter un attribut";
                var memberTargets = Array.from(
                    new Set([].concat(classes, interfaces))
                );
                if (memberTargets.length < 1) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins une <strong>classe</strong> ou une <strong>interface</strong> avant d’ajouter ' +
                        (isMethod ? "une méthode" : "un attribut") +
                        ".</p>";
                    builderApply.classList.add("hidden");
                } else {
                    builderApply.classList.remove("hidden");
                    appendBuilderDesc(
                        builderBody,
                        isMethod
                            ? {
                                  boxClass: "border-pink-200 bg-pink-50/95 text-pink-950",
                                  title: "Méthode",
                                  titleClass: "text-pink-900",
                                  quote: "Un comportement de la classe / interface",
                                  quoteClass: "text-pink-950",
                                  detailHtml:
                                      "Visibilité <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">+</code> public, <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">-</code> privé, <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">#</code> protégé. Exemple : <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">+ login(email: String) : bool</code>.",
                                  detailClass: "text-pink-900/90",
                              }
                            : {
                                  boxClass: "border-rose-200 bg-rose-50/95 text-rose-950",
                                  title: "Attribut",
                                  titleClass: "text-rose-900",
                                  quote: "Une donnée / un état de la classe",
                                  quoteClass: "text-rose-950",
                                  detailHtml:
                                      "Visibilité <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">+</code> public, <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">-</code> privé, <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">#</code> protégé. Exemple : <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">- password : String</code>.",
                                  detailClass: "text-rose-900/90",
                              }
                    );

                    var mt = document.createElement("div");
                    mt.innerHTML =
                        '<label class="' +
                        labelClass +
                        '">Classe / interface cible</label>';
                    var selTarget = document.createElement("select");
                    selTarget.id = "umlBuilderMemberTarget";
                    selTarget.className = selectClass;
                    fillSelect(selTarget, memberTargets, "— Choisir —");
                    mt.appendChild(selTarget);
                    builderBody.appendChild(mt);

                    var mv = document.createElement("div");
                    mv.className = "mt-4";
                    mv.innerHTML =
                        '<label class="' + labelClass + '">Visibilité</label>';
                    var selVis = document.createElement("select");
                    selVis.id = "umlBuilderMemberVisibility";
                    selVis.className = selectClass;
                    [
                        ["+", "Public ( + )"],
                        ["-", "Privé ( - )"],
                        ["#", "Protégé ( # )"],
                    ].forEach(function (pair) {
                        var o = document.createElement("option");
                        o.value = pair[0];
                        o.textContent = pair[1];
                        selVis.appendChild(o);
                    });
                    mv.appendChild(selVis);
                    builderBody.appendChild(mv);

                    var mn = document.createElement("div");
                    mn.className = "mt-4";
                    mn.innerHTML =
                        '<label class="' + labelClass + '">Nom</label>';
                    var inpName = document.createElement("input");
                    inpName.type = "text";
                    inpName.id = "umlBuilderMemberName";
                    inpName.className = inputClass;
                    inpName.placeholder = isMethod ? "ex. login" : "ex. email";
                    mn.appendChild(inpName);
                    builderBody.appendChild(mn);

                    if (isMethod) {
                        var mp = document.createElement("div");
                        mp.className = "mt-4";
                        mp.innerHTML =
                            '<label class="' +
                            labelClass +
                            '">Paramètres (optionnel)</label>';
                        var inpParams = document.createElement("input");
                        inpParams.type = "text";
                        inpParams.id = "umlBuilderMethodParams";
                        inpParams.className = inputClass;
                        inpParams.placeholder = "ex. email: String, force: bool";
                        mp.appendChild(inpParams);
                        builderBody.appendChild(mp);

                        var mr = document.createElement("div");
                        mr.className = "mt-4";
                        mr.innerHTML =
                            '<label class="' +
                            labelClass +
                            '">Type de retour (optionnel)</label>';
                        var inpRet = document.createElement("input");
                        inpRet.type = "text";
                        inpRet.id = "umlBuilderMethodReturn";
                        inpRet.className = inputClass;
                        inpRet.placeholder = "ex. bool";
                        mr.appendChild(inpRet);
                        builderBody.appendChild(mr);
                    } else {
                        var mty = document.createElement("div");
                        mty.className = "mt-4";
                        mty.innerHTML =
                            '<label class="' +
                            labelClass +
                            '">Type (optionnel)</label>';
                        var inpType = document.createElement("input");
                        inpType.type = "text";
                        inpType.id = "umlBuilderAttrType";
                        inpType.className = inputClass;
                        inpType.placeholder = "ex. String";
                        mty.appendChild(inpType);
                        builderBody.appendChild(mty);
                    }

                    var memberIconPicker = appendIconPicker(builderBody, {
                        hiddenId: "umlBuilderMemberIcon",
                        suggested: "",
                    });
                    if (window.UmlIcons) {
                        inpName.addEventListener("input", function () {
                            var v = inpName.value.trim();
                            var suggestion = v
                                ? isMethod
                                    ? window.UmlIcons.suggestForMethod(v)
                                    : window.UmlIcons.suggestForAttribute(v)
                                : "";
                            memberIconPicker.setSuggestion(suggestion);
                        });
                    }
                }
            } else if (action === "note") {
                builderTitle.textContent = "Ajouter une note";
                var allTargets = Array.from(
                    new Set([].concat(classes, interfaces, enums))
                );
                if (allTargets.length < 1) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins une classe, interface ou enum avant une note.</p>';
                    builderApply.classList.add("hidden");
                } else {
                    builderApply.classList.remove("hidden");
                    appendBuilderDesc(builderBody, {
                        boxClass: "border-teal-200 bg-teal-50/95 text-teal-950",
                        title: "Note",
                        titleClass: "text-teal-900",
                        quote: "Commentaire sur le diagramme",
                        quoteClass: "text-teal-950",
                        detailHtml:
                            "Texte libre attaché à un élément ; n’ajoute pas de relation UML. Utile pour expliquer un choix ou une contrainte.",
                        detailClass: "text-teal-900/90",
                    });
                    var nt = document.createElement("div");
                    nt.innerHTML =
                        '<label class="' + labelClass + '">Élément cible</label>';
                    var selT = document.createElement("select");
                    selT.id = "umlBuilderNoteTarget";
                    selT.className = selectClass;
                    fillSelect(selT, allTargets, "— Choisir —");
                    nt.appendChild(selT);
                    builderBody.appendChild(nt);

                    appendNotePositionCompass(builderBody);

                    var nt2 = document.createElement("div");
                    nt2.className = "mt-4";
                    nt2.innerHTML =
                        '<label class="' + labelClass + '">Texte</label>';
                    var ta = document.createElement("textarea");
                    ta.id = "umlBuilderNoteText";
                    ta.rows = 3;
                    ta.className = inputClass + " font-sans";
                    ta.placeholder = "Texte de la note…";
                    nt2.appendChild(ta);
                    builderBody.appendChild(nt2);
                }
            } else if (action === "add_package") {
                builderTitle.textContent = "Ajouter un package";
                builderApply.classList.remove("hidden");
                appendBuilderDesc(builderBody, {
                    boxClass: "border-sky-200 bg-sky-50/95 text-sky-950",
                    title: "Package / namespace",
                    titleClass: "text-sky-900",
                    quote: "Regrouper des éléments liés",
                    quoteClass: "text-sky-950",
                    detailHtml:
                        "Crée une zone <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">package \"Nom\" { … }</code>. Ajoute ensuite des classes à l'intérieur, ou relie le package à d'autres éléments.",
                    detailClass: "text-sky-900/95",
                });
                var pkgWrap = document.createElement("div");
                pkgWrap.innerHTML =
                    '<label class="' + labelClass + '">Nom du package</label>';
                var pkgInp = document.createElement("input");
                pkgInp.type = "text";
                pkgInp.id = "umlBuilderPackageName";
                pkgInp.className = inputClass;
                pkgInp.placeholder = "ex. domain, infra, application…";
                pkgWrap.appendChild(pkgInp);
                builderBody.appendChild(pkgWrap);
            } else if (action === "add_database") {
                builderTitle.textContent = "Zone base de données";
                builderApply.classList.remove("hidden");
                appendBuilderDesc(builderBody, {
                    boxClass: "border-emerald-200 bg-emerald-50/95 text-emerald-950",
                    title: "Base de données (database)",
                    titleClass: "text-emerald-900",
                    quote: "Un stockage persistant",
                    quoteClass: "text-emerald-950",
                    detailHtml:
                        "Zone native <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">database \"Nom\" as alias</code>. L'alias sert d'extrémité de lien (ex. <code class=\"text-[10px] bg-white/80 px-1 rounded font-mono\">Parser --&gt; postgres</code>).",
                    detailClass: "text-emerald-900/95",
                });

                var dbNameWrap = document.createElement("div");
                dbNameWrap.innerHTML =
                    '<label class="' + labelClass + '">Nom affiché</label>';
                var dbName = document.createElement("input");
                dbName.type = "text";
                dbName.id = "umlBuilderDbName";
                dbName.className = inputClass;
                dbName.value = "Stockage (PostgreSQL)";
                dbNameWrap.appendChild(dbName);
                builderBody.appendChild(dbNameWrap);

                var dbAliasWrap = document.createElement("div");
                dbAliasWrap.className = "mt-4";
                dbAliasWrap.innerHTML =
                    '<label class="' + labelClass + '">Alias (référence courte)</label>';
                var dbAlias = document.createElement("input");
                dbAlias.type = "text";
                dbAlias.id = "umlBuilderDbAlias";
                dbAlias.className = inputClass;
                dbAlias.value = "postgres";
                dbAlias.placeholder = "ex. postgres";
                dbAliasWrap.appendChild(dbAlias);
                builderBody.appendChild(dbAliasWrap);

                var dbSkelWrap = document.createElement("label");
                dbSkelWrap.className =
                    "mt-4 flex items-center gap-2 text-xs font-semibold text-slate-600 cursor-pointer";
                var dbSkel = document.createElement("input");
                dbSkel.type = "checkbox";
                dbSkel.id = "umlBuilderDbSkeleton";
                dbSkel.checked = true;
                dbSkel.className = "uml-db-check";
                dbSkelWrap.appendChild(dbSkel);
                var dbSkelTxt = document.createElement("span");
                dbSkelTxt.textContent =
                    "Générer le squelette (folder « Tables » + table « Données »)";
                dbSkelWrap.appendChild(dbSkelTxt);
                builderBody.appendChild(dbSkelWrap);

                appendIconPicker(builderBody, {
                    hiddenId: "umlBuilderDbIcon",
                    suggested: "data-transfer-download",
                });
            }

            builderModal.classList.remove("hidden");
        }

        if (builderCancel) builderCancel.addEventListener("click", closeBuilderModal);
        if (builderBackdrop) builderBackdrop.addEventListener("click", closeBuilderModal);

        function isBuilderApplyVisible() {
            return builderApply && !builderApply.classList.contains("hidden");
        }

        function applyBuilderModal() {
            var uml = textarea.value ?? "";
            if (!builderAction) return;

            /** Stéréotype d'icône native pour une déclaration de type (`<< <&x> >>`). */
            function typeStereotype() {
                var el = document.getElementById("umlBuilderTypeIcon");
                return el && el.value ? " << <&" + el.value + "> >>" : "";
            }

            if (builderAction === "extends") {
                var c = document.getElementById("umlBuilderExtendsChild");
                var p = document.getElementById("umlBuilderExtendsParent");
                if (!c || !p || !c.value || !p.value) {
                    window.alert("Choisis une classe enfant et une classe parent.");
                    return;
                }
                if (c.value === p.value) {
                    window.alert("Enfant et parent doivent être différents.");
                    return;
                }
                var parentToken = selectedEndpointToken(p);
                var dirE = getBuilderLinkDirection();
                var lineE =
                    dirE !== ""
                        ? c.value + " -" + dirE + "-|> " + parentToken
                        : c.value + " --|> " + parentToken;
                updateUml(insertBeforeEnduml(uml, lineE));
            } else if (builderAction === "implements") {
                var ii = document.getElementById("umlBuilderImplementsInterface");
                var cc = document.getElementById("umlBuilderImplementsClass");
                if (!ii || !cc || !ii.value || !cc.value) {
                    window.alert("Choisis une interface (ou package) et une classe.");
                    return;
                }
                var ifaceToken = selectedEndpointToken(ii);
                var dirI = getBuilderLinkDirection();
                var lineI =
                    dirI !== ""
                        ? ifaceToken + " <|-" + dirI + ".. " + cc.value
                        : ifaceToken + " <|.. " + cc.value;
                updateUml(insertBeforeEnduml(uml, lineI));
            } else if (
                builderAction === "rel_aggregate" ||
                builderAction === "rel_compose" ||
                builderAction === "rel_depend" ||
                builderAction === "rel_associate"
            ) {
                var rf = document.getElementById("umlBuilderRelFrom");
                var rt = document.getElementById("umlBuilderRelTo");
                var lb = document.getElementById("umlBuilderLinkLabel");
                if (!rf || !rt || !rf.value || !rt.value) {
                    window.alert("Choisis une source et une cible.");
                    return;
                }
                if (rf.value === rt.value) {
                    window.alert("Source et cible doivent être différentes.");
                    return;
                }
                var lbl = lb && lb.value ? lb.value.trim() : "";
                var dirR = getBuilderLinkDirection();
                var mid =
                    builderAction === "rel_aggregate"
                        ? dirR !== ""
                          ? " -" + dirR + "-o "
                          : " o-- "
                        : builderAction === "rel_compose"
                          ? dirR !== ""
                            ? " -" + dirR + "-*-- "
                            : " *-- "
                          : builderAction === "rel_depend"
                            ? dirR !== ""
                              ? " -" + dirR + "..> "
                              : " ..> "
                            : dirR !== ""
                              ? " -" + dirR + "-> "
                              : " --> ";
                var multEl = document.getElementById("umlBuilderRelMultiplicity");
                var cards = multiplicityCards(multEl ? multEl.value : "");
                var fromCard = cards[0];
                var toCard = cards[1];
                var fromToken = selectedEndpointToken(rf);
                var toToken = selectedEndpointToken(rt);
                var lineR =
                    fromToken +
                    (fromCard ? ' "' + fromCard + '"' : "") +
                    mid +
                    (toCard ? '"' + toCard + '" ' : "") +
                    toToken;
                if (lbl) lineR += " : " + lbl;
                updateUml(insertBeforeEnduml(uml, lineR));
            } else if (builderAction === "add_class") {
                var n = document.getElementById("umlBuilderNameInput");
                var name = (n && n.value ? n.value : "").trim();
                if (!name || !isValidIdentifier(name)) {
                    window.alert("Nom invalide (lettres, chiffres, _ ; pas d’espace).");
                    return;
                }
                updateUml(
                    insertBeforeEnduml(uml, "class " + name + typeStereotype() + " {\n}")
                );
            } else if (builderAction === "add_abstract_class") {
                var n2 = document.getElementById("umlBuilderNameInput");
                var name2 = (n2 && n2.value ? n2.value : "").trim();
                if (!name2 || !isValidIdentifier(name2)) {
                    window.alert("Nom invalide.");
                    return;
                }
                updateUml(
                    insertBeforeEnduml(
                        uml,
                        "abstract class " + name2 + typeStereotype() + " {\n}"
                    )
                );
            } else if (builderAction === "add_interface") {
                var n3 = document.getElementById("umlBuilderNameInput");
                var name3 = (n3 && n3.value ? n3.value : "").trim();
                if (!name3 || !isValidIdentifier(name3)) {
                    window.alert("Nom invalide.");
                    return;
                }
                updateUml(
                    insertBeforeEnduml(
                        uml,
                        "interface " + name3 + typeStereotype() + " {\n}"
                    )
                );
            } else if (builderAction === "add_enum") {
                var n4 = document.getElementById("umlBuilderNameInput");
                var name4 = (n4 && n4.value ? n4.value : "").trim();
                if (!name4 || !isValidIdentifier(name4)) {
                    window.alert("Nom invalide.");
                    return;
                }
                updateUml(
                    insertBeforeEnduml(
                        uml,
                        "enum " + name4 + typeStereotype() + " {\n  VALUE\n}"
                    )
                );
            } else if (
                builderAction === "add_attribute" ||
                builderAction === "add_method"
            ) {
                var isM = builderAction === "add_method";
                var tgt = document.getElementById("umlBuilderMemberTarget");
                var vis = document.getElementById("umlBuilderMemberVisibility");
                var nm = document.getElementById("umlBuilderMemberName");
                if (!tgt || !tgt.value) {
                    window.alert("Choisis une classe ou une interface cible.");
                    return;
                }
                var memberName = (nm && nm.value ? nm.value : "").trim();
                if (!memberName || !isValidIdentifier(memberName)) {
                    window.alert("Nom invalide (lettres, chiffres, _ ; pas d’espace).");
                    return;
                }
                var visSym =
                    vis && ["+", "-", "#"].indexOf(vis.value) !== -1
                        ? vis.value
                        : "+";
                var iconElM = document.getElementById("umlBuilderMemberIcon");
                var iconTokM = iconElM && iconElM.value ? "<&" + iconElM.value + "> " : "";
                var memberLine;
                if (isM) {
                    var prm = document.getElementById("umlBuilderMethodParams");
                    var ret = document.getElementById("umlBuilderMethodReturn");
                    var paramsTxt = (prm && prm.value ? prm.value : "").trim();
                    var retTxt = (ret && ret.value ? ret.value : "").trim();
                    memberLine =
                        visSym + " " + iconTokM + memberName + "(" + paramsTxt + ")";
                    if (retTxt) memberLine += " : " + retTxt;
                } else {
                    var typ = document.getElementById("umlBuilderAttrType");
                    var typeTxt = (typ && typ.value ? typ.value : "").trim();
                    memberLine = visSym + " " + iconTokM + memberName;
                    if (typeTxt) memberLine += " : " + typeTxt;
                }
                updateUml(insertMemberIntoType(uml, tgt.value, memberLine));
            } else if (builderAction === "note") {
                var t = document.getElementById("umlBuilderNoteTarget");
                var s = document.getElementById("umlBuilderNoteSide");
                var tx = document.getElementById("umlBuilderNoteText");
                if (!t || !t.value) {
                    window.alert("Choisis un élément cible.");
                    return;
                }
                var sideRaw = s && s.value != null ? String(s.value).trim().toLowerCase() : "";
                var side =
                    ["left", "right", "top", "bottom"].indexOf(sideRaw) !== -1
                        ? sideRaw
                        : "";
                var txt = (tx && tx.value ? tx.value : "").trim() || "Note";
                var block =
                    side === ""
                        ? "note of " +
                          t.value +
                          "\n  " +
                          txt +
                          "\nend note"
                        : "note " +
                          side +
                          " of " +
                          t.value +
                          "\n  " +
                          txt +
                          "\nend note";
                updateUml(insertBeforeEnduml(uml, block));
            } else if (builderAction === "add_package") {
                var pkg = document.getElementById("umlBuilderPackageName");
                var pkgName = (pkg && pkg.value ? pkg.value : "").trim();
                if (!pkgName) {
                    window.alert("Renseigne un nom de package.");
                    return;
                }
                updateUml(insertBeforeEnduml(uml, 'package "' + pkgName + '" {\n}'));
            } else if (builderAction === "add_database") {
                var dbN = document.getElementById("umlBuilderDbName");
                var dbA = document.getElementById("umlBuilderDbAlias");
                var dbS = document.getElementById("umlBuilderDbSkeleton");
                var dbI = document.getElementById("umlBuilderDbIcon");
                var dbNameVal =
                    (dbN && dbN.value ? dbN.value : "").trim() || "Base de données";
                var dbAliasVal = (dbA && dbA.value ? dbA.value : "").trim();
                var dbHeader =
                    'database "' +
                    dbNameVal +
                    '"' +
                    (dbAliasVal && isValidIdentifier(dbAliasVal) ? " as " + dbAliasVal : "");
                var dbBlock;
                if (dbS && dbS.checked) {
                    var dbIconTok = dbI && dbI.value ? "<&" + dbI.value + "> " : "";
                    dbBlock =
                        dbHeader +
                        " {\n" +
                        '  folder "Tables" {\n' +
                        '    class "Données" {\n' +
                        "      + " +
                        dbIconTok +
                        "Valeurs\n" +
                        "    }\n" +
                        "  }\n" +
                        "}";
                } else {
                    dbBlock = dbHeader + " {\n}";
                }
                updateUml(insertBeforeEnduml(uml, dbBlock));
            }

            closeBuilderModal();
        }

        if (builderApply) {
            builderApply.addEventListener("click", applyBuilderModal);
        }

        /* Entrée = valider la modale (Ctrl+Entrée dans le textarea « note » pour garder la ligne) */
        if (builderModal) {
            builderModal.addEventListener("keydown", function (e) {
                if (e.key !== "Enter") return;
                if (builderModal.classList.contains("hidden")) return;
                if (!isBuilderApplyVisible()) return;

                var t = e.target;
                var tag = t && t.tagName ? t.tagName.toUpperCase() : "";
                if (tag === "TEXTAREA" && t.id === "umlBuilderNoteText") {
                    if (!e.ctrlKey && !e.metaKey) return;
                }
                if (tag === "BUTTON") {
                    if (t.id === "umlBuilderModalCancel") return;
                    if (t.id === "umlBuilderModalApply") {
                        e.preventDefault();
                        applyBuilderModal();
                    }
                    return;
                }

                e.preventDefault();
                applyBuilderModal();
            });
        }

        function handleBuilderAction(action) {
            var uml = textarea.value ?? "";

            if (action === "start") {
                updateUml("@startuml\n\n@enduml");
                return;
            }

            if (
                action === "extends" ||
                action === "implements" ||
                action === "rel_aggregate" ||
                action === "rel_compose" ||
                action === "rel_depend" ||
                action === "rel_associate" ||
                action === "add_class" ||
                action === "add_abstract_class" ||
                action === "add_interface" ||
                action === "add_enum" ||
                action === "add_attribute" ||
                action === "add_method" ||
                action === "note" ||
                action === "add_package" ||
                action === "add_database"
            ) {
                openBuilderModal(action, uml);
                return;
            }
        }

        var builderItems = document.querySelectorAll(".uml-builder-item");

        function onBuilderDrop(e) {
            e.preventDefault();
            var act = e.dataTransfer ? e.dataTransfer.getData("text/plain") : "";
            if (act) handleBuilderAction(act);
        }

        function onBuilderDragOver(e) {
            e.preventDefault();
            if (e.dataTransfer) e.dataTransfer.dropEffect = "copy";
        }

        /* Glisser-déposer des tuiles sur le source PlantUML */
        var sourceDropHighlightClasses = [
            "ring-2",
            "ring-violet-400",
            "ring-offset-2",
            "border-violet-300",
        ];

        function setSourceDropHighlight(on) {
            sourceDropHighlightClasses.forEach(function (cls) {
                textarea.classList.toggle(cls, !!on);
            });
        }

        function clearSourceDropHighlight() {
            setSourceDropHighlight(false);
        }

        textarea.addEventListener("dragenter", function (e) {
            e.preventDefault();
            setSourceDropHighlight(true);
        });
        textarea.addEventListener("dragleave", function (e) {
            var rel = e.relatedTarget;
            if (!rel || !textarea.contains(rel)) clearSourceDropHighlight();
        });
        textarea.addEventListener("dragover", function (e) {
            onBuilderDragOver(e);
            setSourceDropHighlight(true);
        });
        textarea.addEventListener("drop", function (e) {
            clearSourceDropHighlight();
            onBuilderDrop(e);
            textarea.focus();
        });
        document.addEventListener("dragend", function () {
            clearSourceDropHighlight();
        });

        builderItems.forEach(function (item) {
            var act = item.getAttribute("data-action") || "";
            item.addEventListener("dragstart", function (e) {
                e.dataTransfer.setData("text/plain", act);
                e.dataTransfer.effectAllowed = "copy";
            });
            item.addEventListener("click", function () {
                if (act) handleBuilderAction(act);
            });
        });

        /* ---------- Aide syntaxe ---------- */
        var helpToggle = document.getElementById("umlHelpToggle");
        var helpPanel = document.getElementById("umlHelpPanel");
        if (helpToggle && helpPanel) {
            helpToggle.addEventListener("click", function () {
                var willShow = helpPanel.classList.contains("hidden");
                helpPanel.classList.toggle("hidden");
                if (willShow) {
                    helpPanel.scrollIntoView({ behavior: "smooth", block: "start" });
                }
            });
        }

        var helpItems = document.querySelectorAll(".uml-help-item");
        var modalTitleEl = document.getElementById("umlHelpModalTitle");
        var modalDescEl = document.getElementById("umlHelpModalDescription");
        var modalCodeEl = document.getElementById("umlHelpModalCode");
        var modalPreviewImg = document.getElementById("umlHelpModalPreviewImg");
        var modalPlaceholder = document.getElementById("umlHelpModalPreviewPlaceholder");

        if (
            helpItems.length &&
            mainModal &&
            userBlock &&
            helpBlock &&
            modalTitleEl &&
            modalDescEl &&
            modalCodeEl &&
            modalPreviewImg &&
            modalPlaceholder &&
            apiUrl
        ) {
            helpItems.forEach(function (item) {
                item.addEventListener("click", function () {
                    var title = item.getAttribute("data-title") || "";
                    var description = item.getAttribute("data-description") || "";
                    var pre = item.querySelector("pre");
                    var code = pre ? pre.textContent.trim() : "";

                    modalTitleEl.textContent = title || "Exemple UML";
                    modalDescEl.textContent = description;
                    modalCodeEl.textContent = code;

                    modalPlaceholder.textContent = "Chargement…";
                    modalPlaceholder.classList.remove("hidden");
                    modalPreviewImg.classList.add("hidden");
                    modalPreviewImg.src = "";
                    userBlock.classList.add("hidden");
                    helpBlock.classList.remove("hidden");
                    mainModal.classList.remove("hidden");
                    document.body.classList.add("overflow-hidden");

                    if (!code) {
                        modalPlaceholder.textContent = "Aucun code à prévisualiser.";
                        return;
                    }
                    var body = new FormData();
                    body.append("uml_text", code);
                    body.append("csrfmiddlewaretoken", csrfToken);
                    fetch(apiUrl, {
                        method: "POST",
                        body: body,
                        headers: { "X-Requested-With": "XMLHttpRequest" },
                    })
                        .then(function (r) {
                            return r.json();
                        })
                        .then(function (data) {
                            if (data.preview_url) {
                                modalPreviewImg.src = data.preview_url;
                                modalPreviewImg.classList.remove("hidden");
                                modalPlaceholder.classList.add("hidden");
                            } else {
                                modalPlaceholder.textContent =
                                    data.error || "Erreur lors du chargement.";
                            }
                        })
                        .catch(function () {
                            modalPlaceholder.textContent = "Erreur réseau.";
                        });
                });
            });
        }

        document.addEventListener("keydown", function (event) {
            if (event.key !== "Escape") return;
            if (builderModal && !builderModal.classList.contains("hidden")) {
                closeBuilderModal();
                event.preventDefault();
                return;
            }
            if (mainModal && !mainModal.classList.contains("hidden")) {
                closeMainModal();
            }
        });
    }

    function bootUmlPreviewer() {
        if (document.getElementById("id_uml_text")) {
            init();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", bootUmlPreviewer);
    } else {
        bootUmlPreviewer();
    }

    document.body.addEventListener("htmx:afterSwap", function (evt) {
        var target = evt.detail && evt.detail.target;
        if (!target) return;
        if (target.id === "gen-tool-panel" || target.querySelector("#id_uml_text")) {
            bootUmlPreviewer();
        }
    });
})();
