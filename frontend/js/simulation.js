/* =================================================================
   SIMULATION — AgriNegotiator
   Handles scenario selection, progress display, and renders
   results with per-scenario cards and summary metrics.
================================================================= */

let _simChart = null;

// ── UI helpers ──────────────────────────────────

function showRunning(on) {
  const el = document.getElementById('simRunning');
  if (el) el.style.display = on ? '' : 'none';
}

function showOutput(on) {
  const el = document.getElementById('simulationOutput');
  if (el) el.style.display = on ? 'flex' : 'none';
}

/** Highlight the selected scenario card. */
function selectScenario(scenarioKey) {
  ['direct', 'storage', 'processing'].forEach((key) => {
    const card = document.getElementById(`scenario-${key}`);
    if (!card) return;
    const isSelected = key === scenarioKey || scenarioKey === 'all';
    card.style.borderColor = isSelected ? 'var(--green-500)' : 'var(--border)';
    card.style.boxShadow   = isSelected ? 'var(--shadow-glow)' : 'none';
  });
}

// ── Metrics summary ─────────────────────────────

function renderMetrics(metrics) {
  const section = document.getElementById('metricsSection');
  const bar     = document.getElementById('simStatsBar');
  if (!section || !bar) return;

  const avgPrice = metrics.average_final_price
    ? `₹${Number(metrics.average_final_price).toFixed(2)}`
    : '—';

  bar.innerHTML = `
    <div class="stat-card">
      <div class="stat-icon si-green">📐</div>
      <div><div class="stat-lbl">Scenarios Run</div><div class="stat-val">${metrics.total_scenarios ?? 0}</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon si-blue">✅</div>
      <div><div class="stat-lbl">Success Rate</div><div class="stat-val">${metrics.success_rate ?? 0}%</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon si-amber">💰</div>
      <div><div class="stat-lbl">Avg Final Price</div><div class="stat-val">${avgPrice}/kg</div></div>
    </div>
    <div class="stat-card">
      <div class="stat-icon si-purple">♻️</div>
      <div><div class="stat-lbl">Waste Diverted</div><div class="stat-val">${metrics.waste_diverted ?? 'N/A'}</div></div>
    </div>`;

  section.style.display = '';
}

// ── Per-scenario result cards ───────────────────────

const SCENARIO_META = {
  'direct-sale': { icon: '🛒', label: 'Direct Sale'   },
  'storage':     { icon: '🏗️', label: 'Storage Fallback' },
  'processing':  { icon: '⚙️', label: 'Processing Route' },
  'default':     { icon: '⚡', label: 'Simulation'  },
};

const STATUS_STYLE = {
  DEAL:                  { badge: 'badge-green',  icon: '✅', text: 'Deal Closed' },
  ESCALATED_STORAGE:     { badge: 'badge-amber',  icon: '🏗️', text: 'Storage Route' },
  ESCALATED_PROCESSING:  { badge: 'badge-purple', icon: '⚙️', text: 'Processing Route' },
  ESCALATED_COMPOST:     { badge: 'badge-lime',   icon: '♻️', text: 'Compost Route' },
  REJECTED:              { badge: 'badge-red',    icon: '❌', text: 'Rejected' },
  FAILED:                { badge: 'badge-red',    icon: '⚠️', text: 'Failed' },
};

function renderScenarioCard(record) {
  const meta   = SCENARIO_META[record.scenario_type] || SCENARIO_META.default;
  const status = record.result?.status || record.status || 'UNKNOWN';
  const ss     = STATUS_STYLE[status] || { badge: 'badge-gray', icon: '💬', text: status };
  const price  = record.result?.final_price || record.final_price;
  const summary = record.result?.summary || record.summary || '';
  const offers  = record.result?.offers || record.offers || [];

  const card = document.createElement('div');
  card.className = 'card';
  card.style.animation = 'fadein .4s ease';
  card.innerHTML = `
    <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem">
      <div style="display:flex;align-items:center;gap:1rem">
        <div style="font-size:2rem">${meta.icon}</div>
        <div>
          <h3>${meta.label}</h3>
          <p style="font-size:.8rem;margin-top:.25rem">${summary || 'Scenario completed.'}</p>
        </div>
      </div>
      <div style="display:flex;flex-direction:column;align-items:flex-end;gap:.5rem">
        <span class="badge ${ss.badge}">${ss.icon} ${ss.text}</span>
        ${price ? `<span style="font-size:1.5rem;font-weight:800;color:var(--green-500)">₹${Number(price).toFixed(2)}/kg</span>` : ''}
      </div>
    </div>
    ${offers.length ? `
      <div style="margin-top:1rem;border-top:1px solid var(--border);padding-top:1rem">
        <p style="font-size:.75rem;color:var(--text-muted);margin-bottom:.5rem">📄 ${offers.length} OFFERS</p>
        <div style="display:flex;flex-wrap:wrap;gap:.5rem">
          ${offers.slice(0,8).map((o) => `
            <span style="background:var(--bg-secondary);border:1px solid var(--border);border-radius:var(--r-sm);padding:3px 10px;font-size:.75rem">
              ${o.from||'?'} → ₹${Number(o.price||0).toFixed(2)}
            </span>`).join('')}
          ${offers.length > 8 ? `<span style="font-size:.75rem;color:var(--text-muted);padding:3px 0">+${offers.length-8} more</span>` : ''}
        </div>
      </div>` : ''}
  `;
  return card;
}

