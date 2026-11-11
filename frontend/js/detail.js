// detail.js - Product Detail Page

let currentConnector = null;
let qty = 1;

function getStockBadge(inStock, minAlert) {
  if (inStock === 0) return `<span class="badge badge-out">&#9679; Hết hàng</span>`;
  if (inStock <= minAlert) return `<span class="badge badge-low">&#9650; Sắp hết (${inStock})</span>`;
  return `<span class="badge badge-stock">&#10003; Còn hàng</span>`;
}

function renderBreadcrumb(conn) {
  const bc = document.getElementById('breadcrumb');
  if (!bc) return;
  bc.innerHTML = `
    <a href="/">Catalog</a>
    <span style="color:var(--text-dim);margin:0 .5rem">›</span>
    <span style="color:var(--text-muted)">${conn.category_name || 'Uncategorized'}</span>
    <span style="color:var(--text-dim);margin:0 .5rem">›</span>
    <span style="color:#fff">${conn.mfr_part_number}</span>
  `;
}

function renderDetailMain(conn) {
  // Image
  const imgBox = document.getElementById('detail-image-box');
  if (imgBox) {
    imgBox.innerHTML = conn.image_url
      ? `<img src="${conn.image_url}" alt="${conn.description}" onerror="this.parentElement.innerHTML=getConnectorSvg('${conn.mfr_part_number}')">`
      : getConnectorSvg(conn.mfr_part_number);
  }

  // Fields
  const fieldsMap = {
    'field-title': conn.mfr_part_number,
    'field-digikey-pn': conn.digikey_part_number || '—',
    'field-manufacturer': conn.manufacturer,
    'field-mfr-pn': conn.mfr_part_number,
    'field-description': conn.description,
    'field-lead-time': conn.lead_time || '—',
    'field-customer-ref': conn.customer_reference || '—',
    'field-detailed-desc': conn.detailed_description || '—',
  };

  Object.entries(fieldsMap).forEach(([id, val]) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  });

  // Datasheet
  const dsLink = document.getElementById('field-datasheet');
  if (dsLink) {
    if (conn.datasheet_url) {
      dsLink.href = conn.datasheet_url;
      dsLink.style.display = 'inline-flex';
    } else {
      dsLink.style.display = 'none';
    }
  }

  // "New Product" badge logic
  const created = new Date(conn.created_at);
  const now = new Date();
  const ageDays = (now - created) / (1000 * 60 * 60 * 24);
  const newBadge = document.getElementById('new-badge');
  if (newBadge) newBadge.style.display = ageDays < 30 ? 'inline-flex' : 'none';
}

function renderInStockWidget(conn) {
  const stockBox = document.getElementById('stock-status-box');
  const stockVal = document.getElementById('stock-value');
  const stockBadge = document.getElementById('stock-badge');
  const requestBtn = document.getElementById('btn-product-request');

  if (stockVal) stockVal.textContent = conn.in_stock_qty;
  if (stockBadge) stockBadge.innerHTML = getStockBadge(conn.in_stock_qty, conn.min_stock_alert);
  if (stockBox) stockBox.className = `stock-status-box${conn.in_stock_qty <= conn.min_stock_alert ? ' low' : ''}`;

  if (requestBtn) {
    requestBtn.disabled = conn.in_stock_qty === 0;
    requestBtn.textContent = conn.in_stock_qty === 0 ? '🚫 Hết hàng' : '📋 Gửi Yêu Cầu Xuất Kho';
  }
}

function renderAttributes(attrs) {
  const grid = document.getElementById('specs-grid');
  if (!grid) return;
  grid.innerHTML = '';

  // Group by group_name
  const groups = {};
  attrs.forEach(a => {
    const g = a.group_name || 'General';
    if (!groups[g]) groups[g] = [];
    groups[g].push(a);
  });

  const groupOrder = ['Classification', 'General', 'Mechanical', 'Electrical', 'Material', 'Appearance', 'Environmental', 'Status', 'Packaging'];
  const sortedGroups = Object.keys(groups).sort((a, b) => {
    const ia = groupOrder.indexOf(a);
    const ib = groupOrder.indexOf(b);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  sortedGroups.forEach(grpName => {
    groups[grpName].forEach(attr => {
      const row = document.createElement('div');
      row.className = 'specs-row';
      row.innerHTML = `<span class="key">${attr.attr_key}</span><span class="val">${attr.attr_value}</span>`;
      grid.appendChild(row);
    });
  });
}

function bindQuantityStepper(maxQty) {
  qty = 1;
  const input = document.getElementById('qty-input');
  const minusBtn = document.getElementById('qty-minus');
  const plusBtn = document.getElementById('qty-plus');

  if (!input) return;

  function updateInput() {
    input.value = qty;
    if (minusBtn) minusBtn.disabled = qty <= 1;
    if (plusBtn) plusBtn.disabled = qty >= maxQty;
  }

  minusBtn?.addEventListener('click', () => { if (qty > 1) { qty--; updateInput(); } });
  plusBtn?.addEventListener('click', () => { if (qty < maxQty) { qty++; updateInput(); } });
  input.addEventListener('change', () => {
    qty = Math.max(1, Math.min(maxQty, parseInt(input.value) || 1));
    updateInput();
  });

  updateInput();
}

function bindRequestModal(conn) {
  const requestBtn = document.getElementById('btn-product-request');
  const modal = document.getElementById('request-modal');
  const form = document.getElementById('request-form');

  if (!requestBtn || !modal || !form) return;

  requestBtn.addEventListener('click', () => {
    if (!requireLogin()) return;
    document.getElementById('req-modal-pn').textContent = conn.mfr_part_number;
    document.getElementById('req-modal-stock').textContent = conn.in_stock_qty;
    document.getElementById('req-qty').value = qty;
    document.getElementById('req-reason').value = '';
    modal.classList.add('active');
  });

  modal.querySelector('.modal-close')?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    const reqQty = parseInt(document.getElementById('req-qty').value) || 1;
    const reason = document.getElementById('req-reason').value.trim();

    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang gửi...';

    try {
      const result = await api.createRequest(conn.id, reqQty, reason);
      showToast(`✅ Đã gửi yêu cầu ${result.request_code} thành công!`, 'success');
      modal.classList.remove('active');
    } catch (err) {
      showToast(`❌ ${err.message}`, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Xác nhận Gửi Yêu Cầu';
    }
  });
}

async function initDetailPage() {
  const params = new URLSearchParams(window.location.search);
  const id = params.get('id');

  if (!id) {
    document.body.innerHTML = '<div style="text-align:center;padding:5rem;color:var(--text-muted)"><h2>Không tìm thấy sản phẩm.</h2><a href="/" class="btn btn-primary" style="margin-top:1rem">← Về Catalog</a></div>';
    return;
  }

  try {
    currentConnector = await api.getConnectorDetail(id);
    document.title = `${currentConnector.mfr_part_number} | Connector Inventory`;

    renderBreadcrumb(currentConnector);
    renderDetailMain(currentConnector);
    renderInStockWidget(currentConnector);
    renderAttributes(currentConnector.attributes || []);
    bindQuantityStepper(currentConnector.in_stock_qty);
    bindRequestModal(currentConnector);
  } catch (err) {
    console.error('initDetailPage error:', err);
    document.getElementById('main-content')?.insertAdjacentHTML('afterbegin',
      `<div style="padding:2rem;color:var(--danger)">⚠️ Không thể tải thông tin linh kiện.</div>`);
  }
}

document.addEventListener('DOMContentLoaded', initDetailPage);
