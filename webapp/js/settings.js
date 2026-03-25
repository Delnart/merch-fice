/**
 * Settings module — manage recipients.
 */
const settings = {
    recipients: [],

    async load() {
        const container = document.getElementById('settingsContent');
        container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

        try {
            const data = await api.getRecipients();
            this.recipients = data.recipients;
            this.render();
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><div class="empty-text">Помилка завантаження</div></div>`;
        }
    },

    render() {
        const container = document.getElementById('settingsContent');

        container.innerHTML = `
            <div class="section-title">Збережені отримувачі</div>
            ${this.recipients.length ? `
                <div class="card" style="margin-bottom:16px">
                    ${this.recipients.map((r, i) => `
                        ${i > 0 ? '<div class="divider"></div>' : ''}
                        <div class="recipient-card">
                            <div class="recipient-info">
                                <div class="recipient-name">${this._esc(r.full_name)}</div>
                                <div class="recipient-phone">${this._esc(r.phone)}</div>
                            </div>
                            ${r.is_default 
                                ? '<span class="default-badge">За замовч.</span>'
                                : `<button class="btn-secondary btn-small" onclick="settings.setDefault(${r.id})">Обрати</button>`
                            }
                            <button class="remove-btn" onclick="settings.remove(${r.id})">✕</button>
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            <div class="section-title">Додати отримувача</div>
            <div class="card" style="padding:14px">
                <div class="form-group">
                    <label class="form-label">ПІБ</label>
                    <input class="form-input" id="settingsName" placeholder="Прізвище Ім'я По-батькові">
                </div>
                <div class="form-group">
                    <label class="form-label">Номер телефону</label>
                    <input class="form-input" id="settingsPhone" type="tel" placeholder="+380XXXXXXXXX">
                </div>
                <button class="btn-primary" onclick="settings.addRecipient()">Додати</button>
            </div>
        `;
    },

    async addRecipient() {
        const name = document.getElementById('settingsName').value.trim();
        const phone = document.getElementById('settingsPhone').value.trim();
        if (!name || !phone) { app.showToast('Заповніть всі поля'); return; }
        try {
            await api.addRecipient(name, phone);
            app.showToast('Отримувача додано');
            await this.load();
        } catch (e) { app.showToast('Помилка'); }
    },

    async setDefault(id) {
        try {
            await api.setDefaultRecipient(id);
            app.showToast('Отримувача обрано');
            await this.load();
        } catch (e) { app.showToast('Помилка'); }
    },

    async remove(id) {
        try {
            await api.deleteRecipient(id);
            app.showToast('Видалено');
            await this.load();
        } catch (e) { app.showToast('Помилка'); }
    },

    _esc(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }
};
