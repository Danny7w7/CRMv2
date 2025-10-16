
// --- Función Auxiliar ---
function calcularPromedio(series) {
    let total = 0;
    let count = 0;
    series.forEach(serie => {
        serie.data.forEach(valor => {
            if (valor > 0) {
                total += valor;
                count++;
            }
        });
    });
    return count ? (total / count) : 0;
}

// --- SCRIPT 1: Gráficos dinámicos por agente/semana ---
// Usamos chartsAgentsData que viene del HTML
chartsAgentsData.forEach((chartData, index) => {
    // Verificar si todas las series están en cero
    const hasValidData = chartData.series.some(serie =>
        serie.data.some(val => val > 0)
    );

    if (!hasValidData) return; // Si no hay datos > 0, no mostrar el gráfico

    // Filtrar series con todos ceros
    chartData.series = chartData.series.filter(serie =>
        serie.data.some(val => val > 0)
    );

    const chartId = `chart-agent-${index}`;
    const container = document.createElement("div");
    container.className = "chart-container";

    const title = document.createElement("h2");
    title.textContent = `Week: ${chartData.semana}`;

    const chartDiv = document.createElement("div");
    chartDiv.id = chartId;
    chartDiv.style.height = "400px";

    container.appendChild(title);
    container.appendChild(chartDiv);
    // Asegurarse de que el elemento 'charts-wrapper' existe antes de añadir hijos
    const chartsWrapper = document.getElementById("charts-wrapper");
    if (chartsWrapper) {
        chartsWrapper.appendChild(container);
    } else {
        console.error("El elemento con id 'charts-wrapper' no se encontró en el DOM.");
    }


    const optionsAgents = {
        chart: {
            type: 'bar',
            height: 400,
            stacked: false,
            toolbar: { show: false },
        },
        annotations: {
            yaxis: [
                {
                    y: calcularPromedio(chartData.series),
                    borderColor: '#FF4560',
                    label: {
                        borderColor: '#FF4560',
                        style: {
                            color: '#fff',
                            background: '#FF4560'
                        },
                        text: 'Promedio'
                    }
                }
            ]
        },
        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: '90%',
                dataLabels: {
                    position: 'top',
                },
            },
        },
        dataLabels: {
            enabled: true,
            formatter: function (val) {
                return val === 0 ? '' : val;
            },
            offsetY: -20,
            style: {
                fontSize: '14px',
                colors: ['#000']
            }
        },
        series: chartData.series,
        xaxis: {
            categories: chartData.categories,
        },
        yaxis: {
            title: {
                text: 'Cantidad de clientes'
            }
        },
        tooltip: {
            shared: true,
            intersect: false,
        },
        legend: {
            position: 'top',
        },
        colors: ['#008FFB', '#00E396', '#FEB019', '#FF4560', '#775DD0', '#26a69a', '#f44336']
    };

    const chartAgent = new ApexCharts(document.querySelector(`#${chartId}`), optionsAgents);
    chartAgent.render();
});

// --- SCRIPT 2: Gráfico de semanas ---
// Usamos chartsWeekPreviusData que viene del HTML
const chartDataSemanas = chartsWeekPreviusData;

// Extraer las categorías (semanas) y reorganizar los datos
const categoriesSemanas = chartDataSemanas.map(item => item.semana);

// Organizar las series
const obamacareDataSemanas = chartDataSemanas.map(item =>
    item.series.find(s => s.name === 'OBAMACARE')?.data[0] || 0
);

const suppDataSemanas = chartDataSemanas.map(item =>
    item.series.find(s => s.name === 'SUPP')?.data[0] || 0
);

