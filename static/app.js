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
    const btnAddTax = document.getElementById('btn-add-tax-toggle');
    const btnExportTax = document.getElementById('btn-export-tax-excel');
    const btnAddCharge = document.getElementById('btn-add-charge-toggle');
    const btnAddChallan = document.getElementById('btn-add-challan-toggle');
    const btnSaveFastag = document.getElementById('btn-save-fastag');

    if (state.user.role === 'admin') {
      userRoleBadge.className = 'badge badge-info';
      if (btnAddVehicle) btnAddVehicle.style.display = 'inline-flex';
      if (navDashboard) navDashboard.style.display = 'inline-block';
      if (btnAddTax) btnAddTax.style.display = 'inline-flex';
      if (btnExportTax) btnExportTax.style.display = 'inline-flex';
      if (btnAddCharge) btnAddCharge.style.display = 'inline-flex';
      if (btnAddChallan) btnAddChallan.style.display = 'inline-flex';
      if (btnSaveFastag) btnSaveFastag.style.display = 'inline-block';
    } else {
      userRoleBadge.className = 'badge badge-success';
      if (btnAddVehicle) btnAddVehicle.style.display = 'none';
      if (navDashboard) navDashboard.style.display = 'none'; // Hide Fleet Dashboard for Drivers
      if (btnAddTax) btnAddTax.style.display = 'none';
      if (btnExportTax) btnExportTax.style.display = 'none';
      if (btnAddCharge) btnAddCharge.style.display = 'none';
      if (btnAddChallan) btnAddChallan.style.display = 'none';
      if (btnSaveFastag) btnSaveFastag.style.display = 'none';
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
  if (tabId === 'taxes') loadTaxes();
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

    if (document.getElementById('metric-active-taxes')) document.getElementById('metric-active-taxes').innerText = data.active_taxes || 0;
    if (document.getElementById('metric-due-soon-taxes')) document.getElementById('metric-due-soon-taxes').innerText = data.taxes_due_soon || 0;
    if (document.getElementById('metric-overdue-taxes')) document.getElementById('metric-overdue-taxes').innerText = data.taxes_overdue || 0;

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
        <div style="display: flex; gap: 0.35rem; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-sm" onclick="selectVehicleDocs(${v.id})">Docs</button>
          <button class="btn btn-secondary btn-sm" onclick="selectVehicleTaxes(${v.id})">Tax & Charges</button>
          ${isAdmin ? `<button class="btn btn-accent btn-sm" onclick="openAssignDriverModal(${v.id}, '${v.vehicle_number}')">Assign Driver</button>` : ''}
        </div>
      </td>
    </tr>
  `).join('');
}

function populateVehicleDropdowns() {
  const docSelect = document.getElementById('doc-vehicle-id');
  const tankerSelect = document.getElementById('tanker-vehicle-id');
  const taxSelect = document.getElementById('tax-vehicle-id');

  const optionsHTML = `<option value="">-- Choose Vehicle --</option>` +
    state.vehicles.map(v => `<option value="${v.id}">${v.vehicle_number} (${v.vehicle_class})</option>`).join('');

  if (docSelect) docSelect.innerHTML = optionsHTML;
  if (tankerSelect) tankerSelect.innerHTML = optionsHTML;
  if (taxSelect) taxSelect.innerHTML = optionsHTML;
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
  
  const sel = document.getElementById('doc-vehicle-id');
  if (!sel) return;

  // Auto-select the first available vehicle if none is selected
  if (!sel.value && state.vehicles.length > 0) {
    sel.value = state.vehicles[0].id;
  }

  const vehicleId = sel.value;
  if (!vehicleId) return;

  try {
    const res = await fetch(`${API_BASE}/documents/vehicle/${vehicleId}`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const errorMsg = err.detail || 'Failed to load documents for this vehicle.';
      const tbody = document.getElementById('tbody-documents');
      if (tbody) tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-error);">${errorMsg}</td></tr>`;
      return;
    }

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

// ==========================================
// Vehicle Tax & Government Charges Module (Frontend)
// ==========================================

let activeTaxSubtab = 'taxes';

