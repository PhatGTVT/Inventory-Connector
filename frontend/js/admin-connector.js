// admin-connector.js - Admin CRUD for connectors

let categories = [];
let editingConnectorId = null;
let connectorList = [];

function renderConnectorRows(connectors) {
  const tbody = document.getElementById('manage-tbody');
  if (!tbody) return;
  tbody.innerHTML = '';

  if (!connectors.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:3rem;color:var(--text-muted)">Chưa có linh kiện nào.</td></tr>`;
    return;
  }

  connectors.forEach(conn => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div style="width:50px;height:50px;background:#0f172a;border-radius:8px;display:flex;align-items:center;justify-content:center;overflow:hidden">
          ${conn.image_url
            ? `<img src="${conn.image_url}" style="max-width:48px;max-height:48px;object-fit:contain" onerror="this.style.display='none'">`
            : `<span style="font-size:1.5rem">🔌</span>`}
        </div>
      </td>
      <td>
        <div style="font-weight:700;color:var(--accent-cyan)">${conn.mfr_part_number}</div>
        <div style="font-size:0.78rem;color:var(--text-muted)">${conn.digikey_part_number || '—'}</div>
      </td>
      <td style="color:#fff;font-weight:500">${conn.manufacturer}</td>
      <td style="color:#60a5fa;font-weight:600;font-size:0.85rem">
        <i class="bi bi-geo-alt" style="font-size:0.8rem"></i> ${conn.location || 'Kệ A1'}
      </td>
      <td style="text-align:center">
        <span class="${conn.in_stock_qty === 0 ? 'badge badge-out' : conn.in_stock_qty <= conn.min_stock_alert ? 'badge badge-low' : 'badge badge-stock'}">${conn.in_stock_qty}</span>
      </td>
      <td style="color:var(--text-muted);font-size:0.85rem">${conn.category_name || '—'}</td>
      <td>
        <div class="action-buttons-group">
          <button class="btn btn-outline btn-sm" data-action="edit" data-id="${conn.id}">✏️ Sửa</button>
          <button class="btn btn-sm" style="background:rgba(239,68,68,0.15);color:#f87171;border:1px solid rgba(239,68,68,0.3)" data-action="del" data-id="${conn.id}">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const action = btn.getAttribute('data-action');
      const id = parseInt(btn.getAttribute('data-id'));
      if (action === 'edit') {
        const conn = connectorList.find(c => c.id === id);
        if (conn) openConnectorForm(conn);
      } else if (action === 'del') {
        const conn = connectorList.find(c => c.id === id);
        if (!confirm(`Xóa connector "${conn?.mfr_part_number}"? Thao tác này không thể hoàn tác.`)) return;
        try {
          await api.deleteConnector(id);
          showToast('Đã xóa connector', 'success');
          loadConnectors();
        } catch (err) {
          showToast(`❌ ${err.message}`, 'error');
        }
      }
    });
  });
}

async function loadConnectors() {
  try {
    connectorList = await api.getConnectors({ limit: 200 });
    renderConnectorRows(connectorList);
    document.getElementById('manage-count').textContent = `${connectorList.length} linh kiện`;
  } catch (err) {
    showToast('Lỗi khi tải danh sách', 'error');
  }
}

async function loadCategories() {
  try {
    categories = await api.getCategories();
    const sel = document.getElementById('form-category');
    if (!sel) return;
    sel.innerHTML = '<option value="">-- Không chọn danh mục --</option>';
    categories.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      sel.appendChild(opt);
    });
  } catch (err) {
    console.error(err);
  }
}

// Attribute list in form
let formAttributes = [];

function renderFormAttributes() {
  const container = document.getElementById('form-attributes-list');
  if (!container) return;
  container.innerHTML = '';
  formAttributes.forEach((attr, idx) => {
    const row = document.createElement('div');
    row.className = 'attr-row';
    row.style.cssText = 'display:grid;grid-template-columns:1fr 1fr auto;gap:0.5rem;margin-bottom:0.5rem;align-items:center';
    row.innerHTML = `
      <input type="text" class="filter-select" placeholder="Tên thuộc tính" value="${attr.attr_key}" data-attr-key="${idx}">
      <input type="text" class="filter-select" placeholder="Giá trị" value="${attr.attr_value}" data-attr-val="${idx}">
      <button type="button" class="btn btn-sm" style="background:rgba(239,68,68,0.2);color:#f87171;border:1px solid rgba(239,68,68,0.3);width:36px" data-remove="${idx}">✕</button>
    `;
    container.appendChild(row);
  });

  container.querySelectorAll('[data-attr-key]').forEach(el => {
    el.addEventListener('input', (e) => {
      formAttributes[parseInt(el.getAttribute('data-attr-key'))].attr_key = e.target.value;
    });
  });
  container.querySelectorAll('[data-attr-val]').forEach(el => {
    el.addEventListener('input', (e) => {
      formAttributes[parseInt(el.getAttribute('data-attr-val'))].attr_value = e.target.value;
    });
  });
  container.querySelectorAll('[data-remove]').forEach(el => {
    el.addEventListener('click', () => {
      formAttributes.splice(parseInt(el.getAttribute('data-remove')), 1);
      renderFormAttributes();
    });
  });
}

