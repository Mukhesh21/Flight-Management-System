/**
 * Admin Dashboard Chart.js Visualizations
 */

function initAdminCharts(flightData, baggageData) {
    // 1. Flights Status Distribution Chart
    const flightCtx = document.getElementById('flightStatusChart')?.getContext('2d');
    if (flightCtx && flightData) {
        new Chart(flightCtx, {
            type: 'doughnut',
            data: {
                labels: flightData.labels,
                datasets: [{
                    data: flightData.values,
                    backgroundColor: [
                        '#0284c7', // Scheduled - Blue
                        '#f59e0b', // Boarding - Gold
                        '#0ea5e9', // Departed - Cyan
                        '#ef4444', // Delayed - Red
                        '#64748b', // Cancelled - Slate
                        '#10b981'  // Arrived - Emerald
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 12,
                            font: { family: 'Plus Jakarta Sans', size: 12 }
                        }
                    }
                },
                cutout: '65%'
            }
        });
    }

    // 2. Baggage Pipeline Breakdown Chart
    const baggageCtx = document.getElementById('baggageStatusChart')?.getContext('2d');
    if (baggageCtx && baggageData) {
        new Chart(baggageCtx, {
            type: 'bar',
            data: {
                labels: baggageData.labels,
                datasets: [{
                    label: 'Number of Bags',
                    data: baggageData.values,
                    backgroundColor: '#1e3a5f',
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}