function switchTaxSubtab(tabName) {
  activeTaxSubtab = tabName;
  document.querySelectorAll('.subtab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.subtab-pane').forEach(pane => pane.style.display = 'none');

  const activeBtn = document.getElementById(`subtab-btn-${tabName}`);
  const activePane = document.getElementById(`subtab-content-${tabName}`);
  if (activeBtn) activeBtn.classList.add('active');
  if (activePane) activePane.style.display = 'block';

  const sel = document.getElementById('tax-vehicle-id');
  const vehicleId = sel ? sel.value : null;
  if (!vehicleId) return;

  if (tabName === 'taxes' || tabName === 'history') loadTaxesForSelectedVehicle();
  if (tabName === 'charges') loadGovernmentCharges(vehicleId);
  if (tabName === 'challans') loadChallans(vehicleId);
  if (tabName === 'fastag') loadFASTag(vehicleId);
}

function selectVehicleTaxes(vehicleId) {
  switchTab('taxes');
  const sel = document.getElementById('tax-vehicle-id');
  if (sel) {
    sel.value = vehicleId;
    loadTaxesForSelectedVehicle();
  }
}

async function loadTaxes() {
  if (state.vehicles.length === 0) await loadVehicles();
  const sel = document.getElementById('tax-vehicle-id');
  if (!sel) return;

  if (!sel.value && state.vehicles.length > 0) {
    sel.value = state.vehicles[0].id;
  }
  loadTaxesForSelectedVehicle();
}

async function loadTaxesForSelectedVehicle() {
  const sel = document.getElementById('tax-vehicle-id');
  if (!sel || !sel.value) return;
  const vehicleId = sel.value;

  const veh = state.vehicles.find(v => v.id === parseInt(vehicleId));
  const infoSpan = document.getElementById('tax-vehicle-info');
  if (infoSpan && veh) {
    infoSpan.innerText = `${veh.make || ''} ${veh.model || ''} | Class: ${veh.vehicle_class}`;
  }

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/taxes`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail || 'Failed to load taxes.';
      document.getElementById('tax-cards-container').innerHTML = `<div style="color: var(--color-error); padding: 1rem;">${msg}</div>`;
      document.getElementById('tbody-tax-history').innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--color-error);">${msg}</td></tr>`;
      return;
    }

    const taxes = await res.json();
    renderTaxCards(taxes, vehicleId);
    renderTaxHistoryTable(taxes);
  } catch (err) {
    console.error(err);
  }

  if (activeTaxSubtab === 'charges') loadGovernmentCharges(vehicleId);
  if (activeTaxSubtab === 'challans') loadChallans(vehicleId);
  if (activeTaxSubtab === 'fastag') loadFASTag(vehicleId);
}

function renderTaxCards(taxes, vehicleId) {
  const container = document.getElementById('tax-cards-container');
  if (!taxes || taxes.length === 0) {
    container.innerHTML = `
      <div style="grid-column: 1 / -1; background: var(--color-surface); padding: 2rem; border-radius: var(--radius-md); border: 1px dashed var(--color-border); text-align: center; color: var(--color-text-muted);">
        No active tax records recorded for this vehicle.
        ${state.user && state.user.role === 'admin' ? '<br><button class="btn btn-accent btn-sm" style="margin-top: 0.75rem;" onclick="toggleAddTaxForm()">+ Record Tax Payment</button>' : ''}
      </div>`;
    return;
  }

  const isAdmin = state.user && state.user.role === 'admin';

  // Sort: Active and Due Soon first, then Overdue, then Expired
  const displayTaxes = [...taxes].slice(0, 6);

  container.innerHTML = displayTaxes.map(t => {
    const statusClass = `badge-${t.status.toLowerCase()}`;
    const amountFmt = Number(t.amount).toLocaleString('en-IN');
    const validUntilStr = t.valid_until ? new Date(t.valid_until).toLocaleDateString('en-GB') : 'N/A';
    const paidStr = t.payment_date ? new Date(t.payment_date).toLocaleDateString('en-GB') : 'Unpaid';
    const dueStr = t.due_date ? new Date(t.due_date).toLocaleDateString('en-GB') : 'N/A';

    const cleanTaxType = t.tax_type.replace(/_/g, ' ');

    let receiptButton = '';
    if (t.receipt_file_url) {
      const receiptFilename = t.receipt_file_url.split('/').pop();
      const receiptUrl = `${API_BASE}/taxes/receipt/${receiptFilename}?token=${state.token}`;
      receiptButton = `<a href="${receiptUrl}" target="_blank" class="btn btn-secondary btn-sm">🧾 View Receipt</a>`;
    } else {
      receiptButton = `<button class="btn btn-secondary btn-sm" onclick="openTaxReceiptModal(${t.id}, ${vehicleId}, '${cleanTaxType} (₹${amountFmt})')">📤 Upload Receipt</button>`;
    }

    return `
      <div class="tax-card">
        <div>
          <div class="tax-card-header">
            <div class="tax-card-title">${cleanTaxType}</div>
            <span class="badge ${statusClass}">${t.status.replace(/_/g, ' ')}</span>
          </div>
          <div class="tax-card-amount">₹${amountFmt}</div>
          <div class="tax-card-meta">
            <span>State / Authority:</span>
            <strong>${t.state}${t.tax_authority ? ` (${t.tax_authority})` : ''}</strong>
          </div>
          <div class="tax-card-meta">
            <span>Valid Until:</span>
            <strong>${validUntilStr}</strong>
          </div>
          <div class="tax-card-meta">
            <span>${t.payment_date ? 'Paid On:' : 'Due Date:'}</span>
            <span>${t.payment_date ? paidStr : dueStr}</span>
          </div>
          ${t.challan_number ? `<div class="tax-card-meta"><span>Challan Ref:</span><span>${t.challan_number}</span></div>` : ''}
        </div>
        <div class="tax-card-actions">
          ${receiptButton}
          ${isAdmin ? `<button class="btn btn-secondary btn-sm" style="color: var(--color-error);" onclick="handleDeleteTax(${t.id}, ${vehicleId})">Delete</button>` : ''}
        </div>
      </div>
    `;
  }).join('');
}

