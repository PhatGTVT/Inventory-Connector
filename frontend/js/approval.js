// approval.js - Admin Approval Page

let allRequests = [];
let currentFilter = '';
let searchQuery = '';

function getStatusBadge(status) {
  const map = {
    pending:  `<span class="badge badge-pending">🕐 Chờ duyệt</span>`,
    approved: `<span class="badge badge-approved">✅ Đã duyệt</span>`,
    rejected: `<span class="badge badge-rejected">❌ Từ chối</span>`,
  };
  return map[status] || `<span class="badge">${status}</span>`;
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  return d.toLocaleString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

function renderTable(requests) {
  const tbody = document.getElementById('requests-tbody');
  const emptyState = document.getElementById('empty-state');
  const statsEl = document.getElementById('requests-count');

  if (statsEl) statsEl.textContent = `${requests.length} yêu cầu`;

  if (!tbody) return;

  if (requests.length === 0) {
    tbody.innerHTML = '';
    if (emptyState) emptyState.style.display = 'flex';
    return;
  }
  if (emptyState) emptyState.style.display = 'none';

  tbody.innerHTML = '';
  requests.forEach((req) => {
    const tr = document.createElement('tr');
    tr.setAttribute('data-req-id', req.id);
    tr.innerHTML = `
      <td>
        <div style="font-weight:700;color:var(--accent-primary);font-size:0.88rem;letter-spacing:0.02em">${req.request_code}</div>
      </td>
      <td>
        <div style="font-weight:500;color:var(--text-main);font-size:0.83rem">${formatDate(req.requested_at)}</div>
      </td>
      <td>

        <div style="font-weight:600;color:#fff">${req.user_name}</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">${req.user_department || '—'}</div>
      </td>
      <td>
        <div style="font-weight:600;color:#fff;font-size:0.9rem">${req.connector_part_number}</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">${req.connector_name}</div>
        <div style="font-size:0.75rem;color:var(--text-dim)">Tồn kho: <b style="color:${req.current_in_stock < 5 ? 'var(--warning)' : 'var(--success)'}">${req.current_in_stock}</b></div>
      </td>
      <td style="text-align:center;font-weight:800;font-size:1.1rem;color:var(--accent-primary)">${req.quantity}</td>
      <td>${getStatusBadge(req.status)}</td>
      <td>
        <div style="max-width:200px;font-size:0.82rem;color:var(--text-muted)">${req.reason || '<em>—</em>'}</div>
      </td>
      <td>
        <div style="max-width:200px;font-size:0.82rem;color:${req.admin_response ? 'var(--text-main)' : 'var(--text-dim)'}">
          ${req.admin_response || '<em>—</em>'}
        </div>
      </td>
      <td>
        <div class="action-buttons-group">
          ${req.status === 'pending' ? `
            <button class="btn btn-success btn-sm" data-action="approve" data-id="${req.id}" title="Duyệt">✅ Duyệt</button>
            <button class="btn btn-danger btn-sm" data-action="reject" data-id="${req.id}" title="Từ chối">❌ Từ chối</button>
          ` : ''}
          <button class="btn btn-secondary btn-sm" data-action="respond" data-id="${req.id}" title="Phản hồi">💬</button>
          <button class="btn btn-sm" style="background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3)" data-action="delete" data-id="${req.id}" title="Xóa">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Bind action buttons
  tbody.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', handleAction);
  });
}

function getFilteredRequests() {
  let filtered = allRequests;
  if (currentFilter) {
    filtered = filtered.filter(r => r.status === currentFilter);
  }
  if (searchQuery) {
    const q = searchQuery.toLowerCase();
    filtered = filtered.filter(r =>
      r.request_code.toLowerCase().includes(q) ||
      r.user_name.toLowerCase().includes(q) ||
      r.connector_part_number.toLowerCase().includes(q) ||
      r.connector_name.toLowerCase().includes(q)
    );
  }
  return filtered;
}

async function loadRequests() {
  const spinner = document.getElementById('table-spinner');
  if (spinner) spinner.style.display = 'flex';

  try {
    allRequests = await api.getRequests();
    updateCountBadges();
    renderTable(getFilteredRequests());
  } catch (err) {
    showToast('Lỗi khi tải danh sách yêu cầu', 'error');
    console.error(err);
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

function updateCountBadges() {
  const pending = allRequests.filter(r => r.status === 'pending').length;
  const approved = allRequests.filter(r => r.status === 'approved').length;
  const rejected = allRequests.filter(r => r.status === 'rejected').length;

  const countAll = document.getElementById('count-all');
  const countPending = document.getElementById('count-pending');
  const countApproved = document.getElementById('count-approved');
  const countRejected = document.getElementById('count-rejected');

  if (countAll) countAll.textContent = allRequests.length;
  if (countPending) countPending.textContent = pending;
  if (countApproved) countApproved.textContent = approved;
  if (countRejected) countRejected.textContent = rejected;
}

// Response modal logic
let respondingRequestId = null;

function openRespondModal(req) {
  const modal = document.getElementById('respond-modal');
  const input = document.getElementById('respond-text');
  if (!modal || !input) return;
  respondingRequestId = req.id;
  document.getElementById('respond-modal-code').textContent = req.request_code;
  input.value = req.admin_response || '';
  modal.classList.add('active');
}

async function handleAction(e) {
  const btn = e.currentTarget;
  const action = btn.getAttribute('data-action');
  const id = parseInt(btn.getAttribute('data-id'));
  const req = allRequests.find(r => r.id === id);
  if (!req) return;

  btn.disabled = true;

  try {
    if (action === 'approve') {
      if (!confirm(`Xác nhận DUYỆT yêu cầu ${req.request_code}?\nSẽ xuất ${req.quantity} chiếc từ tồn kho.`)) return;
      await api.approveRequest(id, 'Yêu cầu đã được phê duyệt và xuất kho.');
      showToast(`✅ Đã duyệt ${req.request_code} - Trừ ${req.quantity} khỏi kho`, 'success');
      await loadRequests();

    } else if (action === 'reject') {
      const reason = prompt(`Lý do từ chối yêu cầu ${req.request_code}:`, 'Yêu cầu vượt hạn mức hoặc tồn kho không đủ.');
      if (reason === null) return;
      await api.rejectRequest(id, reason || 'Không đủ điều kiện phê duyệt.');
      showToast(`Đã từ chối yêu cầu ${req.request_code}`, 'warning');
      await loadRequests();

    } else if (action === 'respond') {
      openRespondModal(req);

    } else if (action === 'delete') {
      if (!confirm(`Xóa vĩnh viễn yêu cầu ${req.request_code}?`)) return;
      await api.deleteRequest(id);
      showToast(`Đã xóa yêu cầu ${req.request_code}`, 'success');
      await loadRequests();
    }
  } catch (err) {
    showToast(`❌ Lỗi: ${err.message}`, 'error');
  } finally {
    btn.disabled = false;
  }
}

function bindFilterTabs() {
  document.querySelectorAll('[data-filter-tab]').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('[data-filter-tab]').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentFilter = tab.getAttribute('data-filter-tab');
      renderTable(getFilteredRequests());
    });
  });

  const searchEl = document.getElementById('requests-search');
  if (searchEl) {
    searchEl.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim();
      renderTable(getFilteredRequests());
    });
  }
}

function bindRespondModal() {
  const modal = document.getElementById('respond-modal');
  const form = document.getElementById('respond-form');
  if (!modal || !form) return;

  modal.querySelector('.modal-close')?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const text = document.getElementById('respond-text').value.trim();
    if (!text) return;

    submitBtn.disabled = true;
    try {
      await api.updateRequestResponse(respondingRequestId, text);
      showToast('✅ Đã cập nhật phản hồi', 'success');
      modal.classList.remove('active');
      await loadRequests();
    } catch (err) {
      showToast(`❌ ${err.message}`, 'error');
    } finally {
      submitBtn.disabled = false;
    }
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAdmin('/')) return;
  bindFilterTabs();
  bindRespondModal();
  await loadRequests();
});
