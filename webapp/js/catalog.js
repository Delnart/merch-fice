/**
 * Catalog module — product grid and detail view.
 */
const catalog = {
    products: [],

    async load() {
        const grid = document.getElementById('catalogGrid');
        const loading = document.getElementById('catalogLoading');
        const empty = document.getElementById('catalogEmpty');

        grid.innerHTML = '';
        loading.style.display = 'flex';
        empty.style.display = 'none';

        try {
            const data = await api.getCatalog();
            this.products = data.products;

            loading.style.display = 'none';

            if (!this.products.length) {
                empty.style.display = 'block';
                return;
            }

            grid.innerHTML = this.products.map(p => `
                <div class="card product-card" onclick="catalog.openProduct(${p.id})">
                    ${p.photo_url
                        ? `<img class="product-image" src="${p.photo_url}" alt="${this._esc(p.title)}" loading="lazy">`
                        : `<div class="product-image" style="display:flex;align-items:center;justify-content:center;font-size:2rem">👕</div>`
                    }
                    <div class="product-info">
                        <div class="product-title">${this._esc(p.title)}</div>
                        <div class="product-price">від ${p.min_price} грн</div>
                    </div>
                </div>
            `).join('');
        } catch (e) {
            loading.style.display = 'none';
            grid.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-text">Помилка завантаження</div></div>`;
        }
    },

    async openProduct(id) {
        app.navigate('product');
        const container = document.getElementById('productDetail');
        container.innerHTML = '<div class="loading"><div class="spinner"></div></div>';

        try {
            const p = await api.getProduct(id);
            document.getElementById('productDetailTitle').textContent = p.title;

            container.innerHTML = `
                ${p.photo_url
                    ? `<img class="product-detail-image" src="${p.photo_url}" alt="${this._esc(p.title)}">`
                    : ''
                }
                <div class="product-detail-title">${this._esc(p.title)}</div>
                <div class="product-detail-description">${this._esc(p.description)}</div>
                
                <div class="section-title">Оберіть розмір</div>
                <div class="size-selector" id="sizeSelector">
                    ${p.sizes.map((s, i) => `
                        <button class="size-btn ${i === 0 ? 'selected' : ''}" 
                                data-size="${s.size}" data-price="${s.price}"
                                onclick="catalog.selectSize(this)">
                            <span class="size-label">${s.size}</span>
                            <span class="size-price">${s.price} грн</span>
                        </button>
                    `).join('')}
                </div>
                
                <button class="btn-primary" id="addToCartBtn" onclick="catalog.addToCart(${p.id})">
                    🛒 Додати до кошика
                </button>
            `;
        } catch (e) {
            container.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><div class="empty-text">Товар не знайдено</div></div>`;
        }
    },

    selectSize(btn) {
        document.querySelectorAll('#sizeSelector .size-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
    },

    async addToCart(productId) {
        const selected = document.querySelector('#sizeSelector .size-btn.selected');
        if (!selected) {
            app.showToast('Оберіть розмір');
            return;
        }

        const btn = document.getElementById('addToCartBtn');
        btn.disabled = true;
        btn.textContent = '⏳ Додаємо...';

        try {
            await api.addToCart(productId, selected.dataset.size);
            app.showToast('✅ Додано в кошик!', 'success');
            await cart.updateBadge();
            btn.textContent = '✅ Додано!';
            setTimeout(() => {
                btn.disabled = false;
                btn.innerHTML = '🛒 Додати до кошика';
            }, 1500);
        } catch (e) {
            btn.disabled = false;
            btn.innerHTML = '🛒 Додати до кошика';
            app.showToast('❌ Помилка');
        }
    },

    _esc(str) {
        const d = document.createElement('div');
        d.textContent = str;
        return d.innerHTML;
    }
};
