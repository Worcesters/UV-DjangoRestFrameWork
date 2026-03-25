/**
 * Onglets Inscription / Connexion : bascule locale (pas de GET HTMX).
 */
(function () {
    "use strict";

    var baseBtn =
        "flex-1 py-3 rounded-[1.6rem] text-sm font-bold transition-all duration-300";
    var activeCls = "bg-white shadow-md text-blue-600";
    var inactiveCls = "text-gray-400 hover:text-gray-600";

    function syncButtons(root, tab) {
        var signupBtn = root.querySelector('[data-auth-tab="signup"]');
        var loginBtn = root.querySelector('[data-auth-tab="login"]');
        if (!signupBtn || !loginBtn) return;
        signupBtn.className = baseBtn + " " + (tab === "signup" ? activeCls : inactiveCls);
        loginBtn.className = baseBtn + " " + (tab === "login" ? activeCls : inactiveCls);
    }

    function showPanel(root, tab) {
        root.querySelectorAll(".auth-tab-panel").forEach(function (panel) {
            var name = panel.getAttribute("data-panel");
            panel.classList.toggle("hidden", name !== tab);
        });
        root.setAttribute("data-active-tab", tab);
        syncButtons(root, tab);
    }

    document.body.addEventListener("click", function (e) {
        var btn = e.target.closest("[data-auth-tab]");
        if (!btn) return;
        var root = btn.closest("#auth-container");
        if (!root) return;
        e.preventDefault();
        var tab = btn.getAttribute("data-auth-tab");
        if (tab !== "signup" && tab !== "login") return;
        showPanel(root, tab);
    });
})();
