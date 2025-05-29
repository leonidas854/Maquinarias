document.addEventListener('DOMContentLoaded', () => {
    const navbarContainer = document.getElementById('navbar-container');
    const mainContent = document.getElementById('main-content');
    const activeUser = "Equipo Coca-Cola"; // Simulado, obtén esto del login real

    // Ya no necesitas cargar el navbar por fetch si fue incluido por Django
    function configurarNavbar() {
        // Actualizar mensaje de bienvenida
        const welcomeMsgElement = document.getElementById('welcome-message');
        if (welcomeMsgElement) {
            welcomeMsgElement.textContent = `¡Bienvenido, ${activeUser}!`;
        }

        // Añadir event listeners a los links del navbar
        const navLinks = navbarContainer.querySelectorAll('.nav-link[data-page]');
        navLinks.forEach(link => {
            link.addEventListener('click', (event) => {
                event.preventDefault();
                const pageName = link.getAttribute('data-page');
                loadPageContent(pageName);

                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });

        // Cargar página por defecto (o hash)
        const initialPage = window.location.hash.substring(1) || 'markov';
        loadPageContent(initialPage);
        const initialLink = navbarContainer.querySelector(`.nav-link[data-page="${initialPage}"]`);
        if (initialLink) {
            navLinks.forEach(l => l.classList.remove('active'));
            initialLink.classList.add('active');
        }
    }

    async function loadPageContent(pageName) {
        const validPages = ['markov', 'qlearning', 'manual', 'reportes'];
        if (!validPages.includes(pageName)) {
            mainContent.innerHTML = `<div class="page-container"><h2>Página no encontrada</h2></div>`;
            window.location.hash = 'markov';
            return;
        }

        try {
            const response = await fetch(`/${pageName}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const pageHtml = await response.text();
            mainContent.innerHTML = pageHtml;
            window.location.hash = pageName;

            if (pageName === 'markov' && typeof initMarkovPage === 'function') initMarkovPage();
            if (pageName === 'qlearning' && typeof initQLearningPage === 'function') initQLearningPage();
            if (pageName === 'manual' && typeof initManualPage === 'function') initManualPage();
            if (pageName === 'reports' && typeof initReportsPage === 'function') initReportsPage();
        } catch (error) {
            console.error(`Error al cargar la página ${pageName}:`, error);
            mainContent.innerHTML = `<div class="page-container"><h2>Error</h2><p>No se pudo cargar la sección.</p></div>`;
        }
    }

    window.addEventListener('hashchange', () => {
        const pageName = window.location.hash.substring(1) || 'markov';
        const navLinks = navbarContainer.querySelectorAll('.nav-link[data-page]');
        const targetLink = navbarContainer.querySelector(`.nav-link[data-page="${pageName}"]`);
        
        if (targetLink) {
            loadPageContent(pageName);
            navLinks.forEach(l => l.classList.remove('active'));
            targetLink.classList.add('active');
        }
    });

    configurarNavbar();
});
