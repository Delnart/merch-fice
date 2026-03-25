/**
 * Settings module — manage saved recipients.
 */
const settingsPage = {
    recipients: [],

    async load() {
        const container = document.getElementById('settingsContent');
        container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

        try {
            const data = await api.getRecipients();
            this.recipients = data.recipients;
            this.render();
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-text">Помилка завантаження</div></div>`;
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
                            ${r.is_default ? '<span class="default-badge">За замовч.</span>' : 
                              `<button class="btn-small btn-secondary" onclick="settingsPage.setDefault(${r.id})">Зробити осн.</button>`}
                            <button class="btn-small btn-secondary" onclick="settingsPage.startEdit(${r.id})">✏️</button>
                            <button class="btn-small btn-secondary btn-danger" onclick="settingsPage.remove(${r.id})">🗑</button>
                        </div>
                    `).join('')}
                </div>
            ` : `
                <div class="empty-state" style="padding:30px">
                    <div class="empty-icon">👤</div>
                    <div class="empty-text">Немає збережених отримувачів</div>
                </div>
            `}

            <div class="section-title" id="recipientFormTitle">Додати отримувача</div>
            <div class="card" style="padding:14px">
                <div class="form-group">
                    <label class="form-label">ПІБ</label>
                    <input class="form-input" id="settingsName" placeholder="Прізвище Ім'я По-батькові">
                </div>
                <div class="form-group">
                    <label class="form-label">Номер телефону</label>
                    <input class="form-input" id="settingsPhone" type="tel" placeholder="+380XXXXXXXXX">
                </div>
                <input type="hidden" id="settingsEditId" value="">
                <button class="btn-primary" onclick="settingsPage.saveRecipient()" id="settingsSaveBtn">
                    ➕ Додати
                </button>
                <button class="btn-secondary" onclick="settingsPage.cancelEdit()" id="settingsCancelBtn" style="margin-top:8px;display:none">
                    Скасувати
                </button>
            </div>
        `;
    },

    startEdit(id) {
        const r = this.recipients.find(x => x.id === id);
        if (!r) return;
        document.getElementById('settingsName').value = r.full_name;
        document.getElementById('settingsPhone').value = r.phone;
        document.getElementById('settingsEditId').value = id;
        document.getElementById('recipientFormTitle').textContent = 'Редагувати отримувача';
        document.getElementById('settingsSaveBtn').textContent = '💾 Зберегти';
        document.getElementById('settingsCancelBtn').style.display = 'block';
        document.getElementById('settingsName').focus();
    },

    cancelEdit() {
        document.getElementById('settingsName').value = '';
        document.getElementById('settingsPhone').value = '';
        document.getElementById('settingsEditId').value = '';
        document.getElementById('recipientFormTitle').textContent = 'Додати отримувача';
        document.getElementById('settingsSaveBtn').textContent = '➕ Додати';
        document.getElementById('settingsCancelBtn').style.display = 'none';
    },

    async saveRecipient() {
        const name = document.getElementById('settingsName').value.trim();
        const phone = document.getElementById('settingsPhone').value.trim();
        const editId = document.getElementById('settingsEditId').value;

        if (!name || !phone) {
            app.showToast('Заповніть ПІБ та телефон');
            return;
        }

        try {
            if (editId) {
                await api.updateRecipient(parseInt(editId), { full_name: name, phone });
                app.showToast('✅ Оновлено', 'success');
            } else {
                await api.createRecipient({ full_name: name, phone, is_default: this.recipients.length === 0 });
                app.showToast('✅ Додано', 'success');
            }
            await this.load();
        } catch (e) {
            app.showToast('❌ Помилка: ' + e.message);
        }
    },

    async setDefault(id) {
        try {
            await api.setDefaultRecipient(id);
            app.showToast('✅ Основний отримувач змінено', 'success');
            await this.load();
        } catch (e) {
            app.showToast('❌ Помилка');
        }
    },

    async remove(id) {
        try {
            await api.deleteRecipient(id);
            app.showToast('Видалено');
            await this.load();
        } catch (e) {
            app.showToast('❌ Помилка');
        }
    },

    _esc(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }
};