// ── Price chart (optional, if price_series available) ─────

function renderSimChart(records) {
  const canvas = document.getElementById('simPriceChart');
  if (!canvas || typeof Chart === 'undefined') return;
  const datasets = records
    .filter((r) => (r.result?.price_series || []).length > 0)
    .map((r, i) => {
      const colours = ['#22c55e','#3b82f6','#f59e0b','#a855f7'];
      const meta = SCENARIO_META[r.scenario_type] || SCENARIO_META.default;
      return {
        label: meta.label,
        data: (r.result.price_series || []).map((p) => (typeof p === 'object' ? p.price : p)),
        borderColor: colours[i % colours.length],
        fill: false, tension: 0.3,
      };
    });
  if (!datasets.length) return;
  if (_simChart) _simChart.destroy();
  const maxLen = Math.max(...datasets.map((d) => d.data.length));
  const labels = Array.from({ length: maxLen }, (_, i) => `R${i+1}`);
  _simChart = new Chart(canvas, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { color: '#94a3b8', font: { size: 11 } } } },
      scales: {
        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,.05)' } },
      },
    },
  });
}

// ── Main entry point ────────────────────────────

/**
 * @param {string} scenarioKey  'all' | 'direct-sale' | 'storage' | 'processing'
 */
async function startSimulation(scenarioKey = 'all') {
  const output = document.getElementById('simulationOutput');
  if (!output) return;

  selectScenario(scenarioKey);
  output.innerHTML = '';
  showRunning(true);
  showOutput(false);
  document.getElementById('metricsSection') && (document.getElementById('metricsSection').style.display = 'none');

  try {
    const result = await runSimulation({ scenario: scenarioKey });
    showRunning(false);
    showOutput(true);

    // Render metrics summary
    if (result.metrics) renderMetrics(result.metrics);

    // Render per-scenario results
    const records = result.results || result.scenarios || [];
    if (records.length) {
      records.forEach((rec) => output.appendChild(renderScenarioCard(rec)));
      // Optional combined chart
      if (records.length > 1) {
        const chartWrap = document.createElement('div');
        chartWrap.innerHTML = `
          <h3 style="margin:1.5rem 0 1rem">📈 Price Comparison</h3>
          <div style="position:relative;height:220px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--r-lg);padding:1rem">
            <canvas id="simPriceChart"></canvas>
          </div>`;
        output.appendChild(chartWrap);
        setTimeout(() => renderSimChart(records), 100);
      }
    } else {
      // Fallback: show single result if no records array
      output.appendChild(renderScenarioCard(result));
    }

    if (typeof showToast !== 'undefined') {
      showToast('success', 'Simulation complete!',
        `${result.metrics?.total_scenarios ?? 1} scenario(s) | Success rate: ${result.metrics?.success_rate ?? '?'}%`);
    }

  } catch (err) {
    showRunning(false);
    showOutput(true);
    output.innerHTML = `
      <div style="text-align:center;padding:3rem;">
        <div style="font-size:3rem;margin-bottom:1rem">❌</div>
        <h3>Simulation Failed</h3>
        <p style="margin-top:.5rem">${err.message}</p>
        <p style="margin-top:1rem;font-size:.83rem;color:var(--text-muted)">Make sure the backend is running:<br><code>python -m uvicorn backend.main:app --reload --port 8000</code></p>
      </div>`;
    if (typeof showToast !== 'undefined') showToast('error', 'Simulation failed', err.message);
  }
}