/* =================================================================
   AUTH GUARD — AgriNegotiator
   Include this as the FIRST <script> on every protected page.
   It immediately redirects to login.html if no valid session exists.
   Also provides signOut() used by all pages.
================================================================= */

(function () {
  'use strict';

  /* ── Session helpers ──────────────────────────────────────────── */
  function _getSession() {
    try {
      return JSON.parse(localStorage.getItem('agri_session') || 'null');
    } catch {
      return null;
    }
  }

  function _isValid(session) {
    return session &&
      typeof session === 'object' &&
      session.user_id &&
      session.email &&
      session.role;
  }

  /* ── Guard — runs immediately on script load ──────────────────── */
  var session = _getSession();
  if (!_isValid(session)) {
    // Save where the user was trying to go so we can redirect back
    var intended = window.location.pathname + window.location.search;
    if (intended && !intended.includes('login') && !intended.includes('signup') && !intended.includes('index')) {
      sessionStorage.setItem('agri_redirect_after_login', intended);
    }
    window.location.replace('login.html');
    // Stop all further JS on this page from running
    throw new Error('AUTH_GUARD: Not authenticated. Redirecting to login.');
  }

  /* ── Sign Out ─────────────────────────────────────────────────── */
  window.signOut = function () {
    localStorage.removeItem('agri_session');
    localStorage.removeItem('latestNegotiationId');
    localStorage.removeItem('agri_leveled_up');
    sessionStorage.removeItem('agri_redirect_after_login');
    // Small delay so any in-progress toast can show
    setTimeout(function () {
      window.location.replace('login.html');
    }, 100);
  };

  /* ── Expose session read helpers (override dashboard.js versions) */
  window.getCurrentSession = function () {
    try {
      return JSON.parse(localStorage.getItem('agri_session') || '{}');
    } catch {
      return {};
    }
  };

  window.getCurrentRole = function () {
    var sessionRole = (window.getCurrentSession().role || '').toLowerCase();
    if (sessionRole) return sessionRole;
    return new URLSearchParams(window.location.search).get('role') || 'farmer';
  };

  /* ── Inject Sign-Out button into nav after DOM ready ─────────── */
  document.addEventListener('DOMContentLoaded', function () {
    var sess = window.getCurrentSession();
    var role = window.getCurrentRole();
    var roleIcons = {
      farmer:'🌾', buyer:'🛒', warehouse:'🏗️', transporter:'🚛',
      processor:'⚙️', compost:'♻️', restaurant:'🍽️', admin:'🔑'
    };
    var icon = roleIcons[role] || '👤';
    var name = sess.name || sess.email || 'User';

    // Find nav-cta to inject signout next to existing buttons
    var navCtas = document.querySelectorAll('.nav-cta, .nav-end');
    navCtas.forEach(function (cta) {
      // Avoid double-injection
      if (cta.querySelector('.signout-btn')) return;

      var userInfo = document.createElement('div');
      userInfo.className = 'nav-user-info';
      userInfo.innerHTML =
        '<span class="nav-user-chip">' +
          '<span class="nav-user-icon">' + icon + '</span>' +
          '<span class="nav-user-name">' + _escape(name) + '</span>' +
          '<span class="nav-user-role">' + _escape(role) + '</span>' +
        '</span>' +
        '<button class="btn btn-ghost btn-sm signout-btn" onclick="signOut()" title="Sign out">' +
          '🚪 Sign Out' +
        '</button>';
      cta.insertBefore(userInfo, cta.firstChild);
    });

    // If no .nav-cta exists, append to nav directly
    var nav = document.querySelector('nav.nav');
    if (nav && !nav.querySelector('.signout-btn')) {
      var fallback = document.createElement('div');
      fallback.className = 'nav-cta';
      fallback.innerHTML =
        '<span class="nav-user-chip">' +
          '<span class="nav-user-icon">' + icon + '</span>' +
          '<span class="nav-user-name">' + _escape(name) + '</span>' +
        '</span>' +
        '<button class="btn btn-ghost btn-sm signout-btn" onclick="signOut()">🚪 Sign Out</button>';
      nav.appendChild(fallback);
    }
  });

  function _escape(str) {
    return String(str || '')
      .replace(/&/g,'&amp;').replace(/</g,'&lt;')
      .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }

})();
