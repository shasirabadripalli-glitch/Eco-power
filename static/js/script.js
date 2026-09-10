/* ==========================================================================
   EcoPower - Smart Renewable Solar Energy Management System (SIH 2026)
   Front-End Client Controller Script
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
    // State Flags
    let isDemoMode = true;
    let pollInterval = null;

    // Chart.js Instances
    let chartPowerTimeline = null;
    let chartGenVsCons = null;
    let chartBatteryTrend = null;
    let chartUsageMix = null;

    // History Buffer for Timeline
    const timeLabels = [];
    const powerHistory = [];
    const currentHistory = [];
    const batteryHistory = [];

    // DOM Elements
    const statusDot = document.getElementById('status-dot');
    const statusModeText = document.getElementById('status-mode-text');
    const btnToggleMode = document.getElementById('btn-toggle-mode');
    const activeModeTag = document.getElementById('active-mode-tag');
    const valActiveScenario = document.getElementById('val-active-scenario');

    // -------------------------------------------------------------------------
    // 1. Initialize Visual Analytics Charts (Chart.js)
    // -------------------------------------------------------------------------
    function initCharts() {
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Plus Jakarta Sans, sans-serif';

        // Chart 1: Solar Power & Current Timeline
        const ctxPower = document.getElementById('chart-power-timeline').getContext('2d');
        chartPowerTimeline = new Chart(ctxPower, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Solar Power (W)',
                        data: [],
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.15)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Solar Current (A)',
                        data: [],
                        borderColor: '#3b82f6',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [4, 4],
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true }
                }
            }
        });

        // Chart 2: Generation vs Consumption Bar Chart
        const ctxGenCons = document.getElementById('chart-gen-vs-cons').getContext('2d');
        chartGenVsCons = new Chart(ctxGenCons, {
            type: 'bar',
            data: {
                labels: ['Solar Generated', 'Energy Consumed', 'Solar Used', 'Excess Solar'],
                datasets: [{
                    label: 'Energy (kWh)',
                    data: [29.82, 14.20, 14.20, 15.62],
                    backgroundColor: [
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(139, 92, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(6, 182, 212, 0.8)'
                    ],
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true }
                }
            }
        });

        // Chart 3: Battery Level Trend Area Chart
        const ctxBattery = document.getElementById('chart-battery-trend').getContext('2d');
        chartBatteryTrend = new Chart(ctxBattery, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Battery Charge Level (%)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.15)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { color: 'rgba(255,255,255,0.05)' } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)' }, min: 0, max: 100 }
                }
            }
        });

        // Chart 4: Renewable vs Grid Mix Doughnut Chart
        const ctxMix = document.getElementById('chart-usage-mix').getContext('2d');
        chartUsageMix = new Chart(ctxMix, {
            type: 'doughnut',
            data: {
                labels: ['Renewable Self-Consumption', 'Grid Supplemental Energy'],
                datasets: [{
                    data: [14.20, 0.0],
                    backgroundColor: ['#10b981', '#8b5cf6'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                cutout: '70%'
            }
        });
    }

    // -------------------------------------------------------------------------
    // 2. Priority Loads Rendering & Interactive Control
    // -------------------------------------------------------------------------
    function renderLoads(loads) {
        const container = document.getElementById('loads-container');
        if (!container) return;

        container.innerHTML = '';
        loads.forEach(load => {
            const card = document.createElement('div');
            card.className = `load-card ${load.status === 'ON' ? 'status-on' : 'status-off'}`;

            card.innerHTML = `
                <div>
                    <div class="load-header">
                        <span class="load-priority-pill priority-${load.priority}">${load.category}</span>
                        <span class="badge ${load.mode === 'AUTO' ? 'badge-accent' : 'badge-outline'}">${load.mode} Control</span>
                    </div>
                    <h4 class="load-name">${load.name}</h4>
                    <p class="load-desc">${load.description}</p>
                </div>
                <div>
                    <div class="load-power-row">
                        <span>Power Demand:</span>
                        <strong>${load.power_w} W</strong>
                    </div>
                    <div class="load-actions">
                        <button class="btn btn-sm ${load.status === 'ON' ? 'btn-accent' : 'btn-outline'} btn-load-toggle" onclick="toggleLoad('${load.id}', '${load.status}')">
                            <i class="fa-solid ${load.status === 'ON' ? 'fa-power-off' : 'fa-play'}"></i> ${load.status === 'ON' ? 'Switch OFF' : 'Switch ON'}
                        </button>
                        <button class="btn btn-sm btn-outline" title="Reset to Auto Smart Mode" onclick="setLoadAutoMode('${load.id}')">
                            <i class="fa-solid fa-wand-magic-sparkles"></i> Auto
                        </button>
                    </div>
                </div>
            `;
            container.appendChild(card);
        });
    }

    // Load Toggle Action Handler
    window.toggleLoad = async (loadId, currentStatus) => {
        const nextStatus = currentStatus === 'ON' ? 'OFF' : 'ON';
        try {
            const res = await fetch('/api/load-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ load_id: loadId, action: nextStatus })
            });
            const result = await res.json();
            if (result.success) {
                renderLoads(result.loads);
                fetchLatestTelemetry();
            }
        } catch (err) {
            console.error('Error toggling load state:', err);
        }
    };

    window.setLoadAutoMode = async (loadId) => {
        try {
            const res = await fetch('/api/load-control', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ load_id: loadId, action: 'set_mode_auto' })
            });
            const result = await res.json();
            if (result.success) {
                renderLoads(result.loads);
                fetchLatestTelemetry();
            }
        } catch (err) {
            console.error('Error setting load to auto mode:', err);
        }
    };

    // -------------------------------------------------------------------------
    // 3. Preset Scenario Simulator Action Handler
    // -------------------------------------------------------------------------
    window.runPresetScenario = async (scenarioName) => {
        try {
            const res = await fetch('/api/simulation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scenario: scenarioName })
            });
            const result = await res.json();
            if (result.success) {
                updateDashboardUI(result.data, result.loads, result.recommendations);
            }
        } catch (err) {
            console.error('Error running simulation scenario:', err);
        }
    };

    // -------------------------------------------------------------------------
    // 4. Update UI Dashboard Cards, Recommendations & Charts
    // -------------------------------------------------------------------------
    function updateDashboardUI(t, loads, recs) {
        if (!t) return;

        // KPI Card Text
        document.getElementById('val-voltage').innerText = t.voltage.toFixed(2);
        document.getElementById('val-current').innerText = t.current.toFixed(2);
        document.getElementById('val-power').innerText = t.power.toFixed(2);
        document.getElementById('val-solar-gen').innerText = t.solar_generated.toFixed(2);
        document.getElementById('val-energy-consumed').innerText = t.energy_consumed.toFixed(2);
        document.getElementById('val-battery-pct').innerText = Math.round(t.battery_pct);
        document.getElementById('val-utilization').innerText = (t.renewable_utilization || 100.0).toFixed(1);
        document.getElementById('val-money-saved').innerText = t.money_saved.toFixed(2);
        document.getElementById('val-co2-reduction').innerText = t.co2_reduction.toFixed(2);

        // Battery Progress Bar
        const fill = document.getElementById('battery-fill');
        if (fill) fill.style.width = `${Math.min(100, Math.max(0, t.battery_pct))}%`;

        // Active Scenario & Load Counters
        if (valActiveScenario) valActiveScenario.innerText = t.active_scenario || 'Live Run';
        if (document.getElementById('val-active-loads-count')) {
            const activeCount = loads ? loads.filter(l => l.status === 'ON').length : (t.active_loads_count || 2);
            document.getElementById('val-active-loads-count').innerText = `${activeCount} / 3`;
        }
        if (document.getElementById('val-energy-saved-kWh')) {
            document.getElementById('val-energy-saved-kWh').innerText = (t.energy_saved_kWh || 4.80).toFixed(2);
        }

        // Mode Status Badge
        if (t.source === 'esp32_hardware') {
            statusDot.className = 'status-dot green-pulse';
            statusModeText.innerText = 'ESP32 Hardware Connected';
            activeModeTag.innerText = 'Live ESP32 IoT Node';
        } else {
            statusDot.className = 'status-dot';
            statusModeText.innerText = 'Software Simulation Active';
            activeModeTag.innerText = 'Hackathon Simulator Active';
        }

        // Render Loads & Recommendations
        if (loads) renderLoads(loads);
        if (recs) renderRecommendations(recs);

        // Update Charts Data
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        timeLabels.push(now);
        powerHistory.push(t.power);
        currentHistory.push(t.current);
        batteryHistory.push(t.battery_pct);

        if (timeLabels.length > 10) {
            timeLabels.shift();
            powerHistory.shift();
            currentHistory.shift();
            batteryHistory.shift();
        }

        if (chartPowerTimeline) {
            chartPowerTimeline.data.labels = timeLabels;
            chartPowerTimeline.data.datasets[0].data = powerHistory;
            chartPowerTimeline.data.datasets[1].data = currentHistory;
            chartPowerTimeline.update();
        }

        if (chartGenVsCons) {
            chartGenVsCons.data.datasets[0].data = [t.solar_generated, t.energy_consumed, t.solar_used, t.excess_energy];
            chartGenVsCons.update();
        }

        if (chartBatteryTrend) {
            chartBatteryTrend.data.labels = timeLabels;
            chartBatteryTrend.data.datasets[0].data = batteryHistory;
            chartBatteryTrend.update();
        }

        if (chartUsageMix) {
            chartUsageMix.data.datasets[0].data = [t.solar_used, t.grid_energy];
            chartUsageMix.update();
        }
    }

    function renderRecommendations(recs) {
        const container = document.getElementById('recommendations-container');
        if (!container) return;

        container.innerHTML = '';
        if (!recs || recs.length === 0) {
            container.innerHTML = '<p class="text-muted">System operating normally with balanced solar generation.</p>';
            return;
        }

        recs.forEach(r => {
            const alert = document.createElement('div');
            alert.className = `rec-alert type-${r.type}`;
            alert.innerHTML = `
                <div class="rec-title">${r.title}</div>
                <div class="rec-desc">${r.message}</div>
            `;
            container.appendChild(alert);
        });
    }

    // -------------------------------------------------------------------------
    // 5. Telemetry Ingestion & Polling API
    // -------------------------------------------------------------------------
    async function fetchLatestTelemetry() {
        try {
            const res = await fetch('/api/latest');
            const result = await res.json();
            if (result.success) {
                updateDashboardUI(result.telemetry, result.loads, null);
            }
        } catch (err) {
            console.error('Error fetching latest telemetry:', err);
        }
    }

    async function fetchHistoryLogs() {
        try {
            const res = await fetch('/api/history');
            const data = await res.json();
            if (data.history) {
                const tbody = document.getElementById('history-table-body');
                if (!tbody) return;
                tbody.innerHTML = '';

                data.history.reverse().forEach(row => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${row.date}</td>
                        <td>${row.voltage.toFixed(2)} V</td>
                        <td>${row.current.toFixed(2)} A</td>
                        <td>${row.power.toFixed(2)} W</td>
                        <td>${row.solar_generated.toFixed(2)} kWh</td>
                        <td>${row.energy_consumed.toFixed(2)} kWh</td>
                        <td>${Math.round(row.battery_pct)} %</td>
                        <td>₹${row.money_saved.toFixed(2)}</td>
                        <td>${row.co2_reduction.toFixed(2)} kg</td>
                        <td>${row.active_loads || '2/3'}</td>
                        <td><span class="badge ${row.source === 'esp32_hardware' ? 'badge-accent' : 'badge-outline'}">${row.source}</span></td>
                    `;
                    tbody.appendChild(tr);
                });

                if (data.summary) {
                    document.getElementById('sum-records').innerText = data.summary.record_count;
                    document.getElementById('sum-solar').innerText = data.summary.total_solar;
                    document.getElementById('sum-savings').innerText = data.summary.total_savings;
                    document.getElementById('sum-co2').innerText = data.summary.total_co2;
                }
            }
        } catch (err) {
            console.error('Error fetching history logs:', err);
        }
    }

    // Custom Telemetry Form Submit
    const form = document.getElementById('energy-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const payload = Object.fromEntries(formData.entries());
            payload.source = 'manual_simulation';

            try {
                const res = await fetch('/api/energy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const result = await res.json();
                if (result.success) {
                    updateDashboardUI(result.data, result.loads, result.recommendations);
                    fetchHistoryLogs();
                }
            } catch (err) {
                console.error('Error submitting custom telemetry:', err);
            }
        });
    }

    // Randomize Button
    const btnRandomize = document.getElementById('btn-randomize-demo');
    if (btnRandomize) {
        btnRandomize.addEventListener('click', () => {
            const v = (10 + Math.random() * 10).toFixed(1);
            const c = (0.5 + Math.random() * 2.5).toFixed(1);
            const b = Math.floor(30 + Math.random() * 65);
            const l = (5 + Math.random() * 20).toFixed(1);

            document.getElementById('input_voltage').value = v;
            document.getElementById('input_current').value = c;
            document.getElementById('input_battery').value = b;
            document.getElementById('input_load').value = l;

            form.dispatchEvent(new Event('submit'));
        });
    }

    // Initialize Page
    initCharts();
    fetchLatestTelemetry();
    fetchHistoryLogs();

    // Set automatic polling
    pollInterval = setInterval(() => {
        fetchLatestTelemetry();
    }, 3000);
});