// Configuración del gráfico
const optionsSemanas = {
    chart: {
        type: 'line',
        height: 400,
        toolbar: { show: false }
    },
    series: [
        {
            name: 'OBAMACARE',
            type: 'column',
            data: obamacareDataSemanas
        },
        {
            name: 'SUPP',
            type: 'column',
            data: suppDataSemanas
        }
    ],
    xaxis: {
        categories: categoriesSemanas,
        labels: {
            rotate: -45,
            style: {
                fontSize: '12px'
            }
        }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded'
        },
    },
    markers: {
        size: 0
    },
    dataLabels: {
        enabled: true,
        style: {
            fontSize: '12px',
            fontWeight: 'bold'
        }
    },
    title: {
        text: 'Registros por Semana',
        align: 'center',
        style: {
            fontSize: '18px',
            fontWeight: 'bold'
        }
    },
    colors: ['#00b894', '#0984e3'],
    stroke: {
        width: 0
    },
    legend: {
        position: 'top',
        horizontalAlign: 'center',
        floating: false
    },
    grid: {
        borderColor: '#e7e7e7',
        row: {
            colors: ['#f3f3f3', 'transparent'],
            opacity: 0.5
        },
    },
    tooltip: {
        shared: true,
        intersect: false,
        y: {
            formatter: function (val) {
                return val + " registros";
            }
        }
    }
};

// Renderizar gráfico de semanas
const chartSemanasElement = document.querySelector("#chart-semanas");
if (chartSemanasElement) {
    const chartSemanas = new ApexCharts(chartSemanasElement, optionsSemanas);
    chartSemanas.render();
} else {
    console.error("El elemento con id 'chart-semanas' no se encontró en el DOM.");
}


