const API_BASE = '/api/v1';

let state = {
  token: localStorage.getItem('access_token') || null,
  user: null,
  vehicles: [],
  drivers: []
};

document.addEventListener('DOMContentLoaded', () => {
  // Set default dates
  const todayStr = new Date().toISOString().split('T')[0];
  const dateInput = document.getElementById('tanker-date');
  if (dateInput) dateInput.value = todayStr;

  if (state.token) {
    fetchCurrentUser();
  } else {
    showSection('auth');
  }
});

// Toast notification
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerText = message;
  container.appendChild(toast);

  setTimeout(() => {
    toast.remove();
  }, 4000);
}

// Authentication
function switchAuthTab(tab) {
  const formLogin = document.getElementById('form-login');
  const formRegister = document.getElementById('form-register');
  const tabLogin = document.getElementById('tab-login');
  const tabRegister = document.getElementById('tab-register');
  const authSubtitle = document.getElementById('auth-subtitle');

  if (tab === 'login') {
    formLogin.style.display = 'block';
    formRegister.style.display = 'none';
    tabLogin.classList.add('active');
    tabRegister.classList.remove('active');
    if (authSubtitle) authSubtitle.innerText = 'Sign in to access vehicle fleet management & tanker daily reports';
  } else {
    formLogin.style.display = 'none';
    formRegister.style.display = 'block';
    tabLogin.classList.remove('active');
    tabRegister.classList.add('active');
    if (authSubtitle) authSubtitle.innerText = 'Register a new account as Driver or Admin';
  }
}

function toggleAdminCodeInput() {
  const roleSelect = document.getElementById('reg-role');
  const adminCodeGroup = document.getElementById('reg-admin-code-group');
  const adminCodeInput = document.getElementById('reg-admin-code');

  if (roleSelect && roleSelect.value === 'admin') {
    if (adminCodeGroup) adminCodeGroup.style.display = 'block';
    if (adminCodeInput) adminCodeInput.setAttribute('required', 'required');
  } else {
    if (adminCodeGroup) adminCodeGroup.style.display = 'none';
    if (adminCodeInput) adminCodeInput.removeAttribute('required');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const name = document.getElementById('reg-name').value;
  const email = document.getElementById('reg-email').value;
  const phone = document.getElementById('reg-phone').value || null;
  const password = document.getElementById('reg-password').value;
  const role = document.getElementById('reg-role').value;
  const admin_access_code = role === 'admin' ? document.getElementById('reg-admin-code').value : null;

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, phone, password, role, admin_access_code })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registration failed');
    }

    showToast('Account registered successfully! Signing in...', 'success');

    document.getElementById('login-email').value = email;
    document.getElementById('login-password').value = password;
    switchAuthTab('login');

    const loginRes = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (loginRes.ok) {
      const data = await loginRes.json();
      state.token = data.access_token;
      localStorage.setItem('access_token', state.token);
      await fetchCurrentUser();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}


async function handleLogin(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Login failed');
    }

    const data = await res.json();
    state.token = data.access_token;
    localStorage.setItem('access_token', state.token);
    showToast('Signed in successfully', 'success');
    await fetchCurrentUser();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function fetchCurrentUser() {
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      handleLogout();
      return;
    }

    state.user = await res.json();
    updateUserUI();
    if (state.user.role === 'admin') {
      switchTab('dashboard');
    } else {
      switchTab('vehicles');
    }
  } catch (err) {
    handleLogout();
  }
}

function updateUserUI() {
  const navLinks = document.getElementById('nav-links');
  const userInfo = document.getElementById('user-info');
  const btnLogout = document.getElementById('btn-logout');
  const btnChangePassword = document.getElementById('btn-change-password');
  const userNameDisplay = document.getElementById('user-name-display');
  const userRoleBadge = document.getElementById('user-role-badge');
  const btnAddVehicle = document.getElementById('btn-add-vehicle-toggle');

  if (state.user) {
    navLinks.style.display = 'flex';
    userInfo.style.display = 'flex';
    if (btnLogout) btnLogout.style.display = 'block';
    if (btnChangePassword) btnChangePassword.style.display = 'block';

    userNameDisplay.innerText = state.user.name;
    userRoleBadge.innerText = state.user.role.toUpperCase();

    const navDashboard = document.getElementById('nav-item-dashboard');

    if (state.user.role === 'admin') {
      userRoleBadge.className = 'badge badge-info';
      if (btnAddVehicle) btnAddVehicle.style.display = 'inline-flex';
      if (navDashboard) navDashboard.style.display = 'inline-block';
    } else {
      userRoleBadge.className = 'badge badge-success';
      if (btnAddVehicle) btnAddVehicle.style.display = 'none';
      if (navDashboard) navDashboard.style.display = 'none'; // Hide Fleet Dashboard for Drivers
    }
  }
}

