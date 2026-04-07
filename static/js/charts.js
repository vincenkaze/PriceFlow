(function() {
    'use strict';

    const REFRESH_INTERVAL = 30000;
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

    function renderTrendChart(product) {
        const canvas = document.getElementById('trendChart');
        if (!canvas) return;

        const existingChart = Chart.getChart(canvas);
        if (existingChart) existingChart.destroy();

        const chartData = product.chart_data;
        if (!chartData.raw_points || chartData.raw_points.length < 3) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.font = '14px system-ui';
            ctx.fillStyle = '#94a3b8';
            ctx.textAlign = 'center';
            ctx.fillText(`Insufficient data for ${product.name}`, canvas.width / 2, canvas.height / 2);
            return;
        }

        const labels = chartData.timestamps.map((t, i) => {
            const minsAgo = (chartData.raw_points.length - 1 - i) * 15;
            return minsAgo === 0 ? 'now' : `-${minsAgo}m`;
        });

        const forecastStart = chartData.raw_points.length - 3;

        const ctx = canvas.getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: [...labels, 'T+1', 'T+2', 'T+3'],
                datasets: [
                    {
                        label: 'Raw Demand',
                        data: chartData.raw_points,
                        borderColor: 'rgba(148,163,184,0.4)',
                        backgroundColor: 'rgba(148,163,184,0.05)',
                        borderWidth: 1,
                        tension: 0.4,
                        fill: true,
                        pointRadius: 2
                    },
                    {
                        label: 'EMA-3 (Short)',
                        data: chartData.ema_short,
                        borderColor: '#22c55e',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 3
                    },
                    {
                        label: 'EMA-7 (Long)',
                        data: chartData.ema_long,
                        borderColor: '#3b82f6',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 3
                    },
                    {
                        label: 'ML Forecast',
                        data: [...Array(forecastStart).fill(null), ...(chartData.ml_forecast_line?.slice(-3) || [])],
                        borderColor: '#f59e0b',
                        borderDash: [5, 5],
                        borderWidth: 2,
                        tension: 0.3,
                        fill: false,
                        pointRadius: 4,
                        pointBackgroundColor: '#f59e0b'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    title: {
                        display: true,
                        text: `${product.name} — ${product.trend?.toUpperCase() || 'ANALYZING'}`,
                        color: '#e2e8f0',
                        font: { size: 14, weight: 'bold' }
                    },
                    legend: { position: 'bottom', labels: { color: '#94a3b8', boxWidth: 12 } },
                    tooltip: {
                        backgroundColor: 'rgba(6,14,32,0.95)',
                        titleColor: '#e2e8f0',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(163,166,255,0.2)',
                        borderWidth: 1
                    }
                },
                scales: {
                    y: { min: 0, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } },
                    x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#64748b' } }
                }
            }
        });

        updateTrendSummary(product);
    }

    function updateTrendSummary(product) {
        const summaryName = document.getElementById('summaryProductName');
        const summaryTrend = document.getElementById('summaryTrend');
        const summaryVelocity = document.getElementById('summaryVelocity');
        const summaryConfidence = document.getElementById('summaryConfidence');
        const summaryForecast = document.getElementById('summaryForecast');

        if (!summaryName) return;

        summaryName.textContent = product.name;

        const trendColors = { rising: 'text-green-400', falling: 'text-red-400', stable: 'text-slate-400' };
        const trendIcons = { rising: '↑', falling: '↓', stable: '→' };
        const trend = product.trend || 'stable';

        summaryTrend.className = `font-semibold ${trendColors[trend] || 'text-slate-400'}`;
        summaryTrend.textContent = `${trendIcons[trend]} ${trend.toUpperCase()}`;
        summaryVelocity.textContent = product.velocity;
        summaryConfidence.textContent = ((product.confidence || 0) * 100).toFixed(0);
        summaryForecast.textContent = product.ml_forecast != null ? product.ml_forecast.toFixed(1) : '—';
    }

    function renderProductTable(products) {
        const container = document.getElementById('trendsTableBody');
        if (!container) return;
        if (!products.length) {
            container.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-slate-500">No trend data</td></tr>';
            return;
        }

        const trendColors = { rising: 'text-green-400 bg-green-400/10', falling: 'text-red-400 bg-red-400/10', stable: 'text-slate-400 bg-slate-400/10' };
        const trendIcons = { rising: '↑', falling: '↓', stable: '→' };

        let html = '';
        products.forEach(p => {
            const trend = p.trend || 'stable';
            const cls = trendColors[trend] || trendColors.stable;
            html += `<tr class="border-b border-white/5 hover:bg-white/5 transition">
                <td class="py-3 pr-4 text-white font-medium">${p.name}</td>
                <td class="py-3 px-2">
                    <span class="px-2 py-1 rounded text-xs font-bold ${cls}">${trendIcons[trend]} ${trend}</span>
                </td>
                <td class="py-3 px-2 text-slate-300">${(p.velocity || 0) > 0 ? '+' : ''}${p.velocity}</td>
                <td class="py-3 px-2 text-slate-300">${((p.confidence || 0) * 100).toFixed(0)}%</td>
                <td class="py-3 pl-2 text-amber-400 font-medium">${p.ml_forecast != null ? p.ml_forecast.toFixed(1) : '—'}</td>
            </tr>`;
        });
        container.innerHTML = html;
    }

    async function initTrendCharts() {
        const products = await loadTrendData();
        window._cachedTrends = products;

        if (products.length > 0) {
            renderTrendChart(products[0]);
            renderProductTable(products);

            const select = document.getElementById('trendProductSelect');
            if (select) {
                select.addEventListener('change', function() {
                    const selected = products.find(p => p.product_id == parseInt(this.value));
                    if (selected) renderTrendChart(selected);
                });
            }
        }

        if (refreshTimer) clearInterval(refreshTimer);
        refreshTimer = setInterval(async () => {
            const newData = await loadTrendData();
            window._cachedTrends = newData;
            const selectedId = parseInt(document.getElementById('trendProductSelect')?.value);
            const selected = newData.find(p => p.product_id == selectedId) || newData[0];
            if (selected) renderTrendChart(selected);
            renderProductTable(newData);
        }, REFRESH_INTERVAL);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTrendCharts);
    } else {
        initTrendCharts();
    }
})();