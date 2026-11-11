// admin-library.js - Master Library Management Logic

let libraryItems = [];
let categoriesList = [];
let selectedExcelFile = null;

document.addEventListener('DOMContentLoaded', async () => {
  renderNavAuth();
  
  const user = api.getCurrentUser();
  if (!user) {
    showToast('Vui lòng đăng nhập với quyền Admin để truy cập Thư viện', 'warning');
    setTimeout(() => {
      document.getElementById('login-modal')?.classList.add('active');
    }, 200);
    return;
  }
  
  if (user.role !== 'admin') {
    showToast('Tài khoản của bạn không có quyền truy cập Thư viện (Chỉ dành cho Admin)', 'error');
    setTimeout(() => {
      window.location.href = '/';
    }, 1500);
    return;
  }

  await loadCategories();
  await loadLibraryData();

  initEventHandlers();
  initExcelDropzone();
  initImageDropzone();
});

// Load Categories
async function loadCategories() {
  try {
    categoriesList = await api.getCategories();
    const filterCat = document.getElementById('lib-filter-cat');
    const formCat = document.getElementById('lib-form-cat');

    if (filterCat) {
      filterCat.innerHTML = '<option value="">Tất cả danh mục</option>' +
        categoriesList.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }
    if (formCat) {
      formCat.innerHTML = '<option value="">-- Chọn danh mục --</option>' +
        categoriesList.map(c => `<option value="${c.id}">${c.name}</option>`).join('');
    }
  } catch (err) {
    console.error('Error loading categories:', err);
  }
}

// Load Library Data
async function loadLibraryData() {
  const spinner = document.getElementById('table-spinner');
  const tbody = document.getElementById('lib-table-body');
  const emptyState = document.getElementById('empty-state');

  if (spinner) spinner.style.display = 'block';
  if (tbody) tbody.innerHTML = '';
  if (emptyState) emptyState.style.display = 'none';

  try {
    const q = document.getElementById('lib-search')?.value.trim() || '';
    const category_id = document.getElementById('lib-filter-cat')?.value || '';
    const manufacturer = document.getElementById('lib-filter-mfr')?.value || '';

    libraryItems = await api.getLibrary({ q, category_id, manufacturer });

    updateStats(libraryItems);
    updateManufacturerDropdown(libraryItems);
    renderLibraryTable(libraryItems);
  } catch (err) {
    showToast(err.message || 'Lỗi tải dữ liệu thư viện', 'error');
  } finally {
    if (spinner) spinner.style.display = 'none';
  }
}

// Update KPI Stats
function updateStats(items) {
  const totalEl = document.getElementById('stat-total-lib');
  const inWhEl = document.getElementById('stat-in-wh');
  const notInWhEl = document.getElementById('stat-not-in-wh');
  const mfrsEl = document.getElementById('stat-mfrs');

  const total = items.length;
  const inWh = items.filter(i => i.in_warehouse).length;
  const notInWh = total - inWh;
  const mfrs = new Set(items.map(i => i.manufacturer).filter(Boolean)).size;

  if (totalEl) totalEl.textContent = total;
  if (inWhEl) inWhEl.textContent = inWh;
  if (notInWhEl) notInWhEl.textContent = notInWh;
  if (mfrsEl) mfrsEl.textContent = mfrs;
}

// Populate Manufacturer Filter
function updateManufacturerDropdown(items) {
  const select = document.getElementById('lib-filter-mfr');
  if (!select) return;

  const currentVal = select.value;
  const uniqueMfrs = Array.from(new Set(items.map(i => i.manufacturer).filter(Boolean))).sort();

  select.innerHTML = '<option value="">Tất cả nhà sản xuất</option>' +
    uniqueMfrs.map(m => `<option value="${m}" ${m === currentVal ? 'selected' : ''}>${m}</option>`).join('');
}