function handleLogout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('access_token');
  document.getElementById('nav-links').style.display = 'none';
  document.getElementById('user-info').style.display = 'none';
  if (document.getElementById('btn-logout')) document.getElementById('btn-logout').style.display = 'none';
  if (document.getElementById('btn-change-password')) document.getElementById('btn-change-password').style.display = 'none';
  showSection('auth');
  showToast('Logged out', 'info');
}

// Navigation Tab Switching
function switchTab(tabId) {
  if (state.user && state.user.role !== 'admin' && tabId === 'dashboard') {
    showToast('Access denied: Fleet Dashboard is restricted to Admin', 'error');
    tabId = 'vehicles';
  }

  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-tab') === tabId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  showSection(tabId);

  if (tabId === 'dashboard' && state.user && state.user.role === 'admin') loadDashboardMetrics();
  if (tabId === 'vehicles') loadVehicles();
  if (tabId === 'documents') loadDocuments();
  if (tabId === 'tanker-reports') loadTankerReports();
}

function showSection(sectionId) {
  document.querySelectorAll('.section').forEach(sec => sec.classList.remove('active'));
  const target = document.getElementById(`section-${sectionId}`);
  if (target) target.classList.add('active');
}

// Dashboard Metrics
async function loadDashboardMetrics() {
  try {
    const res = await fetch(`${API_BASE}/admin/dashboard`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;

    const data = await res.json();
    document.getElementById('metric-total-vehicles').innerText = data.total_vehicles;
    document.getElementById('metric-total-drivers').innerText = data.total_drivers;
    document.getElementById('metric-expired-docs').innerText = data.expired_documents;
    document.getElementById('metric-expiring-docs').innerText = data.documents_expiring_soon;
    document.getElementById('metric-monthly-freight').innerText = `₹${data.total_freight_this_month.toLocaleString()}`;

    // Load Expiry Alerts list
    const resExp = await fetch(`${API_BASE}/documents/expiring-soon?days=30`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (resExp.ok) {
      const expiringDocs = await resExp.json();
      const tbody = document.getElementById('tbody-expiry-alerts');
      if (expiringDocs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--color-success);">✓ All vehicle documents are up to date!</td></tr>`;
      } else {
        tbody.innerHTML = expiringDocs.map(d => `
          <tr>
            <td><strong>Vehicle #${d.vehicle_id}</strong></td>
            <td>${d.document_type}</td>
            <td>${d.document_number || 'N/A'}</td>
            <td>${d.expiry_date}</td>
            <td><span class="badge badge-${d.status.toLowerCase()}">${d.status}</span></td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Failed to load dashboard metrics', err);
  }
}

// Vehicle Management
async function loadVehicles() {
  try {
    const res = await fetch(`${API_BASE}/vehicles`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;

    state.vehicles = await res.json();
    renderVehiclesTable();
    populateVehicleDropdowns();
  } catch (err) {
    console.error(err);
  }
}

function renderVehiclesTable() {
  const tbody = document.getElementById('tbody-vehicles');
  if (state.vehicles.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-text-muted);">No vehicles recorded yet. ${state.user && state.user.role === 'admin' ? "Click '+ Add Vehicle' to start." : ''}</td></tr>`;
    return;
  }

  const isAdmin = state.user && state.user.role === 'admin';

  tbody.innerHTML = state.vehicles.map(v => `
    <tr>
      <td><strong>${v.vehicle_number}</strong></td>
      <td>${v.vehicle_class}</td>
      <td>${v.active_driver ? v.active_driver.name : '<em style="color: var(--color-text-muted);">Unassigned</em>'}</td>
      <td>${v.make || ''} ${v.model || ''}</td>
      <td>${v.chassis_number || 'N/A'}</td>
      <td><span class="badge badge-${v.status.toLowerCase()}">${v.status}</span></td>
      <td>
        <div style="display: flex; gap: 0.35rem;">
          <button class="btn btn-secondary btn-sm" onclick="selectVehicleDocs(${v.id})">View Docs</button>
          ${isAdmin ? `<button class="btn btn-accent btn-sm" onclick="openAssignDriverModal(${v.id}, '${v.vehicle_number}')">Assign Driver</button>` : ''}
        </div>
      </td>
    </tr>
  `).join('');
}

function populateVehicleDropdowns() {
  const docSelect = document.getElementById('doc-vehicle-id');
  const tankerSelect = document.getElementById('tanker-vehicle-id');

  const optionsHTML = `<option value="">-- Choose Vehicle --</option>` +
    state.vehicles.map(v => `<option value="${v.id}">${v.vehicle_number} (${v.vehicle_class})</option>`).join('');

  if (docSelect) docSelect.innerHTML = optionsHTML;
  if (tankerSelect) tankerSelect.innerHTML = optionsHTML;
}

function toggleAddVehicleForm() {
  const form = document.getElementById('card-add-vehicle');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function handleCreateVehicle(e) {
  e.preventDefault();
  const payload = {
    vehicle_number: document.getElementById('veh-number').value,
    vehicle_class: document.getElementById('veh-class').value,
    make: document.getElementById('veh-make').value,
    model: document.getElementById('veh-model').value,
    chassis_number: document.getElementById('veh-chassis').value,
    engine_number: document.getElementById('veh-engine').value,
    status: 'ACTIVE'
  };

  try {
    const res = await fetch(`${API_BASE}/vehicles`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create vehicle');
    }

    showToast('Vehicle registered successfully', 'success');
    document.getElementById('form-add-vehicle').reset();
    toggleAddVehicleForm();
    loadVehicles();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Documents Management
async function loadDocuments() {
  if (state.vehicles.length === 0) await loadVehicles();
  const vehicleId = document.getElementById('doc-vehicle-id').value;
  if (!vehicleId) return;

  try {
    const res = await fetch(`${API_BASE}/documents/vehicle/${vehicleId}`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;

    const docs = await res.json();
    renderDocumentsTable(docs);
  } catch (err) {
    console.error(err);
  }
}

function selectVehicleDocs(vehicleId) {
  switchTab('documents');
  const sel = document.getElementById('doc-vehicle-id');
  if (sel) {
    sel.value = vehicleId;
    loadDocuments();
  }
}

function renderDocumentsTable(docs) {
  const tbody = document.getElementById('tbody-documents');
  if (!docs || docs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted);">No documents uploaded for this vehicle yet.</td></tr>`;
    return;
  }

  const isAdmin = state.user && state.user.role === 'admin';
  const isDriver = state.user && state.user.role === 'driver';

  tbody.innerHTML = docs.map(d => {
    // 1. Determine Re-upload status badge
    let reuploadBadge = '<span class="badge badge-pending">Locked</span>';
    if (d.can_reupload) {
      reuploadBadge = '<span class="badge badge-success">Unlocked</span>';
    } else if (d.reupload_requested) {
      const reasonText = d.reupload_reason ? ` (${d.reupload_reason})` : '';
      reuploadBadge = `<span class="badge badge-warning" title="Requested: ${d.reupload_reason || 'No reason'}">Requested${reasonText}</span>`;
    }

    // 2. Action buttons based on role & document status
    let actionButtons = '';

    if (isAdmin) {
      if (!d.can_reupload) {
        const btnText = d.reupload_requested ? '✅ Approve Re-upload' : '🔓 Allow Re-upload';
        const btnClass = d.reupload_requested ? 'btn-accent' : 'btn-secondary';
        actionButtons += `<button class="btn ${btnClass} btn-sm" onclick="handleAllowReupload(${d.id})">${btnText}</button>`;
      }
    } else if (isDriver) {
      if (!d.can_reupload && !d.reupload_requested) {
        actionButtons += `<button class="btn btn-secondary btn-sm" onclick="handleRequestReupload(${d.id})">📩 Request Re-upload</button>`;
      } else if (d.reupload_requested) {
        actionButtons += `<span style="font-size: 0.75rem; color: var(--color-warning);">Awaiting Admin Approval</span>`;
      }
    }

    actionButtons += `<button class="btn btn-danger btn-sm" onclick="handleDeleteDocument(${d.id})">Delete</button>`;

    return `
      <tr>
        <td>#${d.vehicle_id}</td>
        <td><strong>${d.document_type}</strong></td>
        <td>${d.document_number || 'N/A'}</td>
        <td>${d.expiry_date}</td>
        <td><span class="badge badge-${d.status.toLowerCase()}">${d.status}</span></td>
        <td>${reuploadBadge}</td>
        <td>
          <a href="${d.file_url}?token=${encodeURIComponent(state.token)}" target="_blank" class="btn btn-secondary btn-sm">📄 View File</a>
        </td>
        <td>
          <div style="display: flex; gap: 0.35rem; align-items: center;">
            ${actionButtons}
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

async function handleDocumentUpload(e) {
  e.preventDefault();
  const formData = new FormData();
  formData.append('vehicle_id', document.getElementById('doc-vehicle-id').value);
  formData.append('document_type', document.getElementById('doc-type').value);
  formData.append('document_number', document.getElementById('doc-number').value);
  formData.append('expiry_date', document.getElementById('doc-expiry-date').value);
  formData.append('file', document.getElementById('doc-file').files[0]);

  try {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` },
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Document upload failed');
    }

    showToast('Document uploaded successfully', 'success');
    document.getElementById('form-upload-doc').reset();
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleDeleteDocument(docId) {
  if (!confirm('Are you sure you want to delete this document?')) return;
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error('Failed to delete document');
    showToast('Document deleted', 'info');
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Driver requests reupload permission
async function handleRequestReupload(docId) {
  const reason = prompt('Please enter the reason for re-uploading this document (e.g., Updated RC, Clearer scan needed):');
  if (reason === null) return; // User clicked cancel

  try {
    const res = await fetch(`${API_BASE}/documents/${docId}/request-reupload`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ reason: reason })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to submit reupload request');
    }

    showToast('Re-upload request sent to Admin', 'success');
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Admin allows reupload permission
async function handleAllowReupload(docId) {
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}/allow-reupload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to grant reupload permission');
    }

    showToast('Re-upload permission granted to driver', 'success');
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}


// Tanker Daily Report Calculations & Logic
function calculateFreightAndHSD() {
  const rtkm = parseFloat(document.getElementById('tanker-rtkm').value) || 0;
  const rate = parseFloat(document.getElementById('tanker-rate').value) || 0;
  const hsdLtr = parseFloat(document.getElementById('tanker-hsd-ltr').value) || 0;
  const hsdRate = parseFloat(document.getElementById('tanker-hsd-rate').value) || 0;

  const freight = (rtkm * rate).toFixed(2);
  const hsdAmount = (hsdLtr * hsdRate).toFixed(2);

  document.getElementById('tanker-freight').value = freight;
  document.getElementById('tanker-hsd-amount').value = hsdAmount;
}

async function handleCreateTankerReport(e) {
  e.preventDefault();
  const payload = {
    report_date: document.getElementById('tanker-date').value,
    vehicle_id: parseInt(document.getElementById('tanker-vehicle-id').value),
    ul_point: document.getElementById('tanker-ul-point').value,
    rtkm: parseFloat(document.getElementById('tanker-rtkm').value) || 0,
    rate: parseFloat(document.getElementById('tanker-rate').value) || 0,
    freight: parseFloat(document.getElementById('tanker-freight').value) || 0,
    pump: document.getElementById('tanker-pump').value,
    hsd_ltr: parseFloat(document.getElementById('tanker-hsd-ltr').value) || 0,
    hsd_rate: parseFloat(document.getElementById('tanker-hsd-rate').value) || 0,
    hsd_amount: parseFloat(document.getElementById('tanker-hsd-amount').value) || 0,
    khuraki: parseFloat(document.getElementById('tanker-khuraki').value) || 0
  };

  try {
    const res = await fetch(`${API_BASE}/tanker-reports`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create tanker daily entry');
    }

    showToast('Tanker report entry saved!', 'success');
    document.getElementById('form-tanker-report').reset();
    document.getElementById('tanker-date').value = new Date().toISOString().split('T')[0];
    loadTankerReports();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function loadTankerReports() {
  if (state.vehicles.length === 0) await loadVehicles();
  const month = document.getElementById('filter-month').value;
  let url = `${API_BASE}/tanker-reports`;
  if (month) url += `?month=${month}`;

  try {
    const res = await fetch(url, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;

    const reports = await res.json();
    renderTankerReportsTable(reports);
  } catch (err) {
    console.error(err);
  }
}

function renderTankerReportsTable(reports) {
  const tbody = document.getElementById('tbody-tanker-reports');
  if (!reports || reports.length === 0) {
    tbody.innerHTML = `<tr><td colspan="11" style="text-align: center; color: var(--color-text-muted);">No tanker entries recorded for this filter.</td></tr>`;
    return;
  }

  tbody.innerHTML = reports.map((r, idx) => `
    <tr>
      <td>${idx + 1}</td>
      <td>${r.report_date}</td>
      <td><strong>${r.vehicle_number || '#' + r.vehicle_id}</strong></td>
      <td>${r.ul_point}</td>
      <td>${r.rtkm}</td>
      <td>${r.rate}</td>
      <td><strong>₹${r.freight.toLocaleString()}</strong></td>
      <td>${r.pump || '-'}</td>
      <td>${r.hsd_ltr}</td>
      <td>₹${r.hsd_amount.toLocaleString()}</td>
      <td>₹${r.khuraki.toLocaleString()}</td>
    </tr>
  `).join('');
}

function handleExportExcel() {
  const month = document.getElementById('filter-month').value;
  let url = `${API_BASE}/tanker-reports/export`;
  if (month) url += `?month=${month}`;
  window.open(url, '_blank');
}

// Change Password Modal Handlers
function openChangePasswordModal() {
  const modal = document.getElementById('modal-change-password');
  if (modal) modal.classList.add('active');
}

function closeChangePasswordModal() {
  const modal = document.getElementById('modal-change-password');
  if (modal) modal.classList.remove('active');
  const form = document.getElementById('form-change-password');
  if (form) form.reset();
}

async function handleAuthChangePassword(e) {
  e.preventDefault();
  const old_password = document.getElementById('cp-old-password').value;
  const new_password = document.getElementById('cp-new-password').value;
  const confirm_password = document.getElementById('cp-confirm-password').value;

  if (new_password !== confirm_password) {
    showToast('New passwords do not match', 'error');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/change-password`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ old_password, new_password })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Password change failed');
    }

    showToast('Password updated successfully!', 'success');
    closeChangePasswordModal();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Assign Driver Modal Handlers (Admin Only)
async function openAssignDriverModal(vehicleId, vehicleNumber) {
  document.getElementById('assign-vehicle-id').value = vehicleId;
  document.getElementById('assign-vehicle-number').value = vehicleNumber;

  try {
    const res = await fetch(`${API_BASE}/admin/drivers`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) throw new Error('Failed to fetch drivers list');

    const drivers = await res.json();
    const select = document.getElementById('assign-driver-id');
    select.innerHTML = '<option value="">-- Choose Active Driver --</option>' +
      drivers.map(d => `<option value="${d.id}">${d.name} (${d.email})</option>`).join('');

    document.getElementById('modal-assign-driver').classList.add('active');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function closeAssignDriverModal() {
  const modal = document.getElementById('modal-assign-driver');
  if (modal) modal.classList.remove('active');
  const form = document.getElementById('form-assign-driver');
  if (form) form.reset();
}

async function handleAssignDriver(e) {
  e.preventDefault();
  const vehicleId = document.getElementById('assign-vehicle-id').value;
  const driverId = parseInt(document.getElementById('assign-driver-id').value);

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/assign`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ driver_id: driverId })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to assign driver');
    }

    showToast('Driver assigned successfully!', 'success');
    closeAssignDriverModal();
    loadVehicles();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Admin Document Re-Upload Permission Grant Handler
async function handleAllowReupload(docId) {
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}/allow-reupload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to grant re-upload permission');
    }

    showToast('Re-upload permission granted for driver!', 'success');
    loadDocuments();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
