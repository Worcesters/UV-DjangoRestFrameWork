/**
 * Pan & zoom sur les aperçus PlantUML ([data-panzoom]).
 * Molette : zoom · Clic droit + glisser : déplacer · Clic gauche : ouvrir l’aperçu agrandi.
 */
(function () {
    "use strict";

    var MIN_SCALE = 0.2;
    var MAX_SCALE = 8;
    var ZOOM_FACTOR = 1.12;
    var MOVE_THRESHOLD = 4;

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    function getStage(canvas) {
        return canvas.querySelector(".gen-preview-diagram__stage");
    }

    function fitToCanvas(state) {
        var canvas = state.canvas;
        var img = state.img;
        if (!img.naturalWidth || !img.naturalHeight) return;

        var cw = canvas.clientWidth;
        var ch = canvas.clientHeight;
        if (cw < 2 || ch < 2) return;

        var padding = 16;
        var availableW = Math.max(cw - padding * 2, 1);
        var availableH = Math.max(ch - padding * 2, 1);
        var scale = Math.min(1, availableW / img.naturalWidth, availableH / img.naturalHeight);

        state.scale = scale;
        state.tx = (cw - img.naturalWidth * scale) / 2;
        state.ty = (ch - img.naturalHeight * scale) / 2;
        applyTransform(state);
    }

    function scheduleFit(state, attempt) {
        var tries = attempt || 0;
        if (state.canvas.classList.contains("hidden") || state.canvas.clientWidth < 2) {
            if (tries < 80) {
                requestAnimationFrame(function () {
                    scheduleFit(state, tries + 1);
                });
            }
            return;
        }
        fitToCanvas(state);
    }

    function resetCanvas(canvas) {
        var state = canvas && canvas._panzoomState;
        if (!state) return;
        scheduleFit(state, 0);
    }

    function applyTransform(state) {
        state.stage.style.transform =
            "translate(" + state.tx + "px, " + state.ty + "px) scale(" + state.scale + ")";
    }

    function tryOpenModal(canvas) {
        if (canvas.hasAttribute("data-panzoom-modal")) return;
        var img = canvas.querySelector(".gen-preview-diagram__img");
        if (!img || !img.getAttribute("src")) return;

        var modalBtnId = canvas.getAttribute("data-open-modal");
        if (!modalBtnId) return;
        var btn = document.getElementById(modalBtnId);
        if (btn) btn.click();
    }

    function collectPanzoomRoots(root) {
        var list = [];
        if (!root) return list;
        if (root.nodeType === 1 && root.matches && root.matches("[data-panzoom]")) {
            list.push(root);
        }
        if (root.querySelectorAll) {
            root.querySelectorAll("[data-panzoom]").forEach(function (el) {
                if (list.indexOf(el) === -1) list.push(el);
            });
        }
        return list;
    }

    function initCanvas(canvas) {
        if (!canvas) return;

        var stage = getStage(canvas);
        var img = canvas.querySelector(".gen-preview-diagram__img");
        if (!stage || !img) return;

        if (canvas.dataset.panzoomBound === "1") {
            if (canvas._panzoomState) scheduleFit(canvas._panzoomState, 0);
            return;
        }
        canvas.dataset.panzoomBound = "1";

        var state = {
            canvas: canvas,
            stage: stage,
            img: img,
            scale: 1,
            tx: 0,
            ty: 0,
            dragging: false,
            leftDown: false,
            pointerId: null,
            startX: 0,
            startY: 0,
            startTx: 0,
            startTy: 0,
            moved: false,
        };
        canvas._panzoomState = state;

        if (!canvas.hasAttribute("data-panzoom-modal")) {
            canvas.setAttribute(
                "title",
                "Molette : zoom · Clic droit : déplacer · Clic gauche : agrandir"
            );
        } else {
            canvas.setAttribute("title", "Molette : zoom · Clic droit : déplacer · Double-clic : réinitialiser");
        }

        canvas.addEventListener("contextmenu", function (event) {
            event.preventDefault();
        });

        canvas.addEventListener(
            "wheel",
            function (event) {
                if (canvas.classList.contains("hidden")) return;
                event.preventDefault();

                var rect = canvas.getBoundingClientRect();
                var mouseX = event.clientX - rect.left;
                var mouseY = event.clientY - rect.top;
                var factor = event.deltaY < 0 ? ZOOM_FACTOR : 1 / ZOOM_FACTOR;
                var newScale = clamp(state.scale * factor, MIN_SCALE, MAX_SCALE);

                state.tx = mouseX - (mouseX - state.tx) * (newScale / state.scale);
                state.ty = mouseY - (mouseY - state.ty) * (newScale / state.scale);
                state.scale = newScale;
                applyTransform(state);
            },
            { passive: false }
        );

        canvas.addEventListener("pointerdown", function (event) {
            if (canvas.classList.contains("hidden")) return;

            if (event.button === 2) {
                event.preventDefault();
                state.dragging = true;
                state.moved = false;
                state.pointerId = event.pointerId;
                state.startX = event.clientX;
                state.startY = event.clientY;
                state.startTx = state.tx;
                state.startTy = state.ty;
                canvas.classList.add("is-panning");
                canvas.setPointerCapture(event.pointerId);
                return;
            }

            if (event.button === 0) {
                state.leftDown = true;
                state.moved = false;
                state.startX = event.clientX;
                state.startY = event.clientY;
            }
        });

        canvas.addEventListener("pointermove", function (event) {
            var dx = event.clientX - state.startX;
            var dy = event.clientY - state.startY;

            if (state.leftDown && (Math.abs(dx) > MOVE_THRESHOLD || Math.abs(dy) > MOVE_THRESHOLD)) {
                state.moved = true;
            }

            if (!state.dragging || event.pointerId !== state.pointerId) return;

            if (Math.abs(dx) > MOVE_THRESHOLD || Math.abs(dy) > MOVE_THRESHOLD) {
                state.moved = true;
            }
            state.tx = state.startTx + dx;
            state.ty = state.startTy + dy;
            applyTransform(state);
        });

        function endPan(event) {
            if (event.button === 0) {
                if (state.leftDown && !state.moved) {
                    tryOpenModal(canvas);
                }
                state.leftDown = false;
            }

            if (event.button !== 2 || !state.dragging || event.pointerId !== state.pointerId) {
                return;
            }

            state.dragging = false;
            state.pointerId = null;
            canvas.classList.remove("is-panning");
            try {
                canvas.releasePointerCapture(event.pointerId);
            } catch (_err) {
                /* ignore */
            }
        }

        canvas.addEventListener("pointerup", endPan);
        canvas.addEventListener("pointercancel", endPan);
        canvas.addEventListener("lostpointercapture", function () {
            state.dragging = false;
            state.leftDown = false;
            state.pointerId = null;
            canvas.classList.remove("is-panning");
        });

        canvas.addEventListener("dblclick", function (event) {
            event.preventDefault();
            resetCanvas(canvas);
        });

        img.addEventListener("load", function () {
            scheduleFit(state, 0);
        });

        img.addEventListener("dragstart", function (event) {
            event.preventDefault();
        });

        if (img.complete && img.naturalWidth) {
            scheduleFit(state, 0);
        }

        if (typeof ResizeObserver !== "undefined") {
            var ro = new ResizeObserver(function () {
                if (!canvas.classList.contains("hidden") && canvas.clientWidth > 2) {
                    scheduleFit(state, 0);
                }
            });
            ro.observe(canvas);
            state.resizeObserver = ro;
        }
    }

    function wireModal(modal, options) {
        options = options || {};
        if (!modal || modal.dataset.modalWired === "1") return null;
        modal.dataset.modalWired = "1";

        var openBtn = options.openButtonId ? document.getElementById(options.openButtonId) : null;
        var closeBtn = options.closeButtonId ? document.getElementById(options.closeButtonId) : null;
        var backdrop = options.backdropId ? document.getElementById(options.backdropId) : null;
        var sourceImg = options.sourceImageId ? document.getElementById(options.sourceImageId) : null;

        function openModal() {
            var canvas = modal.querySelector("[data-panzoom]");
            var modalImg = canvas && canvas.querySelector(".gen-preview-diagram__img");
            if (modalImg && sourceImg && sourceImg.src) {
                modalImg.src = sourceImg.src;
            }
            modal.classList.remove("hidden");
            document.body.classList.add("overflow-hidden");
            window.GenPreviewPanZoom.init(modal);
            if (canvas) resetCanvas(canvas);
        }

        function closeModal() {
            modal.classList.add("hidden");
            document.body.classList.remove("overflow-hidden");
        }

        modal._genPreviewClose = closeModal;

        if (openBtn) openBtn.addEventListener("click", openModal);
        if (closeBtn) closeBtn.addEventListener("click", closeModal);
        if (backdrop) backdrop.addEventListener("click", closeModal);

        if (!window.GenPreviewPanZoom._escapeBound) {
            window.GenPreviewPanZoom._escapeBound = true;
            document.addEventListener("keydown", function (event) {
                if (event.key !== "Escape") return;
                document.querySelectorAll(".gen-preview-modal-mark:not(.hidden)").forEach(function (el) {
                    el.classList.add("hidden");
                    if (el._genPreviewClose) el._genPreviewClose();
                    else document.body.classList.remove("overflow-hidden");
                });
            });
        }

        return { open: openModal, close: closeModal };
    }

    window.GenPreviewPanZoom = {
        init: function (root) {
            collectPanzoomRoots(root || document).forEach(initCanvas);
        },
        reset: resetCanvas,
        wireModal: wireModal,
        wasDragged: function (canvas) {
            var state = canvas && canvas._panzoomState;
            return Boolean(state && state.moved);
        },
    };
})();