// Render Table
function renderLibraryTable(items) {
  const tbody = document.getElementById('lib-table-body');
  const emptyState = document.getElementById('empty-state');
  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = '';
    if (emptyState) emptyState.style.display = 'block';
    return;
  }

  if (emptyState) emptyState.style.display = 'none';

  tbody.innerHTML = items.map(item => {
    const imgHtml = item.image_url
      ? `<img src="${item.image_url}" alt="${item.mfr_part_number}" style="width:40px;height:40px;object-fit:contain;border-radius:var(--radius-sm);background:rgba(255,255,255,0.03)" onerror="this.outerHTML=getConnectorSvg('${item.mfr_part_number}')" />`
      : `<div style="width:40px;height:40px">${getConnectorSvg(item.mfr_part_number)}</div>`;

    const statusBadge = item.in_warehouse
      ? `<span class="badge-in-wh"><i class="bi bi-check2"></i> Có trong kho (${item.warehouse_stock_qty} cái)</span>`
      : `<span class="badge-not-in-wh"><i class="bi bi-dash-circle"></i> Chưa nhập kho</span>`;

    return `
      <tr>
        <td style="vertical-align:middle;padding:0.75rem 0.5rem 0.75rem 1rem">${imgHtml}</td>
        <td>
          <div style="font-weight:700;color:var(--text-main);font-size:0.95rem">${item.mfr_part_number}</div>
          ${item.digikey_part_number ? `<div style="font-size:0.75rem;color:var(--text-muted);font-family:var(--font-mono)">${item.digikey_part_number}</div>` : ''}
        </td>
        <td><span style="font-weight:600;color:#93c5fd">${item.manufacturer}</span></td>
        <td><span style="font-size:0.82rem;color:var(--text-muted)">${item.category_name || '—'}</span></td>
        <td style="max-width:280px">
          <div style="font-size:0.83rem;color:var(--text-main);line-height:1.35">${item.description}</div>
          ${item.datasheet_url ? `<a href="${item.datasheet_url}" target="_blank" style="font-size:0.75rem;color:var(--accent-primary);display:inline-flex;align-items:center;gap:0.25rem;margin-top:0.2rem"><i class="bi bi-file-earmark-pdf"></i> Datasheet</a>` : ''}
        </td>
        <td>${statusBadge}</td>
        <td style="text-align:right">
          <div style="display:flex;gap:0.4rem;justify-content:flex-end;align-items:center">
            <button class="btn btn-sm ${item.in_warehouse ? 'btn-secondary' : 'btn-primary'}" onclick="openStockInModal(${item.id})" title="Nhập vào kho hàng">
              <i class="bi bi-box-arrow-in-down"></i> ${item.in_warehouse ? 'Cộng thêm' : 'Nhập vào Kho'}
            </button>
            <button class="btn btn-secondary btn-sm" onclick="openEditModal(${item.id})" title="Chỉnh sửa thông số">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-danger btn-sm" onclick="deleteItem(${item.id})" title="Xóa khỏi thư viện">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

// Event Handlers
function initEventHandlers() {
  const searchInput = document.getElementById('lib-search');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => loadLibraryData(), 300);
    });
  }

  document.getElementById('lib-filter-cat')?.addEventListener('change', () => loadLibraryData());
  document.getElementById('lib-filter-mfr')?.addEventListener('change', () => loadLibraryData());

  // Template download
  document.getElementById('btn-download-template')?.addEventListener('click', () => {
    window.location.href = '/api/library/template';
  });

  // Excel Modal
  document.getElementById('btn-open-excel-modal')?.addEventListener('click', () => {
    document.getElementById('excel-modal')?.classList.add('active');
    resetExcelForm();
  });
  document.getElementById('close-excel-modal')?.addEventListener('click', () => {
    document.getElementById('excel-modal')?.classList.remove('active');
  });
  document.getElementById('btn-cancel-excel')?.addEventListener('click', () => {
    document.getElementById('excel-modal')?.classList.remove('active');
  });

  // Create Modal
  document.getElementById('btn-open-create-modal')?.addEventListener('click', () => {
    openCreateModal();
  });
  document.getElementById('close-lib-modal')?.addEventListener('click', () => {
    document.getElementById('library-modal')?.classList.remove('active');
  });
  document.getElementById('btn-cancel-lib')?.addEventListener('click', () => {
    document.getElementById('library-modal')?.classList.remove('active');
  });

  // Stock In Modal
  document.getElementById('close-stock-modal')?.addEventListener('click', () => {
    document.getElementById('stock-in-modal')?.classList.remove('active');
  });
  document.getElementById('btn-cancel-stock')?.addEventListener('click', () => {
    document.getElementById('stock-in-modal')?.classList.remove('active');
  });

  // Form Submissions
  document.getElementById('library-form')?.addEventListener('submit', handleSaveLibraryItem);
  document.getElementById('stock-in-form')?.addEventListener('submit', handleStockInSubmit);
  document.getElementById('btn-submit-excel')?.addEventListener('click', handleExcelUpload);
}

// ================= EXCEL DROPZONE & IMPORT =================
function initExcelDropzone() {
  const dropzone = document.getElementById('excel-dropzone');
  const fileInput = document.getElementById('excel-file-input');
  const btnChange = document.getElementById('btn-change-excel');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('#btn-change-excel')) return;
    fileInput.click();
  });

  btnChange?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleSelectedExcelFile(files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleSelectedExcelFile(e.target.files[0]);
    }
  });
}

function handleSelectedExcelFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['xlsx', 'xls', 'csv'].includes(ext)) {
    showToast('Chỉ chấp nhận tệp định dạng .xlsx, .xls hoặc .csv', 'error');
    return;
  }

  selectedExcelFile = file;
  document.getElementById('excel-drop-prompt').style.display = 'none';
  document.getElementById('excel-file-info').style.display = 'block';
  document.getElementById('excel-file-name').textContent = file.name;
  document.getElementById('excel-file-size').textContent = `${(file.size / 1024).toFixed(1)} KB`;
  document.getElementById('btn-submit-excel').removeAttribute('disabled');
}

function resetExcelForm() {
  selectedExcelFile = null;
  const fileInput = document.getElementById('excel-file-input');
  if (fileInput) fileInput.value = '';
  document.getElementById('excel-drop-prompt').style.display = 'block';
  document.getElementById('excel-file-info').style.display = 'none';
  document.getElementById('excel-result-box').style.display = 'none';
  document.getElementById('btn-submit-excel')?.setAttribute('disabled', 'true');
}

async function handleExcelUpload() {
  if (!selectedExcelFile) return;

  const btnSubmit = document.getElementById('btn-submit-excel');
  const resultBox = document.getElementById('excel-result-box');
  const summaryEl = document.getElementById('excel-result-summary');
  const errorsEl = document.getElementById('excel-result-errors');

  btnSubmit.disabled = true;
  btnSubmit.innerHTML = '<span class="spinner" style="width:16px;height:16px;display:inline-block;vertical-align:middle;margin-right:0.4rem"></span> Đang nạp dữ liệu...';

  try {
    const res = await api.importLibraryExcel(selectedExcelFile);
    resultBox.style.display = 'block';

    summaryEl.innerHTML = `
      <span style="color:#34d399">✓ Nạp thành công: ${res.success_count} linh kiện mới</span> | 
      <span style="color:#60a5fa">Cập nhật: ${res.updated_count}</span> | 
      <span style="color:${res.error_count > 0 ? '#f87171' : 'var(--text-muted)'}">Lỗi: ${res.error_count}</span>
    `;

    if (res.errors && res.errors.length > 0) {
      errorsEl.innerHTML = res.errors.map(err => `<div>• ${err}</div>`).join('');
      errorsEl.style.display = 'block';
    } else {
      errorsEl.innerHTML = '';
      errorsEl.style.display = 'none';
    }

    showToast(`Đã nạp xong file Excel (${res.success_count} mới, ${res.updated_count} cập nhật)`, 'success');
    await loadLibraryData();
  } catch (err) {
    showToast(err.message || 'Lỗi khi nhập file Excel', 'error');
  } finally {
    btnSubmit.disabled = false;
    btnSubmit.innerHTML = '<i class="bi bi-upload"></i> Bắt Đầu Nhập';
  }
}

// ================= IMAGE DROPZONE =================
function initImageDropzone() {
  const dropzone = document.getElementById('lib-image-dropzone');
  const fileInput = document.getElementById('lib-image-file-input');
  const btnChange = document.getElementById('btn-change-lib-img');
  const btnRemove = document.getElementById('btn-remove-lib-img');

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener('click', (e) => {
    if (e.target.closest('#btn-change-lib-img') || e.target.closest('#btn-remove-lib-img')) return;
    fileInput.click();
  });

  btnChange?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  btnRemove?.addEventListener('click', (e) => {
    e.stopPropagation();
    clearLibImage();
  });

  ['dragenter', 'dragover'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });
  });

  ['dragleave', 'drop'].forEach(name => {
    dropzone.addEventListener(name, (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
    });
  });

  dropzone.addEventListener('drop', async (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await uploadLibImageFile(files[0]);
    }
  });

  fileInput.addEventListener('change', async (e) => {
    if (e.target.files.length > 0) {
      await uploadLibImageFile(e.target.files[0]);
    }
  });
}

async function uploadLibImageFile(file) {
  try {
    showToast('Đang tải ảnh lên...', 'info');
    const res = await api.uploadImage(file);
    setLibImagePreview(res.url);
    showToast('Tải ảnh thành công!', 'success');
  } catch (err) {
    showToast(err.message || 'Lỗi tải ảnh', 'error');
  }
}

function setLibImagePreview(url) {
  document.getElementById('lib-form-image-url').value = url;
  document.getElementById('lib-preview-img').src = url;
  document.getElementById('lib-drop-prompt').style.display = 'none';
  document.getElementById('lib-drop-preview').style.display = 'block';
}

function clearLibImage() {
  document.getElementById('lib-form-image-url').value = '';
  document.getElementById('lib-preview-img').src = '';
  document.getElementById('lib-drop-prompt').style.display = 'block';
  document.getElementById('lib-drop-preview').style.display = 'none';
  const fileInput = document.getElementById('lib-image-file-input');
  if (fileInput) fileInput.value = '';
}

// ================= MODAL CREATE / EDIT =================
function openCreateModal() {
  document.getElementById('library-form').reset();
  document.getElementById('lib-form-id').value = '';
  document.getElementById('library-modal-title').textContent = 'Thêm Connector Vào Thư Viện';
  clearLibImage();
  document.getElementById('library-modal').classList.add('active');
}

function openEditModal(id) {
  const item = libraryItems.find(i => i.id === id);
  if (!item) return;

  document.getElementById('lib-form-id').value = item.id;
  document.getElementById('lib-form-mpn').value = item.mfr_part_number;
  document.getElementById('lib-form-digikey').value = item.digikey_part_number || '';
  document.getElementById('lib-form-mfr').value = item.manufacturer;
  document.getElementById('lib-form-cat').value = item.category_id || '';
  document.getElementById('lib-form-desc').value = item.description;
  document.getElementById('lib-form-detail').value = item.detailed_description || '';
  document.getElementById('lib-form-datasheet').value = item.datasheet_url || '';
  document.getElementById('lib-form-lead').value = item.lead_time || 'Immediate / In Stock';

  if (item.image_url) {
    setLibImagePreview(item.image_url);
  } else {
    clearLibImage();
  }

  document.getElementById('library-modal-title').textContent = `Chỉnh Sửa Connector (${item.mfr_part_number})`;
  document.getElementById('library-modal').classList.add('active');
}

async function handleSaveLibraryItem(e) {
  e.preventDefault();
  const id = document.getElementById('lib-form-id').value;

  const payload = {
    mfr_part_number: document.getElementById('lib-form-mpn').value.trim(),
    digikey_part_number: document.getElementById('lib-form-digikey').value.trim() || null,
    manufacturer: document.getElementById('lib-form-mfr').value.trim(),
    category_id: document.getElementById('lib-form-cat').value ? parseInt(document.getElementById('lib-form-cat').value) : null,
    description: document.getElementById('lib-form-desc').value.trim(),
    detailed_description: document.getElementById('lib-form-detail').value.trim() || null,
    datasheet_url: document.getElementById('lib-form-datasheet').value.trim() || null,
    lead_time: document.getElementById('lib-form-lead').value.trim() || 'Immediate / In Stock',
    image_url: document.getElementById('lib-form-image-url').value.trim() || null
  };

  try {
    if (id) {
      await api.updateLibraryItem(id, payload);
      showToast('Cập nhật thông tin thư viện thành công!', 'success');
    } else {
      await api.createLibraryItem(payload);
      showToast('Thêm linh kiện vào Thư viện thành công!', 'success');
    }

    document.getElementById('library-modal').classList.remove('active');
    await loadLibraryData();
  } catch (err) {
    showToast(err.message || 'Lỗi khi lưu linh kiện', 'error');
  }
}

async function deleteItem(id) {
  const item = libraryItems.find(i => i.id === id);
  if (!item) return;

  if (item.in_warehouse) {
    showToast(`Không thể xóa '${item.mfr_part_number}' vì đang tồn tại trong Kho hàng (${item.warehouse_stock_qty} cái). Vui lòng xóa khỏi Kho trước.`, 'error');
    return;
  }

  if (!confirm(`Bạn có chắc chắn muốn xóa linh kiện '${item.mfr_part_number}' khỏi Thư viện?`)) return;

  try {
    await api.deleteLibraryItem(id);
    showToast('Đã xóa linh kiện khỏi Thư viện', 'success');
    await loadLibraryData();
  } catch (err) {
    showToast(err.message || 'Lỗi khi xóa linh kiện', 'error');
  }
}

// ================= MODAL NHẬP VÀO KHO =================
function openStockInModal(id) {
  const item = libraryItems.find(i => i.id === id);
  if (!item) return;

  document.getElementById('stock-lib-id').value = item.id;
  document.getElementById('stock-item-mpn').textContent = item.mfr_part_number;
  document.getElementById('stock-item-mfr').textContent = `${item.manufacturer} • ${item.category_name || 'Chưa phân loại'}`;

  const imgContainer = document.getElementById('stock-item-img');
  if (item.image_url) {
    imgContainer.innerHTML = `<img src="${item.image_url}" alt="${item.mfr_part_number}" style="width:100%;height:100%;object-fit:contain" />`;
  } else {
    imgContainer.innerHTML = getConnectorSvg(item.mfr_part_number);
  }

  const alertEl = document.getElementById('stock-item-status-alert');
  if (item.in_warehouse) {
    alertEl.innerHTML = `<span style="color:#60a5fa"><i class="bi bi-info-circle"></i> Đang có trong kho (${item.warehouse_stock_qty} cái). Thao tác này sẽ <b>cộng thêm tồn kho</b>.</span>`;
  } else {
    alertEl.innerHTML = `<span style="color:#34d399"><i class="bi bi-plus-circle"></i> Chưa có trong kho. Thao tác này sẽ <b>tạo mới vị trí lưu kho</b>.</span>`;
  }

  document.getElementById('stock-qty').value = '10';
  document.getElementById('stock-location').value = 'Kệ A1';
  document.getElementById('stock-min').value = '5';

  document.getElementById('stock-in-modal').classList.add('active');
}

async function handleStockInSubmit(e) {
  e.preventDefault();
  const libId = parseInt(document.getElementById('stock-lib-id').value);
  const qty = parseInt(document.getElementById('stock-qty').value);
  const loc = document.getElementById('stock-location').value.trim();
  const minStock = parseInt(document.getElementById('stock-min').value);

  if (!libId || !qty || qty <= 0) {
    showToast('Vui lòng nhập số lượng hợp lệ', 'error');
    return;
  }

  try {
    await api.importFromLibraryToStock({
      library_id: libId,
      quantity: qty,
      location: loc,
      min_stock_alert: minStock
    });

    showToast('Đã nhập linh kiện vào Kho thành công! 🎉', 'success');
    document.getElementById('stock-in-modal').classList.remove('active');
    await loadLibraryData();
  } catch (err) {
    showToast(err.message || 'Lỗi nhập vào kho', 'error');
  }
}
