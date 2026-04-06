/* =================================================================
   ADMIN CONSOLE — AgriNegotiator
   Governs node verification and global network trust scores.
================================================================= */

document.addEventListener('DOMContentLoaded', async () => {
    // 🛡️ Access Control: Strict check for admin@agri.ai
    const session = window.getCurrentSession();
    const role = window.getCurrentRole();
    if (role !== 'admin' && !session.email?.includes('admin')) {
        showToast('error', 'Access Denied', 'Administrators only.');
        setTimeout(() => window.location.replace('dashboard.html'), 1500);
        return;
    }

    await loadAdminDashboard();
});

async function loadAdminDashboard() {
    try {
        const nodes_res = await fetch(`${API_URL}/nodes`);
        const nodes = await nodes_res.json();

        const history_res = await fetch(`${API_URL}/history/all`);
        const history = await history_res.json();

        renderStats(nodes, history);
        renderNodeTable(nodes);
    } catch (err) {
        showToast('error', 'Fetch Error', 'Failed to load network stats. Is the backend on Port 8000?');
    }
}

function renderStats(nodes, history) {
    const totalNodesEl = document.getElementById('totalNodes');
    const totalTxEl = document.getElementById('totalTx');
    const avgTrustEl = document.getElementById('avgTrust');

    if (totalNodesEl) totalNodesEl.textContent = Object.keys(nodes).length;
    if (totalTxEl) totalTxEl.textContent = history.length;
    
    // Average Trust Score Calculation
    let sum = 0;
    let count = 0;
    Object.values(nodes).forEach(n => {
        sum += (n.trust_score || 0);
        count++;
    });
    const avg = count > 0 ? (sum / count).toFixed(2) : '0.0';
    if (avgTrustEl) avgTrustEl.textContent = avg;
}

function renderNodeTable(nodes) {
    const tbody = document.getElementById('nodeTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    Object.entries(nodes).forEach(([id, n]) => {
        const row = document.createElement('tr');
        const role_icon = {
            farmer:'🌾', buyer:'🛒', warehouse:'🏗️', transporter:'🚛',
            processor:'⚙️', compost:'♻️', restaurant:'🍽️', admin:'🔑'
        }[n.role] || '👤';

        row.innerHTML = `
            <td class="font-mono text-sm">${id}</td>
            <td><strong>${n.business_name || n.farmer_name || 'Generic Node'}</strong></td>
            <td>${role_icon} ${n.role.toUpperCase()}</td>
            <td>${n.history ? n.history.length : 0}</td>
            <td>
                <span class="${n.verified ? 'badge-verified' : 'badge-pending'}">
                    ${n.verified ? '✅ Verified' : '⏳ Pending'}
                </span>
            </td>
            <td class="font-bold text-success">${Number(n.trust_score || 0).toFixed(1)}</td>
            <td>
                <button class="btn btn-ghost btn-sm" onclick="showToast('info','Action Blocked','Node governance requires manual override in production.')">🔧 Manage</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function showToast(type, title, msg) {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `<strong>${title}</strong><p>${msg}</p>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
