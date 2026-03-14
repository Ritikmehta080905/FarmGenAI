/* =================================================================
   NEGOTIATION FLOW — AgriNegotiator
   Manages WebSocket connection, renders timestamped log entries,
   and exposes startNegotiationFlow() for the dashboard.
================================================================= */

let _activeSocket = null;

// ── Log classification ───────────────────────────

const LOG_ICONS = { deal: '✅', counter: '🔄', reject: '❌', info: '💬', system: '⚡' };

/** Classify a log message string into a CSS type. */
function classifyLog(msg) {
  const m = msg.toLowerCase();
  if (m.includes('deal') || m.includes('accept') || m.includes('success') || m.includes('agreed')) return 'deal';
  if (m.includes('counter') || m.includes('offer') || m.includes('propose') || m.includes('bid'))  return 'counter';
  if (m.includes('reject') || m.includes('fail') || m.includes('decline') || m.includes('esclat')) return 'reject';
  if (m.includes('start') || m.includes('connect') || m.includes('escalat') || m.includes('trying')) return 'system';
  return 'info';
}

// ── Log rendering ─────────────────────────────

/** Append a styled, timestamped entry to the negotiation log. */
function appendLog(message, typeOverride) {
  const log = document.getElementById('negotiationLog');
  if (!log) return;

  // Hide empty state
  const empty = document.getElementById('logEmpty');
  if (empty) empty.style.display = 'none';

  const type = typeOverride || classifyLog(message);
  const icon = LOG_ICONS[type] || '💬';
  const now  = new Date().toLocaleTimeString('en-GB', { hour12: false });

  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  entry.innerHTML = `
    <span class="log-time">${now}</span>
    <span class="log-icon">${icon}</span>
    <span class="log-text">${escapeHtml(message)}</span>`;

  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
}

/** Clear all log entries. */
function clearLog() {
  const log = document.getElementById('negotiationLog');
  if (!log) return;
  log.innerHTML = '';
  const empty = document.getElementById('logEmpty');
  if (empty) { empty.style.display = ''; log.appendChild(empty); }
}

/** Escape HTML to prevent injection from server messages. */
function escapeHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── WebSocket management ────────────────────────

/** Update the WebSocket badge in the nav. */
function setWsBadge(state) {
  const badge = document.getElementById('wsBadge');
  const dot   = document.getElementById('wsDot');
  const text  = document.getElementById('wsText');
  if (!badge) return;

  badge.className = `ws-badge ${state}`;
  if (state === 'connected') {
    if (dot)  { dot.className = 'dot dot-green'; }
    if (text) text.textContent = 'Live';
  } else if (state === 'error') {
    if (dot)  { dot.className = 'dot dot-red'; }
    if (text) text.textContent = 'Error';
  } else {
    if (dot)  { dot.className = 'dot dot-gray'; }
    if (text) text.textContent = 'Offline';
  }
}

// ── Main flow ─────────────────────────────────

/**
 * Open a WebSocket, run a negotiation, stream results to the log.
 * Returns the full negotiation result object.
 * If the server is using LLM reasoning, the POST returns status=RUNNING
 * immediately and this function polls until the result is ready.
 */
async function startNegotiationFlow(payload) {
  appendLog('🚀 Starting negotiation…', 'system');

  // Close any existing socket
  if (_activeSocket && _activeSocket.readyState <= 1) {
    _activeSocket.close();
  }

  // Open new WS for real-time events
  _activeSocket = connectNegotiationSocket(
    (event) => {
      if (event.event === 'NEGOTIATION_LOG') {
        appendLog(event.message);
        // Update agent card if type is known
        if (event.agent_type && event.offer != null) {
          updateAgentCard(event.agent_type, { offer: event.offer, status: 'negotiating' });
        }
      }
      if (event.event === 'NEGOTIATION_FINISHED') {
        const price = event.final_price ? `₹${Number(event.final_price).toFixed(2)}/kg` : 'N/A';
        appendLog(`🏁 Finished — ${event.status} | Final: ${price}`,
                  event.status.includes('DEAL') ? 'deal' : 'reject');
      }
    },
    setWsBadge
  );

  // Wait for WebSocket to open before sending HTTP request so we don't miss
  // any broadcast events that the backend emits before returning its response.
  await new Promise((resolve) => {
    if (_activeSocket.readyState === WebSocket.OPEN) {
      resolve();
    } else {
      _activeSocket.addEventListener('open', resolve, { once: true });
      setTimeout(resolve, 2500); // failsafe: don't block forever if WS fails
    }
  });

  try {
    const result = await startNegotiation(payload);
    localStorage.setItem('latestNegotiationId', result.negotiation_id);

    // ── RUNNING path: negotiate happens in background (LLM enabled) ──
    if (result.status === 'RUNNING') {
      appendLog('⏳ LLM agents are reasoning… polling for updates (this may take up to 60s)', 'system');
      const final = await _pollUntilDone(result.negotiation_id);
      (final.logs || []).forEach((line) => appendLog(line));
      if (final.summary) appendLog(`📌 Summary: ${final.summary}`, 'system');
      return final;
    }

    // ── Immediate path: LLM disabled or fast fallback ──
    // Append all pre-computed logs from the API response
    (result.logs || []).forEach((line) => appendLog(line));
    if (result.summary) appendLog(`📌 Summary: ${result.summary}`, 'system');

    return result;
  } catch (err) {
    appendLog(`⚠️ Error: ${err.message}`, 'reject');
    throw err;
  }
}

/**
 * Poll /negotiation-status/{id} every 3 s until status is no longer RUNNING.
 * Times out after 120 s and returns whatever result we have.
 */
async function _pollUntilDone(negId, timeoutMs = 120000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, 3000));
    try {
      const status = await getNegotiationStatus(negId);
      if (status.status !== 'RUNNING') return status;
      appendLog('⏳ Still processing…', 'system');
    } catch { /* ignore transient fetch errors */ }
  }
  // Return whatever we have after timeout
  try { return await getNegotiationStatus(negId); } catch { return { negotiation_id: negId, status: 'TIMEOUT', logs: [], summary: 'Timed out waiting for LLM' }; }
}