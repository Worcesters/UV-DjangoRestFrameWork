/**
 * Page 404 : scène 3D (rotateX/Y) + parallax des couches data-depth.
 * Touch : suivi du doigt sur mobile. Désactivé si prefers-reduced-motion.
 */
(function () {
    "use strict";

    var root = document.getElementById("error404-parallax");
    var scene = document.getElementById("error404-stage-3d");
    if (!root || !scene) return;

    var layers = root.querySelectorAll("[data-depth]");
    var digits = root.querySelectorAll(".error404-digit[data-z]");

    digits.forEach(function (el) {
        var z = parseFloat(el.getAttribute("data-z")) || 0;
        el.style.transform = "translateZ(" + z + "px)";
    });

    var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    if (reduceMotion.matches) return;

    var raf = null;
    var maxRx = 16;
    var maxRy = 22;

    function applyParallax(x, y) {
        var nx = x / window.innerWidth - 0.5;
        var ny = y / window.innerHeight - 0.5;
        var rx = -ny * 2 * maxRx;
        var ry = nx * 2 * maxRy;
        scene.style.transform =
            "rotateX(" + rx.toFixed(2) + "deg) rotateY(" + ry.toFixed(2) + "deg) translateZ(0)";

        layers.forEach(function (el) {
            var d = parseFloat(el.getAttribute("data-depth")) || 0.1;
            var mx = nx * d * 72;
            var my = ny * d * 56;
            el.style.transform = "translate3d(" + mx + "px," + my + "px,0)";
        });
    }

    function onMove(e) {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
            applyParallax(e.clientX, e.clientY);
        });
    }

    function onTouch(e) {
        if (!e.touches || !e.touches[0]) return;
        var t = e.touches[0];
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(function () {
            applyParallax(t.clientX, t.clientY);
        });
    }

    document.addEventListener("mousemove", onMove, { passive: true });
    document.addEventListener(
        "touchmove",
        function (e) {
            onTouch(e);
        },
        { passive: true }
    );

    applyParallax(window.innerWidth / 2, window.innerHeight / 2);
})();
