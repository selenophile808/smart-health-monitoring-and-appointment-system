/**
 * Health Trends and Dashboard Analytics Charts using Chart.js
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Patient Dashboard Sparkline Chart
    initPatientSparkline();

    // 2. Comprehensive Health Trends Charts
    initHealthTrendsCharts();

    // 3. Admin Analytics Charts
    initAdminCharts();

    // 4. Doctor Patient Detail Health Trends Chart
    initDoctorPatientTrendsChart();
});

function initPatientSparkline() {
    const canvas = document.getElementById('dashboardTrendChart');
    if (!canvas) return;

    const labels = JSON.parse(canvas.getAttribute('data-labels') || '[]');
    const hrData = JSON.parse(canvas.getAttribute('data-hr') || '[]');
    const sysData = JSON.parse(canvas.getAttribute('data-sys') || '[]');

    if (labels.length === 0) return;

    new Chart(canvas, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Heart Rate (BPM)',
                    data: hrData,
                    borderColor: '#2563EB',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                },
                {
                    label: 'Systolic BP (mmHg)',
                    data: sysData,
                    borderColor: '#0F766E',
                    backgroundColor: 'rgba(15, 118, 110, 0.1)',
                    tension: 0.3,
                    fill: false,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'top', labels: { boxWidth: 12 } },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: {
                y: { beginAtZero: false, grid: { color: '#F1F5F9' } },
                x: { grid: { display: false } }
            }
        }
    });
}

function initHealthTrendsCharts() {
    const trendsContainer = document.getElementById('healthTrendsChartsContainer');
    if (!trendsContainer) return;

    const rawData = JSON.parse(trendsContainer.getAttribute('data-chart-data') || '{}');
    if (!rawData.labels || rawData.labels.length === 0) return;

    // Blood Pressure Chart
    const bpCanvas = document.getElementById('bpChart');
    if (bpCanvas) {
        new Chart(bpCanvas, {
            type: 'line',
            data: {
                labels: rawData.labels,
                datasets: [
                    {
                        label: 'Systolic (mmHg)',
                        data: rawData.systolic_bps,
                        borderColor: '#DC2626',
                        backgroundColor: 'rgba(220, 38, 38, 0.05)',
                        tension: 0.2,
                        pointRadius: 5,
                    },
                    {
                        label: 'Diastolic (mmHg)',
                        data: rawData.diastolic_bps,
                        borderColor: '#2563EB',
                        backgroundColor: 'rgba(37, 99, 235, 0.05)',
                        tension: 0.2,
                        pointRadius: 5,
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: {
                        suggestedMin: 50,
                        suggestedMax: 160,
                        grid: { color: '#E2E8F0' }
                    }
                }
            }
        });
    }

    // Heart Rate Chart
    const hrCanvas = document.getElementById('hrChart');
    if (hrCanvas) {
        new Chart(hrCanvas, {
            type: 'line',
            data: {
                labels: rawData.labels,
                datasets: [{
                    label: 'Pulse Rate (BPM)',
                    data: rawData.heart_rates,
                    borderColor: '#0F766E',
                    backgroundColor: 'rgba(15, 118, 110, 0.1)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 5,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { suggestedMin: 50, suggestedMax: 120, grid: { color: '#E2E8F0' } }
                }
            }
        });
    }

    // Blood Sugar Chart
    const sugarCanvas = document.getElementById('sugarChart');
    if (sugarCanvas) {
        new Chart(sugarCanvas, {
            type: 'bar',
            data: {
                labels: rawData.labels,
                datasets: [{
                    label: 'Blood Sugar (mg/dL)',
                    data: rawData.blood_sugars,
                    backgroundColor: 'rgba(245, 158, 11, 0.7)',
                    borderColor: '#F59E0B',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { suggestedMin: 60, suggestedMax: 200, grid: { color: '#E2E8F0' } }
                }
            }
        });
    }

    // Weight Chart
    const weightCanvas = document.getElementById('weightChart');
    if (weightCanvas) {
        new Chart(weightCanvas, {
            type: 'line',
            data: {
                labels: rawData.labels,
                datasets: [{
                    label: 'Weight (kg)',
                    data: rawData.weights,
                    borderColor: '#6366F1',
                    backgroundColor: 'rgba(99, 102, 241, 0.1)',
                    tension: 0.2,
                    pointRadius: 5,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { grid: { color: '#E2E8F0' } }
                }
            }
        });
    }
}

function initAdminCharts() {
    const statusCanvas = document.getElementById('adminStatusChart');
    if (statusCanvas) {
        const labels = JSON.parse(statusCanvas.getAttribute('data-labels') || '[]');
        const data = JSON.parse(statusCanvas.getAttribute('data-values') || '[]');

        new Chart(statusCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: [
                        '#F59E0B', // Pending
                        '#0284C7', // Approved
                        '#2563EB', // In Progress
                        '#16A34A', // Completed
                        '#64748B', // Cancelled
                        '#DC2626', // Rejected
                    ],
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    const specCanvas = document.getElementById('adminSpecChart');
    if (specCanvas) {
        const labels = JSON.parse(specCanvas.getAttribute('data-labels') || '[]');
        const data = JSON.parse(specCanvas.getAttribute('data-values') || '[]');

        new Chart(specCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Registered Doctors',
                    data: data,
                    backgroundColor: '#0F766E',
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true, ticks: { precision: 0 } }
                }
            }
        });
    }
}

function initDoctorPatientTrendsChart() {
    const container = document.getElementById('doctorPatientTrendsContainer');
    if (!container) return;

    let labels = [], sysData = [], diaData = [], hrData = [], sugarData = [];
    try {
        labels = JSON.parse(container.getAttribute('data-labels') || '[]');
        sysData = JSON.parse(container.getAttribute('data-sys') || '[]');
        diaData = JSON.parse(container.getAttribute('data-dia') || '[]');
        hrData = JSON.parse(container.getAttribute('data-hr') || '[]');
        sugarData = JSON.parse(container.getAttribute('data-sugar') || '[]');
    } catch (e) {
        console.error('Failed to parse doctor patient trend data', e);
        return;
    }

    if (!labels || labels.length === 0) return;

    const bpCanvas = document.getElementById('doctorBpChart');
    if (bpCanvas) {
        new Chart(bpCanvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Systolic (mmHg)',
                        data: sysData,
                        borderColor: '#DC2626',
                        backgroundColor: 'rgba(220, 38, 38, 0.05)',
                        tension: 0.2,
                        pointRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Diastolic (mmHg)',
                        data: diaData,
                        borderColor: '#2563EB',
                        backgroundColor: 'rgba(37, 99, 235, 0.05)',
                        tension: 0.2,
                        pointRadius: 4,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Heart Rate (BPM)',
                        data: hrData,
                        borderColor: '#0F766E',
                        backgroundColor: 'rgba(15, 118, 110, 0.05)',
                        borderDash: [5, 5],
                        tension: 0.2,
                        pointRadius: 4,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 12 } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        suggestedMin: 50,
                        suggestedMax: 160,
                        title: { display: true, text: 'BP (mmHg)' },
                        grid: { color: '#E2E8F0' }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        suggestedMin: 50,
                        suggestedMax: 120,
                        title: { display: true, text: 'HR (BPM)' },
                        grid: { drawOnChartArea: false }
                    }
                }
            }
        });
    }

    const sugarCanvas = document.getElementById('doctorSugarChart');
    if (sugarCanvas) {
        new Chart(sugarCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Blood Sugar (mg/dL)',
                    data: sugarData,
                    backgroundColor: 'rgba(245, 158, 11, 0.8)',
                    borderColor: '#F59E0B',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'top', labels: { boxWidth: 12 } }
                },
                scales: {
                    y: {
                        suggestedMin: 60,
                        suggestedMax: 200,
                        title: { display: true, text: 'mg/dL' },
                        grid: { color: '#E2E8F0' }
                    }
                }
            }
        });
    }
}