function openConnectorForm(conn = null) {
  const modal = document.getElementById('connector-form-modal');
  const form = document.getElementById('connector-form');
  const title = document.getElementById('form-title');
  if (!modal) return;

  editingConnectorId = conn ? conn.id : null;
  if (title) title.textContent = conn ? `Sửa: ${conn.mfr_part_number}` : 'Thêm Connector Mới';

  function setImagePreview(url, name = 'Ảnh linh kiện') {
    const promptEl = document.getElementById('dropzone-prompt');
    const previewEl = document.getElementById('dropzone-preview');
    const previewImg = document.getElementById('preview-img');
    const filenameEl = document.getElementById('preview-filename');
    const hiddenUrl = document.getElementById('form-image-url');

    if (url) {
      hiddenUrl.value = url;
      previewImg.src = url;
      filenameEl.textContent = name;
      previewEl.style.display = 'flex';
      promptEl.style.display = 'none';
    } else {
      hiddenUrl.value = '';
      previewImg.src = '';
      filenameEl.textContent = '';
      previewEl.style.display = 'none';
      promptEl.style.display = 'block';
    }
  }

  if (conn) {
    document.getElementById('form-mpn').value = conn.mfr_part_number || '';
    document.getElementById('form-digikey-pn').value = conn.digikey_part_number || '';
    document.getElementById('form-manufacturer').value = conn.manufacturer || '';
    document.getElementById('form-desc').value = conn.description || '';
    document.getElementById('form-detail-desc').value = conn.detailed_description || '';
    document.getElementById('form-lead-time').value = conn.lead_time || '';
    document.getElementById('form-datasheet-url').value = conn.datasheet_url || '';
    document.getElementById('form-stock').value = conn.in_stock_qty || 0;
    document.getElementById('form-min-stock').value = conn.min_stock_alert || 5;
    document.getElementById('form-category').value = conn.category_id || '';
    formAttributes = (conn.attributes || []).map(a => ({ ...a }));
    setImagePreview(conn.image_url, conn.image_url ? conn.image_url.split('/').pop() : '');
  } else {
    form.reset();
    document.getElementById('form-min-stock').value = 5;
    formAttributes = [];
    setImagePreview(null);
  }

  renderFormAttributes();
  modal.classList.add('active');
}

