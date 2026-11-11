// catalog.js - Trang danh mục, tìm kiếm và lọc linh kiện

let allCategories = [];
let filterOptions = {};
let activeFilters = {
  q: '',
  category_id: null,
  manufacturer: null,
  fastening_type: null,
  positions: null,
  contact_type: null,
  color: null,
};
let searchDebounceTimer = null;

// ---- Render Helpers ----

function getStockBadge(qty, min) {
  if (qty === 0) return `<span class="badge badge-out">&#9679; Hết hàng</span>`;
  if (qty <= min) return `<span class="badge badge-low">&#9650; Sắp hết (${qty})</span>`;
  return `<span class="badge badge-stock">&#10003; Còn hàng: ${qty}</span>`;
}

function renderProductCard(conn) {
  const el = document.createElement('div');
  el.className = 'product-card';
  el.setAttribute('data-id', conn.id);
  el.innerHTML = `
    <div class="card-image-box">
      ${conn.image_url
        ? `<img src="${conn.image_url}" alt="${conn.description}" loading="lazy" onerror="this.parentElement.innerHTML=getConnectorSvg('${conn.mfr_part_number}')">`
        : getConnectorSvg(conn.mfr_part_number)}
    </div>
    <div class="card-body">
      <div class="card-mfr">${conn.manufacturer}</div>
      <div class="card-title">${conn.mfr_part_number}</div>
      <div class="card-desc">${conn.description}</div>
      <div class="card-footer">
        ${getStockBadge(conn.in_stock_qty, conn.min_stock_alert)}
        <a href="/product-detail?id=${conn.id}" class="btn btn-outline btn-sm">Chi tiết</a>
      </div>
    </div>
  `;
  el.querySelector('.card-image-box').addEventListener('click', () => {
    window.location.href = `/product-detail?id=${conn.id}`;
  });
  return el;
}

function renderSuggestionCard(conn) {
  const el = document.createElement('div');
  el.className = 'suggestion-card';
  el.setAttribute('role', 'button');
  el.setAttribute('tabindex', '0');
  el.innerHTML = `
    <div class="suggestion-icon">${getConnectorSvg(conn.mfr_part_number)}</div>
    <div class="suggestion-info">
      <h4>${conn.mfr_part_number}</h4>
      <p>${conn.manufacturer}</p>
      <p style="color:var(--accent-cyan);font-size:0.78rem;margin-top:2px">🔥 ${conn.view_count || 0} lượt tra cứu</p>
    </div>
  `;
  el.addEventListener('click', () => window.location.href = `/product-detail?id=${conn.id}`);
  el.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') window.location.href = `/product-detail?id=${conn.id}`;
  });
  return el;
}

// ---- Load Data ----

async function loadSuggestions() {
  const grid = document.getElementById('suggestion-grid');
  if (!grid) return;
  try {
    const items = await api.getFrequentlyViewed(4);
    grid.innerHTML = '';
    if (!items || items.length === 0) {
      grid.innerHTML = '<p style="color:var(--text-muted);font-size:0.9rem">Chưa có dữ liệu gợi ý.</p>';
      return;
    }
    items.forEach(item => grid.appendChild(renderSuggestionCard(item)));
  } catch (e) {
    console.error('loadSuggestions error:', e);
  }
}

async function loadCategories() {
  const ul = document.getElementById('category-list');
  if (!ul) return;
  try {
    allCategories = await api.getCategories();
    ul.innerHTML = '';

    // "All" item
    const allLi = document.createElement('li');
    allLi.className = 'category-item active';
    allLi.setAttribute('data-cat-id', '');
    allLi.innerHTML = `<span>🔗 Tất cả danh mục</span><span class="category-badge">—</span>`;
    ul.appendChild(allLi);

    allCategories.forEach(cat => {
      const li = document.createElement('li');
      li.className = 'category-item';
      li.setAttribute('data-cat-id', cat.id);
      li.innerHTML = `
        <span>${cat.icon ? `<i class="bi ${cat.icon}"></i> ` : ''}${cat.name}</span>
        <span class="category-badge">${cat.connector_count}</span>
      `;
      ul.appendChild(li);
    });

    ul.querySelectorAll('.category-item').forEach(item => {
      item.addEventListener('click', () => {
        ul.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        const catId = item.getAttribute('data-cat-id');
        activeFilters.category_id = catId ? parseInt(catId) : null;
        doSearch();
      });
    });
  } catch (e) {
    console.error('loadCategories error:', e);
  }
}

