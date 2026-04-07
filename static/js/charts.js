(function() {
    'use strict';

    const REFRESH_INTERVAL = 30000;
    let trendChart = null;
    let refreshTimer = null;

    async function loadTrendData() {
        try {
            const response = await fetch('/api/dashboard/trends?limit=10');
            if (!response.ok) throw new Error('Failed to fetch trends');
            const data = await response.json();
            return data.products || [];
        } catch (error) {
            console.error('[Charts] Error loading trends:', error);
            return [];
        }
    }

    function renderTrendChart(products, selectedId) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) {
            console.warn('[Charts] Canvas not found');
            return;
        }

        if (products.length === 0) {
            showNoDataMessage(canvas);
            return;
        }

        if (trendChart) {
            trendChart.destroy();
        }

        const product = products.find(p => p.id === selectedId) || products[0];
        const chartData = product.chart_data;

        if (!chartData.raw_points || chartData.raw_points.length < 3) {
            showInsufficientData(canvas, product.name);
            return;
        }

        const ctx = canvas.getContext('2d');
        trendChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.timestamps.map(t => `T${t}`),
                datasets: [
                    {
                        label: 'Raw Demand Score',
                        data: chartData.raw_points,
                        borderColor: '#94a3b8',
                        backgroundColor: 'rgba(148, 163, 184, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'EMA Short (3)',
                        data: chartData.ema_short,
                        borderColor: '#22c55e',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false
                    },
                    {
                        label: 'EMA Long (7)',
                        data: chartData.ema_long,
                        borderColor: '#3b82f6',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false
                    },
                    ...(chartData.ml_forecast_line && chartData.ml_forecast_line.length > 0 ? [{
                        label: 'ML Forecast',
                        data: chartData.ml_forecast_line,
                        borderColor: '#f59e0b',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false
                    }] : [])
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `${product.name} - Demand Trend`
                    },
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        suggestedMin: 0,
                        title: {
                            display: true,
                            text: 'Demand Score'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    }
                }
            }
        });
    }

    function renderProductTable(products) {
        const container = document.getElementById('trendsTableBody');
        if (!container) return;

        if (products.length === 0) {
            container.innerHTML = '<tr><td colspan="6">No trend data available</td></tr>';
            return;
        }

        let html = '';
        products.forEach(p => {
            const trendClass = p.trend === 'rising' ? 'text-green-600' :
                              p.trend === 'falling' ? 'text-red-600' : 'text-gray-600';
            
            html += `
                <tr>
                    <td>${p.name}</td>
                    <td><span class="${trendClass} font-semibold">${p.trend}</span></td>
                    <td>${p.velocity}</td>
                    <td>${(p.confidence * 100).toFixed(0)}%</td>
                    <td>${p.forecast !== null ? p.forecast : '-'}</td>
                    <td>${p.stock}</td>
                </tr>
            `;
        });
        container.innerHTML = html;
    }

    function showNoDataMessage(canvas) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = '16px system-ui';
        ctx.fillStyle = '#64748b';
        ctx.textAlign = 'center';
        ctx.fillText('No trend data available', canvas.width / 2, canvas.height / 2);
    }

    function showInsufficientData(canvas, productName) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.font = '14px system-ui';
        ctx.fillStyle = '#94a3b8';
        ctx.textAlign = 'center';
        ctx.fillText(`Insufficient data for ${productName}`, canvas.width / 2, canvas.height / 2);
    }

    async function initTrendCharts() {
        const products = await loadTrendData();
        window._cachedTrendProducts = products;
        
        const select = document.getElementById('trendProductSelect');
        const defaultId = select ? parseInt(select.value) : null;
        
        renderTrendChart(products, defaultId);
        renderProductTable(products);

        select?.addEventListener('change', (e) => {
            const selectedId = parseInt(e.target.value);
            renderTrendChart(products, selectedId);
        });

        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(async () => {
            const newData = await loadTrendData();
            window._cachedTrendProducts = newData;
            renderTrendChart(newData, defaultId);
            renderProductTable(newData);
        }, REFRESH_INTERVAL);
    }

    function destroyTrendCharts() {
        if (refreshTimer) {
            clearInterval(refreshTimer);
            refreshTimer = null;
        }
        if (trendChart) {
            trendChart.destroy();
            trendChart = null;
        }
    }

    if (typeof window !== 'undefined') {
        window.initTrendCharts = initTrendCharts;
        window.destroyTrendCharts = destroyTrendCharts;
    }

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { loadTrendData, renderTrendChart, initTrendCharts };
    }
})();