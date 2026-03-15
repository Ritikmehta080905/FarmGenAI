/* =================================================================
   DASHBOARD — AgriNegotiator
   Initialises stats, chart, agent cards, and runs the first
   negotiation. Handles the "New Negotiation" button.
================================================================= */

let _chartInstance = null;
let _offerHistory  = []; // { label, price, type }

function getCurrentRole() {
  return new URLSearchParams(window.location.search).get('role') || 'farmer';
}

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
  const role  = getCurrentRole();
  const badge = document.getElementById('roleBadge');
  const icons = { farmer:'🌾', buyer:'🛒', warehouse:'🏗️', transporter:'🚛', processor:'⚙️', compost:'♻️' };
  if (badge && role) badge.textContent = `${icons[role]||'👤'} ${role.charAt(0).toUpperCase()+role.slice(1)}`;
}

function configureDashboard(role) {
  const subtitle = document.getElementById('dashSubtitle');
  const btn = document.getElementById('newNegBtn');
  if (role === 'buyer') {
    if (subtitle) subtitle.textContent = 'Browse active farmer listings and compare supply options across the marketplace';
    if (btn) btn.textContent = '↻ Refresh Listings';
    return;
  }

  if (subtitle) subtitle.textContent = 'Compare competing buyer offers and monitor the selected negotiation in real time';
  if (btn) btn.textContent = '+ New Negotiation';
}

function setMarketplaceContent(title, countLabel, html) {
  const titleEl = document.getElementById('marketplaceTitle');
  const countEl = document.getElementById('marketplaceCount');
  const board = document.getElementById('marketplaceBoard');
  if (titleEl) titleEl.textContent = title;
  if (countEl) countEl.textContent = countLabel;
  if (board) board.innerHTML = html;
}

function renderFarmerOfferBoard(result) {
  const offers = (result.market_offers || []).slice().sort((left, right) => right.offered_price - left.offered_price);
  if (!offers.length) {
    setMarketplaceContent(
      'Buyer Offer Comparison',
      '0 bids',
      '<div class="market-empty"><div class="empty-icon">🧾</div><p>No buyer bids were generated yet for this listing.</p></div>'
    );
    return;
  }

  const selected = result.selected_buyer || {};
  const cards = offers.map((offer, index) => {
    const isSelected = selected.buyer_id === offer.buyer_id || selected.buyer_name === offer.buyer_name;
    return `
      <article class="market-card${isSelected ? ' selected' : ''}">
        <div class="market-meta">Rank #${index + 1}</div>
        <h4>${escapeHtml(offer.buyer_name)}</h4>
        <div class="market-price">₹${Number(offer.offered_price).toFixed(2)}/kg</div>
        <div class="market-price-note">${Number(offer.offered_quantity).toFixed(0)}kg • ${escapeHtml(offer.location || 'Market')}</div>
        <div class="market-badges">
          <span class="market-pill ${offer.status === 'VIABLE' ? 'good' : 'warn'}">${escapeHtml(offer.status)}</span>
          ${isSelected ? '<span class="market-pill good">Selected for negotiation</span>' : ''}
        </div>
        <div class="market-strategy">${escapeHtml(offer.strategy || 'Marketplace buyer')}</div>
      </article>`;
  }).join('');

  setMarketplaceContent('Buyer Offer Comparison', `${offers.length} buyer bids`, cards);
}

