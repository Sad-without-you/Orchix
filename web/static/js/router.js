// ORCHIX v1.3 - SPA Hash Router

const Router = {
    routes: {},
    currentSSE: null,

    register(hash, renderFn) {
        this.routes[hash] = renderFn;
    },

    navigate() {
        // Close active SSE connection
        if (this.currentSSE) {
            this.currentSSE.close();
            this.currentSSE = null;
        }

        const hash = window.location.hash || '#/dashboard';
        const route = this.routes[hash];

        // Update nav active state
        document.querySelectorAll('.nav-link').forEach(el => {
            el.classList.toggle('active', el.getAttribute('href') === hash);
        });

        const content = document.getElementById('content');
        content.scrollTop = 0;
        if (route) {
            route(content);
        } else {
            content.innerHTML = '<div class="empty-state"><h2>Page not found</h2></div>';
        }
    },

    init() {
        window.addEventListener('hashchange', () => this.navigate());
        this.navigate();
    }
};

// Init router after all page scripts are loaded
window.addEventListener('DOMContentLoaded', () => {
    // Small delay to ensure all route registrations are done
    setTimeout(() => Router.init(), 10);
});
