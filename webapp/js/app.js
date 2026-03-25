/**
 * App router & toast utility.
 */
const app = {
    currentPage: 'catalog',
    _toastTimeout: null,

    init() {
        /* nav clicks */
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => this.navigate(btn.dataset.page));
        });

        /* initial data */
        catalog.load();
        cart.updateBadge();
        this.checkAdmin();

        /* deep link from URL, e.g. ?page=admin */
        const urlPage = new URLSearchParams(window.location.search).get('page');
        if (urlPage) this.navigate(urlPage);
    },

    navigate(page) {
        this.currentPage = page;

        /* hide all pages, show target */
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        const target = document.getElementById('page-' + page);
        if (target) target.classList.add('active');

        /* update nav */
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const navBtn = document.querySelector(`.nav-item[data-page="${page}"]`);
        if (navBtn) navBtn.classList.add('active');

        /* load page data */
        switch (page) {
            case 'catalog':  catalog.load(); break;
            case 'cart':     cart.load(); break;
            case 'checkout': checkout.load(); break;
            case 'settings': settings.load(); break;
            case 'admin':    admin.load(); break;
        }

        window.scrollTo(0, 0);
    },

    showToast(message, duration = 2500) {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.classList.add('show');

        if (this._toastTimeout) clearTimeout(this._toastTimeout);
        this._toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    },

    async checkAdmin() {
        try {
            const data = await api.checkAdmin();
            if (data.is_admin) {
                document.getElementById('adminNavItem').style.display = '';
            }
        } catch (e) {}
    }
};

document.addEventListener('DOMContentLoaded', () => app.init());