function bindConnectorForm() {
  const modal = document.getElementById('connector-form-modal');
  const form = document.getElementById('connector-form');
  if (!modal || !form) return;

  modal.querySelector('.modal-close')?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', e => { if (e.target === modal) modal.classList.remove('active'); });

  document.getElementById('btn-add-connector')?.addEventListener('click', () => openConnectorForm());

  // Image Dropzone Handling
  const dropzone = document.getElementById('image-dropzone');
  const fileInput = document.getElementById('form-image-file');
  const btnBrowse = document.getElementById('btn-browse-file');
  const btnRemoveImg = document.getElementById('btn-remove-image');

  async function handleFile(file) {
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      showToast('❌ Chỉ được chọn tệp hình ảnh (.png, .jpg, .webp)', 'error');
      return;
    }
    const statusEl = document.getElementById('preview-status');
    const promptEl = document.getElementById('dropzone-prompt');
    const previewEl = document.getElementById('dropzone-preview');
    const previewImg = document.getElementById('preview-img');
    const filenameEl = document.getElementById('preview-filename');

    // Local instant preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      filenameEl.textContent = file.name;
      statusEl.textContent = '⏳ Đang tải lên máy chủ...';
      statusEl.style.color = 'var(--warning)';
      promptEl.style.display = 'none';
      previewEl.style.display = 'flex';
    };
    reader.readAsDataURL(file);

    try {
      const res = await api.uploadImage(file);
      document.getElementById('form-image-url').value = res.url;
      statusEl.textContent = '✅ Đã tải lên máy chủ';
      statusEl.style.color = 'var(--success)';
      showToast('✅ Đã tải ảnh lên thành công', 'success');
    } catch (err) {
      statusEl.textContent = '❌ Lỗi tải ảnh';
      statusEl.style.color = 'var(--danger)';
      showToast(`❌ ${err.message}`, 'error');
    }
  }

  btnBrowse?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput?.click();
  });

  dropzone?.addEventListener('click', (e) => {
    if (e.target.closest('#btn-remove-image') || e.target.closest('#dropzone-preview')) return;
    fileInput?.click();
  });

  fileInput?.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFile(fileInput.files[0]);
    }
  });

  dropzone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('drag-over');
  });

  dropzone?.addEventListener('dragleave', () => {
    dropzone.classList.remove('drag-over');
  });

  dropzone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('drag-over');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  btnRemoveImg?.addEventListener('click', (e) => {
    e.stopPropagation();
    document.getElementById('form-image-url').value = '';
    document.getElementById('form-image-file').value = '';
    document.getElementById('preview-img').src = '';
    document.getElementById('dropzone-preview').style.display = 'none';
    document.getElementById('dropzone-prompt').style.display = 'block';
  });

  document.getElementById('btn-add-attr')?.addEventListener('click', () => {
    formAttributes.push({ attr_key: '', attr_value: '', group_name: 'General' });
    renderFormAttributes();
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang lưu...';

    const rawMpn = document.getElementById('form-mpn').value.trim();
    const rawDk = document.getElementById('form-digikey-pn').value.trim();
    const rawDesc = document.getElementById('form-desc').value.trim();
    const rawMfr = document.getElementById('form-manufacturer').value.trim();

    const payload = {
      mfr_part_number: rawMpn,
      digikey_part_number: rawDk || null,
      manufacturer: rawMfr,
      description: rawDesc,
      detailed_description: document.getElementById('form-detail-desc').value.trim() || null,
      lead_time: document.getElementById('form-lead-time').value.trim() || null,
      image_url: document.getElementById('form-image-url').value.trim() || null,
      datasheet_url: document.getElementById('form-datasheet-url').value.trim() || null,
      in_stock_qty: parseInt(document.getElementById('form-stock').value) || 0,
      min_stock_alert: parseInt(document.getElementById('form-min-stock').value) || 5,
      category_id: parseInt(document.getElementById('form-category').value) || null,
      attributes: formAttributes.filter(a => a.attr_key && a.attr_value),
    };

    try {
      if (editingConnectorId) {
        await api.updateConnector(editingConnectorId, payload);
        showToast('✅ Đã cập nhật connector', 'success');
      } else {
        await api.createConnector(payload);
        showToast('✅ Đã thêm connector mới', 'success');
      }
      modal.classList.remove('active');
      loadConnectors();
    } catch (err) {
      showToast(`❌ ${err.message}`, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Lưu Connector';
    }
  });
}

