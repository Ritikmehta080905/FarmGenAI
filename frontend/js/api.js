/* =================================================================
   API CLIENT — AgriNegotiator
   All HTTP + WebSocket calls to the backend.
================================================================= */

const API_BASE = 'http://localhost:8000';

// ── HTTP helpers ───────────────────────────

/**
 * POST a negotiation payload. Returns { negotiation_id, status,
 * summary, final_price, offers, logs, events, price_series, deal }.
 */
async function startNegotiation(payload) {
  const res = await fetch(`${API_BASE}/start-negotiation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(`Negotiation failed (${res.status}): ${err}`);
  }
  return res.json();
}

/**
 * GET current status for a negotiation_id.
 */
async function getNegotiationStatus(negotiationId) {
  const res = await fetch(`${API_BASE}/negotiation-status/${encodeURIComponent(negotiationId)}`);
  if (!res.ok) throw new Error(`Status fetch failed: ${res.status}`);
  return res.json();
}

/**
 * GET all registered agents.
 */
async function getAgents() {
  const res = await fetch(`${API_BASE}/agents`);
  if (!res.ok) throw new Error(`Agents fetch failed: ${res.status}`);
  return res.json();
}

/**
 * GET all buyers available in the marketplace.
 */
async function getBuyers() {
  const res = await fetch(`${API_BASE}/api/buyer/`);
  if (!res.ok) throw new Error(`Buyers fetch failed: ${res.status}`);
  return res.json();
}

async function getBuyerOffers(userId) {
  const suffix = userId ? `?user_id=${encodeURIComponent(userId)}` : '';
  const res = await fetch(`${API_BASE}/api/buyer/offers${suffix}`);
  if (!res.ok) throw new Error(`Buyer offers fetch failed: ${res.status}`);
  return res.json();
}

async function createBuyerOffer(payload) {
  const res = await fetch(`${API_BASE}/api/buyer/offers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(`Buyer offer creation failed (${res.status}): ${err}`);
  }
  return res.json();
}

/**
 * GET all produce listings from farmers.
 */
async function getProduceListings() {
  const res = await fetch(`${API_BASE}/api/farmer/produce`);
  if (!res.ok) throw new Error(`Produce fetch failed: ${res.status}`);
  return res.json();
}

/**
 * GET all past negotiations (most-recent first, max 50).
 */
async function getNegotiations() {
  const res = await fetch(`${API_BASE}/api/negotiations`);
  if (!res.ok) throw new Error(`Negotiations fetch failed: ${res.status}`);
  return res.json();
}

/**
 * POST to run a simulation scenario.
 * payload: { scenario: 'all' | 'direct-sale' | 'storage' | 'processing' }
 */
async function runSimulation(payload) {
  const res = await fetch(`${API_BASE}/run-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.text().catch(() => res.statusText);
    throw new Error(`Simulation failed (${res.status}): ${err}`);
  }
  return res.json();
}

/** Quick health-check: returns true if backend is reachable. */
async function checkBackend() {
  try {
    const res = await fetch(`${API_BASE}/`, { signal: AbortSignal.timeout(3000) });
    return res.ok || res.status === 404; // any valid HTTP response
  } catch {
    return false;
  }
}

// ── WebSocket ─────────────────────────────

/**
 * Opens a WebSocket to /ws/negotiation.
 * onMessage(parsedEvent) is called for every JSON event.
 * Returns the WebSocket instance.
 */
function connectNegotiationSocket(onMessage, onStatusChange) {
  if (!window.__agriSocketSubscribers) {
    window.__agriSocketSubscribers = { messages: [], statuses: [] };
  }

  if (onMessage && !window.__agriSocketSubscribers.messages.includes(onMessage)) {
    window.__agriSocketSubscribers.messages.push(onMessage);
  }

  if (onStatusChange && !window.__agriSocketSubscribers.statuses.includes(onStatusChange)) {
    window.__agriSocketSubscribers.statuses.push(onStatusChange);
  }

  if (window.__agriNegotiationSocket && window.__agriNegotiationSocket.readyState <= 1) {
    if (window.__agriNegotiationSocket.readyState === WebSocket.OPEN && onStatusChange) {
      onStatusChange('connected');
    }
    return window.__agriNegotiationSocket;
  }

  const ws = new WebSocket(`ws://localhost:8000/ws/negotiation`);
  window.__agriNegotiationSocket = ws;

  ws.onopen = () => {
    ws.send('subscribe');
    window.__agriSocketSubscribers.statuses.forEach((handler) => {
      try { handler('connected'); } catch {}
    });
  };

  ws.onclose = () => {
    window.__agriSocketSubscribers.statuses.forEach((handler) => {
      try { handler('disconnected'); } catch {}
    });
    if (window.__agriNegotiationSocket === ws) {
      window.__agriNegotiationSocket = null;
    }
  };

  ws.onerror = () => {
    window.__agriSocketSubscribers.statuses.forEach((handler) => {
      try { handler('error'); } catch {}
    });
  };

  ws.onmessage = (evt) => {
    try {
      const data = JSON.parse(evt.data);
      window.__agriSocketSubscribers.messages.forEach((handler) => {
        try { handler(data); } catch {}
      });
    } catch {
      // Non-JSON pings — ignore
    }
  };

  return ws;
}

// ── Toast notifications ──────────────────────

const TOAST_ICONS = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };

/**
 * Display a brief toast message.
 * @param {string} type  'success' | 'error' | 'info' | 'warning'
 * @param {string} title Short title
 * @param {string} msg   Optional detail message
 */
function showToast(type, title, msg = '') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `
    <div class="toast-icon">${TOAST_ICONS[type] || '💬'}</div>
    <div class="toast-body">
      <div class="toast-title">${title}</div>
      ${msg ? `<div class="toast-msg">${msg}</div>` : ''}
    </div>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4200);
}