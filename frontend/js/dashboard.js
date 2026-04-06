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

  // Support for Deal Approval UI
  const approveContainer = document.getElementById('approveActionContainer');
  if (approveContainer) {
    if (result.status === 'DEAL_PENDING' || result.status === 'DEAL' || result.status === 'PENDING_APPROVAL') {
      const role = getCurrentRole();
      approveContainer.innerHTML = `
        <div class="approval-card" style="background: rgba(34, 197, 94, 0.1); border: 1px solid #22c55e; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; text-align: center; border-left: 5px solid var(--green-500);">
          <p style="margin-bottom: 0.75rem; font-size:0.9rem;">🤝 <strong>Handshake Requested!</strong> Confirm to finalize your part of the deal.</p>
          <button class="btn btn-primary" style="width:100%" onclick="confirmFinalDeal('${result.negotiation_id}', '${role}')">Approve & Sign Now</button>
        </div>
      `;
    } else {
      approveContainer.innerHTML = '';
    }
  }
}

function incrementNotifCount() {
  const el = document.getElementById('notifCount');
  if (!el) return;
  const curr = parseInt(el.textContent || '0');
  el.textContent = curr + 1;
  el.classList.add('bump');
  setTimeout(() => el.classList.remove('bump'), 300);
}

function applyTrustScore() {
    const session = getCurrentSession();
    const scoreVal = document.getElementById('trustScoreVal');
    if (scoreVal && session.trust_score != null) {
        const score = Number(session.trust_score);
        scoreVal.textContent = score.toFixed(1);
        
        // Level Up Logic
        if (score >= 5.0 && !localStorage.getItem('agri_leveled_up')) {
            setTimeout(() => {
                showToast('success', '🏆 Trust Level Up!', 'You reached a 5.0 Trust Score! You are now a Premium Member.');
                localStorage.setItem('agri_leveled_up', 'true');
            }, 1500);
        }
    }
}