async function renderBuyerListingsBoard() {
  const data = await getProduceListings();
  const produce = (data.produce || []).slice().reverse();
  if (!produce.length) {
    setMarketplaceContent(
      'Active Farmer Listings',
      '0 listings',
      '<div class="market-empty"><div class="empty-icon">🌾</div><p>No farmer listings are active yet. Ask a farmer to submit produce from the listing form.</p></div>'
    );
    return;
  }

  const cards = produce.map((item) => `
    <article class="market-card">
      <div class="market-meta">${escapeHtml(item.farmer_name || 'Farmer')}</div>
      <h4>${escapeHtml(item.crop || 'Produce')}</h4>
      <div class="market-price">₹${Number(item.min_price || 0).toFixed(2)}/kg</div>
      <div class="market-price-note">${Number(item.quantity || 0).toFixed(0)}kg • ${escapeHtml(item.location || 'Unknown')}</div>
      <div class="market-badges">
        <span class="market-pill good">${escapeHtml(item.status || 'ACTIVE')}</span>
        <span class="market-pill">Shelf life: ${escapeHtml(String(item.shelf_life || '—'))} days</span>
      </div>
      <div class="market-strategy">Quality ${escapeHtml(item.quality || 'A')} • ${escapeHtml(item.language || 'English')}</div>
    </article>`
  ).join('');

  setMarketplaceContent('Active Farmer Listings', `${produce.length} listings`, cards);
}

async function renderDefaultBuyerBoard() {
  const data = await getBuyers();
  const buyers = data.buyers || [];
  if (!buyers.length) {
    setMarketplaceContent(
      'Marketplace Board',
      '0 buyers',
      '<div class="market-empty"><div class="empty-icon">🛒</div><p>No marketplace buyers are configured.</p></div>'
    );
    return;
  }

  const cards = buyers.map((buyer) => `
    <article class="market-card">
      <div class="market-meta">${escapeHtml(buyer.location || 'Market')}</div>
      <h4>${escapeHtml(buyer.name || 'Buyer')}</h4>
      <div class="market-price">₹${Number(buyer.target_price || 0).toFixed(2)}/kg</div>
      <div class="market-price-note">Budget ₹${Number(buyer.budget || 0).toFixed(0)} • Capacity ${Number(buyer.max_quantity || 0).toFixed(0)}kg</div>
      <div class="market-strategy">${escapeHtml(buyer.strategy || 'Marketplace participant')}</div>
    </article>`
  ).join('');

  setMarketplaceContent('Marketplace Buyers', `${buyers.length} buyers`, cards);
}

async function renderMarketplaceBoard(role, result) {
  if (role === 'buyer') {
    await renderBuyerListingsBoard();
    return;
  }

  if (role === 'farmer' && result && (result.market_offers || []).length) {
    renderFarmerOfferBoard(result);
    return;
  }

  await renderDefaultBuyerBoard();
}

// ── History panel ──────────────────────────────