// ================= MODAL THÊM TỪ THƯ VIỆN VÀO KHO =================
function initLibraryPicker() {
  const modal = document.getElementById('modal-add-from-lib');
  const btnOpen = document.getElementById('btn-add-from-lib');
  const btnClose = document.getElementById('close-add-lib-modal');
  const btnCancel = document.getElementById('btn-cancel-picker');
  const searchInput = document.getElementById('lib-picker-search');
  const resultsContainer = document.getElementById('lib-picker-results');
  const selectedBox = document.getElementById('lib-picker-selected');
  const submitBtn = document.getElementById('btn-submit-picker');
  const form = document.getElementById('form-stock-in-from-lib');

  if (!modal) return;

  function resetPicker() {
    if (searchInput) searchInput.value = '';
    if (resultsContainer) {
      resultsContainer.innerHTML = '';
      resultsContainer.style.display = 'none';
    }
    if (selectedBox) selectedBox.style.display = 'none';
    document.getElementById('picker-selected-id').value = '';
    document.getElementById('picker-stock-qty').value = '10';
    document.getElementById('picker-location').value = 'Kệ A1';
    document.getElementById('picker-min-alert').value = '5';
    if (submitBtn) submitBtn.disabled = true;
  }

  btnOpen?.addEventListener('click', () => {
    resetPicker();
    modal.classList.add('active');
    setTimeout(() => searchInput?.focus(), 100);
    searchAndRenderLibrary('');
  });

  btnClose?.addEventListener('click', () => modal.classList.remove('active'));
  btnCancel?.addEventListener('click', () => modal.classList.remove('active'));
  modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });

  let debounceTimer;
  searchInput?.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      searchAndRenderLibrary(searchInput.value.trim());
    }, 250);
  });

  async function searchAndRenderLibrary(q) {
    if (!resultsContainer) return;
    try {
      const items = await api.getLibrary({ q, limit: 20 });
      if (!items.length) {
        resultsContainer.innerHTML = '<div style="padding:1rem;color:var(--text-muted);text-align:center;font-size:0.85rem">Không tìm thấy linh kiện nào trong Thư viện.</div>';
        resultsContainer.style.display = 'block';
        return;
      }

      resultsContainer.innerHTML = items.map(item => `
        <div class="lib-picker-item" data-lib-id="${item.id}" style="padding:0.6rem 0.85rem;border-bottom:1px solid var(--border-color);display:flex;align-items:center;gap:0.75rem;cursor:pointer;transition:background 0.15s">
          <div style="width:36px;height:36px;border-radius:4px;overflow:hidden;background:#020617;display:flex;align-items:center;justify-content:center;flex-shrink:0">
            ${item.image_url ? `<img src="${item.image_url}" style="max-width:32px;max-height:32px;object-fit:contain" onerror="this.outerHTML=getConnectorSvg('${item.mfr_part_number}')" />` : getConnectorSvg(item.mfr_part_number)}
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-weight:700;color:var(--text-main);font-size:0.88rem">${item.mfr_part_number}</div>
            <div style="font-size:0.75rem;color:var(--text-muted)">${item.manufacturer} • ${item.description || ''}</div>
          </div>
          <div>
            ${item.in_warehouse 
              ? `<span style="font-size:0.72rem;background:rgba(59,130,246,0.15);color:#60a5fa;padding:0.2rem 0.5rem;border-radius:12px;font-weight:600">Trong kho (${item.warehouse_stock_qty})</span>` 
              : `<span style="font-size:0.72rem;background:rgba(148,163,184,0.12);color:var(--text-muted);padding:0.2rem 0.5rem;border-radius:12px">Chưa có</span>`}
          </div>
        </div>
      `).join('');

      resultsContainer.style.display = 'block';

      resultsContainer.querySelectorAll('.lib-picker-item').forEach(el => {
        el.addEventListener('mouseenter', () => el.style.background = 'rgba(59,130,246,0.1)');
        el.addEventListener('mouseleave', () => el.style.background = 'transparent');
        el.addEventListener('click', () => {
          const id = parseInt(el.getAttribute('data-lib-id'));
          const selected = items.find(i => i.id === id);
          if (selected) selectLibraryItem(selected);
        });
      });
    } catch (err) {
      console.error(err);
    }
  }

  function selectLibraryItem(item) {
    document.getElementById('picker-selected-id').value = item.id;
    document.getElementById('picker-item-mpn').textContent = item.mfr_part_number;
    document.getElementById('picker-item-desc').textContent = `${item.manufacturer} • ${item.description || ''}`;

    const imgEl = document.getElementById('picker-item-img');
    if (imgEl) {
      imgEl.innerHTML = item.image_url 
        ? `<img src="${item.image_url}" style="width:100%;height:100%;object-fit:contain" onerror="this.outerHTML=getConnectorSvg('${item.mfr_part_number}')" />` 
        : getConnectorSvg(item.mfr_part_number);
    }

    const alertEl = document.getElementById('picker-item-alert');
    if (alertEl) {
      if (item.in_warehouse) {
        alertEl.innerHTML = `<span style="color:#60a5fa"><i class="bi bi-info-circle"></i> Linh kiện này đã có trong kho (${item.warehouse_stock_qty} cái). Thao tác này sẽ cộng dồn số lượng.</span>`;
      } else {
        alertEl.innerHTML = `<span style="color:#34d399"><i class="bi bi-check-circle"></i> Chưa có trong kho. Sẽ tạo mới vị trí lưu kho.</span>`;
      }
    }

    selectedBox.style.display = 'block';
    resultsContainer.style.display = 'none';
    submitBtn.disabled = false;
  }

  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const libId = parseInt(document.getElementById('picker-selected-id').value);
    const qty = parseInt(document.getElementById('picker-stock-qty').value);
    const loc = document.getElementById('picker-location').value.trim();
    const minAlert = parseInt(document.getElementById('picker-min-alert').value);

    if (!libId) {
      showToast('Vui lòng chọn một linh kiện từ Thư viện', 'warning');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang nhập...';

    try {
      await api.importFromLibraryToStock({
        library_id: libId,
        quantity: qty,
        location: loc,
        min_stock_alert: minAlert
      });

      showToast('Đã nhập linh kiện từ Thư viện vào Kho thành công! 🎉', 'success');
      modal.classList.remove('active');
      await loadConnectors();
    } catch (err) {
      showToast(`❌ ${err.message}`, 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Xác Nhận Nhập Kho';
    }
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAdmin('/')) return;
  await Promise.all([loadCategories(), loadConnectors()]);
  bindConnectorForm();
  initLibraryPicker();

  // Search filter
  document.getElementById('manage-search')?.addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase().trim();
    const filtered = q ? connectorList.filter(c =>
      c.mfr_part_number.toLowerCase().includes(q) ||
      c.manufacturer.toLowerCase().includes(q) ||
      (c.location && c.location.toLowerCase().includes(q)) ||
      c.description.toLowerCase().includes(q)
    ) : connectorList;
    renderConnectorRows(filtered);
  });
});
