/**
 * Pan & zoom sur les aperçus diagramme PlantUML (.gen-preview-diagram__canvas).
 * Molette : zoom · Clic gauche + glisser : déplacer · Double-clic : réinitialiser.
 */
(function () {
    "use strict";

    var MIN_SCALE = 0.25;
    var MAX_SCALE = 6;
    var ZOOM_FACTOR = 1.12;

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

        var padding = 20;
        var cw = canvas.clientWidth;
        var ch = canvas.clientHeight;
        var availableW = Math.max(cw - padding, 1);
        var availableH = Math.max(ch - padding, 1);
        var scale = Math.min(1, availableW / img.naturalWidth, availableH / img.naturalHeight);

        state.scale = scale;
        state.tx = (cw - img.naturalWidth * scale) / 2;
        state.ty = (ch - img.naturalHeight * scale) / 2;
        applyTransform(state);
    }

    function resetCanvas(canvas) {
        var state = canvas._panzoomState;
        if (!state) return;
        if (state.img.complete && state.img.naturalWidth) {
            fitToCanvas(state);
            return;
        }
        state.scale = 1;
        state.tx = 0;
        state.ty = 0;
        applyTransform(state);
    }

    function applyTransform(state) {
        state.stage.style.transform =
            "translate(" + state.tx + "px, " + state.ty + "px) scale(" + state.scale + ")";
    }

    function initCanvas(canvas) {
        if (!canvas || canvas.classList.contains("hidden")) return;

        var stage = getStage(canvas);
        var img = canvas.querySelector(".gen-preview-diagram__img");
        if (!stage || !img) return;

        if (canvas.dataset.panzoomBound === "1") {
            var existing = canvas._panzoomState;
            if (existing && existing.img.complete && existing.img.naturalWidth) {
                fitToCanvas(existing);
            }
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
            pointerId: null,
            startX: 0,
            startY: 0,
            startTx: 0,
            startTy: 0,
            moved: false,
        };
        canvas._panzoomState = state;

        canvas.setAttribute(
            "title",
            "Molette : zoom · Glisser : déplacer · Double-clic : réinitialiser"
        );

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
            if (event.button !== 0 || canvas.classList.contains("hidden")) return;
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
        });

        canvas.addEventListener("pointermove", function (event) {
            if (!state.dragging || event.pointerId !== state.pointerId) return;

            var dx = event.clientX - state.startX;
            var dy = event.clientY - state.startY;
            if (Math.abs(dx) > 3 || Math.abs(dy) > 3) {
                state.moved = true;
            }
            state.tx = state.startTx + dx;
            state.ty = state.startTy + dy;
            applyTransform(state);
        });

        function endPan(event) {
            if (!state.dragging || (event && event.pointerId !== state.pointerId)) return;
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
            state.pointerId = null;
            canvas.classList.remove("is-panning");
        });

        canvas.addEventListener("dblclick", function (event) {
            event.preventDefault();
            resetCanvas(canvas);
            canvas.dispatchEvent(
                new CustomEvent("gen-preview-dblclick", { bubbles: true, detail: { canvas: canvas } })
            );
        });

        img.addEventListener("load", function () {
            fitToCanvas(state);
        });

        if (img.complete && img.naturalWidth) {
            fitToCanvas(state);
        }

        img.addEventListener("dragstart", function (event) {
            event.preventDefault();
        });
    }

    window.GenPreviewPanZoom = {
        init: function (root) {
            var scope = root && root.querySelectorAll ? root : document;
            var canvases = scope.querySelectorAll
                ? scope.querySelectorAll(".gen-preview-diagram__canvas")
                : [];
            canvases.forEach(initCanvas);
        },
        reset: resetCanvas,
        wasDragged: function (canvas) {
            var state = canvas && canvas._panzoomState;
            return Boolean(state && state.moved);
        },
    };
})();