async function renderHistoryPanel() {
  const board = document.getElementById('historyBoard');
  const count = document.getElementById('historyCount');
  if (!board) return;

  let negs = [];
  try {
    const data = await getNegotiations();
    negs = (data.negotiations || []).filter((n) => n.status !== 'RUNNING');
  } catch {
    return; // silently skip if endpoint unreachable
  }

  if (count) count.textContent = `${negs.length}`;

  if (!negs.length) {
    board.innerHTML = '<div class="market-empty"><div class="empty-icon">📜</div><p>No past negotiations yet.</p></div>';
    return;
  }

  const statusClass = (s) => {
    if (!s) return '';
    if (s.includes('DEAL')) return 'deal';
    if (s.includes('FAIL') || s.includes('REJECT')) return 'failed';
    return 'running';
  };

  const statusIcon = (s) => {
    if (!s) return '⚡';
    if (s.includes('DEAL')) return '✅';
    if (s.includes('STORAGE')) return '🏗️';
    if (s.includes('PROCESSING')) return '⚙️';
    if (s.includes('COMPOST')) return '♻️';
    if (s.includes('FAIL')) return '❌';
    return '⚡';
  };

  board.innerHTML = negs.map((neg) => {
    const priceHtml = neg.final_price
      ? `<div class="history-price">₹${Number(neg.final_price).toFixed(2)}<span class="history-price-unit">/kg</span></div>`
      : `<div class="history-price none">No deal price</div>`;

    const logsHtml = (neg.logs || []).slice(0, 6).map((l) =>
      `<span>${escapeHtml(l)}</span>`
    ).join('');

    const farmerName = neg.farmer || '?';
    const buyerName = neg.selected_buyer
      ? (typeof neg.selected_buyer === 'string'
          ? neg.selected_buyer
          : (neg.selected_buyer.buyer_name || '—'))
      : '—';

    // All agents who participated
    const agents = neg.agents_involved && neg.agents_involved.length
      ? neg.agents_involved
      : [farmerName, ...(buyerName !== '—' ? [buyerName] : [])];

    // Add escalation agents from status if not already listed
    const statusStr = neg.status || '';
    if (statusStr.includes('STORAGE')    && !agents.includes('WarehouseAgent'))  agents.push('WarehouseAgent');
    if (statusStr.includes('PROCESSING') && !agents.includes('ProcessorAgent'))  agents.push('ProcessorAgent');
    if (statusStr.includes('COMPOST')    && !agents.includes('CompostAgent'))    agents.push('CompostAgent');

    const agentIcons = { WarehouseAgent:'🏗️', ProcessorAgent:'⚙️', CompostAgent:'♻️' };
    const agentBadges = agents.map((a) => {
      const icon = agentIcons[a] || (a === farmerName ? '🌾' : '🛒');
      return `<span class="market-pill agent-pill">${icon} ${escapeHtml(a)}</span>`;
    }).join('');

    const quantityNote = neg.quantity ? `${Number(neg.quantity).toFixed(0)} kg · ` : '';

    return `
    <article class="history-card ${statusClass(neg.status)}">
      <div class="history-meta">${neg.created_at ? new Date(neg.created_at).toLocaleString() : '—'} · ID: ${escapeHtml(String(neg.negotiation_id || '').slice(-6))}</div>
      <h4>${statusIcon(neg.status)} ${escapeHtml(neg.crop || '?')} <span class="history-farmer-tag">by ${escapeHtml(farmerName)}</span></h4>
      <div class="history-agents-row">
        <span class="history-agents-label">Agents:</span>
        ${agentBadges}
      </div>
      ${priceHtml}
      <div class="market-badges">
        <span class="market-pill ${neg.status && neg.status.includes('DEAL') ? 'good' : 'warn'}">${escapeHtml(neg.status || '?')}</span>
        <span class="market-pill">${quantityNote}${escapeHtml(neg.scenario || 'direct-sale')}</span>
      </div>
      <div class="history-meta">${escapeHtml(neg.summary || '')}</div>
      ${logsHtml ? `<div class="history-logs">${logsHtml}</div>` : ''}
    </article>`;
  }).join('');
}

// ── New Negotiation button ─────────────────────

function triggerNewNegotiation() {
  if (getCurrentRole() === 'buyer') {
    renderMarketplaceBoard('buyer').then(() => {
      showToast('info', 'Listings refreshed', 'Loaded the latest farmer listings from the marketplace.');
    }).catch((err) => {
      showToast('error', 'Could not refresh listings', err.message);
    });
    return;
  }

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
    await renderMarketplaceBoard(getCurrentRole(), result);
    await renderHistoryPanel();
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
  const role = getCurrentRole();
  applyRoleBadge();
  configureDashboard(role);
  await renderAgents();
  await renderMarketplaceBoard(role);
  await renderHistoryPanel();

  // Auto-run from stored ID, or run a default negotiation
  const storedId = localStorage.getItem('latestNegotiationId');
  if (storedId) {
    // Try to fetch existing result
    try {
      const result = await getNegotiationStatus(storedId);
      updateStats(result);
      updateOfferDisplay(result);
      renderPriceChart(result.price_series || []);
      await renderMarketplaceBoard(role, result);
      await renderHistoryPanel();
      appendLog(`💼 Loaded existing negotiation: ${storedId}`, 'system');
      setStage(4);
      return;
    } catch {
      // fall through to default
    }
  }

  if (role === 'buyer') {
    return;
  }

  // Default demo negotiation
  const payload = {
    farmer_name: 'Ramesh Kumar', crop: 'Tomato', quantity: 1000,
    min_price: 18, shelf_life: 4, location: 'Nashik', quality: 'A', language: 'Marathi',
  };
  await runNegotiationAndUpdate(payload);
}

initializeDashboard();