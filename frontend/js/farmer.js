/* =================================================================
   FARMER FORM — AgriNegotiator
   Full validation, submission, loading state, success screen.
================================================================= */

try {
  const session = JSON.parse(localStorage.getItem('agri_session') || '{}');
  const role = String(session.role || '').toLowerCase();
  if (session.email && role && role !== 'farmer') {
    window.location.href = `dashboard.html?role=${encodeURIComponent(role)}`;
  }
} catch {}

// ── Validation rules ───────────────────────────

/** Returns an error string or null if valid. */
function validateField(id, value) {
  switch (id) {
    case 'farmerName': return value.trim().length < 2 ? 'Please enter your name (min 2 characters)' : null;
    case 'crop':       return !value ? 'Please select a crop type' : null;
    case 'qty':        return (!value || Number(value) < 1) ? 'Quantity must be at least 1 kg' : null;
    case 'price':      return (!value || Number(value) <= 0) ? 'Minimum price must be greater than 0' : null;
    case 'shelfLife':  return (!value || Number(value) < 1) ? 'Shelf life must be at least 1 day' : null;
    case 'location':   return value.trim().length < 2 ? 'Please enter your location' : null;
    default:           return null;
  }
}

/** Show / hide error message for a field. */
function setFieldError(id, msg) {
  const errEl = document.getElementById(`err-${id}`);
  const input = document.getElementById(id);
  if (!errEl || !input) return;
  if (msg) {
    errEl.textContent = `⚠️ ${msg}`;
    errEl.style.display = 'flex';
    input.classList.add('err');
    input.classList.remove('ok');
  } else {
    errEl.style.display = 'none';
    input.classList.remove('err');
    input.classList.add('ok');
  }
}

/** Validate all required fields. Returns true if all pass. */
function validateAll() {
  const fields = ['farmerName', 'crop', 'qty', 'price', 'shelfLife', 'location'];
  let valid = true;
  fields.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    const err = validateField(id, el.value);
    setFieldError(id, err);
    if (err) valid = false;
  });
  return valid;
}

// ── Loading state ────────────────────────────

function setSubmitLoading(on) {
  const btn = document.getElementById('submitBtn');
  if (!btn) return;
  if (on) {
    btn.disabled = true;
    btn.classList.add('loading');
    btn.innerHTML = `<div class="spinner"></div><span>Finding buyers…</span>`;
  } else {
    btn.disabled = false;
    btn.classList.remove('loading');
    btn.innerHTML = `<span class="btn-txt">🚀 Start Negotiation</span>`;
  }
}

// ── Success screen ──────────────────────────

function showSuccess(negotiationId) {
  const form = document.getElementById('cropForm');
  const screen = document.getElementById('successScreen');
  const scenarioScreen = document.getElementById('scenarioScreen');
  const display = document.getElementById('negIdDisplay');
  if (form)    form.style.display = 'none';
  if (scenarioScreen) scenarioScreen.classList.remove('show');
  if (screen)  screen.classList.add('show');
  if (display) display.textContent = negotiationId || 'N/A';
  // Also save for dashboard
  localStorage.setItem('latestNegotiationId', negotiationId || '');
}

function showScenarios(analysisResult, originalPayload) {
  const form = document.getElementById('cropForm');
  const screen = document.getElementById('scenarioScreen');
  const list = document.getElementById('scenarioList');
  if (!form || !screen || !list) return;

  form.style.display = 'none';
  screen.classList.add('show');
  list.innerHTML = '';

  const scenarios = analysisResult.scenarios || [];
  scenarios.forEach(s => {
    const card = document.createElement('div');
    card.className = 'card';
    card.style.cursor = 'pointer';
    card.style.transition = 'transform 0.2s';
    
    let icon = '🛒';
    if (s.scenario_type === 'storage') icon = '🏗️';
    if (s.scenario_type === 'processing') icon = '⚙️';

    card.innerHTML = `
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <div style="display:flex; gap:1rem; align-items:center;">
          <div style="font-size:1.5rem;">${icon}</div>
          <div>
            <h4 style="margin:0;">${s.type.replace('-', ' ').toUpperCase()}</h4>
            <p style="font-size:0.75rem; color:var(--text-secondary); margin:0;">Target Node: ${s.peer_node || 'Unknown'}</p>
            <p style="font-size:0.65rem; color:var(--text-muted); margin:0;">${s.summary || 'AI negotiation path'}</p>
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-size:1.2rem; font-weight:800; color:var(--green-500);">₹${Number(s.estimated_price || 0).toFixed(2)}</div>
          <div style="font-size:0.6rem; color:var(--text-muted);">CONFIDENCE: ${s.score}/100</div>
        </div>
      </div>
    `;
    
    card.onclick = () => {
      card.style.transform = 'scale(0.98)';
      startDecentralizedHandshake(payload.node_id, s.peer_node, payload.crop);
    };
    
    list.appendChild(card);
  });
}