function applyNodeInfo() {
    const session = getCurrentSession();
    const nodeIdEl = document.getElementById('nodeIdVal');
    const peerCountEl = document.getElementById('peerCountVal');
    if (nodeIdEl) nodeIdEl.textContent = session.user_id || 'node_f_user';
    // We assume 3 peers for this MVP discovery simulation
    if (peerCountEl) peerCountEl.textContent = '3 Connected Peers'; 
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
  // Auth guard is enforced by auth-guard.js (loaded before this file).
  // Nothing to do here — if we reach this point the user is authenticated.
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
  const buyers = (data.buyers || []).filter((buyer) => buyer.kind !== 'offer');
  if (!buyers.length) {
    setMarketplaceContent(
      'Retail Buyer Benchmarks',
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

  setMarketplaceContent('Retail Buyer Benchmarks', `${buyers.length} buyers`, cards);
}

async function renderFarmerBuyerBoard(result) {
  const [buyersData, buyerOffersData] = await Promise.all([
    getBuyers(),
    getBuyerOffers(),
  ]);

  const retailBuyers = (buyersData.buyers || []).filter((buyer) => buyer.kind !== 'offer');
  const buyerOffers = (buyerOffersData.offers || []).slice().reverse();
  const retailByName = new Map(retailBuyers.map((buyer) => [String(buyer.name || '').toLowerCase(), buyer]));

  let boardOffers = [];
  if (result && Array.isArray(result.market_offers) && result.market_offers.length) {
    boardOffers = result.market_offers.map((offer) => {
      const retail = retailByName.get(String(offer.buyer_name || '').toLowerCase()) || null;
      return {
        buyer_name: offer.buyer_name,
        crop: result.crop,
        quantity: offer.offered_quantity,
        offered_price: offer.offered_price,
        location: offer.location,
        strategy: offer.strategy || 'Negotiation round offer',
        status: offer.status,
        retail_price: retail ? retail.target_price : null,
      };
    });
  } else {
    boardOffers = buyerOffers.map((offer) => {
      const retail = retailByName.get(String(offer.buyer_name || '').toLowerCase()) || null;
      return {
        buyer_name: offer.buyer_name,
        crop: offer.crop,
        quantity: offer.quantity,
        offered_price: offer.offered_price,
        location: offer.location,
        strategy: offer.strategy || 'Direct procurement offer',
        status: offer.status || 'OPEN',
        retail_price: retail ? retail.target_price : null,
      };
    });
  }

  if (!boardOffers.length && !retailBuyers.length) {
    setMarketplaceContent(
      'Buyer Offers & Retail Prices',
      '0 offers',
      '<div class="market-empty"><div class="empty-icon">🛒</div><p>No buyer demand data available yet.</p></div>'
    );
    return;
  }

  const offerCards = boardOffers.slice(0, 16).map((item) => {
    const offered = Number(item.offered_price || 0);
    const retail = item.retail_price != null ? Number(item.retail_price) : null;
    const spread = retail != null ? (offered - retail) : null;
    return `
      <article class="market-card">
        <div class="market-meta">${escapeHtml(item.location || 'Market')}</div>
        <h4>🛒 ${escapeHtml(item.buyer_name || 'Buyer')} • ${escapeHtml(item.crop || 'Produce')}</h4>
        <div class="market-price">₹${offered.toFixed(2)}/kg offer</div>
        <div class="market-price-note">${Number(item.quantity || 0).toFixed(0)}kg • ${escapeHtml(item.status || 'OPEN')}</div>
        <div class="market-badges">
          ${retail != null ? `<span class="market-pill">Retail ₹${retail.toFixed(2)}/kg</span>` : '<span class="market-pill warn">Retail N/A</span>'}
          ${spread != null ? `<span class="market-pill ${spread >= 0 ? 'good' : 'warn'}">Spread ${spread >= 0 ? '+' : ''}₹${spread.toFixed(2)}</span>` : ''}
        </div>
        <div class="market-strategy">${escapeHtml(item.strategy || 'Marketplace participant')}</div>
      </article>`;
  }).join('');

  const benchmarkCards = retailBuyers.slice(0, 8).map((buyer) => `
    <article class="market-card">
      <div class="market-meta">${escapeHtml(buyer.location || 'Market')}</div>
      <h4>🏷️ ${escapeHtml(buyer.name || 'Retail Buyer')}</h4>
      <div class="market-price">₹${Number(buyer.target_price || 0).toFixed(2)}/kg retail</div>
      <div class="market-price-note">Budget ₹${Number(buyer.budget || 0).toFixed(0)} • Capacity ${Number(buyer.max_quantity || 0).toFixed(0)}kg</div>
      <div class="market-strategy">${escapeHtml(buyer.strategy || 'Retail benchmark buyer')}</div>
    </article>`).join('');

  const sections = [];
  if (offerCards) {
    sections.push(`<div class="market-section"><h4 class="market-section-title">Buyer Offers</h4><div class="market-section-grid">${offerCards}</div></div>`);
  }
  if (benchmarkCards) {
    sections.push(`<div class="market-section"><h4 class="market-section-title">Retail Price Benchmarks</h4><div class="market-section-grid">${benchmarkCards}</div></div>`);
  }

  setMarketplaceContent(
    'Buyer Offers & Retail Prices',
    `${boardOffers.length} offers • ${retailBuyers.length} benchmarks`,
    sections.join('')
  );
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
        <div>
          <div class="agent-name">${item.actor_name || role}</div>
          <div class="agent-role">${role} node</div>
          <div style="font-family:monospace; font-size:0.6rem; color:var(--text-muted);">${item.node_id || ''}</div>
        </div>
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

  if (role === 'farmer') {
    await renderFarmerBuyerBoard(result);
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

  await renderDefaultBuyerBoard();
}

// ── History panel ──────────────────────────────

const STATUS_HISTORY_STYLE = {
  DEAL:                 { cls: 'badge-green',  icon: '✅', text: 'Deal' },
  CONTRACT:             { cls: 'badge-green',  icon: '📜', text: 'Contract' },
  ESCALATED_STORAGE:    { cls: 'badge-amber',  icon: '🏗️', text: 'Stored' },
  ESCALATED_PROCESSING: { cls: 'badge-purple', icon: '⚙️', text: 'Processed' },
  ESCALATED_COMPOST:    { cls: 'badge-lime',   icon: '♻️', text: 'Compost' },
  PENDING_APPROVAL:     { cls: 'badge-amber',  icon: '⏳', text: 'Pending' },
  FAILED:               { cls: 'badge-red',    icon: '⚠️', text: 'Failed' },
  RUNNING:              { cls: 'badge-blue',   icon: '🔄', text: 'Live' },
};

function _histStatusStyle(status) {
  return STATUS_HISTORY_STYLE[status] || { cls: 'badge-gray', icon: '💬', text: status || 'Unknown' };
}

function _histRoleLabel(role) {
  const m = { farmer:'🌾 My Deals', buyer:'🛒 My Purchases', warehouse:'🏗️ Storage Jobs',
              transporter:'🚛 Transport Jobs', processor:'⚙️ Processing Jobs',
              compost:'♻️ Compost Routes', restaurant:'🍽️ Restaurant Deals', admin:'🔑 All Activity' };
  return m[role] || '📋 History';
}

function _histContextLine(neg, role) {
  const price = neg.final_price ? `₹${Number(neg.final_price).toFixed(2)}/kg` : '';
  const qty   = neg.quantity    ? `${Number(neg.quantity).toFixed(0)}kg`       : '';
  const crop  = neg.crop        ? neg.crop                                      : '';
  const buyer = typeof neg.selected_buyer === 'object'
    ? (neg.selected_buyer?.buyer_name || '') : (neg.selected_buyer || '');
  const farmer = neg.farmer || neg.farmer_name || '';
  if (role === 'farmer')     return `Sold ${qty} ${crop} ${price ? '@ ' + price : ''}${buyer ? ' to ' + escapeHtml(buyer) : ''}`;
  if (role === 'buyer')      return `Purchased ${qty} ${crop} from ${escapeHtml(farmer)} ${price ? '@ ' + price : ''}`;
  if (role === 'warehouse')  return `Stored ${qty} ${crop} from ${escapeHtml(farmer)}`;
  if (role === 'transporter')return `Transported ${qty} ${crop} — ${escapeHtml(neg.transport_plan?.agent||'Route')}`;
  if (role === 'processor')  return `Processed ${qty} ${crop} from ${escapeHtml(farmer)}`;
  if (role === 'compost')    return `Composted ${qty} ${crop} from ${escapeHtml(farmer)}`;
  if (role === 'restaurant') return `Procured ${qty} ${crop} ${price ? '@ ' + price : ''} from ${escapeHtml(farmer)}`;
  return `${escapeHtml(farmer)} — ${crop} ${qty} ${price}`;
}

async function renderHistoryPanel() {
  const board = document.getElementById('historyBoard');
  const count = document.getElementById('historyCount');
  if (!board) return;

  const role    = getCurrentRole();
  const session = getCurrentSession();
  const userId  = session.user_id || null;

  try {
    // Fetch role-filtered negotiations as the real history
    const data = await getNegotiations(role, userId);
    const negs = data.negotiations || [];

    if (count) count.textContent = `${negs.length} records`;

    // Update history panel heading to be role-specific
    const panelHdr = board.closest('.history-panel')?.querySelector('h2');
    if (panelHdr) {
      panelHdr.innerHTML = `<span class="panel-icon">📋</span> ${_histRoleLabel(role)}`;
    }

    if (negs.length === 0) {
      board.innerHTML = `
        <div class="market-empty">
          <div class="empty-icon">📜</div>
          <p>No ${role} activity yet.<br>
          ${role === 'farmer' ? 'Start a negotiation to see your deal history here.' :
            role === 'buyer'  ? 'Submit a buyer offer to appear in matched negotiations.' :
            'Your role-specific jobs will appear here once supply chain events occur.'}
          </p>
        </div>`;
      return;
    }

    board.innerHTML = '';
    negs.forEach((neg) => {
      const ss   = _histStatusStyle(neg.status);
      const ctx  = _histContextLine(neg, role);
      const logs = (neg.logs || []).slice(0, 5);
      const ts   = neg.created_at || neg.timestamp || '';
      const timeStr = ts ? new Date(ts).toLocaleString('en-IN', {
        day:'2-digit', month:'short', hour:'2-digit', minute:'2-digit' }) : '';

      const card = document.createElement('article');
      card.className = 'hist-card';
      const sigs = neg.signatures || {};
      const pendingApproval = neg.status === 'PENDING_APPROVAL';

      card.innerHTML = `
        <div class="hist-header">
          <div class="hist-id">
            <span class="hist-dot"></span>
            <code>${(neg.negotiation_id || '').slice(0,12)}…</code>
          </div>
          <span class="badge ${ss.cls}" style="font-size:.7rem">${ss.icon} ${ss.text}</span>
        </div>
        <div class="hist-body">
          <div class="hist-ctx">${escapeHtml(ctx)}</div>
          ${timeStr ? `<div class="hist-time">🕐 ${timeStr}</div>` : ''}
          ${neg.score != null ? `<div class="hist-score">Farmer Score: <b>${neg.score}</b>/100</div>` : ''}
          
          ${pendingApproval ? `
          <div class="sig-progress" style="margin-top:0.5rem; display:flex; gap:0.5rem;">
            <span class="sig-dot ${sigs.farmer ? 'done' : 'wait'}" title="Farmer Signature">🌾</span>
            <span class="sig-dot ${sigs.buyer ? 'done' : 'wait'}" title="Buyer Signature">🛒</span>
            <span class="sig-dot ${sigs.transporter ? 'done' : 'wait'}" title="Logistics Signature">🚛</span>
          </div>` : ''}
        </div>
        ${logs.length ? `
        <details class="hist-logs" style="margin-top:.5rem">
          <summary style="cursor:pointer;font-size:.7rem;color:var(--text-muted)">📝 View ${logs.length} log entries</summary>
          <div style="padding:.5rem 0;font-size:.7rem;color:var(--text-secondary);line-height:1.6">
            ${logs.map(l => `<div>• ${escapeHtml(String(l))}</div>`).join('')}
            ${(neg.logs||[]).length > 5 ? `<div style="color:var(--text-muted)">+ ${(neg.logs||[]).length - 5} more…</div>` : ''}
          </div>
        </details>` : ''}
        ${pendingApproval && !sigs[role] ? `
        <button class="btn btn-primary btn-sm" style="margin-top:.75rem;width:100%"
          onclick="confirmFinalDeal('${neg.negotiation_id}', '${role}')">
          ✅ Sign & Finalize Deal
        </button>` : ''}
        ${pendingApproval && sigs[role] ? `
        <div class="text-center p-2" style="font-size:0.7rem; color:var(--text-muted)">⏳ Waiting for others to sign...</div>
        ` : ''}`;
      board.appendChild(card);
    });

  } catch (err) {
    board.innerHTML = `<div class="market-empty"><p>⚠️ Could not load history: ${escapeHtml(err.message)}</p></div>`;
  }
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
  applyTrustScore();
  applyNodeInfo();
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
      const data = await getNegotiations(role, session.user_id, 'RUNNING');
      const running = (data.negotiations || []).find((n) => _isNegotiationRelevant(n, role, session));
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
      const data = await getNegotiations(role, session.user_id);
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

// ── Role-Specific Handshake (Phase F Confirm) ────────

async function confirmFinalDeal(negId, role) {
  try {
    const res = await window.approveNegotiation(negId, role);
    
    if (res.status === 'success') {
      window.showToast('success', '📜 Contract Finalized!', 'Full consensus reached. Block committed to ledger.');
    } else {
      window.showToast('info', '✍️ Signature Recorded', 'Stored. Waiting for other supply chain partners…');
    }
    
    // Refresh to show progress
    await renderHistoryPanel();
    
    if (window.appendLog) {
      window.appendLog(`🤝 ${role.toUpperCase()} signed contract: ${negId.slice(0,8)}`, 'deal');
    }

  } catch (err) {
    window.showToast('error', 'Signing Failed', err.message);
  }
}window.confirmFinalDeal = confirmFinalDeal;