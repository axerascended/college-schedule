(function () {
    const STORAGE_KEY = "schedule-theme";

    function systemTheme() {
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function currentTheme() {
        return document.documentElement.getAttribute("data-bs-theme") || "light";
    }

    function apply(theme) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        localStorage.setItem(STORAGE_KEY, theme);
        updateToggleButton(theme);
    }

    function updateToggleButton(theme) {
        const btn = document.getElementById("themeToggle");
        if (!btn) return;
        const isDark = theme === "dark";
        btn.setAttribute("aria-pressed", isDark ? "true" : "false");
        btn.title = isDark ? "Светлая тема" : "Тёмная тема";
        btn.setAttribute("aria-label", btn.title);
    }

    function toggle() {
        apply(currentTheme() === "dark" ? "light" : "dark");
    }

    function init() {
        const saved = localStorage.getItem(STORAGE_KEY);
        const theme = saved === "light" || saved === "dark" ? saved : systemTheme();
        apply(theme);

        const btn = document.getElementById("themeToggle");
        if (btn) {
            btn.addEventListener("click", toggle);
        }

        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
            if (!localStorage.getItem(STORAGE_KEY)) {
                apply(e.matches ? "dark" : "light");
            }
        });
    }

    window.ThemeToggle = { apply, toggle, init, STORAGE_KEY };

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
