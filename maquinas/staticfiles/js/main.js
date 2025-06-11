document.addEventListener('DOMContentLoaded', () => {
    if (window.location.hash) {
        history.replaceState(null, '', window.location.pathname); // borra el hash
    }

    const welcomeMsgElement = document.getElementById('welcome-message');
    const activeUser = "Equipo Coca-Cola";
    if (welcomeMsgElement) {
        welcomeMsgElement.textContent = `¡Bienvenido, ${activeUser}}!`;
    }
});
