// API Client for Connector Inventory
const API_BASE = '/api';

const api = {
  getToken() {
    return localStorage.getItem('connector_token');
  },

  setAuth(token, user) {
    localStorage.setItem('connector_token', token);
    localStorage.setItem('connector_user', JSON.stringify(user));
  },

  getCurrentUser() {
    const userStr = localStorage.getItem('connector_user');
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch (e) {
      return null;
    }
  },

  logout() {
    localStorage.removeItem('connector_token');
    localStorage.removeItem('connector_user');
    window.location.reload();
  },

  async request(endpoint, options = {}) {
    const isFormData = options.body instanceof FormData;
    const headers = {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...(options.headers || {})
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    try {
      const res = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers
      });

      if (res.status === 204) {
        return null;
      }

      const text = await res.text();
      let data = {};
      try {
        data = text ? JSON.parse(text) : {};
      } catch (parseErr) {
        data = { detail: text || `Lỗi máy chủ (${res.status})` };
      }

      if (!res.ok) {
        const errorMsg = data.detail || (typeof data === 'string' ? data : `Lỗi hệ thống (${res.status})`);
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      console.error(`API Error [${endpoint}]:`, err);
      throw err;
    }
  },

  async uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch('/api/upload/image', {
      method: 'POST',
      headers,
      body: formData
    });

    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = { detail: text || `Lỗi tải ảnh (${res.status})` };
    }

    if (!res.ok) {
      throw new Error(data.detail || 'Không thể tải tệp ảnh lên');
    }
    return data;
  },


  // Auth
  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    this.setAuth(data.access_token, data.user);
    return data;
  },

  async register(userData) {
    const data = await this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
    this.setAuth(data.access_token, data.user);
    return data;
  },

  async getMe() {
    return await this.request('/auth/me');
  },

  async getUsers() {
    return await this.request('/auth/users');
  },

  async createUser(data) {
    return await this.request('/auth/users', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateUser(id, data) {
    return await this.request(`/auth/users/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async resetUserPassword(id, newPassword) {
    return await this.request(`/auth/users/${id}/reset-password`, {
      method: 'PUT',
      body: JSON.stringify({ new_password: newPassword })
    });
  },

  async toggleUserStatus(id) {
    return await this.request(`/auth/users/${id}/toggle-status`, {
      method: 'PUT'
    });
  },

  async deleteUser(id) {
    return await this.request(`/auth/users/${id}`, {
      method: 'DELETE'
    });
  },

  downloadUsersExcel() {
    window.location.href = '/api/auth/users/export-excel';
  },

  // Categories & Filters
  async getCategories() {
    return await this.request('/categories');
  },

  async getFilterOptions() {
    return await this.request('/connectors/filters/options');
  },

  // Connectors
  async getConnectors(params = {}) {
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        query.append(k, params[k]);
      }
    });
    return await this.request(`/connectors?${query.toString()}`);
  },

  async getConnectorDetail(id) {
    return await this.request(`/connectors/${id}`);
  },

  async getFrequentlyViewed(limit = 4) {
    return await this.request(`/connectors/suggestions/frequently-viewed?limit=${limit}`);
  },

  async createConnector(data) {
    return await this.request('/connectors', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateConnector(id, data) {
    return await this.request(`/connectors/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async deleteConnector(id) {
    return await this.request(`/connectors/${id}`, {
      method: 'DELETE'
    });
  },

  // Requests
  async createRequest(connectorId, quantity, reason) {
    return await this.request('/requests', {
      method: 'POST',
      body: JSON.stringify({
        connector_id: parseInt(connectorId),
        quantity: parseInt(quantity),
        reason
      })
    });
  },

  async getRequests(params = {}) {
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        query.append(k, params[k]);
      }
    });
    return await this.request(`/requests?${query.toString()}`);
  },

  async approveRequest(id, responseNote = 'Đã duyệt xuất kho') {
    return await this.request(`/requests/${id}/approve`, {
      method: 'PUT',
      body: JSON.stringify({ admin_response: responseNote })
    });
  },

  async rejectRequest(id, responseNote) {
    return await this.request(`/requests/${id}/reject`, {
      method: 'PUT',
      body: JSON.stringify({ admin_response: responseNote })
    });
  },

  async deleteRequest(id) {
    return await this.request(`/requests/${id}`, {
      method: 'DELETE'
    });
  },

  async updateRequestResponse(id, responseNote) {
    return await this.request(`/requests/${id}/response`, {
      method: 'PUT',
      body: JSON.stringify({ admin_response: responseNote })
    });
  },

  // Library APIs
  async getLibrary(params = {}) {
    const query = new URLSearchParams();
    Object.keys(params).forEach(k => {
      if (params[k] !== undefined && params[k] !== null && params[k] !== '') {
        query.append(k, params[k]);
      }
    });
    return await this.request(`/library?${query.toString()}`);
  },

  async getLibraryItem(id) {
    return await this.request(`/library/${id}`);
  },

  async createLibraryItem(data) {
    return await this.request('/library', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },

  async updateLibraryItem(id, data) {
    return await this.request(`/library/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  },

  async deleteLibraryItem(id) {
    return await this.request(`/library/${id}`, {
      method: 'DELETE'
    });
  },

  async importLibraryExcel(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = this.getToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const res = await fetch('/api/library/import-excel', {
      method: 'POST',
      headers,
      body: formData
    });

    const text = await res.text();
    let data = {};
    try {
      data = text ? JSON.parse(text) : {};
    } catch (e) {
      data = { detail: text || `Lỗi tải tệp (${res.status})` };
    }

    if (!res.ok) {
      throw new Error(data.detail || 'Không thể nhập dữ liệu từ tệp');
    }
    return data;
  },

  async importFromLibraryToStock(payload) {
    return await this.request('/connectors/import-from-library', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  }
};

// Toast notification helper
function showToast(message, type = 'info') {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span>${message}</span>
  `;

  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Generate inline dynamic SVG placeholder if image is missing
function getConnectorSvg(partNumber) {
  return `
    <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
      <rect width="120" height="120" rx="20" fill="#1e293b"/>
      <circle cx="60" cy="60" r="45" stroke="#38bdf8" stroke-width="4" stroke-dasharray="8 4" fill="#0f172a"/>
      <circle cx="60" cy="60" r="32" fill="#1e293b" stroke="#64748b" stroke-width="2"/>
      <circle cx="60" cy="42" r="5" fill="#38bdf8"/>
      <circle cx="75" cy="50" r="5" fill="#38bdf8"/>
      <circle cx="75" cy="70" r="5" fill="#38bdf8"/>
      <circle cx="60" cy="78" r="5" fill="#38bdf8"/>
      <circle cx="45" cy="70" r="5" fill="#38bdf8"/>
      <circle cx="45" cy="50" r="5" fill="#38bdf8"/>
      <circle cx="60" cy="60" r="4" fill="#f59e0b"/>
    </svg>
  `;
}