async function loadFilterOptions() {
  try {
    filterOptions = await api.getFilterOptions();
    populateFilterSelects();
  } catch (e) {
    console.error('loadFilterOptions error:', e);
  }
}

function populateFilterSelects() {
  const map = {
    'filter-manufacturer': filterOptions.manufacturers || [],
    'filter-fastening': filterOptions.attributes?.['Fastening Type'] || [],
    'filter-positions': filterOptions.attributes?.['Number of Positions'] || [],
    'filter-contact': filterOptions.attributes?.['Contact Type'] || [],
    'filter-color': filterOptions.attributes?.['Housing Color'] || [],
  };

  Object.entries(map).forEach(([id, options]) => {
    const sel = document.getElementById(id);
    if (!sel) return;
    options.forEach(opt => {
      const o = document.createElement('option');
      o.value = opt;
      o.textContent = opt;
      sel.appendChild(o);
    });
  });
}

async function doSearch() {
  const grid = document.getElementById('product-grid');
  const resultsCount = document.getElementById('results-count');
  if (!grid) return;

  grid.innerHTML = `
    <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted)">
      <div class="spinner"></div>
      <p style="margin-top:1rem">Đang tải linh kiện...</p>
    </div>`;

  try {
    const connectors = await api.getConnectors({ ...activeFilters });
    grid.innerHTML = '';

    if (resultsCount) {
      resultsCount.textContent = `${connectors.length} kết quả`;
    }

    if (connectors.length === 0) {
      grid.innerHTML = `
        <div style="grid-column:1/-1;text-align:center;padding:3rem;color:var(--text-muted)">
          <div style="font-size:3rem;margin-bottom:1rem">🔍</div>
          <h3>Không tìm thấy kết quả</h3>
          <p>Thử điều chỉnh bộ lọc hoặc từ khóa tìm kiếm</p>
        </div>`;
      return;
    }

    connectors.forEach(conn => grid.appendChild(renderProductCard(conn)));
  } catch (e) {
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:2rem;color:var(--danger)">
      <p>⚠️ Lỗi khi tải dữ liệu. Vui lòng thử lại.</p></div>`;
    console.error('doSearch error:', e);
  }
}

// ---- Event Binding ----

function bindFilters() {
  const searchInput = document.getElementById('global-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchDebounceTimer);
      searchDebounceTimer = setTimeout(() => {
        activeFilters.q = e.target.value.trim();
        doSearch();
      }, 400);
    });
  }

  const filterMap = {
    'filter-manufacturer': 'manufacturer',
    'filter-fastening': 'fastening_type',
    'filter-positions': 'positions',
    'filter-contact': 'contact_type',
    'filter-color': 'color',
  };

  Object.entries(filterMap).forEach(([id, key]) => {
    const sel = document.getElementById(id);
    if (sel) {
      sel.addEventListener('change', () => {
        activeFilters[key] = sel.value || null;
        doSearch();
      });
    }
  });

  document.getElementById('btn-reset-filters')?.addEventListener('click', () => {
    activeFilters = { q: '', category_id: null, manufacturer: null, fastening_type: null, positions: null, contact_type: null, color: null };
    document.querySelectorAll('.filter-select').forEach(s => s.value = '');
    if (searchInput) searchInput.value = '';
    document.querySelectorAll('.category-item').forEach(i => i.classList.remove('active'));
    document.querySelector('.category-item[data-cat-id=""]')?.classList.add('active');
    doSearch();
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  await Promise.all([
    loadSuggestions(),
    loadCategories(),
    loadFilterOptions()
  ]);
  bindFilters();
  doSearch();
});
