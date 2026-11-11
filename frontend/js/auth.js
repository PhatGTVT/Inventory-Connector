// auth.js - Authentication state management

function renderNavAuth() {
  const user = api.getCurrentUser();
  const loginEl = document.getElementById('nav-login-section');
  const userEl = document.getElementById('nav-user-section');
  const adminLinks = document.querySelectorAll('.admin-only-nav');

  if (!loginEl || !userEl) return;

  if (user) {
    loginEl.style.display = 'none';
    userEl.style.display = 'flex';

    const avatarEl = document.getElementById('user-avatar');
    const nameEl = document.getElementById('user-fullname');
    const roleEl = document.getElementById('user-role-tag');

    if (avatarEl) avatarEl.textContent = (user.full_name || user.username).charAt(0).toUpperCase();
    if (nameEl) nameEl.textContent = user.full_name || user.username;
    if (roleEl) roleEl.textContent = user.role === 'admin' ? '⚡ Admin' : '👤 User';

    adminLinks.forEach(el => {
      el.style.display = user.role === 'admin' ? 'flex' : 'none';
    });
  } else {
    loginEl.style.display = 'flex';
    userEl.style.display = 'none';
    adminLinks.forEach(el => el.style.display = 'none');
  }
}

async function handleLogin(username, password) {
  try {
    const data = await api.login(username, password);
    showToast(`Chào mừng, ${data.user.full_name}! 🎉`, 'success');
    renderNavAuth();
    return data;
  } catch (err) {
    showToast(err.message || 'Đăng nhập thất bại', 'error');
    throw err;
  }
}

function requireAdmin(redirectUrl = '/') {
  const user = api.getCurrentUser();
  if (!user || user.role !== 'admin') {
    showToast('Bạn cần đăng nhập với quyền Admin', 'error');
    setTimeout(() => { window.location.href = redirectUrl; }, 1500);
    return false;
  }
  return true;
}

function requireLogin(redirectUrl = '/') {
  const user = api.getCurrentUser();
  if (!user) {
    showToast('Vui lòng đăng nhập để tiếp tục', 'warning');
    document.getElementById('login-modal')?.classList.add('active');
    return false;
  }
  return true;
}

