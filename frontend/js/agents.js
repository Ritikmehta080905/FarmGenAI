/* =================================================================
   AGENTS — AgriNegotiator
   Renders and dynamically updates agent cards with type-based
   color coding, status indicators, and offer trend bars.
================================================================= */

/** Map agent type/role string to display metadata. */
const AGENT_META = {
  farmer:      { icon: '🌾', color: '#22c55e', label: 'Farmer Agent',      caps: ['Price Negotiation', 'Quality Grading'] },
  buyer:       { icon: '🛒', color: '#3b82f6', label: 'Buyer Agent',       caps: ['Budget Management', 'Bid Optimisation'] },
  warehouse:   { icon: '🏗️', color: '#f59e0b', label: 'Warehouse Agent',   caps: ['Storage Allocation', 'Cold Chain'] },
  transporter: { icon: '🚛', color: '#06b6d4', label: 'Transporter Agent', caps: ['Route Optimisation', 'Scheduling'] },
  processor:   { icon: '⚙️', color: '#a855f7', label: 'Processor Agent',   caps: ['Value Processing', 'Bulk Buying'] },
  compost:     { icon: '♻️', color: '#84cc16', label: 'Compost Agent',     caps: ['Waste Reduction', 'Feed Market'] },
};

/** Derive a type key from an agent's role string (case-insensitive prefix match). */
function resolveType(role) {
  const r = (role || '').toLowerCase();
  return Object.keys(AGENT_META).find((k) => r.includes(k)) || 'buyer';
}

/**
 * Build an agent card DOM element.
 * @param {object} agent  { role, capability, name?, offer?, status? }
 */
function buildAgentCard(agent) {
  const type = resolveType(agent.role);
  const meta = AGENT_META[type];
  const name = agent.name || meta.label;
  const offer = agent.offer ? `₹${Number(agent.offer).toFixed(2)}` : '—';
  const statusLabel = agent.status || 'idle';
  const isActive = statusLabel === 'negotiating';
  const caps = agent.capability
    ? [agent.capability]
    : meta.caps;

  const card = document.createElement('div');
  card.className = `agent-card${isActive ? ' active' : ''}`;
  card.dataset.type = type;
  card.dataset.agentId = agent.id || type;

  card.innerHTML = `
    <div class="card-hdr">
      <div class="agent-ident">
        <div class="agent-avatar">${meta.icon}</div>
        <div>
          <div class="agent-name">${name}</div>
          <div class="agent-role">${type} agent</div>
        </div>
      </div>
      <span class="status-chip ${statusLabel}">
        <span class="dot"></span>${statusLabel}
      </span>
    </div>
    <div class="agent-offer">
      <div class="offer-row">
        <span class="offer-lbl">Current Offer</span>
        <span class="offer-val">${offer}/kg</span>
      </div>
      <div class="offer-trend">
        <div class="trend-bar-bg">
          <div class="trend-bar-fg" style="width:${agent.trendPct || 0}%"></div>
        </div>
        <span class="trend-pct">${agent.trendPct || 0}% fair</span>
      </div>
    </div>
    <div class="cap-tags">${caps.map((c) => `<span class="cap-tag">${c}</span>`).join('')}</div>
  `;
  return card;
}

/**
 * Fetch agents from API and render cards.
 * Falls back to a hardcoded list if the backend is unavailable.
 */
async function renderAgents() {
  const container = document.getElementById('agentContainer');
  if (!container) return;

  try {
    const data = await getAgents();
    const agents = data.agents || [];
    container.innerHTML = '';

    if (agents.length === 0) {
      container.innerHTML = '<p class="text-muted text-sm">No agents registered.</p>';
      return;
    }

    agents.forEach((agent) => container.appendChild(buildAgentCard(agent)));

    const badge = document.getElementById('agentCount');
    if (badge) badge.textContent = `${agents.length} agents`;

  } catch {
    // Backend unreachable — show default agent list
    container.innerHTML = '';
    const defaults = [
      { role:'farmer', status:'idle' },
      { role:'buyer', status:'idle' },
      { role:'warehouse', status:'idle' },
      { role:'transporter', status:'idle' },
      { role:'processor', status:'idle' },
      { role:'compost', status:'idle' },
    ];
    defaults.forEach((a) => container.appendChild(buildAgentCard(a)));
    const badge = document.getElementById('agentCount');
    if (badge) badge.textContent = `${defaults.length} agents (offline)`;
  }
}

/**
 * Update a specific agent card's offer and status.
 * @param {string} type   Agent type key (e.g. 'farmer')
 * @param {object} update { offer, status, trendPct }
 */
function updateAgentCard(type, update) {
  const card = document.querySelector(`.agent-card[data-type="${type}"]`);
  if (!card) return;

  if (update.status) {
    const chip = card.querySelector('.status-chip');
    if (chip) {
      chip.className = `status-chip ${update.status}`;
      chip.innerHTML = `<span class="dot"></span>${update.status}`;
    }
    card.classList.toggle('active', update.status === 'negotiating');
  }

  if (update.offer != null) {
    const val = card.querySelector('.offer-val');
    if (val) {
      const prev = parseFloat(val.textContent.replace(/[^\.\d]/g, '')) || 0;
      const next = Number(update.offer);
      val.textContent = `₹${next.toFixed(2)}/kg`;

      // Floating animation
      if (prev && prev !== next) {
        const float = document.createElement('div');
        float.className = `price-float${next < prev ? ' down' : ''}`;
        float.textContent = next > prev ? `+₹${(next - prev).toFixed(2)}` : `-₹${(prev - next).toFixed(2)}`;
        card.appendChild(float);
        setTimeout(() => float.remove(), 1300);
      }
    }

    if (update.trendPct != null) {
      const bar = card.querySelector('.trend-bar-fg');
      const pct = card.querySelector('.trend-pct');
      if (bar) bar.style.width = `${update.trendPct}%`;
      if (pct) pct.textContent = `${update.trendPct}% fair`;
    }
  }
}