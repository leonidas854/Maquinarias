function initReportsPage() {
    const sidebarLinks = document.querySelectorAll('.reports-sidebar .sidebar-menu a');
    const reportTitle = document.getElementById('report-title');
    const reportDataView = document.getElementById('report-data-view');

    sidebarLinks.forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault();
            const reportType = link.getAttribute('data-report');
            
            sidebarLinks.forEach(l => l.classList.remove('active-report'));
            link.classList.add('active-report');

            loadReportData(reportType);
        });
    });

    function loadReportData(type) {
        reportTitle.textContent = `Reporte: ${type.charAt(0).toUpperCase() + type.slice(1)}`;
        reportDataView.innerHTML = '<p>Cargando datos del reporte...</p>';

        // Simulación de carga de datos
        setTimeout(() => {
            let tableHtml = '<p>No hay datos disponibles para este reporte.</p>';
            if (type === 'markov') {
                tableHtml = generateDummyTable(
                    ['Máquina', 'Estado Óptimo', 'Probabilidad', 'Fecha Simulación'],
                    [
                        ['Embotelladora A1', 'Operando', '0.95', '2023-10-26'],
                        ['Etiquetadora B2', 'Mantenimiento', '0.03', '2023-10-25'],
                        ['Llenadora C3', 'Operando', '0.98', '2023-10-26']
                    ]
                );
            } else if (type === 'qlearning') {
                tableHtml = generateDummyTable(
                    ['Proceso', 'Acción Recomendada', 'Valor Q Estimado', 'Último Entrenamiento'],
                    [
                        ['Transporte X', 'Ruta Alterna', '8.75', '2023-10-20'],
                        ['Control Calidad Y', 'Aumentar Muestreo', '7.20', '2023-10-22']
                    ]
                );
            } else if (type === 'manual') {
                 tableHtml = generateDummyTable(
                    ['Máquina', 'Parámetro Ajustado', 'Nuevo Valor', 'Fecha Ajuste', 'Responsable'],
                    [
                        ['Línea Ensamblaje Z', 'Velocidad Cinta', '1.5 m/s', '2023-10-24', 'J.Perez'],
                        ['Paletizadora P1', 'Altura Pallet', '1.8 m', '2023-10-23', 'M.Gomez']
                    ]
                );
            }
            reportDataView.innerHTML = tableHtml;
        }, 500); // Simular delay de red
    }

    function generateDummyTable(headers, dataRows) {
        let table = '<table class="data-table"><thead><tr>';
        headers.forEach(header => table += `<th>${header}</th>`);
        table += '</tr></thead><tbody>';
        dataRows.forEach(row => {
            table += '<tr>';
            row.forEach(cell => table += `<td>${cell}</td>`);
            table += '</tr>';
        });
        table += '</tbody></table>';
        return table;
    }
     // Cargar un reporte por defecto si no hay hash o es la página de reportes
    if (document.querySelector('.reports-page')) { // Asegurarse que estamos en la página de reportes
        const defaultReportLink = document.querySelector('.reports-sidebar .sidebar-menu a[data-report="markov"]');
        if (defaultReportLink) {
            defaultReportLink.click(); // Simula un click para cargar el primer reporte
        } else {
             reportDataView.innerHTML = '<p class="placeholder-text">Seleccione un reporte del menú para ver los datos.</p>';
        }
    }
}