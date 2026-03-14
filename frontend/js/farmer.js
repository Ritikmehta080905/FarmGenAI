/* =================================================================
   FARMER FORM — AgriNegotiator
   Full validation, submission, loading state, success screen.
================================================================= */

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
  const display = document.getElementById('negIdDisplay');
  if (form)    form.style.display = 'none';
  if (screen)  screen.classList.add('show');
  if (display) display.textContent = negotiationId || 'N/A';
  // Also save for dashboard
  localStorage.setItem('latestNegotiationId', negotiationId || '');
}

/** Reset form back to default state. */
function resetForm() {
  const form = document.getElementById('cropForm');
  const screen = document.getElementById('successScreen');
  if (form)   { form.reset(); form.style.display = ''; }
  if (screen) screen.classList.remove('show');
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

  if (!validateAll()) {
    showToast('warning', 'Please fix the errors above', 'All required fields must be filled correctly.');
    return;
  }

  const payload = {
    farmer_name: document.getElementById('farmerName').value.trim(),
    crop:        document.getElementById('crop').value,
    quantity:    Number(document.getElementById('qty').value),
    min_price:   Number(document.getElementById('price').value),
    shelf_life:  Number(document.getElementById('shelfLife').value),
    location:    document.getElementById('location').value.trim(),
    quality:     document.getElementById('quality').value || 'A',
    language:    document.getElementById('language')?.value || 'English',
  };

  setSubmitLoading(true);

  try {
    const result = await startNegotiation(payload);
    showToast('success', 'Negotiation started!', `ID: ${result.negotiation_id}`);
    showSuccess(result.negotiation_id);
  } catch (err) {
    setSubmitLoading(false);
    showToast('error', 'Could not start negotiation', err.message);
  }
});