/**
 * Générateur de code : bouton copier.
 */
(function () {
    "use strict";

    var copyBtn = document.getElementById("copyGeneratedCodeBtn");
    var output = document.getElementById("id_generated_code");
    if (!copyBtn || !output) {
        return;
    }

    var defaultLabel = copyBtn.textContent;
    function resetState() {
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
                setTimeout(resetState, 900);
            },
            function (error) {
                if (typeof console !== "undefined" && console.warn) {
                    console.warn("Clipboard copy failed:", error);
                }
                copyBtn.textContent = "Erreur";
                copyBtn.classList.remove("bg-slate-100", "text-slate-700", "scale-105");
                copyBtn.classList.add("bg-rose-100", "text-rose-700");
                setTimeout(resetState, 900);
            }
        );
    });
})();
