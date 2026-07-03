/**
 * Code → BPMN : copier le PlantUML, modale preview.
 */
(function () {
    "use strict";

    var copyBtn = document.getElementById("copyBpmnBtn");
    var output = document.getElementById("id_bpmn_output");
    if (copyBtn && output) {
        var defaultLabel = copyBtn.textContent;
        copyBtn.addEventListener("click", function () {
            navigator.clipboard.writeText(output.value).then(
                function () {
                    copyBtn.textContent = "Copié !";
                    copyBtn.classList.remove("bg-slate-100", "text-slate-700");
                    copyBtn.classList.add("bg-emerald-100", "text-emerald-700");
                    setTimeout(function () {
                        copyBtn.textContent = defaultLabel;
                        copyBtn.classList.remove("bg-emerald-100", "text-emerald-700");
                        copyBtn.classList.add("bg-slate-100", "text-slate-700");
                    }, 900);
                },
                function () {
                    copyBtn.textContent = "Erreur";
                    setTimeout(function () {
                        copyBtn.textContent = defaultLabel;
                    }, 900);
                }
            );
        });
    }

    var modal = document.getElementById("bpmnPreviewModal");
    if (modal && window.GenPreviewPanZoom) {
        GenPreviewPanZoom.wireModal(modal, {
            openButtonId: "openPreviewModal",
            closeButtonId: "closePreviewModal",
            backdropId: "bpmnPreviewBackdrop",
            sourceImageId: "bpmnPreviewImage",
        });
    }
})();
