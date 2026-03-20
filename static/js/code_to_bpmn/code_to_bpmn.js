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
    var openBtn = document.getElementById("openPreviewModal");
    var closeBtn = document.getElementById("closePreviewModal");
    var backdrop = document.getElementById("bpmnPreviewBackdrop");
    var previewImage = document.getElementById("bpmnPreviewImage");

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
