/**
 * Catalogue d'icônes natives PlantUML (OpenIconic) pour le UML Builder.
 *
 * Expose `window.UmlIcons` :
 *   - groups   : catalogue curé, groupé par thème (affichage par défaut du picker).
 *   - all      : liste complète des glyphes OpenIconic (recherche étendue).
 *   - suggestForMethod(name)    -> glyphe conseillé selon le nom de méthode.
 *   - suggestForAttribute(name) -> glyphe conseillé selon le nom d'attribut.
 *   - suggestForClass(name)     -> glyphe conseillé selon le nom de type.
 *
 * Le token PlantUML d'un glyphe `cog` est `<&cog>`.
 */
(function () {
    "use strict";

    /** Liste complète des glyphes OpenIconic embarqués (open-iconic.css). */
    var ALL = [
        "account-login", "account-logout", "action-redo", "action-undo", "align-center",
        "align-left", "align-right", "aperture", "arrow-bottom", "arrow-circle-bottom",
        "arrow-circle-left", "arrow-circle-right", "arrow-circle-top", "arrow-left",
        "arrow-right", "arrow-thick-bottom", "arrow-thick-left", "arrow-thick-right",
        "arrow-thick-top", "arrow-top", "audio-spectrum", "audio", "badge", "ban",
        "bar-chart", "basket", "battery-empty", "battery-full", "beaker", "bell",
        "bluetooth", "bold", "bolt", "book", "bookmark", "box", "briefcase",
        "british-pound", "browser", "brush", "bug", "bullhorn", "calculator", "calendar",
        "camera-slr", "caret-bottom", "caret-left", "caret-right", "caret-top", "cart",
        "chat", "check", "chevron-bottom", "chevron-left", "chevron-right", "chevron-top",
        "circle-check", "circle-x", "clipboard", "clock", "cloud-download", "cloud-upload",
        "cloud", "cloudy", "code", "cog", "collapse-down", "collapse-left",
        "collapse-right", "collapse-up", "command", "comment-square", "compass",
        "contrast", "copywriting", "credit-card", "crop", "dashboard",
        "data-transfer-download", "data-transfer-upload", "delete", "dial", "document",
        "dollar", "double-quote-sans-left", "double-quote-sans-right",
        "double-quote-serif-left", "double-quote-serif-right", "droplet", "eject",
        "elevator", "ellipses", "envelope-closed", "envelope-open", "euro", "excerpt",
        "expand-down", "expand-left", "expand-right", "expand-up", "external-link", "eye",
        "eyedropper", "file", "fire", "flag", "flash", "folder", "fork",
        "fullscreen-enter", "fullscreen-exit", "globe", "graph", "grid-four-up",
        "grid-three-up", "grid-two-up", "hard-drive", "header", "headphones", "heart",
        "home", "image", "inbox", "infinity", "info", "italic", "justify-center",
        "justify-left", "justify-right", "key", "laptop", "layers", "lightbulb",
        "link-broken", "link-intact", "list-rich", "list", "location", "lock-locked",
        "lock-unlocked", "loop-circular", "loop-square", "loop", "magnifying-glass",
        "map-marker", "map", "media-pause", "media-play", "media-record",
        "media-skip-backward", "media-skip-forward", "media-step-backward",
        "media-step-forward", "media-stop", "medical-cross", "menu", "microphone",
        "minus", "monitor", "moon", "move", "musical-note", "paperclip", "pencil",
        "people", "person", "phone", "pie-chart", "pin", "play-circle", "plus",
        "power-standby", "print", "project", "pulse", "puzzle-piece", "question-mark",
        "rain", "random", "reload", "resize-both", "resize-height", "resize-width",
        "rss-alt", "rss", "script", "share-boxed", "share", "shield", "signal",
        "signpost", "sort-ascending", "sort-descending", "spreadsheet", "star", "sun",
        "tablet", "tag", "tags", "target", "task", "terminal", "text", "thumb-down",
        "thumb-up", "timer", "transfer", "trash", "underline", "vertical-align-bottom",
        "vertical-align-center", "vertical-align-top", "video", "volume-high",
        "volume-low", "volume-off", "warning", "wifi", "wrench", "x", "yen", "zoom-in",
        "zoom-out",
    ];

    /** Catalogue curé, groupé par thème (le plus utile pour un diagramme logiciel). */
    var GROUPS = [
        {
            label: "Actions",
            icons: [
                "cog", "wrench", "bolt", "flash", "reload", "loop-circular", "play-circle",
                "media-play", "power-standby", "task", "check", "circle-check", "x", "ban",
                "plus", "minus", "pencil", "trash", "delete", "magnifying-glass",
            ],
        },
        {
            label: "Données",
            icons: [
                "data-transfer-download", "data-transfer-upload", "cloud-download",
                "cloud-upload", "spreadsheet", "list", "list-rich", "layers", "box",
                "inbox", "clipboard", "hard-drive", "graph", "bar-chart", "pie-chart",
                "pulse", "dashboard",
            ],
        },
        {
            label: "Système",
            icons: [
                "terminal", "code", "command", "script", "monitor", "laptop", "tablet",
                "phone", "dial", "timer", "clock", "bug", "fork", "puzzle-piece",
                "project", "beaker",
            ],
        },
        {
            label: "Réseau",
            icons: [
                "globe", "cloud", "wifi", "signal", "share", "share-boxed", "link-intact",
                "link-broken", "rss", "transfer", "location", "map", "map-marker",
                "external-link", "browser", "signpost",
            ],
        },
        {
            label: "Sécurité",
            icons: [
                "shield", "lock-locked", "lock-unlocked", "key", "eye", "account-login",
                "account-logout", "badge", "warning", "fire",
            ],
        },
        {
            label: "Interface",
            icons: [
                "browser", "menu", "home", "grid-three-up", "bell", "envelope-closed",
                "chat", "comment-square", "person", "people", "star", "heart", "flag",
                "tag", "tags", "bookmark", "calendar", "info", "question-mark",
            ],
        },
        {
            label: "Fichiers",
            icons: [
                "file", "folder", "document", "spreadsheet", "clipboard", "book", "box",
                "paperclip", "print", "image", "copywriting", "text",
            ],
        },
    ];

    /**
     * Cherche le premier motif contenu dans `name` (déjà normalisé) et renvoie
     * le glyphe associé, sinon `fallback`.
     */
    function matchByKeywords(name, rules, fallback) {
        var n = String(name || "").toLowerCase();
        for (var i = 0; i < rules.length; i++) {
            var keys = rules[i][0];
            for (var k = 0; k < keys.length; k++) {
                if (n.indexOf(keys[k]) !== -1) return rules[i][1];
            }
        }
        return fallback || "";
    }

    var METHOD_RULES = [
        [["login", "signin", "connect", "authenticate"], "account-login"],
        [["logout", "signout", "disconnect"], "account-logout"],
        [["search", "query", "filter", "lookup"], "magnifying-glass"],
        [["get", "list", "fetch", "index", "read", "load", "all"], "list"],
        [["save", "persist", "store", "insert", "flush", "commit"], "data-transfer-download"],
        [["create", "add", "register", "new"], "plus"],
        [["update", "edit", "modify", "change", "patch", "set"], "pencil"],
        [["delete", "remove", "destroy", "drop", "clear", "purge"], "trash"],
        [["upload"], "cloud-upload"],
        [["download", "export"], "cloud-download"],
        [["send", "emit", "dispatch", "push", "produce"], "data-transfer-upload"],
        [["mail", "email", "notify"], "envelope-closed"],
        [["publish", "broadcast", "announce"], "bullhorn"],
        [["validate", "verify", "check", "confirm", "ensure"], "check"],
        [["calculate", "compute", "count", "sum", "total"], "calculator"],
        [["parse", "convert", "transform", "map", "serialize"], "transfer"],
        [["build", "generate", "render", "compile"], "code"],
        [["run", "execute", "exec", "start", "launch", "perform", "process"], "cog"],
        [["job", "task", "schedule", "cron", "worker"], "task"],
        [["request", "call", "api", "http", "fetch"], "globe"],
        [["encrypt", "hash", "secure", "protect", "sign"], "shield"],
        [["lock"], "lock-locked"],
        [["unlock"], "lock-unlocked"],
        [["token", "key", "credential"], "key"],
        [["log", "debug", "trace"], "bug"],
        [["config", "setup", "init", "configure"], "cog"],
        [["print"], "print"],
        [["open"], "folder"],
        [["close", "cancel", "abort"], "x"],
        [["wait", "delay", "sleep", "timeout"], "timer"],
    ];

    var ATTRIBUTE_RULES = [
        [["password", "secret", "token"], "lock-locked"],
        [["email", "mail"], "envelope-closed"],
        [["_id", "uuid", "guid", "pk"], "key"],
        [["url", "link", "href", "endpoint"], "link-intact"],
        [["path", "dir", "directory", "folder"], "folder"],
        [["file", "filename"], "file"],
        [["date", "created", "updated", "timestamp", "time"], "calendar"],
        [["count", "total", "number", "qty", "quantity", "amount"], "bar-chart"],
        [["price", "cost", "salary", "balance"], "calculator"],
        [["status", "state", "phase"], "flag"],
        [["list", "items", "collection", "array", "set"], "list"],
        [["user", "owner", "author", "member", "person"], "person"],
        [["config", "settings", "option"], "cog"],
        [["description", "content", "body", "note", "comment"], "document"],
        [["image", "photo", "avatar", "picture", "thumbnail"], "image"],
        [["active", "enabled", "valid", "is_", "has_", "can_"], "check"],
        [["tag", "label", "category"], "tag"],
        [["name", "title"], "text"],
    ];

    var CLASS_RULES = [
        [["controller", "api", "view", "endpoint", "handler", "resource"], "browser"],
        [["repository", "repo", "dao", "store", "storage"], "hard-drive"],
        [["service", "usecase", "interactor"], "cog"],
        [["task", "job", "worker", "consumer"], "task"],
        [["factory", "builder", "provider"], "wrench"],
        [["manager", "coordinator", "orchestrator"], "briefcase"],
        [["queue", "buffer", "stream"], "layers"],
        [["cache"], "bolt"],
        [["event", "signal", "message"], "flash"],
        [["config", "settings"], "cog"],
        [["user", "account", "person", "member", "customer"], "person"],
        [["model", "entity", "record", "dto", "schema"], "box"],
        [["client", "gateway", "adapter", "connector", "http"], "globe"],
        [["parser", "serializer", "converter", "mapper"], "transfer"],
        [["validator", "guard", "policy", "auth"], "shield"],
        [["logger", "log", "monitor", "tracer"], "bug"],
        [["util", "helper", "tool"], "wrench"],
    ];

    window.UmlIcons = {
        groups: GROUPS,
        all: ALL,
        has: function (name) {
            return ALL.indexOf(String(name || "")) !== -1;
        },
        suggestForMethod: function (name) {
            return matchByKeywords(name, METHOD_RULES, "cog");
        },
        suggestForAttribute: function (name) {
            return matchByKeywords(name, ATTRIBUTE_RULES, "");
        },
        suggestForClass: function (name) {
            return matchByKeywords(name, CLASS_RULES, "");
        },
    };
})();