async function startDecentralizedHandshake(nodeId, peerNode, crop) {
  setSubmitLoading(true);
  try {
    const res = await fetch(`${API_BASE}/api/node/${nodeId}/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_node: peerNode, crop: crop })
    });
    const result = await res.json();
    
    if (result.block) {
        showToast('success', '🤝 Multi-Party Handshake Complete!', 'Deal signed by both nodes and appended to the shared ledger.');
        showSuccess(result.block.block_id);
    } else {
        throw new Error(result.reason || 'Handshake failed');
    }
  } catch (err) {
    setSubmitLoading(false);
    showToast('error', 'Decentralized handshake failed', err.message);
  }
}

/** Reset form back to default state. */
function resetForm() {
  const form = document.getElementById('cropForm');
  const screen = document.getElementById('successScreen');
  const scenarioScreen = document.getElementById('scenarioScreen');
  if (form)   { form.reset(); form.style.display = ''; }
  if (screen) screen.classList.remove('show');
  if (scenarioScreen) scenarioScreen.classList.remove('show');
  // Clear validation states
  document.querySelectorAll('.form-input').forEach((el) => el.classList.remove('ok', 'err'));
  document.querySelectorAll('.field-err').forEach((el) => (el.style.display = 'none'));
  setSubmitLoading(false);
}

// ── Inline validation on blur ────────────────────

['farmerName', 'crop', 'qty', 'price', 'shelfLife', 'location'].forEach((id) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.addEventListener('blur', () => setFieldError(id, validateField(id, el.value)));
  el.addEventListener('input', () => {
    if (el.classList.contains('err')) setFieldError(id, validateField(id, el.value));
  });
});

// ── Form submission ───────────────────────────

document.getElementById('cropForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  let session = {};
  try {
    session = JSON.parse(localStorage.getItem('agri_session') || '{}');
  } catch {}

  if (!validateAll()) {
    showToast('warning', 'Please fix the errors above', 'All required fields must be filled correctly.');
    return;
  }

  const payload = {
    node_id:      session.user_id || 'node_f_user',
    name:        document.getElementById('farmerName').value.trim() || 'Anonymous Farmer',
    crop:        document.getElementById('crop').value,
    quantity:    Number(document.getElementById('qty').value),
    min_price:   Number(document.getElementById('price').value),
    shelf_life:  Number(document.getElementById('shelfLife').value),
    location:    document.getElementById('location').value.trim(),
    quality:     document.getElementById('quality').value || 'A',
    urgency:     document.getElementById('urgency')?.value || 'Normal',
    neg_mode:    document.querySelector('input[name="negMode"]:checked')?.value || 'auto',
  };

  setSubmitLoading(true);

  try {
    // 1. ANNOUNCE_SUPPLY to the P2P Discovery Hub
    const announceRes = await fetch(`${API_BASE}/api/node/${payload.node_id}/announce`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    const broadcast = await announceRes.json();
    
    showToast('info', '🛰️ Decentralized Announcement Sent!', 'Nodes in the peer network are now responding…');

    // 2. FETCH_LOCAL_SCENARIOS generated by the farmer's local agent
    // We wait 1 second for peer responses to propagate through the node hub
    await new Promise(r => setTimeout(r, 1500));
    const analysisRes = await fetch(`${API_BASE}/api/node/${payload.node_id}/scenarios?crop=${payload.crop}`);
    const analysis = await analysisRes.json();
    
    setSubmitLoading(false);
    showScenarios(analysis, payload);
    
  } catch (err) {
    setSubmitLoading(false);
    showToast('error', 'Decentralized request failed', err.message);
  }
});