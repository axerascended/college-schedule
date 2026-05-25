window.SavedAccounts = (function () {
    const STORAGE_KEY = "kyrs_saved_accounts";
    const LAST_EMAIL_KEY = "kyrs_last_email";
    const MAX_ACCOUNTS = 8;

    const ROLE_LABELS = {
        admin: "Администратор",
        student: "Студент",
        teacher: "Преподаватель",
    };

    function load() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            return raw ? JSON.parse(raw) : [];
        } catch {
            return [];
        }
    }

    function saveList(list) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX_ACCOUNTS)));
    }

    function save(account) {
        if (!account || !account.email) return;
        const email = account.email.trim().toLowerCase();
        const entry = {
            email,
            fullName: account.fullName || account.full_name || email,
            role: account.role || "",
            roleLabel: ROLE_LABELS[account.role] || account.role || "",
            savedAt: Date.now(),
        };
        let list = load().filter((a) => a.email !== email);
        list.unshift(entry);
        saveList(list);
        localStorage.setItem(LAST_EMAIL_KEY, email);
    }

    function remove(email) {
        const norm = email.trim().toLowerCase();
        saveList(load().filter((a) => a.email !== norm));
        if (localStorage.getItem(LAST_EMAIL_KEY) === norm) {
            localStorage.removeItem(LAST_EMAIL_KEY);
        }
    }

    function getLastEmail() {
        return localStorage.getItem(LAST_EMAIL_KEY) || "";
    }

    function roleLabel(role) {
        return ROLE_LABELS[role] || role;
    }

    return { load, save, remove, getLastEmail, roleLabel, ROLE_LABELS };
})();
