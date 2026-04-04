/* =================================================================
   DASHBOARD — AgriNegotiator
   Initialises stats, chart, agent cards, and runs the first
   negotiation. Handles the "New Negotiation" button.
================================================================= */

let _chartInstance = null;
let _offerHistory  = []; // { label, price, type }
let _buyerProduceListings = [];

function getCurrentSession() {
  try {
    return JSON.parse(localStorage.getItem('agri_session') || '{}');
  } catch {
    return {};
  }
}

function getCurrentRole() {
  const sessionRole = (getCurrentSession().role || '').toLowerCase();
  if (sessionRole) return sessionRole;
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

function applyRoleGuards(role) {
  const session = getCurrentSession();
  if (!session || !session.email) {
    window.location.href = 'login.html';
    return;
  }

  const activeClass = document.querySelector('a[href="dashboard.html"].active');
  if (activeClass && role !== 'farmer') {
    activeClass.setAttribute('href', `dashboard.html?role=${encodeURIComponent(role)}`);
  }
}

function configureDashboard(role) {
  const subtitle = document.getElementById('dashSubtitle');
  const btn = document.getElementById('newNegBtn');
  const marketplaceTitle = document.getElementById('marketplaceTitle');
  const navListProduce = document.querySelector('a[href="farmer_form.html"]') ||
    document.querySelector('a[href^="dashboard.html?role="]');

  if (role === 'buyer') {
    if (subtitle) subtitle.textContent = 'Browse demo farmer listings, start live negotiations, and monitor decisions in real time';
    if (btn) btn.textContent = '+ New Buyer Offer';
    if (marketplaceTitle) marketplaceTitle.textContent = 'Demo Farmer Listings';
    if (navListProduce) {
      navListProduce.textContent = 'Buyer Offers';
      navListProduce.setAttribute('href', 'dashboard.html?role=buyer');
    }
    return;
  }

  if (role === 'warehouse') {
    if (subtitle) subtitle.textContent = 'Monitor storage escalation requests and warehouse utilization in real time';
    if (btn) btn.style.display = '';
    if (btn) btn.textContent = '+ New Warehouse Offer';
    if (marketplaceTitle) marketplaceTitle.textContent = 'Warehouse Utilization';
    if (navListProduce) {
      navListProduce.textContent = 'Warehouse Board';
      navListProduce.setAttribute('href', 'dashboard.html?role=warehouse');
    }
    return;
  }

  if (role === 'transporter') {
    if (subtitle) subtitle.textContent = 'Track transport-ready deals and logistics assignments';
    if (btn) btn.style.display = '';
    if (btn) btn.textContent = '+ New Transport Offer';
    if (marketplaceTitle) marketplaceTitle.textContent = 'Transport Readiness';
    if (navListProduce) {
      navListProduce.textContent = 'Transport Board';
      navListProduce.setAttribute('href', 'dashboard.html?role=transporter');
    }
    return;
  }

  if (role === 'processor') {
    if (subtitle) subtitle.textContent = 'View processing escalations and value-add opportunities';
    if (btn) btn.style.display = '';
    if (btn) btn.textContent = '+ New Processor Offer';
    if (marketplaceTitle) marketplaceTitle.textContent = 'Processing Opportunities';
    if (navListProduce) {
      navListProduce.textContent = 'Processor Board';
      navListProduce.setAttribute('href', 'dashboard.html?role=processor');
    }
    return;
  }

  if (role === 'compost') {
    if (subtitle) subtitle.textContent = 'Track compost/fallback flows for near-expiry produce';
    if (btn) btn.style.display = '';
    if (btn) btn.textContent = '+ New Compost Offer';
    if (marketplaceTitle) marketplaceTitle.textContent = 'Compost Flow Board';
    if (navListProduce) {
      navListProduce.textContent = 'Compost Board';
      navListProduce.setAttribute('href', 'dashboard.html?role=compost');
    }
    return;
  }

  if (subtitle) subtitle.textContent = 'Compare competing buyer offers and monitor the selected negotiation in real time';
  if (btn) btn.textContent = '+ New Negotiation';
  if (navListProduce) {
    navListProduce.textContent = 'List Produce';
    navListProduce.setAttribute('href', 'farmer_form.html');
  }
}

function renderNegotiationLogSnapshot(result) {
  if (!result) return;
  clearLog();
  (result.logs || []).forEach((line) => appendLog(line));
  if (result.summary) appendLog(`📌 Summary: ${result.summary}`, 'system');
}

function syncAgentsFromResult(result) {
  const neutral = ['farmer', 'buyer', 'warehouse', 'transporter', 'processor', 'compost'];
  neutral.forEach((type) => updateAgentCard(type, { status: 'idle' }));

  if (!result) return;

  const status = result.status || '';
  const latestOffer = (result.offers || []).slice(-1)[0];
  if (latestOffer) {
    const agentName = String(latestOffer.agent || '').toLowerCase();
    const mapped = agentName.includes('farmer') ? 'farmer' : 'buyer';
    updateAgentCard(mapped, { status: status === 'RUNNING' ? 'negotiating' : 'deal', offer: latestOffer.price });
  }

  const buyerPrice = (result.offers || []).filter((o) => String(o.agent || '').toLowerCase().includes('buyer')).slice(-1)[0]?.price;
  const farmerPrice = (result.offers || []).filter((o) => String(o.agent || '').toLowerCase().includes('farmer')).slice(-1)[0]?.price;

  if (farmerPrice != null) updateAgentCard('farmer', { offer: farmerPrice, status: status === 'RUNNING' ? 'negotiating' : 'deal' });
  if (buyerPrice != null) updateAgentCard('buyer', { offer: buyerPrice, status: status === 'RUNNING' ? 'negotiating' : 'deal' });

  if (status.includes('STORAGE')) updateAgentCard('warehouse', { status: 'negotiating' });
  if (status.includes('PROCESSING')) updateAgentCard('processor', { status: 'negotiating' });
  if (status.includes('COMPOST')) updateAgentCard('compost', { status: 'negotiating' });
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

function getNegotiationButtonLabel(role) {
  if (role === 'buyer') return '+ New Buyer Offer';
  if (role === 'warehouse') return '+ New Warehouse Offer';
  if (role === 'transporter') return '+ New Transport Offer';
  if (role === 'processor') return '+ New Processor Offer';
  if (role === 'compost') return '+ New Compost Offer';
  return '+ New Negotiation';
}

async function renderBuyerListingsBoard() {
  const session = getCurrentSession();
  const [offerData, produceData] = await Promise.all([
    getBuyerOffers(session.user_id),
    getProduceListings(),
  ]);
  const offers = (offerData.offers || []).slice().reverse();
  const produce = (produceData.produce || []).slice().reverse();
  _buyerProduceListings = produce;

  if (!produce.length) {
    setMarketplaceContent(
      'Demo Farmer Listings',
      '0 listings',
      '<div class="market-empty"><div class="empty-icon">🌾</div><p>No farmer listings available right now.</p></div>'
    );
    return;
  }

  const latestOffer = offers[0] || null;
  const cards = produce.slice(0, 18).map((item) => {
    const minPrice = Number(item.min_price || 0);
    const suggestedPrice = latestOffer && latestOffer.crop === item.crop
      ? Number(latestOffer.offered_price || 0)
      : Number((minPrice + 1.5).toFixed(2));

    return `
    <article class="market-card">
      <div class="market-meta">${escapeHtml(item.location || 'Unknown')}</div>
      <h4>🌾 ${escapeHtml(item.crop || 'Produce')} • ${escapeHtml(item.farmer_name || 'Demo Farmer')}</h4>
      <div class="market-price">₹${minPrice.toFixed(2)}/kg min</div>
      <div class="market-price-note">${Number(item.quantity || 0).toFixed(0)}kg • Shelf life ${Number(item.shelf_life || 0)} days • Quality ${escapeHtml(item.quality || 'A')}</div>
      <div class="market-badges">
        <span class="market-pill good">${escapeHtml(item.status || 'LISTED')}</span>
        <span class="market-pill">Suggested opening ₹${suggestedPrice.toFixed(2)}</span>
      </div>
      <div class="market-strategy">Negotiate directly with this farmer using your buyer profile.</div>
      <div style="margin-top:.65rem">
        <button class="btn btn-sm btn-primary" onclick="startBuyerNegotiationFromListing('${escapeHtml(String(item.id || ''))}')">Start Negotiation</button>
      </div>
    </article>`;
  }).join('');

  const countLabel = `${produce.length} listings${offers.length ? ` • ${offers.length} my offers` : ''}`;
  setMarketplaceContent('Demo Farmer Listings', countLabel, cards);
}

async function startBuyerNegotiationFromListing(produceId) {
  const session = getCurrentSession();
  const selected = (_buyerProduceListings || []).find((p) => String(p.id) === String(produceId));

  if (!selected) {
    showToast('warning', 'Listing not found', 'Please refresh board and try again.');
    return;
  }

  let myOffer = null;
  try {
    const offers = await getBuyerOffers(session.user_id);
    myOffer = (offers.offers || []).find((entry) => entry.crop === selected.crop) || (offers.offers || [])[0] || null;
  } catch {}

  const quantity = Number(selected.quantity || 0) || 100;
  const minPrice = Number(selected.min_price || 0) || 18;
  const targetPrice = myOffer ? Number(myOffer.offered_price || minPrice + 1) : (minPrice + 1);

  const payload = {
    user_id: session.user_id || null,
    farmer_name: selected.farmer_name || 'Demo Farmer',
    crop: selected.crop || 'Tomato',
    quantity,
    min_price: minPrice,
    shelf_life: Number(selected.shelf_life || 3),
    location: selected.location || 'Market',
    quality: selected.quality || 'A',
    language: selected.language || 'English',
    buyer_mode: true,
    buyer_name: session.name || 'Buyer',
    buyer_location: session.location || 'Market',
    buyer_max_quantity: quantity,
    buyer_target_price: targetPrice,
    buyer_budget: Number((targetPrice * quantity * 1.2).toFixed(2)),
    buyer_strategy: myOffer?.strategy || 'Buyer initiated direct negotiation',
  };

  clearLog();
  setStage(1);
  await runNegotiationAndUpdate(payload);

  const safeFarmer = selected.farmer_name || 'farmer';
  showToast('success', 'Negotiation launched', `Started with ${safeFarmer} for ${selected.crop}.`);
}

window.startBuyerNegotiationFromListing = startBuyerNegotiationFromListing;

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

async function renderRoleOpportunityBoard(role) {
  const session = getCurrentSession();
  const offerData = await getRoleOffers(role, session.user_id);
  const offers = offerData.offers || [];

  if (offers.length) {
    const iconByRole = { transporter: '🚛', processor: '⚙️', compost: '♻️', warehouse: '🏗️' };
    const cards = offers.slice(0, 20).map((item) => `
      <article class="market-card">
        <div class="market-meta">${escapeHtml(item.id || '')}</div>
        <h4>${iconByRole[role] || '📦'} ${escapeHtml(item.crop || 'Produce')}</h4>
        <div class="market-price">${Number(item.quantity || 0).toFixed(0)}kg</div>
        <div class="market-price-note">${escapeHtml(item.location || 'Unknown')} • ${escapeHtml(item.actor_name || role)}</div>
        <div class="market-badges">
          <span class="market-pill good">${escapeHtml(item.status || 'OPEN')}</span>
          ${item.offered_price ? `<span class="market-pill">₹${Number(item.offered_price).toFixed(2)}/kg</span>` : ''}
        </div>
        <div class="market-strategy">${escapeHtml(item.notes || 'Role offer')}</div>
      </article>`).join('');

    setMarketplaceContent(`${role.charAt(0).toUpperCase() + role.slice(1)} Offers`, `${offers.length} offers`, cards);
    return;
  }

  const data = await getNegotiations();
  const negs = (data.negotiations || []).slice().reverse();

  const byRole = {
    transporter: negs.filter((n) => !!n.transport_plan || String(n.next_action || '').toLowerCase().includes('transport')),
    processor: negs.filter((n) => String(n.status || '').includes('PROCESSING')),
    compost: negs.filter((n) => String(n.status || '').includes('COMPOST')),
  };

  const records = byRole[role] || [];
  const titleByRole = {
    transporter: 'Transport Opportunities',
    processor: 'Processing Opportunities',
    compost: 'Compost Opportunities',
  };

  if (!records.length) {
    setMarketplaceContent(
      titleByRole[role] || 'Role Opportunities',
      '0 records',
      '<div class="market-empty"><div class="empty-icon">📭</div><p>No role-specific opportunities available right now.</p></div>'
    );
    return;
  }

  const iconByRole = { transporter: '🚛', processor: '⚙️', compost: '♻️' };
  const cards = records.slice(0, 20).map((item) => `
    <article class="market-card">
      <div class="market-meta">${escapeHtml(item.negotiation_id || '')}</div>
      <h4>${iconByRole[role] || '📦'} ${escapeHtml(item.crop || 'Produce')}</h4>
      <div class="market-price">${Number(item.quantity || 0).toFixed(0)}kg</div>
      <div class="market-price-note">Status: ${escapeHtml(item.status || 'UNKNOWN')}</div>
      <div class="market-badges">
        <span class="market-pill">Farmer: ${escapeHtml(item.farmer || '—')}</span>
        ${item.final_price ? `<span class="market-pill good">₹${Number(item.final_price).toFixed(2)}/kg</span>` : '<span class="market-pill warn">No final price</span>'}
      </div>
    </article>`).join('');

  setMarketplaceContent(titleByRole[role] || 'Role Opportunities', `${records.length} records`, cards);
}

async function renderMarketplaceBoard(role, result) {
  if (role === 'buyer') {
    await renderBuyerListingsBoard();
    return;
  }

  if (role === 'transporter' || role === 'processor' || role === 'compost') {
    await renderRoleOpportunityBoard(role);
    return;
  }

  if (role === 'warehouse') {
    const wh = await fetch(`${API_BASE}/api/warehouse/`).then((res) => res.json()).catch(() => ({ warehouses: [] }));
    const cards = (wh.warehouses || []).map((item) => `
      <article class="market-card">
        <div class="market-meta">${escapeHtml(item.location || 'Unknown')}</div>
        <h4>${escapeHtml(item.name || 'Warehouse')}</h4>
        <div class="market-price">${Number(item.available_capacity_kg || 0).toFixed(0)}kg free</div>
        <div class="market-price-note">Used: ${Number(item.used_capacity_kg || 0).toFixed(0)}kg / ${Number(item.capacity_kg || 0).toFixed(0)}kg</div>
      </article>`).join('');
    setMarketplaceContent('Warehouse Utilization', `${(wh.warehouses || []).length} warehouses`, cards || '<div class="market-empty"><p>No warehouse data.</p></div>');
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

  const role = getCurrentRole();
  const session = getCurrentSession();
  const userName = String(session.name || '').trim().toLowerCase();

  if (role === 'farmer') {
    const byUserId = session.user_id
      ? negs.filter((n) => String(n.user_id || '').trim() === String(session.user_id || '').trim())
      : [];
    const byName = userName
      ? negs.filter((n) => String(n.farmer || '').trim().toLowerCase() === userName)
      : [];
    const merged = [...byUserId, ...byName].filter((value, index, self) =>
      index === self.findIndex((entry) => entry.negotiation_id === value.negotiation_id)
    );

    if (merged.length) {
      negs = merged;
    }
  } else if (role === 'buyer') {
    negs = negs.filter((n) => {
      if (session.user_id && String(n.user_id || '').trim() === String(session.user_id || '').trim()) {
        return true;
      }
      const buyer = n.selected_buyer;
      const buyerName = typeof buyer === 'string' ? buyer : (buyer?.buyer_name || '');
      return String(buyerName).trim().toLowerCase() === userName;
    });
  } else if (role === 'warehouse') {
    negs = negs.filter((n) => String(n.status || '').includes('STORAGE'));
  } else if (role === 'processor') {
    negs = negs.filter((n) => String(n.status || '').includes('PROCESSING'));
  } else if (role === 'compost') {
    negs = negs.filter((n) => String(n.status || '').includes('COMPOST'));
  } else if (role === 'transporter') {
    negs = negs.filter((n) => !!n.transport_plan || String(n.next_action || '').toLowerCase().includes('transport'));
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
  const role = getCurrentRole();
  if (role === 'buyer') {
    window.location.href = 'buyer_offer_form.html';
    return;
  }

  if (['warehouse', 'transporter', 'processor', 'compost'].includes(role)) {
    window.location.href = 'role_offer_form.html';
    return;
  }

  const payload = {
    user_id: getCurrentSession().user_id || null,
    farmer_name: getCurrentSession().name || 'Demo Farmer',
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
  const role = getCurrentRole();
  if (btn) { btn.disabled = true; btn.textContent = '⏳ Running…'; }

  setStage(1);
  try {
    const result = await startNegotiationFlow(payload);
    setStage(result.status && result.status.includes('DEAL') ? 4 : 3);
    updateStats(result);
    updateOfferDisplay(result);
    syncAgentsFromResult(result);
    renderNegotiationLogSnapshot(result);
    renderPriceChart(result.price_series || []);
    await renderMarketplaceBoard(getCurrentRole(), result);
    await renderHistoryPanel();
    showToast(
      result.status?.includes('DEAL') ? 'success' : 'info',
      `Negotiation complete: ${result.status}`,
      result.summary
    );
  } catch (err) {
    showToast('error', 'Negotiation error', err.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = getNegotiationButtonLabel(role); }
  }
}

async function initializeDashboard() {
  const role = getCurrentRole();
  applyRoleGuards(role);
  applyRoleBadge();
  configureDashboard(role);
  await renderAgents();
  await renderMarketplaceBoard(role);
  await renderHistoryPanel();

  function _isNegotiationRelevant(negotiation, role, session) {
    if (!negotiation) return false;
    if (role === 'farmer') return !session.user_id || negotiation.user_id === session.user_id;
    if (role === 'buyer') {
      if (session.user_id && String(negotiation.user_id || '') === String(session.user_id)) {
        return true;
      }
      const buyer = negotiation.selected_buyer;
      const buyerName = typeof buyer === 'string' ? buyer : (buyer?.buyer_name || '');
      return String(buyerName || '').trim().toLowerCase() === String(session.name || '').trim().toLowerCase();
    }
    if (role === 'warehouse') return String(negotiation.status || '').includes('STORAGE');
    if (role === 'processor') return String(negotiation.status || '').includes('PROCESSING');
    if (role === 'compost') return String(negotiation.status || '').includes('COMPOST');
    if (role === 'transporter') return !!negotiation.transport_plan || String(negotiation.next_action || '').toLowerCase().includes('transport');
    return true;
  }

  async function watchRunningNegotiationIfAny() {
    try {
      const data = await getNegotiations();
      const session = getCurrentSession();
      const running = (data.negotiations || []).find((n) => n.status === 'RUNNING' && _isNegotiationRelevant(n, role, session));
      if (!running) return false;

      clearLog();
      setStage(2);
      appendLog(`🛰️ Connected to live negotiation: ${running.negotiation_id}`, 'system');

      const final = await resumeNegotiationFlow(running.negotiation_id);
      setStage(final.status && final.status.includes('DEAL') ? 4 : 3);
      updateStats(final);
      updateOfferDisplay(final);
      syncAgentsFromResult(final);
      renderNegotiationLogSnapshot(final);
      renderPriceChart(final.price_series || []);
      await renderMarketplaceBoard(role, final);
      await renderHistoryPanel();
      return true;
    } catch {
      return false;
    }
  }

  async function hydrateFromLatestRelevantNegotiation() {
    try {
      const data = await getNegotiations();
      const session = getCurrentSession();
      const latest = (data.negotiations || []).find((n) => _isNegotiationRelevant(n, role, session));
      if (!latest) return;

      updateStats(latest);
      updateOfferDisplay(latest);
      syncAgentsFromResult(latest);
      renderNegotiationLogSnapshot(latest);
      renderPriceChart(latest.price_series || []);
    } catch {}
  }

  // Auto-run from stored ID, or run a default negotiation
  const storedId = localStorage.getItem('latestNegotiationId');
  if (storedId) {
    // Try to fetch existing result
    try {
      const result = await getNegotiationStatus(storedId);
      clearLog();
      updateStats(result);
      updateOfferDisplay(result);
      syncAgentsFromResult(result);
      renderNegotiationLogSnapshot(result);
      renderPriceChart(result.price_series || []);
      await renderMarketplaceBoard(role, result);
      await renderHistoryPanel();
      appendLog(`💼 Loaded existing negotiation: ${storedId}`, 'system');

      if (result.status === 'RUNNING') {
        setStage(2);
        const final = await resumeNegotiationFlow(storedId);
        setStage(final.status && final.status.includes('DEAL') ? 4 : 3);
        updateStats(final);
        updateOfferDisplay(final);
        syncAgentsFromResult(final);
        renderNegotiationLogSnapshot(final);
        renderPriceChart(final.price_series || []);
        await renderMarketplaceBoard(role, final);
        await renderHistoryPanel();
      } else {
        setStage(result.status && result.status.includes('DEAL') ? 4 : 3);
      }
      return;
    } catch {
      // fall through to default
    }
  }

  if (await watchRunningNegotiationIfAny()) {
    return;
  }

  await hydrateFromLatestRelevantNegotiation();

  if (role === 'buyer') {
    return;
  }

  if (role !== 'farmer') {
    return;
  }

  // Default demo negotiation
  const payload = {
    user_id: getCurrentSession().user_id || null,
    farmer_name: getCurrentSession().name || 'Ramesh Kumar', crop: 'Tomato', quantity: 1000,
    min_price: 18, shelf_life: 4, location: 'Nashik', quality: 'A', language: 'Marathi',
  };
  await runNegotiationAndUpdate(payload);
}

initializeDashboard();