function renderTaxHistoryTable(taxes) {
  const tbody = document.getElementById('tbody-tax-history');
  if (!taxes || taxes.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--color-text-muted);">No history recorded yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = taxes.map(t => {
    const statusClass = `badge-${t.status.toLowerCase()}`;
    const pStart = t.period_start ? new Date(t.period_start).toLocaleDateString('en-GB') : '';
    const pEnd = t.period_end ? new Date(t.period_end).toLocaleDateString('en-GB') : '';
    const paid = t.payment_date ? new Date(t.payment_date).toLocaleDateString('en-GB') : 'Pending';
    const valid = t.valid_until ? new Date(t.valid_until).toLocaleDateString('en-GB') : '';

    let receiptLink = '<span style="color: var(--color-text-muted);">-</span>';
    if (t.receipt_file_url) {
      const receiptFilename = t.receipt_file_url.split('/').pop();
      receiptLink = `<a href="${API_BASE}/taxes/receipt/${receiptFilename}?token=${state.token}" target="_blank" style="color: var(--color-accent); font-weight: 600;">Receipt ↗</a>`;
    }

    return `
      <tr>
        <td>${pStart} – ${pEnd}</td>
        <td><strong>${t.tax_type.replace(/_/g, ' ')}</strong></td>
        <td>${t.state}</td>
        <td>₹${Number(t.amount).toLocaleString('en-IN')}</td>
        <td>${paid}</td>
        <td>${valid}</td>
        <td><span class="badge ${statusClass}">${t.status.replace(/_/g, ' ')}</span></td>
        <td>${t.challan_number || t.payment_reference || '-'}</td>
        <td>${receiptLink}</td>
      </tr>
    `;
  }).join('');
}

