/* =================================================================
   NEGOTIATION FLOW — AgriNegotiator
   Manages WebSocket connection, renders timestamped log entries,
   and exposes startNegotiationFlow() for the dashboard.
================================================================= */

let _activeSocket = null;
let _activeNegotiationId = null;
const _renderedLogLines = new Set();

// ── Log classification ───────────────────────────

const LOG_ICONS = { deal: '✅', counter: '🔄', reject: '❌', info: '💬', system: '⚡' };
const AGENT_ICONS = { 
  farmer: '🌾', buyer: '🛒', warehouse: '🏗️', transporter: '🚛', 
  processor: '⚙️', compost: '♻️', system: '⚡', admin: '🔑' 
};

function classifyLog(msg) {
  const m = msg.toLowerCase();
  if (m.includes('deal') || m.includes('accept') || m.includes('success') || m.includes('agreed')) return 'deal';
  if (m.includes('counter') || m.includes('offer') || m.includes('propose') || m.includes('bid')) return 'counter';
  if (m.includes('reject') || m.includes('fail') || m.includes('decline') || m.includes('esclat')) return 'reject';
  if (m.includes('start') || m.includes('connect') || m.includes('escalat') || m.includes('trying') || m.includes('node joined')) return 'system';
  return 'info';
}

// ── Log rendering ─────────────────────────────

