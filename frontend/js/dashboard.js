/* =================================================================
   DASHBOARD — AgriNegotiator
   Initialises stats, chart, agent cards, and runs the first
   negotiation. Handles the "New Negotiation" button.
================================================================= */

let _chartInstance = null;
let _offerHistory  = []; // { label, price, type }

// ── Progress steps ─────────────────────────────

/** Advance the negotiation stage indicator. Stage: 1–4. */
function setStage(stage) {
  for (let i = 1; i <= 4; i++) {
    const node = document.getElementById(`step-s${i}`) ||
                 document.getElementById(`step-${['open','counter','deal','done'][i-1]}`);
    const line = document.getElementById(`line-${i}`);
    if (node) { node.classList.toggle('done', i < stage); node.classList.toggle('active', i === stage); }
    if (line) line.classList.toggle('done', i < stage);
  }
}

// ── Stats bar ─────────────────────────────────

function updateStats(result) {
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  const offers = result.offers || [];
  set('statOffers', offers.length);
  set('statDeals',  result.status && result.status.includes('DEAL') ? 1 : 0);
  if (result.final_price) set('statAvgPrice', `₹${Number(result.final_price).toFixed(2)}`);
  set('statStatus', result.status || '—');
  const negIdEl = document.getElementById('statNegId');
  if (negIdEl) negIdEl.textContent = result.negotiation_id || '—';
}

// ── Offer display ──────────────────────────────

function updateOfferDisplay(result) {
  const priceEl  = document.getElementById('currentOfferPrice');
  const detailEl = document.getElementById('currentOfferDetail');
  const histEl   = document.getElementById('offerHistory');
  if (!priceEl) return;

  const price = result.final_price || (result.offers && result.offers.slice(-1)[0]?.price);
  if (price) priceEl.textContent = `₹${Number(price).toFixed(2)}`;

  if (detailEl) {
    const statusMap = {
      DEAL: '✅ Deal accepted',
      ESCALATED_STORAGE: '🏗️ Routed to warehouse',
      ESCALATED_PROCESSING: '⚙️ Routed to processor',
      ESCALATED_COMPOST: '♻️ Routed to compost',
      REJECTED: '❌ Rejected by both parties',
      FAILED: '⚠️ Negotiation failed',
    };
    detailEl.textContent = statusMap[result.status] || result.status || 'Awaiting…';
  }

  // Offer history list (last 5)
  const offers = result.offers || [];
  _offerHistory = offers.slice(-5).map((o) => ({
    label: `${o.agent || o.from || 'Agent'} → ${o.to || ''}`,
    price: o.price,
    type:  o.action || 'offer',
  }));

  if (histEl) {
    histEl.innerHTML = _offerHistory.map((o) => `
      <div class="offer-hist-item">
        <span class="oh-label">${escapeHtml(o.label)}</span>
        <span class="oh-price ${o.type === 'ACCEPT' ? 'green' : 'amber'}">₹${Number(o.price).toFixed(2)}</span>
      </div>`).join('');
  }
}

// ── Price chart ─────────────────────────────────

function renderPriceChart(priceSeries) {
  const ctx = document.getElementById('priceChart');
  if (!ctx || typeof Chart === 'undefined') return;

  const labels = priceSeries.map((_, i) => `Round ${i + 1}`);
  const prices = priceSeries.map((p) => (typeof p === 'object' ? p.price : p));

  if (_chartInstance) _chartInstance.destroy();

  _chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: 'Offer Price (₹/kg)',
        data: prices,
        borderColor: '#22c55e',
        backgroundColor: 'rgba(34,197,94,0.08)',
        tension: 0.4,
        fill: true,
        pointBackgroundColor: '#22c55e',
        pointRadius: 4,
        pointHoverRadius: 6,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: '#94a3b8', font: { size: 11 } }, grid: { color: 'rgba(255,255,255,0.05)' } },
      },
    },
  });

  const badge = document.getElementById('priceBadge');
  if (badge) badge.style.display = '';
}

// ── Role from URL ──────────────────────────────

function applyRoleBadge() {
  const role  = new URLSearchParams(window.location.search).get('role');
  const badge = document.getElementById('roleBadge');
  const icons = { farmer:'🌾', buyer:'🛒', warehouse:'🏗️', transporter:'🚛', processor:'⚙️', compost:'♻️' };
  if (badge && role) badge.textContent = `${icons[role]||'👤'} ${role.charAt(0).toUpperCase()+role.slice(1)}`;
}

// ── New Negotiation button ─────────────────────

function triggerNewNegotiation() {
  // Use stored payload if available, otherwise use default
  const stored = localStorage.getItem('latestNegotiationId');
  const payload = {
    farmer_name: 'Demo Farmer',
    crop: 'Tomato', quantity: 500, min_price: 18,
    shelf_life: 4, location: 'Nashik', quality: 'A', language: 'English',
  };
  clearLog();
  setStage(1);
  runNegotiationAndUpdate(payload);
}

// ── Core init ───────────────────────────────────

async function runNegotiationAndUpdate(payload) {
  const btn = document.getElementById('newNegBtn');
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Running…'; }

  setStage(1);
  try {
    const result = await startNegotiationFlow(payload);
    setStage(result.status && result.status.includes('DEAL') ? 4 : 3);
    updateStats(result);
    updateOfferDisplay(result);
    renderPriceChart(result.price_series || []);
    // Set agents to idle after negotiation
    ['farmer','buyer','warehouse','transporter','processor','compost'].forEach((t) =>
      updateAgentCard(t, { status: 'idle' })
    );
    showToast(
      result.status?.includes('DEAL') ? 'success' : 'info',
      `Negotiation complete: ${result.status}`,
      result.summary
    );
  } catch (err) {
    showToast('error', 'Negotiation error', err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '+ New Negotiation'; }
  }
}

async function initializeDashboard() {
  applyRoleBadge();
  await renderAgents();

  // Auto-run from stored ID, or run a default negotiation
  const storedId = localStorage.getItem('latestNegotiationId');
  if (storedId) {
    // Try to fetch existing result
    try {
      const result = await getNegotiationStatus(storedId);
      updateStats(result);
      updateOfferDisplay(result);
      renderPriceChart(result.price_series || []);
      appendLog(`💼 Loaded existing negotiation: ${storedId}`, 'system');
      setStage(4);
      return;
    } catch {
      // fall through to default
    }
  }

  // Default demo negotiation
  const payload = {
    farmer_name: 'Ramesh Kumar', crop: 'Tomato', quantity: 1000,
    min_price: 18, shelf_life: 4, location: 'Nashik', quality: 'A', language: 'Marathi',
  };
  await runNegotiationAndUpdate(payload);
}

initializeDashboard();