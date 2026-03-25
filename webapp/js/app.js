/**
 * Main SPA router and initialization.
 */
const app = {
    currentPage: 'catalog',
    isAdmin: false,
    _toastTimeout: null,

    async init() {
        // Telegram WebApp setup
        if (window.Telegram?.WebApp) {
            const tg = window.Telegram.WebApp;
            tg.ready();
            tg.expand();
            tg.enableClosingConfirmation();
        }

        // Check URL params for initial page
        const params = new URLSearchParams(window.location.search);
        const initialPage = params.get('page');

        // Setup bottom nav
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.addEventListener('click', () => {
                this.navigate(btn.dataset.page);
            });
        });

        // Check admin status
        this.checkAdmin();

        // Load initial page
        if (initialPage === 'admin') {
            this.navigate('admin');
        } else {
            this.navigate('catalog');
        }

        // Update cart badge
        cart.updateBadge();
    },

    async checkAdmin() {
        try {
            await api.checkAdmin();
            this.isAdmin = true;
            document.getElementById('adminNavItem').style.display = 'flex';
        } catch {
            this.isAdmin = false;
        }
    },

    navigate(page) {
        // Hide all pages
        document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
        
        // Show target page
        const target = document.getElementById(`page-${page}`);
        if (target) {
            target.classList.add('active');
        }

        // Update nav active state (only for main pages)
        const mainPages = ['catalog', 'cart', 'settings', 'admin'];
        document.querySelectorAll('.nav-item').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.page === page);
        });

        // Show/hide bottom nav (hide on subpages)
        const hideNav = ['product', 'checkout', 'admin-edit', 'success'].includes(page);
        document.getElementById('bottomNav').style.display = hideNav ? 'none' : 'flex';

        this.currentPage = page;

        // Load page data
        switch (page) {
            case 'catalog':
                catalog.load();
                break;
            case 'cart':
                cart.load();
                break;
            case 'checkout':
                checkout.load();
                break;
            case 'settings':
                settingsPage.load();
                break;
            case 'admin':
                admin.load();
                break;
        }
    },

    showToast(message, type = '') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast show' + (type ? ` ${type}` : '');
        
        if (this._toastTimeout) clearTimeout(this._toastTimeout);
        this._toastTimeout = setTimeout(() => {
            toast.classList.remove('show');
        }, 2500);
    },
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => app.init());