// Login & Register Modal logic
function initLoginModal() {
  const modal = document.getElementById('login-modal');
  if (!modal) return;

  const modalContent = modal.querySelector('.modal-content');
  if (!modalContent) return;

  modalContent.style.maxWidth = '440px';
  modalContent.innerHTML = `
    <div class="modal-header" style="padding:1.25rem 1.5rem 0.5rem;align-items:center">
      <div style="display:flex;gap:0.5rem;flex:1">
        <button id="tab-login" type="button" class="btn btn-sm auth-tab active" style="flex:1;padding:0.45rem;border-radius:8px">Đăng Nhập</button>
        <button id="tab-register" type="button" class="btn btn-sm auth-tab" style="flex:1;padding:0.45rem;border-radius:8px;background:transparent;color:var(--text-muted);border:1px solid var(--border-color)">Đăng Ký</button>
      </div>
      <button class="modal-close" style="margin-left:0.75rem">&times;</button>
    </div>
    <div class="modal-body" style="padding:1rem 1.5rem 1.5rem">
      <!-- Login Form -->
      <form id="login-form">
        <div class="filter-group">
          <label class="filter-label">Tên đăng nhập</label>
          <input type="text" id="login-username" class="filter-select" placeholder="admin / user" required autocomplete="username" />
        </div>
        <div class="filter-group" style="margin-top:1rem">
          <label class="filter-label">Mật khẩu</label>
          <input type="password" id="login-password" class="filter-select" placeholder="admin123 / user123" required autocomplete="current-password" />
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:1.25rem;padding:0.75rem">
          Đăng nhập
        </button>
        <p style="text-align:center;color:var(--text-muted);font-size:0.82rem;margin-top:1.25rem">
          Chưa có tài khoản? <a href="#" id="link-to-register" style="color:var(--accent-primary);text-decoration:underline;font-weight:600">Đăng ký ngay</a>
        </p>
      </form>

      <!-- Register Form -->
      <form id="register-form" style="display:none">
        <div class="filter-group">
          <label class="filter-label">Tên đăng nhập *</label>
          <input type="text" id="reg-username" class="filter-select" placeholder="vd: ky_su_01" required autocomplete="username" />
        </div>
        <div class="filter-group" style="margin-top:0.75rem">
          <label class="filter-label">Họ và tên *</label>
          <input type="text" id="reg-fullname" class="filter-select" placeholder="vd: Nguyễn Văn A" required />
        </div>
        <div class="filter-group" style="margin-top:0.75rem">
          <label class="filter-label">Email</label>
          <input type="email" id="reg-email" class="filter-select" placeholder="email@congty.com" />
        </div>
        <div class="filter-group" style="margin-top:0.75rem">
          <label class="filter-label">Phòng ban / Bộ phận</label>
          <input type="text" id="reg-dept" class="filter-select" placeholder="vd: Phòng R&D Điện tử" />
        </div>
        <div class="filter-group" style="margin-top:0.75rem">
          <label class="filter-label">Mật khẩu *</label>
          <input type="password" id="reg-password" class="filter-select" placeholder="••••••••" required autocomplete="new-password" />
        </div>
        <button type="submit" class="btn btn-primary btn-block" style="margin-top:1.25rem;padding:0.75rem">
          Tạo tài khoản
        </button>
        <p style="text-align:center;color:var(--text-muted);font-size:0.82rem;margin-top:1.25rem">
          Đã có tài khoản? <a href="#" id="link-to-login" style="color:var(--accent-primary);text-decoration:underline;font-weight:600">Đăng nhập ngay</a>
        </p>
      </form>
    </div>
  `;

  const tabLogin = modalContent.querySelector('#tab-login');
  const tabRegister = modalContent.querySelector('#tab-register');
  const loginForm = modalContent.querySelector('#login-form');
  const registerForm = modalContent.querySelector('#register-form');

  function showLoginTab() {
    tabLogin.classList.add('active');
    tabLogin.style.background = 'var(--accent-primary)';
    tabLogin.style.color = '#fff';
    tabLogin.style.border = 'none';

    tabRegister.classList.remove('active');
    tabRegister.style.background = 'transparent';
    tabRegister.style.color = 'var(--text-muted)';
    tabRegister.style.border = '1px solid var(--border-color)';

    loginForm.style.display = 'block';
    registerForm.style.display = 'none';
  }

  function showRegisterTab() {
    tabRegister.classList.add('active');
    tabRegister.style.background = 'var(--accent-primary)';
    tabRegister.style.color = '#fff';
    tabRegister.style.border = 'none';

    tabLogin.classList.remove('active');
    tabLogin.style.background = 'transparent';
    tabLogin.style.color = 'var(--text-muted)';
    tabLogin.style.border = '1px solid var(--border-color)';

    registerForm.style.display = 'block';
    loginForm.style.display = 'none';
  }

  tabLogin?.addEventListener('click', showLoginTab);
  tabRegister?.addEventListener('click', showRegisterTab);
  modalContent.querySelector('#link-to-register')?.addEventListener('click', (e) => { e.preventDefault(); showRegisterTab(); });
  modalContent.querySelector('#link-to-login')?.addEventListener('click', (e) => { e.preventDefault(); showLoginTab(); });

  // Handle Login submit
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = loginForm.querySelector('button[type="submit"]');
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang đăng nhập...';

    try {
      await handleLogin(username, password);
      modal.classList.remove('active');
      window.location.reload();
    } catch (err) {
      // error shown by handleLogin
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Đăng nhập';
    }
  });

  // Handle Register submit
  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = registerForm.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Đang đăng ký...';

    const payload = {
      username: document.getElementById('reg-username').value.trim(),
      full_name: document.getElementById('reg-fullname').value.trim(),
      email: document.getElementById('reg-email').value.trim() || null,
      department: document.getElementById('reg-dept').value.trim() || null,
      password: document.getElementById('reg-password').value,
      role: 'user'
    };

    try {
      const data = await api.register(payload);
      showToast(`Đăng ký thành công! Chào mừng, ${data.user.full_name} 🎉`, 'success');
      modal.classList.remove('active');
      renderNavAuth();
      window.location.reload();
    } catch (err) {
      showToast(err.message || 'Đăng ký thất bại', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Tạo tài khoản';
    }
  });

  document.getElementById('logout-btn')?.addEventListener('click', () => {
    api.logout();
  });

  document.getElementById('open-login-btn')?.addEventListener('click', () => {
    showLoginTab();
    modal.classList.add('active');
  });

  modalContent.querySelector('.modal-close')?.addEventListener('click', () => {
    modal.classList.remove('active');
  });

  modal?.addEventListener('click', (e) => {
    if (e.target === modal) modal.classList.remove('active');
  });
}

// Theme Toggle Management
function initTheme() {
  const savedTheme = localStorage.getItem('connector_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);

  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      localStorage.setItem('connector_theme', newTheme);
      updateThemeIcon(newTheme);
      showToast(newTheme === 'dark' ? '🌙 Đã chuyển sang Giao diện Tối' : '☀️ Đã chuyển sang Giao diện Sáng', 'info');
    });
  }
}

function updateThemeIcon(theme) {
  const icon = document.getElementById('theme-icon');
  if (icon) {
    if (theme === 'light') {
      icon.className = 'bi bi-moon-stars-fill';
      icon.style.color = '#475569';
    } else {
      icon.className = 'bi bi-sun-fill';
      icon.style.color = '#f59e0b';
    }
  }
}

// Immediate theme apply to prevent white/dark flash
(function() {
  const savedTheme = localStorage.getItem('connector_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
})();

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  renderNavAuth();
  initLoginModal();
});