function toggleAddTaxForm() {
  const form = document.getElementById('card-add-tax');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function handleCreateTax(e) {
  e.preventDefault();
  const vehicleId = document.getElementById('tax-vehicle-id').value;
  if (!vehicleId) {
    showToast('Please select a vehicle first', 'error');
    return;
  }

  const payload = {
    tax_type: document.getElementById('tax-type').value,
    state: document.getElementById('tax-state').value,
    tax_authority: document.getElementById('tax-authority').value || null,
    amount: parseFloat(document.getElementById('tax-amount').value),
    period_start: document.getElementById('tax-period-start').value,
    period_end: document.getElementById('tax-period-end').value,
    payment_date: document.getElementById('tax-payment-date').value || null,
    due_date: document.getElementById('tax-due-date').value || null,
    valid_from: document.getElementById('tax-valid-from').value || null,
    valid_until: document.getElementById('tax-valid-until').value,
    payment_reference: document.getElementById('tax-payment-ref').value || null,
    challan_number: document.getElementById('tax-challan-number').value || null,
    notes: document.getElementById('tax-notes').value || null
  };

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/taxes`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to record tax');
    }

    showToast('Tax record saved successfully!', 'success');
    document.getElementById('form-add-tax').reset();
    toggleAddTaxForm();
    loadTaxesForSelectedVehicle();
    if (state.user && state.user.role === 'admin') loadDashboardMetrics();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleDeleteTax(taxId, vehicleId) {
  if (!confirm('Are you sure you want to delete this tax record?')) return;
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/taxes/${taxId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to delete tax record');
    }
    showToast('Tax record deleted', 'info');
    loadTaxesForSelectedVehicle();
    if (state.user && state.user.role === 'admin') loadDashboardMetrics();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Receipt Modal Handlers
function openTaxReceiptModal(taxId, vehicleId, details) {
  document.getElementById('receipt-tax-id').value = taxId;
  document.getElementById('receipt-vehicle-id').value = vehicleId;
  document.getElementById('receipt-tax-details').value = details;
  document.getElementById('receipt-tax-file').value = '';
  document.getElementById('modal-upload-tax-receipt').classList.add('active');
}

function closeTaxReceiptModal() {
  document.getElementById('modal-upload-tax-receipt').classList.remove('active');
}

async function handleTaxReceiptUploadSubmit(e) {
  e.preventDefault();
  const taxId = document.getElementById('receipt-tax-id').value;
  const vehicleId = document.getElementById('receipt-vehicle-id').value;
  const fileInput = document.getElementById('receipt-tax-file');

  if (!fileInput.files || fileInput.files.length === 0) {
    showToast('Please select a receipt file', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/taxes/${taxId}/receipt`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` },
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to upload receipt');
    }

    showToast('Receipt uploaded successfully!', 'success');
    closeTaxReceiptModal();
    loadTaxesForSelectedVehicle();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// Government Charges
// ==========================================

function toggleAddChargeForm() {
  const form = document.getElementById('card-add-charge');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function loadGovernmentCharges(vehicleId) {
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/government-charges`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;
    const charges = await res.json();
    renderGovernmentChargesTable(charges, vehicleId);
  } catch (err) {
    console.error(err);
  }
}

function renderGovernmentChargesTable(charges, vehicleId) {
  const tbody = document.getElementById('tbody-charges');
  if (!charges || charges.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-text-muted);">No government charges recorded.</td></tr>`;
    return;
  }

  const isAdmin = state.user && state.user.role === 'admin';
  tbody.innerHTML = charges.map(c => `
    <tr>
      <td><strong>${c.charge_type.replace(/_/g, ' ')}</strong></td>
      <td>${c.state} ${c.authority ? `(${c.authority})` : ''}</td>
      <td>${new Date(c.period_start).toLocaleDateString('en-GB')} – ${new Date(c.period_end).toLocaleDateString('en-GB')}</td>
      <td>${new Date(c.valid_until).toLocaleDateString('en-GB')}</td>
      <td>₹${Number(c.amount).toLocaleString('en-IN')}</td>
      <td><span class="badge badge-${c.status.toLowerCase()}">${c.status.replace(/_/g, ' ')}</span></td>
      <td>
        ${isAdmin ? `<button class="btn btn-secondary btn-sm" style="color: var(--color-error);" onclick="handleDeleteCharge(${c.id}, ${vehicleId})">Delete</button>` : '-'}
      </td>
    </tr>
  `).join('');
}

async function handleCreateCharge(e) {
  e.preventDefault();
  const vehicleId = document.getElementById('tax-vehicle-id').value;
  if (!vehicleId) {
    showToast('Select a vehicle first', 'error');
    return;
  }

  const payload = {
    charge_type: document.getElementById('charge-type').value,
    state: document.getElementById('charge-state').value,
    authority: document.getElementById('charge-authority').value || null,
    amount: parseFloat(document.getElementById('charge-amount').value),
    period_start: document.getElementById('charge-period-start').value,
    period_end: document.getElementById('charge-period-end').value,
    payment_date: document.getElementById('charge-payment-date').value || null,
    valid_until: document.getElementById('charge-valid-until').value,
    payment_reference: document.getElementById('charge-payment-ref').value || null
  };

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/government-charges`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save charge');
    }

    showToast('Government charge recorded!', 'success');
    document.getElementById('form-add-charge').reset();
    toggleAddChargeForm();
    loadGovernmentCharges(vehicleId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleDeleteCharge(chargeId, vehicleId) {
  if (!confirm('Delete this government charge record?')) return;
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/government-charges/${chargeId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      showToast('Charge deleted', 'info');
      loadGovernmentCharges(vehicleId);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// Challans
// ==========================================

function toggleAddChallanForm() {
  const form = document.getElementById('card-add-challan');
  form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

async function loadChallans(vehicleId) {
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/challans`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;
    const challans = await res.json();
    renderChallansTable(challans, vehicleId);
  } catch (err) {
    console.error(err);
  }
}

