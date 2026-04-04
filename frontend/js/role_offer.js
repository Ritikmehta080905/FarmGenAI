function _session() {
  try {
    return JSON.parse(localStorage.getItem('agri_session') || '{}');
  } catch {
    return {};
  }
}

function _roleMeta(role) {
  const map = {
    warehouse: { icon: '🏗️', title: 'Create Warehouse Offer', desc: 'Submit storage capacity and pricing intent.' },
    transporter: { icon: '🚛', title: 'Create Transport Offer', desc: 'Submit transport handling and route intent.' },
    processor: { icon: '⚙️', title: 'Create Processor Offer', desc: 'Submit processing demand and pricing intent.' },
    compost: { icon: '♻️', title: 'Create Compost Offer', desc: 'Submit fallback recovery offer details.' },
    buyer: { icon: '🛒', title: 'Create Buyer Offer', desc: 'Submit your buying demand and offered price.' },
  };
  return map[role] || { icon: '📦', title: 'Create Role Offer', desc: 'Submit your role-specific offer.' };
}

(function guardRole() {
  const session = _session();
  const role = String(session.role || '').toLowerCase();
  if (!session.email) {
    window.location.href = 'login.html';
    return;
  }
  if (!role || role === 'farmer') {
    window.location.href = 'farmer_form.html';
    return;
  }

  if (role === 'buyer') {
    window.location.href = 'buyer_offer_form.html';
    return;
  }

  const meta = _roleMeta(role);
  const roleIcon = document.getElementById('roleIcon');
  const roleTitle = document.getElementById('roleTitle');
  const roleDesc = document.getElementById('roleDesc');
  const dashNav = document.getElementById('dashNavLink');
  const backDash = document.getElementById('backDashLink');
  const openDash = document.getElementById('openDashBtn');

  if (roleIcon) roleIcon.textContent = meta.icon;
  if (roleTitle) roleTitle.textContent = meta.title;
  if (roleDesc) roleDesc.textContent = meta.desc;

  const dashHref = `dashboard.html?role=${encodeURIComponent(role)}`;
  if (dashNav) dashNav.setAttribute('href', dashHref);
  if (backDash) backDash.setAttribute('href', dashHref);
  if (openDash) openDash.setAttribute('href', dashHref);

  const actorName = document.getElementById('actorName');
  if (actorName && session.name) actorName.value = session.name;
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
    btn.innerHTML = '<span class="btn-txt">📨 Submit Offer</span>';
  }
}

function resetRoleOfferForm() {
  const form = document.getElementById('roleOfferForm');
  const screen = document.getElementById('successScreen');
  if (form) { form.reset(); form.style.display = ''; }
  if (screen) screen.classList.remove('show');
  _setLoading(false);
}

document.getElementById('roleOfferForm')?.addEventListener('submit', async (e) => {
  e.preventDefault();

  const session = _session();
  const role = String(session.role || '').toLowerCase();

  const offeredRaw = document.getElementById('offeredPrice')?.value;
  const offeredPrice = offeredRaw ? Number(offeredRaw) : null;

  const payload = {
    user_id: session.user_id || null,
    role,
    actor_name: (document.getElementById('actorName')?.value || '').trim() || (session.name || role),
    crop: document.getElementById('crop')?.value || '',
    quantity: Number(document.getElementById('quantity')?.value || 0),
    offered_price: offeredPrice,
    location: (document.getElementById('location')?.value || '').trim(),
    notes: (document.getElementById('notes')?.value || '').trim(),
  };

  let ok = true;
  if (!payload.actor_name) { _setErr('actorName', true, 'Please enter name'); ok = false; } else { _setErr('actorName', false); }
  if (!payload.crop) { _setErr('crop', true, 'Please select crop'); ok = false; } else { _setErr('crop', false); }
  if (!(payload.quantity > 0)) { _setErr('quantity', true, 'Quantity must be greater than 0'); ok = false; } else { _setErr('quantity', false); }
  if (payload.offered_price != null && !(payload.offered_price > 0)) { _setErr('offeredPrice', true, 'Price must be greater than 0'); ok = false; } else { _setErr('offeredPrice', false); }
  if (!payload.location) { _setErr('location', true, 'Please enter location'); ok = false; } else { _setErr('location', false); }

  if (!ok) {
    showToast('warning', 'Fix form errors', 'Please complete all required fields.');
    return;
  }

  _setLoading(true);
  try {
    const result = await createRoleOffer(payload);
    const form = document.getElementById('roleOfferForm');
    const screen = document.getElementById('successScreen');
    const idBox = document.getElementById('offerIdDisplay');
    if (form) form.style.display = 'none';
    if (screen) screen.classList.add('show');
    if (idBox) idBox.textContent = result.id || '—';
    showToast('success', 'Offer submitted', `${payload.crop} • ${payload.quantity}kg`);
  } catch (err) {
    _setLoading(false);
    showToast('error', 'Could not submit offer', err.message);
  }
});