function appendLog(message, typeOverride, agentType) {
  const log = document.getElementById('negotiationLog');
  if (!log) return;

  const empty = document.getElementById('logEmpty');
  if (empty) empty.style.display = 'none';

  const type = typeOverride || classifyLog(message);
  const icon = AGENT_ICONS[agentType] || LOG_ICONS[type] || '💬';
  const now = new Date().toLocaleTimeString('en-GB', { hour12: false });

  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  if (agentType) entry.setAttribute('data-agent', agentType);
  
  entry.innerHTML = `
    <span class="log-time">${now}</span>
    <span class="log-icon">${icon}</span>
    <span class="log-text">${escapeHtml(message)}</span>`;

  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

function appendUniqueLog(message, typeOverride, agentType) {
  const key = String(message || '').trim();
  if (!key || _renderedLogLines.has(key)) return;
  _renderedLogLines.add(key);
  appendLog(message, typeOverride, agentType);
}

function clearLog() {
  const log = document.getElementById('negotiationLog');
  if (!log) return;
  log.innerHTML = '';
  const empty = document.getElementById('logEmpty');
  if (empty) { empty.style.display = ''; log.appendChild(empty); }
  _renderedLogLines.clear();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── WebSocket badge ─────────────────────

function setWsBadge(state) {
  const badge = document.getElementById('wsBadge');
  const dot = document.getElementById('wsDot');
  const text = document.getElementById('wsText');
  if (!badge) return;

  badge.className = `ws-badge ${state}`;

  if (state === 'connected') {
    if (dot) dot.className = 'dot dot-green';
    if (text) text.textContent = 'Live';
  } else if (state === 'error') {
    if (dot) dot.className = 'dot dot-red';
    if (text) text.textContent = 'Error';
  } else {
    if (dot) dot.className = 'dot dot-gray';
    if (text) text.textContent = 'Offline';
  }
}

// ── Main flow ─────────────────────────────────

async function startNegotiationFlow(payload) {

  appendLog('🚀 Starting negotiation…', 'system');

  _activeSocket = connectNegotiationSocket(_handleSocketEvent, setWsBadge);

  await new Promise((resolve) => {
    if (_activeSocket.readyState === WebSocket.OPEN) {
      resolve();
    } else {
      _activeSocket.addEventListener('open', resolve, { once: true });
      setTimeout(resolve, 2500);
    }
  });

  try {

    const result = await startNegotiation(payload);

    _activeNegotiationId = result.negotiation_id;
    localStorage.setItem('latestNegotiationId', result.negotiation_id);

    if (result.status === 'RUNNING') {

      appendUniqueLog('⏳ LLM agents reasoning… polling updates', 'system');

      const final = await _pollUntilDone(result.negotiation_id);

      (final.logs || []).forEach((line) => appendUniqueLog(line));

      if (final.summary)
        appendUniqueLog(`📌 Summary: ${final.summary}`, 'system');

      return final;
    }

    (result.logs || []).forEach((line) => appendUniqueLog(line));

    if (result.summary)
      appendUniqueLog(`📌 Summary: ${result.summary}`, 'system');

    return result;

  } catch (err) {

    appendLog(`⚠️ Error: ${err.message}`, 'reject');

    throw err;
  }
}

async function _pollUntilDone(negId, timeoutMs = 120000) {

  const deadline = Date.now() + timeoutMs;

  while (Date.now() < deadline) {

    await new Promise((r) => setTimeout(r, 3000));

    try {

      const status = await getNegotiationStatus(negId);

      if (status.status !== 'RUNNING')
        return status;

      appendUniqueLog('⏳ Still processing…', 'system');

    } catch {}
  }

  try {
    return await getNegotiationStatus(negId);
  } catch {
    return {
      negotiation_id: negId,
      status: 'TIMEOUT',
      logs: [],
      summary: 'Timed out waiting for LLM'
    };
  }
}

async function resumeNegotiationFlow(negotiationId) {
  _activeNegotiationId = negotiationId;
  _activeSocket = connectNegotiationSocket(_handleSocketEvent, setWsBadge);
  appendLog(`🔎 Watching live negotiation ${negotiationId}`, 'system');
  const final = await _pollUntilDone(negotiationId);

  (final.logs || []).forEach((line) => appendUniqueLog(line));
  if (final.summary) {
    appendUniqueLog(`📌 Summary: ${final.summary}`, 'system');
  }

  return final;
}

function _handleSocketEvent(event) {
  if (event.event === 'CONTRACT_FINALIZED') {
    showToast('success', '📜 Contract Finalized!', 
      `Farmer ${event.farmer || 'user'} completed the deal! Trust: ${event.trust_score || 'up'}`);
    return;
  }

  if (event.event === 'SCENARIO_READY') {
    showToast('info', '🎯 Scenario Ready', 
      `New supply chain match for ${event.farmer}'s ${event.crop}! Status: ${event.status}`);
    return;
  }

  if (event.negotiation_id && _activeNegotiationId && event.negotiation_id !== _activeNegotiationId) {
    return;
  }

  if (event.event === 'NEGOTIATION_LOG') {
    appendUniqueLog(event.message, null, event.agent_type);

    if (event.agent_type && event.offer != null) {
      updateAgentCard(event.agent_type, {
        offer: event.offer,
        status: 'negotiating'
      });
    }
  }

  if (event.event === 'NEGOTIATION_FINISHED') {
    const price = event.final_price
      ? `₹${Number(event.final_price).toFixed(2)}/kg`
      : 'N/A';

    appendUniqueLog(
      `🏁 Finished — ${event.status} | Final: ${price}`,
      event.status.includes('DEAL') ? 'deal' : 'reject'
    );

    (event.logs || []).forEach((line) => appendUniqueLog(line));

    if (event.status && event.status.includes('DEAL')) {
      updateAgentCard('farmer', { status: 'deal' });
      updateAgentCard('buyer', { status: 'deal' });
    }

    if (event.status && event.status.includes('STORAGE')) {
      updateAgentCard('warehouse', { status: 'deal' });
    }

    if (event.status && event.status.includes('PROCESSING')) {
      updateAgentCard('processor', { status: 'deal' });
    }

    if (event.status && event.status.includes('COMPOST')) {
      updateAgentCard('compost', { status: 'deal' });
    }
  }

  // Legacy EventBus-compatible fallback payloads
  if (event.type === "market_tick") {
    appendLog(`📊 Market price: ₹${event.data.market_price}`, "info");
  }

  if (event.type === "offer_made") {
    appendLog(`🌾 Farmer offer: ₹${event.data.price}`, "counter");

    updateAgentCard("farmer", {
      offer: event.data.price,
      status: "negotiating"
    });
  }

  if (event.type === "counter_offer") {
    appendLog(`🛒 Buyer counter: ₹${event.data.price}`, "counter");

    updateAgentCard("buyer", {
      offer: event.data.price,
      status: "negotiating"
    });
  }

  if (event.type === "deal_reached") {
    appendLog(`✅ Deal reached at ₹${event.data.price}`, "deal");

    updateAgentCard("farmer", {
      offer: event.data.price,
      status: "deal"
    });

    updateAgentCard("buyer", {
      offer: event.data.price,
      status: "deal"
    });
  }
}