// Generar tablas dinámicamente
function generateTables() {
    const container = document.getElementById('tablesContainer');
    if (!container) {
        console.error("El elemento con id 'tablesContainer' no se encontró en el DOM.");
        return;
    }
    
    chartDataSemanas.forEach((weekData, index) => {
        const weekSection = document.createElement('div');
        weekSection.className = 'week-section';
        
        const weekTitle = document.createElement('div');
        weekTitle.className = 'week-title';
        weekTitle.textContent = weekData.semana;
        
        const table = document.createElement('table');
        table.className = 'agents-table';
        
        // Cabecera de la tabla
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Agente</th>
                    <th>ObamaCare</th>
                    <th>Supp</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                ${weekData.tabla.map(agente => `
                    <tr class="${agente.tiene_ventas ? 'has-sales' : 'no-sales'}">
                        <td class="agent-name">${agente.agente}</td>
                        <td class="obamacare-cell">${agente.obamacare}</td>
                        <td class="supp-cell">${agente.supp}</td>
                        <td class="total-column">${agente.total}</td>
                    </tr>
                `).join('')}
            </tbody>
        `;
        
        weekSection.appendChild(weekTitle);
        weekSection.appendChild(table);
        container.appendChild(weekSection);
    });
}

// Generar tablas cuando se carga la página (asegurarse de que el DOM esté listo)
document.addEventListener('DOMContentLoaded', generateTables);


// --- SCRIPT 3: Gráfico de 6 meses ---
// Usamos chartSixMonthsAgentsData que viene del HTML
const chartData6Meses = chartSixMonthsAgentsData;

// Extraer las categorías (meses) y reorganizar los datos
const categories6Meses = chartData6Meses.map(item => item.mes);

// Organizar las series
const obamacareData6Meses = chartData6Meses.map(item =>
    item.series.find(s => s.name === 'OBAMACARE')?.data[0] || 0
);

const suppData6Meses = chartData6Meses.map(item =>
    item.series.find(s => s.name === 'SUPP')?.data[0] || 0
);

const options6Meses = {
    chart: {
        type: 'line',
        height: 400,
        toolbar: { show: false }
    },
    series: [
        {
            name: 'OBAMACARE',
            type: 'column',
            data: obamacareData6Meses
        },
        {
            name: 'SUPP',
            type: 'column',
            data: suppData6Meses
        }
    ],
    xaxis: {
        categories: categories6Meses,
        labels: {
            rotate: -45,
            style: {
                fontSize: '12px'
            }
        }
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '55%',
            endingShape: 'rounded'
        },
    },
    markers: {
        size: 0
    },
    dataLabels: {
        enabled: true,
        style: {
            fontSize: '12px',
            fontWeight: 'bold'
        }
    },
    title: {
        text: 'Registros por Mes - Últimos 6 Meses',
        align: 'center',
        style: {
            fontSize: '18px',
            fontWeight: 'bold'
        }
    },
    colors: ['#00b894', '#0984e3'],
    stroke: {
        width: 0
    },
    legend: {
        position: 'top',
        horizontalAlign: 'center',
        floating: false
    },
    grid: {
        borderColor: '#e7e7e7',
        row: {
            colors: ['#f3f3f3', 'transparent'],
            opacity: 0.5
        },
    },
    tooltip: {
        y: {
            formatter: function (val) {
                return val + " registros"
            }
        }
    }
};

const chart6MesesElement = document.querySelector("#chart-6-meses");
if (chart6MesesElement) {
    const chart6Meses = new ApexCharts(chart6MesesElement, options6Meses);
    chart6Meses.render();
} else {
    console.error("El elemento con id 'chart-6-meses' no se encontró en el DOM.");
}


// --- SCRIPT 4: Gráfico histórico completo ---
// Usamos chartAllDataAgentsData que viene del HTML
const chartDataHistorico = chartAllDataAgentsData;

// Extraer las categorías (meses) y reorganizar los datos
const categoriesHistorico = chartDataHistorico.map(item => item.mes);

// Organizar las series
const obamacareDataHistorico = chartDataHistorico.map(item =>
    item.series.find(s => s.name === 'OBAMACARE')?.data[0] || 0
);

const suppDataHistorico = chartDataHistorico.map(item =>
    item.series.find(s => s.name === 'SUPP')?.data[0] || 0
);

const optionsHistorico = {
    chart: {
        type: 'line',
        height: 500,
        toolbar: {
            show: true,
            tools: {
                download: true,
                selection: true,
                zoom: true,
                zoomin: true,
                zoomout: true,
                pan: true,
                reset: true
            }
        },
        zoom: {
            enabled: true,
            type: 'x',
            autoScaleYaxis: true
        }
    },
    series: [
        {
            name: 'OBAMACARE',
            type: 'column',
            data: obamacareDataHistorico
        },
        {
            name: 'SUPP',
            type: 'column',
            data: suppDataHistorico
        }
    ],
    xaxis: {
        categories: categoriesHistorico,
        labels: {
            rotate: -45,
            style: {
                fontSize: '10px'
            },
            maxHeight: 80
        },
        tickAmount: Math.min(categoriesHistorico.length, 12)
    },
    plotOptions: {
        bar: {
            horizontal: false,
            columnWidth: '60%',
            endingShape: 'rounded'
        },
    },
    markers: {
        size: 0
    },
    dataLabels: {
        enabled: true,
        style: {
            fontSize: '10px',
            fontWeight: 'bold'
        },
        offsetY: -5
    },
    title: {
        text: 'Resumen Histórico Completo - Todos los Registros por Mes',
        align: 'center',
        style: {
            fontSize: '18px',
            fontWeight: 'bold'
        }
    },
    colors: ['#00b894', '#0984e3'],
    stroke: {
        width: 0
    },
    legend: {
        position: 'top',
        horizontalAlign: 'center',
        floating: false,
        fontSize: '12px'
    },
    grid: {
        borderColor: '#e7e7e7',
        row: {
            colors: ['#f3f3f3', 'transparent'],
            opacity: 0.5
        },
    },
    tooltip: {
        shared: true,
        intersect: false,
        y: {
            formatter: function (val) {
                return val + " registros";
            }
        }
    },
    responsive: [
        {
            breakpoint: 768,
            options: {
                chart: {
                    height: 400
                },
                xaxis: {
                    labels: {
                        rotate: -90,
                        style: {
                            fontSize: '8px'
                        }
                    }
                },
                dataLabels: {
                    enabled: false
                }
            }
        }
    ]
};

const chartHistoricoElement = document.querySelector("#chart-historico");
if (chartHistoricoElement) {
    const chartHistorico = new ApexCharts(chartHistoricoElement, optionsHistorico);
    chartHistorico.render();
} else {
    console.error("El elemento con id 'chart-historico' no se encontró en el DOM.");
}