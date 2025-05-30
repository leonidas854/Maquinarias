document.addEventListener('DOMContentLoaded', () => {
    const aplicarBtn = document.getElementById('markov-aplicar');
    const maquinaSelect = document.getElementById('markov-maquina');
    const diasInput = document.getElementById('markov-dias');
    const resultsDiv = document.getElementById('markov-results');

    if (aplicarBtn) {
        aplicarBtn.addEventListener('click', () => {
            const maquina = maquinaSelect.value;
            const dias = diasInput.value;

            if (!maquina) {
                alert('Por favor, seleccione una máquina.');
                return;
            }
            if (!dias || dias < 1) {
                alert('Por favor, ingrese un número válido de días.');
                return;
            }

            resultsDiv.innerHTML = `<p>Procesando simulación Markov para <strong>${maquina}</strong> por <strong>${dias} días</strong>...</p>
                                    <p><em>(Aquí se mostrarían los resultados reales)</em></p>`;
        });
    }
});
