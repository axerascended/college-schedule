(function () {
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    const block = document.getElementById("savedAccountsBlock");
    const listEl = document.getElementById("savedAccountsList");

    if (!emailInput || !window.SavedAccounts) return;

    function escapeHtml(text) {
        const d = document.createElement("div");
        d.textContent = text;
        return d.innerHTML;
    }

    function renderSavedAccounts() {
        if (!block || !listEl) return;
        const accounts = SavedAccounts.load();
        if (!accounts.length) {
            block.style.display = "none";
            return;
        }
        block.style.display = "block";
        listEl.innerHTML = "";
        accounts.forEach((acc) => {
            const row = document.createElement("div");
            row.className =
                "saved-account-item d-flex align-items-stretch gap-1 border rounded p-2 bg-light";

            const pick = document.createElement("button");
            pick.type = "button";
            pick.className =
                "btn btn-link text-start text-decoration-none flex-grow-1 p-0 saved-account-pick";
            pick.innerHTML =
                "<strong class=\"d-block\">" +
                escapeHtml(acc.fullName) +
                "</strong>" +
                "<span class=\"small text-muted\">" +
                escapeHtml(acc.email) +
                (acc.roleLabel ? " · " + escapeHtml(acc.roleLabel) : "") +
                "</span>";
            pick.addEventListener("click", () => {
                emailInput.value = acc.email;
                passwordInput.focus();
                row.classList.add("border-primary");
                setTimeout(() => row.classList.remove("border-primary"), 600);
            });

            const removeBtn = document.createElement("button");
            removeBtn.type = "button";
            removeBtn.className = "btn btn-sm btn-outline-danger align-self-center";
            removeBtn.title = "Удалить из списка";
            removeBtn.textContent = "×";
            removeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                SavedAccounts.remove(acc.email);
                renderSavedAccounts();
            });

            row.appendChild(pick);
            row.appendChild(removeBtn);
            listEl.appendChild(row);
        });
    }

    const lastEmail = SavedAccounts.getLastEmail();
    if (lastEmail && !emailInput.value) {
        emailInput.value = lastEmail;
    }
    renderSavedAccounts();
})();
