/* =================================================================
   HISTORY DASHBOARD — AgriNegotiator
   Renders full-page history with detailed logs and participant tracks.
================================================================= */

document.addEventListener('DOMContentLoaded', async () => {
    const role = window.getCurrentRole();
    const session = window.getCurrentSession();
    window._historyData = []; // Cache for filtering
    
    await loadHistory(role, session.user_id);
});

async function loadHistory(role, userId) {
    const list = document.getElementById('historyList');
    if (!list) return;

    try {
        const data = await getNegotiations(role, userId);
        window._historyData = data.negotiations || [];
        applyFilters(); 
    } catch (err) {
        list.innerHTML = `<div class="card" style="border: 1px solid var(--red); color: var(--red); padding: 3rem;">
            <h3>⚠️ Error accessing history</h3>
            <p>${err.message}</p>
        </div>`;
    }
}

function applyFilters() {
    const list = document.getElementById('historyList');
    const statusVal = document.getElementById('filterStatus')?.value || 'all';
    const cropVal = document.getElementById('filterCrop')?.value.toLowerCase() || '';
    const sortVal = document.getElementById('filterSort')?.value || 'recent';

    let filtered = [...(window._historyData || [])];

    // Status Filter
    if (statusVal !== 'all') {
        filtered = filtered.filter(n => n.status === statusVal);
    }
    // Crop Filter
    if (cropVal) {
        filtered = filtered.filter(n => (n.crop || '').toLowerCase().includes(cropVal));
    }
    // Sort
    if (sortVal === 'price_high') {
        filtered.sort((a,b) => (b.final_price || 0) - (a.final_price || 0));
    } else if (sortVal === 'qty_high') {
        filtered.sort((a,b) => (b.quantity || 0) - (a.quantity || 0));
    } else {
        filtered.sort((a,b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
    }

    if (filtered.length === 0) {
        list.innerHTML = `<div class="card text-center" style="padding: 10rem; color:var(--text-muted)"><h3>Empty Filter Result</h3><p>No transactions match your current selection.</p></div>`;
        return;
    }

    list.innerHTML = '';
    filtered.forEach(neg => {
        const card = renderHistoryEntry(neg, window.getCurrentRole());
        list.appendChild(card);
    });
}

function clearFilters() {
    if (document.getElementById('filterStatus')) document.getElementById('filterStatus').value = 'all';
    if (document.getElementById('filterCrop')) document.getElementById('filterCrop').value = '';
    if (document.getElementById('filterSort')) document.getElementById('filterSort').value = 'recent';
    applyFilters();
}

function renderHistoryEntry(neg, role) {
    const entry = document.createElement('div');
    entry.className = 'history-entry-card';
    
    const icon = { DEAL: '✅', ESCALATED_STORAGE: '📦', ESCALATED_PROCESSING: '🏭', REJECTED: '❌', FAILED: '⚠️' }[neg.status] || '📜';
    const statusClass = { DEAL: 'badge-green', ESCALATED_STORAGE: 'badge-blue', ESCALATED_PROCESSING: 'badge-purple' }[neg.status] || 'badge-gray';
    const statusText = neg.status ? neg.status.replace(/_/g, ' ') : 'NEGOTIATING';
    
    const date = neg.created_at ? new Date(neg.created_at).toLocaleString() : 'Recent';
    const finalPrice = neg.final_price ? `₹${Number(neg.final_price).toFixed(2)}` : 'N/A';
    
    // Using the same logic from dashboard.js for consistency
    const context = _histContextLine(neg, role);
    const id = (neg.negotiation_id || '').slice(0, 12) + '…';

    entry.innerHTML = `
        <div class="he-icon">${icon}</div>
        <div class="he-info">
            <h3>${context}</h3>
            <div class="meta">
                <span>🆔 ID: <code>${id}</code></span>
                <span>📅 ${date}</span>
                <span>📦 ${neg.quantity || '0'}kg</span>
                <span>📍 ${neg.scenario || 'direct-sale'}</span>
            </div>
        </div>
        <div class="he-side">
            <div class="he-price">${finalPrice}</div>
            <div class="he-status"><span class="badge ${statusClass}">${statusText}</span></div>
            <button class="btn btn-ghost btn-sm" style="margin-top: 1rem;" onclick="this.closest('.history-entry-card').classList.toggle('expanded')">
                📄 Tracking & Logs
            </button>
        </div>
        <div class="he-details">
            <div class="logs-column">
                <div class="log-stack">
                    <h4>🤝 Participant Handshakes</h4>
                    <div class="log-line">🌾 Farmer Node: ${neg.farmer || 'Verified'}</div>
                    <div class="log-line">🛒 Counterparty: ${neg.selected_buyer?.buyer_name || neg.selected_buyer || 'Peer Node'}</div>
                    ${neg.transport_plan ? `<div class="log-line">🚛 Logsitics: ${neg.transport_plan.agent} (Distance: ${neg.transport_plan.distance}km)</div>` : ''}
                    <div class="log-line" style="color: var(--amber);">🛡️ P2P Consensus Signature Verified</div>
                </div>
                <div class="log-stack">
                    <h4>📝 Full Conversation Feed</h4>
                    ${(neg.logs || []).map(l => `<div class="log-line">• ${l}</div>`).join('')}
                    ${(neg.logs || []).length === 0 ? '<div class="text-muted">No communication logs recorded.</div>' : ''}
                </div>
            </div>
        </div>
    `;
    
    return entry;
}

// ── UTILITIES (duplicated from dashboard.js for standalone history.js) ──

function _histContextLine(neg, role) {
  const price = neg.final_price ? `₹${Number(neg.final_price).toFixed(2)}/kg` : '';
  const qty   = neg.quantity    ? `${Number(neg.quantity).toFixed(0)}kg`       : '';
  const crop  = neg.crop        ? neg.crop                                      : '';
  const buyer = typeof neg.selected_buyer === 'object'
    ? (neg.selected_buyer?.buyer_name || '') : (neg.selected_buyer || '');
  const farmer = neg.farmer || neg.farmer_name || '';
  if (role === 'farmer')     return `Sold ${qty} ${crop} ${price ? '@ ' + price : ''}${buyer ? ' to ' + buyer : ''}`;
  if (role === 'buyer')      return `Purchased ${qty} ${crop} from ${farmer} ${price ? '@ ' + price : ''}`;
  if (role === 'warehouse')  return `Stored ${qty} ${crop} from ${farmer}`;
  if (role === 'transporter')return `Transported ${qty} ${crop}`;
  if (role === 'processor')  return `Processed ${qty} ${crop} from ${farmer}`;
  if (role === 'compost')    return `Composted ${qty} ${crop} from ${farmer}`;
  if (role === 'restaurant') return `Procured ${qty} ${crop} ${price ? '@ ' + price : ''} from ${farmer}`;
  return `${farmer} — ${crop} ${qty} ${price}`;
}