function renderChallansTable(challans, vehicleId) {
  const tbody = document.getElementById('tbody-challans');
  if (!challans || challans.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--color-text-muted);">No challans recorded.</td></tr>`;
    return;
  }

  const isAdmin = state.user && state.user.role === 'admin';
  tbody.innerHTML = challans.map(ch => `
    <tr>
      <td><strong>${ch.challan_number}</strong></td>
      <td>${ch.authority || '-'}</td>
      <td>${ch.reason || '-'}</td>
      <td>${new Date(ch.issue_date).toLocaleDateString('en-GB')}</td>
      <td>${ch.due_date ? new Date(ch.due_date).toLocaleDateString('en-GB') : '-'}</td>
      <td>₹${Number(ch.amount).toLocaleString('en-IN')}</td>
      <td><span class="badge badge-${ch.status.toLowerCase()}">${ch.status}</span></td>
      <td>
        ${isAdmin ? `<button class="btn btn-secondary btn-sm" style="color: var(--color-error);" onclick="handleDeleteChallan(${ch.id}, ${vehicleId})">Delete</button>` : '-'}
      </td>
    </tr>
  `).join('');
}

async function handleCreateChallan(e) {
  e.preventDefault();
  const vehicleId = document.getElementById('tax-vehicle-id').value;
  if (!vehicleId) {
    showToast('Select a vehicle first', 'error');
    return;
  }

  const payload = {
    challan_number: document.getElementById('challan-num').value,
    authority: document.getElementById('challan-authority').value || null,
    issue_date: document.getElementById('challan-issue-date').value,
    amount: parseFloat(document.getElementById('challan-amount').value),
    due_date: document.getElementById('challan-due-date').value || null,
    status: document.getElementById('challan-status').value,
    reason: document.getElementById('challan-reason').value || null
  };

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/challans`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to save challan');
    }

    showToast('Challan record saved!', 'success');
    document.getElementById('form-add-challan').reset();
    toggleAddChallanForm();
    loadChallans(vehicleId);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

async function handleDeleteChallan(challanId, vehicleId) {
  if (!confirm('Delete this challan record?')) return;
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/challans/${challanId}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (res.ok) {
      showToast('Challan deleted', 'info');
      loadChallans(vehicleId);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// FASTag
// ==========================================

async function loadFASTag(vehicleId) {
  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/fastag`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    if (!res.ok) return;
    const tag = await res.json();

    document.getElementById('fastag-number').value = tag.tag_number || '';
    document.getElementById('fastag-provider').value = tag.tag_provider || '';
    document.getElementById('fastag-status').value = tag.tag_status || 'ACTIVE';
    document.getElementById('fastag-account-ref').value = tag.linked_account_ref || '';
    document.getElementById('fastag-balance').value = tag.last_balance !== null && tag.last_balance !== undefined ? tag.last_balance : '';
    document.getElementById('fastag-notes').value = tag.notes || '';
  } catch (err) {
    console.error(err);
  }
}

async function handleSaveFASTag(e) {
  e.preventDefault();
  const vehicleId = document.getElementById('tax-vehicle-id').value;
  if (!vehicleId) {
    showToast('Select a vehicle first', 'error');
    return;
  }

  const payload = {
    tag_number: document.getElementById('fastag-number').value || null,
    tag_provider: document.getElementById('fastag-provider').value || null,
    tag_status: document.getElementById('fastag-status').value,
    linked_account_ref: document.getElementById('fastag-account-ref').value || null,
    last_balance: document.getElementById('fastag-balance').value ? parseFloat(document.getElementById('fastag-balance').value) : null,
    notes: document.getElementById('fastag-notes').value || null
  };

  try {
    const res = await fetch(`${API_BASE}/vehicles/${vehicleId}/fastag`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update FASTag information');
    }

    showToast('FASTag details updated successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ==========================================
// Excel Export
// ==========================================

async function handleExportTaxesExcel() {
  try {
    showToast('Generating Fleet Tax Excel report...', 'info');
    const res = await fetch(`${API_BASE}/admin/taxes/export`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to export tax report');
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Fleet_Taxes_Export_${new Date().toISOString().split('T')[0]}.xlsx`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
    showToast('Tax report downloaded successfully!', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
}
