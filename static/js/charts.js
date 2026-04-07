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
        const container = document.getElementById('trendChart');
        if (!container) {
            console.warn('[Charts] Container not found');
            return;
        }

        if (products.length === 0) {
            container.innerHTML = '<div class="text-slate-400 text-center w-full">No data available</div>';
            return;
        }

        const product = products.find(p => p.id === selectedId) || products[0];
        const chartData = product.chart_data;

        if (!chartData.raw_points || chartData.raw_points.length < 3) {
            container.innerHTML = `<div class="text-slate-400 text-center w-full">Insufficient data for ${product.name}</div>`;
            return;
        }

        const maxScore = Math.max(...chartData.raw_points, 120);
        const barsHtml = chartData.raw_points.slice(-30).map((score, i) => {
            const heightPct = Math.max(5, (score / maxScore) * 100);
            const emaShort = chartData.ema_short?.[chartData.ema_short.length - 30 + i] || 0;
            const emaLong = chartData.ema_long?.[chartData.ema_long.length - 30 + i] || 0;
            return `
                <div class="flex-1 flex flex-col items-center gap-1">
                    <div class="w-full flex gap-[2px] items-end h-[300px]">
                        <div class="flex-1 bg-slate-600/60 rounded-t hover:bg-slate-500 transition relative group" style="height: ${heightPct}%">
                            <div class="absolute -top-6 left-1/2 -translate-x-1/2 text-xs text-slate-300 opacity-0 group-hover:opacity-100 transition">${score}</div>
                        </div>
                        <div class="flex-1 bg-green-500/60 rounded-t" style="height: ${Math.max(5, (emaShort / maxScore) * 100)}%"></div>
                        <div class="flex-1 bg-blue-500/60 rounded-t" style="height: ${Math.max(5, (emaLong / maxScore) * 100)}%"></div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div class="flex items-end gap-1 h-[300px] w-full pb-6 border-b border-white/20 relative">
                ${barsHtml}
                <div class="absolute bottom-0 left-0 w-full flex justify-between text-xs text-slate-500 pt-2">
                    <span>T-${chartData.raw_points.length - 30}</span>
                    <span>T${chartData.raw_points.length}</span>
                </div>
            </div>
            <div class="flex gap-4 mt-2 text-xs">
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-slate-600/60 rounded"></div>
                    <span class="text-slate-400">Raw</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-green-500/60 rounded"></div>
                    <span class="text-slate-400">EMA-3</span>
                </div>
                <div class="flex items-center gap-2">
                    <div class="w-3 h-3 bg-blue-500/60 rounded"></div>
                    <span class="text-slate-400">EMA-7</span>
                </div>
            </div>
        `;
        return;
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
                        min: 0,
                        max: 150,
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