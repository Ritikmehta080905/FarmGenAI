function _session() {
  try {
    return JSON.parse(localStorage.getItem('agri_session') || '{}');
  } catch {
    return {};
  }
}

(function guardBuyerRole() {
  const session = _session();
  const role = String(session.role || '').toLowerCase();
  if (!session.email) {
    window.location.href = 'login.html';
    return;
  }
  if (role !== 'buyer') {
    window.location.href = `dashboard.html?role=${encodeURIComponent(role || 'farmer')}`;
  }
})();

function _setErr(id, on, msg) {
  const el = document.getElementById(`err-${id}`);
  if (!el) return;
  el.style.display = on ? 'flex' : 'none';
  if (msg) el.textContent = `⚠️ ${msg}`;
}

function _setLoading(on) {
  const btn = document.getElementById('submitBtn');
  if (!btn) return;
  if (on) {
    btn.disabled = true;
    btn.classList.add('loading');
    btn.innerHTML = '<div class="spinner"></div><span>Submitting offer…</span>';
  } else {
    btn.disabled = false;
    btn.classList.remove('loading');
    btn.innerHTML = '<span class="btn-txt">📨 Submit Buyer Offer</span>';
  }
}

function resetBuyerForm() {
  const form = document.getElementById('buyerOfferForm');
  const screen = document.getElementById('successScreen');
  if (form) { form.reset(); form.style.display = ''; }
  if (screen) screen.classList.remove('show');
  _setLoading(false);
}

document.getElementById('buyerOfferForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const session = _session();
  const payload = {
    user_id: session.user_id || null,
    buyer_name: (document.getElementById('buyerName')?.value || '').trim() || (session.name || 'Buyer'),
    crop: document.getElementById('crop')?.value || '',
    offered_price: Number(document.getElementById('offeredPrice')?.value || 0),
    quantity: Number(document.getElementById('quantity')?.value || 0),
    location: (document.getElementById('location')?.value || '').trim(),
    strategy: (document.getElementById('strategy')?.value || '').trim() || 'Direct procurement offer',
  };

  let ok = true;
  if (!payload.buyer_name) { _setErr('buyerName', true, 'Please enter buyer name'); ok = false; } else { _setErr('buyerName', false); }
  if (!payload.crop) { _setErr('crop', true, 'Please select produce'); ok = false; } else { _setErr('crop', false); }
  if (!(payload.quantity > 0)) { _setErr('quantity', true, 'Quantity must be greater than 0'); ok = false; } else { _setErr('quantity', false); }
  if (!(payload.offered_price > 0)) { _setErr('offeredPrice', true, 'Price must be greater than 0'); ok = false; } else { _setErr('offeredPrice', false); }
  if (!payload.location) { _setErr('location', true, 'Please enter location'); ok = false; } else { _setErr('location', false); }

  if (!ok) {
    showToast('warning', 'Fix form errors', 'Please complete all required fields.');
    return;
  }

  _setLoading(true);
  try {
    const result = await createBuyerOffer(payload);
    const form = document.getElementById('buyerOfferForm');
    const screen = document.getElementById('successScreen');
    const idBox = document.getElementById('offerIdDisplay');
    if (form) form.style.display = 'none';
    if (screen) screen.classList.add('show');
    if (idBox) idBox.textContent = result.id || '—';
    showToast('success', 'Buyer offer submitted', `${payload.crop} at ₹${payload.offered_price}/kg`);
  } catch (err) {
    _setLoading(false);
    showToast('error', 'Could not submit offer', err.message);
  }
});
