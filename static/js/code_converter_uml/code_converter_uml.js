/**
 * Code → UML : copier PlantUML, modale preview.
 */
(function () {
    "use strict";

    var copyBtn = document.getElementById("copyUmlBtn");
    var output = document.getElementById("id_uml_output");

    if (copyBtn && output) {
        var defaultLabel = copyBtn.textContent;
        var copyResetTimer = null;

        function resetCopyState() {
            copyBtn.textContent = defaultLabel;
            copyBtn.classList.remove("bg-emerald-100", "text-emerald-700", "scale-105");
            copyBtn.classList.add("bg-slate-100", "text-slate-700");
        }

        copyBtn.addEventListener("click", function () {
            navigator.clipboard.writeText(output.value).then(
                function () {
                    copyBtn.textContent = "Copie !";
                    copyBtn.classList.remove("bg-slate-100", "text-slate-700");
                    copyBtn.classList.add("bg-emerald-100", "text-emerald-700", "scale-105");
                    if (copyResetTimer) clearTimeout(copyResetTimer);
                    copyResetTimer = setTimeout(resetCopyState, 900);
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
    }

    var modal = document.getElementById("previewModal");
    var openBtn = document.getElementById("openPreviewModal");
    var closeBtn = document.getElementById("closePreviewModal");
    var backdrop = document.getElementById("previewBackdrop");
    var previewImage = document.getElementById("umlPreviewImage");

    if (!modal || !openBtn || !closeBtn || !backdrop || !previewImage) {
        return;
    }

    function openModal() {
        modal.classList.remove("hidden");
        document.body.classList.add("overflow-hidden");
    }

    function closeModal() {
        modal.classList.add("hidden");
        document.body.classList.remove("overflow-hidden");
    }

    openBtn.addEventListener("click", openModal);
    previewImage.addEventListener("click", openModal);
    closeBtn.addEventListener("click", closeModal);
    backdrop.addEventListener("click", closeModal);

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape" && !modal.classList.contains("hidden")) {
            closeModal();
        }
    });
})();
