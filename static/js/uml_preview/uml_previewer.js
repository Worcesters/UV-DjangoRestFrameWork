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

    /** Deux listes mutuellement exclusives (même pool de noms). */
    function wireMutuallyExclusiveSelects(selA, selB, allNames) {
        function sync() {
            var a = selA.value;
            var b = selB.value;
            fillSelect(selB, allNames, "— Choisir —", a);
            setSelectValueIfPresent(selB, b);
            fillSelect(selA, allNames, "— Choisir —", selB.value);
            setSelectValueIfPresent(selA, a);
        }
        selA.addEventListener("change", sync);
        selB.addEventListener("change", sync);
        sync();
    }

    /** Interface vs classe : exclure le nom choisi s’il existe aussi dans l’autre liste. */
    function wireImplementsSelects(selI, interfaces, selC, classes) {
        function sync() {
            var iface = selI.value;
            var cls = selC.value;
            fillSelect(
                selI,
                interfaces,
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

        function updateUml(newUml) {
            textarea.value = String(newUml ?? "");
            textarea.dispatchEvent(new Event("input", { bubbles: true }));
        }

        function refreshPreviewFromApi() {
            var value = textarea.value.trim();
            setPreviewError("");

            if (!value) {
                form.setAttribute("data-preview-url", "");
                if (previewImageWrap) previewImageWrap.classList.add("hidden");
                if (previewEmpty) previewEmpty.classList.remove("hidden");
                if (previewImage) previewImage.removeAttribute("src");
                return;
            }

            if (!apiUrl || !csrfToken) {
                setPreviewError("Configuration preview manquante.");
                return;
            }

            setPreviewLoading(true);
            var body = new FormData();
            body.append("uml_text", value);
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
                        form.setAttribute("data-preview-url", data.preview_url);
                        if (previewImage) previewImage.src = data.preview_url;
                        if (previewImageWrap) previewImageWrap.classList.remove("hidden");
                        if (previewEmpty) previewEmpty.classList.add("hidden");
                        setPreviewError("");
                    } else {
                        setPreviewError(data.error || "Impossible de générer l’aperçu.");
                    }
                })
                .catch(function () {
                    setPreviewLoading(false);
                    setPreviewError("Erreur réseau lors de l’aperçu.");
                });
        }

        textarea.addEventListener("input", function () {
            if (debounceTimer) clearTimeout(debounceTimer);
            debounceTimer = setTimeout(refreshPreviewFromApi, 2000);
        });

        /* ---------- Modale principale (aperçu user + aide) ---------- */
        var mainModal = document.getElementById("umlPreviewModal");
        var mainBackdrop = document.getElementById("umlPreviewBackdrop");
        var userBlock = document.getElementById("umlUserDiagramBlock");
        var helpBlock = document.getElementById("umlHelpBlock");
        var userDiagramImg = document.getElementById("umlUserDiagramImage");
        var openImg = document.getElementById("umlPreviewImage");

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
            if (userDiagramImg) userDiagramImg.src = url;
            helpBlock.classList.add("hidden");
            userBlock.classList.remove("hidden");
            mainModal.classList.remove("hidden");
            document.body.classList.add("overflow-hidden");
        }

        if (openImg) openImg.addEventListener("click", openUserDiagram);
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

            if (action === "extends") {
                builderTitle.textContent = "Héritage (extends)";
                if (classes.length < 2) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>deux classes</strong> (Add class / Abstract class) avant d’utiliser Extends.</p>';
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
                            "La classe <strong>enfant</strong> est une sorte de <strong>parent</strong> (spécialisation / généralisation). Exemple : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-orange-200/80 font-mono\">Enfant --|&gt; Parent</code>.",
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
                        '">Classe parent</label>';
                    var selParent = document.createElement("select");
                    selParent.id = "umlBuilderExtendsParent";
                    selParent.className = selectClass;
                    fillSelect(selParent, classes, "— Choisir —");
                    row2.appendChild(selParent);
                    builderBody.appendChild(row2);
                    wireMutuallyExclusiveSelects(selChild, selParent, classes);
                }
            } else if (action === "implements") {
                builderTitle.textContent = "Implémentation (interface)";
                if (interfaces.length < 1 || classes.length < 1) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>une interface</strong> et <strong>une classe</strong> avant Implements.</p>';
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
                            "Choisis d’abord l’<strong>interface</strong> (contrat), puis la <strong>classe</strong> qui l’implémente. Syntaxe : <code class=\"text-[10px] bg-white/80 px-1 py-0.5 rounded border border-cyan-200/80 font-mono\">Interface &lt;|.. Classe</code>.",
                        detailClass: "text-cyan-900/95",
                    });
                    var r1 = document.createElement("div");
                    r1.innerHTML =
                        '<label class="' + labelClass + '">Interface</label>';
                    var selI = document.createElement("select");
                    selI.id = "umlBuilderImplementsInterface";
                    selI.className = selectClass;
                    fillSelect(selI, interfaces, "— Choisir —");
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
                    wireImplementsSelects(selI, interfaces, selC, classes);
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
                if (typeNames.length < 2) {
                    builderBody.innerHTML =
                        '<p class="text-sm text-slate-600">Ajoute au moins <strong>deux</strong> types (classe, interface ou enum) avant d’ajouter une relation.</p>';
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
                    fillSelect(selFrom, typeNames, "— Choisir —");
                    rf.appendChild(selFrom);
                    builderBody.appendChild(rf);

                    var rt = document.createElement("div");
                    rt.className = "mt-4";
                    rt.innerHTML =
                        '<label class="' + labelClass + '">Cible (arrivée)</label>';
                    var selTo = document.createElement("select");
                    selTo.id = "umlBuilderRelTo";
                    selTo.className = selectClass;
                    fillSelect(selTo, typeNames, "— Choisir —");
                    rt.appendChild(selTo);
                    builderBody.appendChild(rt);

                    wireMutuallyExclusiveSelects(selFrom, selTo, typeNames);

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

                    var ns = document.createElement("div");
                    ns.className = "mt-4";
                    ns.innerHTML =
                        '<label class="' + labelClass + '">Position</label>';
                    var selS = document.createElement("select");
                    selS.id = "umlBuilderNoteSide";
                    selS.className = selectClass;
                    ["left", "right", "top", "bottom"].forEach(function (s) {
                        var o = document.createElement("option");
                        o.value = s;
                        o.textContent = s;
                        selS.appendChild(o);
                    });
                    selS.value = "right";
                    ns.appendChild(selS);
                    builderBody.appendChild(ns);

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
                updateUml(insertBeforeEnduml(uml, c.value + " --|> " + p.value));
            } else if (builderAction === "implements") {
                var ii = document.getElementById("umlBuilderImplementsInterface");
                var cc = document.getElementById("umlBuilderImplementsClass");
                if (!ii || !cc || !ii.value || !cc.value) {
                    window.alert("Choisis une interface et une classe.");
                    return;
                }
                updateUml(insertBeforeEnduml(uml, ii.value + " <|.. " + cc.value));
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
                var arrow =
                    builderAction === "rel_aggregate"
                        ? " o-- "
                        : builderAction === "rel_compose"
                          ? " *-- "
                          : builderAction === "rel_depend"
                            ? " ..> "
                            : " --> ";
                var line = rf.value + arrow + rt.value;
                if (lbl) line += " : " + lbl;
                updateUml(insertBeforeEnduml(uml, line));
            } else if (builderAction === "add_class") {
                var n = document.getElementById("umlBuilderNameInput");
                var name = (n && n.value ? n.value : "").trim();
                if (!name || !isValidIdentifier(name)) {
                    window.alert("Nom invalide (lettres, chiffres, _ ; pas d’espace).");
                    return;
                }
                updateUml(
                    insertBeforeEnduml(uml, "class " + name + " {\n}\n".trimEnd())
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
                        "abstract class " + name2 + " {\n}\n".trimEnd()
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
                        "interface " + name3 + " {\n}\n".trimEnd()
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
                        "enum " + name4 + " {\n  VALUE\n}\n".trimEnd()
                    )
                );
            } else if (builderAction === "note") {
                var t = document.getElementById("umlBuilderNoteTarget");
                var s = document.getElementById("umlBuilderNoteSide");
                var tx = document.getElementById("umlBuilderNoteText");
                if (!t || !t.value) {
                    window.alert("Choisis un élément cible.");
                    return;
                }
                var side = s && s.value ? s.value : "right";
                var txt = (tx && tx.value ? tx.value : "").trim() || "Note";
                var block =
                    "note " +
                    side +
                    " of " +
                    t.value +
                    "\n  " +
                    txt +
                    "\nend note";
                updateUml(insertBeforeEnduml(uml, block));
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
                action === "note"
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

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
