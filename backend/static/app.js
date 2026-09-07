// Client-Side Logic for AI Code Auditor Web Application
const API_BASE = '/api/v1';

let state = {
  token: localStorage.getItem('auth_token') || null,
  user: JSON.parse(localStorage.getItem('auth_user') || 'null'),
  projects: [],
  currentProject: null,
  currentReview: null,
  currentReviewId: null,
  solverResult: null,
  generatorResult: null,
  pdfResult: null,
  selectedPdfFiles: [],
  notifications: []
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  if (state.token && state.user) {
    showSection('dashboardSection');
    loadNotifications();
  } else {
    showAuth();
  }

  // Setup Form Listeners
  document.getElementById('loginForm').addEventListener('submit', handleLogin);
  document.getElementById('registerForm').addEventListener('submit', handleRegister);
  document.getElementById('titleForm').addEventListener('submit', handleTitleProjectCreate);
  document.getElementById('githubForm').addEventListener('submit', handleGithubImport);
  document.getElementById('zipForm').addEventListener('submit', handleZipUpload);
  document.getElementById('logoutBtn').addEventListener('click', handleLogout);

  // Close notification dropdown when clicking outside
  document.addEventListener('click', (e) => {
    const wrapper = document.getElementById('notifWrapper');
    if (wrapper && !wrapper.contains(e.target)) {
      const dropdown = document.getElementById('notifDropdown');
      if (dropdown) dropdown.classList.add('hidden');
    }
  });
});

// Helper to extract clean user-friendly error messages from any API response
function parseErrorMessage(json, defaultMsg = 'An unexpected error occurred') {
  if (!json) return defaultMsg;

  // 1. Custom APIResponse error object
  if (json.error) {
    if (typeof json.error === 'string') return json.error;
    if (typeof json.error.message === 'string') return json.error.message;
  }

  // 2. Direct message string if success is false
  if (typeof json.message === 'string' && json.success === false) {
    return json.message;
  }

  // 3. FastAPI detail field (string or array of field validation objects)
  if (json.detail) {
    if (typeof json.detail === 'string') return json.detail;
    if (Array.isArray(json.detail)) {
      return json.detail
        .map(item => {
          if (typeof item === 'string') return item;
          const loc = item.loc ? item.loc.filter(l => l !== 'body').join(' → ') : '';
          return (loc ? `${loc}: ` : '') + (item.msg || 'Invalid field input');
        })
        .join(' | ');
    }
    if (typeof json.detail === 'object') {
      return json.detail.message || JSON.stringify(json.detail);
    }
  }

  return defaultMsg;
}

// View Navigation
function showAuth() {
  const sections = ['authSection', 'dashboardSection', 'reportSection', 'solverSection', 'generatorSection', 'pdfSection', 'doubtSection', 'profileSection'];
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });
  document.getElementById('authSection').classList.remove('hidden');
  document.getElementById('userInfo').classList.add('hidden');
  document.getElementById('mainNavLinks').classList.add('hidden');
}

function showSection(sectionId) {
  if (!state.token || !state.user) {
    showAuth();
    return;
  }

  document.getElementById('mainNavLinks').classList.remove('hidden');
  const sections = ['authSection', 'dashboardSection', 'reportSection', 'solverSection', 'generatorSection', 'pdfSection', 'doubtSection', 'profileSection'];
  sections.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });

  const target = document.getElementById(sectionId);
  if (target) target.classList.remove('hidden');

  // Update navbar active link
  const linkMap = {
    'dashboardSection': 'navLinkProjects',
    'solverSection': 'navLinkSolver',
    'generatorSection': 'navLinkGenerator',
    'pdfSection': 'navLinkPdf',
    'doubtSection': 'navLinkDoubt',
    'profileSection': 'navLinkProfile'
  };

  Object.values(linkMap).forEach(linkId => {
    const link = document.getElementById(linkId);
    if (link) link.classList.remove('active');
  });

  if (linkMap[sectionId]) {
    const activeLink = document.getElementById(linkMap[sectionId]);
    if (activeLink) activeLink.classList.add('active');
  }

  updateUserUI();
  if (!state.user && state.token) {
    fetchUserProfile();
  }

  if (sectionId === 'dashboardSection') {
    loadProjects();
  }
  if (sectionId === 'profileSection') {
    loadProfilePage();
  }
}

function showDashboard() {
  showSection('dashboardSection');
}

function showReport(projectId) {
  showSection('reportSection');
  fetchProjectDetails(projectId);
}

// Auth Handlers
function switchAuthTab(type) {
  const loginForm = document.getElementById('loginForm');
  const regForm = document.getElementById('registerForm');
  const loginBtn = document.getElementById('tabLoginBtn');
  const regBtn = document.getElementById('tabRegisterBtn');

  if (type === 'login') {
    loginForm.classList.remove('hidden');
    regForm.classList.add('hidden');
    loginBtn.classList.add('active');
    regBtn.classList.remove('active');
  } else {
    loginForm.classList.add('hidden');
    regForm.classList.remove('hidden');
    loginBtn.classList.remove('active');
    regBtn.classList.add('active');
  }
  hideAlert('authAlert');
}

async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value.trim();

  hideAlert('authAlert');

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      const errorMsg = parseErrorMessage(json, 'Login failed. Please check credentials.');
      throw new Error(errorMsg);
    }

    state.token = json.data.access_token;
    localStorage.setItem('auth_token', state.token);
    
    await fetchUserProfile();
    showDashboard();
  } catch (err) {
    showAlert('authAlert', err.message, 'error');
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const email = document.getElementById('regEmail').value.trim();
  const username = document.getElementById('regUsername').value.trim();
  const password = document.getElementById('regPassword').value.trim();

  hideAlert('authAlert');

  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, username, password })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      const errorMsg = parseErrorMessage(json, 'Registration failed. User or email may already exist.');
      throw new Error(errorMsg);
    }

    showAlert('authAlert', 'Account created successfully! Logging in...', 'success');
    
    // Auto login
    document.getElementById('loginUsername').value = username;
    document.getElementById('loginPassword').value = password;
    setTimeout(() => {
      handleLogin({ preventDefault: () => {} });
    }, 800);

  } catch (err) {
    showAlert('authAlert', err.message, 'error');
  }
}

function updateUserUI() {
  if (state.user) {
    const name = state.user.username || 'Student';
    const userDisplay = document.getElementById('usernameDisplay');
    const dashUser = document.getElementById('dashUser');
    const userInfo = document.getElementById('userInfo');

    if (userDisplay) userDisplay.textContent = name;
    if (dashUser) dashUser.textContent = name;
    if (userInfo) userInfo.classList.remove('hidden');
  }
}

async function fetchUserProfile() {
  if (!state.token) return;
  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();
    if (json.success) {
      state.user = json.data;
      localStorage.setItem('auth_user', JSON.stringify(state.user));
      updateUserUI();
    }
  } catch (err) {
    console.error('Fetch profile error:', err);
  }
}

function handleLogout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  showAuth();
}

// Projects Logic
async function loadProjects() {
  const grid = document.getElementById('projectsGrid');
  grid.innerHTML = '<div class="spinner"></div>';

  try {
    const res = await fetch(`${API_BASE}/projects`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Failed to fetch projects'));
    }

    state.projects = json.data || [];

    if (state.projects.length === 0) {
      grid.innerHTML = `
        <div class="auth-card" style="grid-column: 1 / -1; max-width: 500px; margin: 40px auto; text-align: center;">
          <i class="fa-solid fa-folder-open" style="font-size: 48px; color: var(--text-muted); margin-bottom: 16px;"></i>
          <h3>No Projects Imported Yet</h3>
          <p style="color: var(--text-muted); margin: 8px 0 20px;">Import a GitHub repository URL or upload a ZIP file to get AI code review scores.</p>
          <button class="btn btn-primary" onclick="openModal('uploadModal')"><i class="fa-solid fa-plus"></i> Import First Project</button>
        </div>
      `;
      return;
    }

    grid.innerHTML = state.projects.map(p => `
      <div class="project-card" onclick="showReport('${p.id}')">
        <div class="pc-top">
          <span class="pc-title">${escapeHtml(p.title)}</span>
          <span class="pc-badge status-${(p.status || 'READY').toLowerCase()}">${p.status || 'READY'}</span>
        </div>
        <div class="pc-meta">
          <span><i class="fa-solid fa-code"></i> ${p.detected_languages?.join(', ') || 'Codebase'}</span>
          <span><i class="fa-solid fa-file"></i> ${p.total_files || 0} files</span>
          <span><i class="fa-solid fa-list-ol"></i> ${p.total_lines_of_code || 0} LOC</span>
        </div>
        <div class="pc-footer">
          <span style="color: var(--text-muted);"><i class="fa-solid fa-calendar"></i> ${new Date(p.created_at).toLocaleDateString()}</span>
          <span class="btn btn-sm btn-outline"><i class="fa-solid fa-microchip"></i> View Audit <i class="fa-solid fa-chevron-right"></i></span>
        </div>
      </div>
    `).join('');
  } catch (err) {
    grid.innerHTML = `<div class="alert alert-error">${escapeHtml(err.message)}</div>`;
  }
}

// Report Logic
async function fetchProjectDetails(projectId) {
  state.currentProject = { id: projectId };
  const loading = document.getElementById('reviewLoading');
  const content = document.getElementById('reviewContent');
  
  loading.classList.remove('hidden');
  content.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();
    const projData = json.data;

    document.getElementById('reportProjectTitle').textContent = projData.project.title;
    document.getElementById('reportProjectMeta').textContent = `${projData.framework || 'Codebase'} • ${projData.file_count} Files • ${projData.lines_of_code} LOC`;

    // Fetch Review
    const revRes = await fetch(`${API_BASE}/projects/${projectId}/review`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (revRes.status === 404) {
      await triggerReview();
      return;
    }

    const revJson = await revRes.json();
    renderReview(revJson.data);
  } catch (err) {
    loading.classList.add('hidden');
    content.classList.remove('hidden');
  }
}

async function triggerReview() {
  const loading = document.getElementById('reviewLoading');
  const content = document.getElementById('reviewContent');

  loading.classList.remove('hidden');
  content.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/projects/${state.currentProject.id}/review`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();
    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'AI Review failed'));
    }
    renderReview(json.data);
  } catch (err) {
    alert('AI Review run failed: ' + err.message);
    loading.classList.add('hidden');
  }
}

function renderReview(data) {
  state.currentReview = data;
  state.currentReviewId = data.id || data.review_id || null;
  const loading = document.getElementById('reviewLoading');
  const content = document.getElementById('reviewContent');

  loading.classList.add('hidden');
  content.classList.remove('hidden');

  const grade = data.grade || 'B';
  const gradeCircle = document.getElementById('gradeCircle');
  gradeCircle.textContent = grade;
  gradeCircle.className = `grade-circle grade-${grade[0]}`;

  document.getElementById('overallScoreText').textContent = `Overall Quality Grade: ${grade} (${data.overall_score?.toFixed(1) || 85}/100)`;
  document.getElementById('overallSummary').textContent = data.summary || 'Consolidated multi-agent code analysis complete.';

  // Component Scores
  const scores = data.component_scores || {};
  setScore('Sec', scores.security || 85);
  setScore('Maint', scores.maintainability || 85);
  setScore('Perf', scores.performance || 85);
  setScore('Read', scores.readability || 85);

  // Render Findings
  const findings = data.findings || {};
  const allFindings = [
    ...(findings.security || []),
    ...(findings.bugs || []),
    ...(findings.code_smells || []),
    ...(findings.code_review || [])
  ];

  document.getElementById('countFindings').textContent = allFindings.length;
  const findingsList = document.getElementById('findingsList');

  if (allFindings.length === 0) {
    findingsList.innerHTML = `
      <div class="alert alert-success"><i class="fa-solid fa-circle-check"></i> Great Job! No critical bugs or security risks detected.</div>
    `;
  } else {
    findingsList.innerHTML = allFindings.map(f => `
      <div class="finding-tile ${(f.severity || 'low').toLowerCase()}">
        <div class="ft-top">
          <span class="ft-title"><i class="fa-solid fa-triangle-exclamation"></i> ${escapeHtml(f.title || f.issue || 'Finding')}</span>
          <span class="ft-loc">${f.file_path ? f.file_path + (f.line_number ? ':' + f.line_number : '') : ''}</span>
        </div>
        <div class="ft-desc">${escapeHtml(f.description || f.suggestion || '')}</div>
        ${f.remediation ? `<div class="ft-fix">💡 <b>Fix Recommendation:</b> ${escapeHtml(f.remediation)}</div>` : ''}
      </div>
    `).join('');
  }

  // Render Docs
  const docs = data.documentation || {};
  document.getElementById('docsMarkdown').textContent = docs.readme_markdown || 'No documentation generated.';

  // Render Tests
  const tests = data.test_cases || [];
  document.getElementById('countTests').textContent = tests.length;
  const testsList = document.getElementById('testsList');

  if (tests.length === 0) {
    testsList.innerHTML = `<div class="alert alert-error">No test cases generated.</div>`;
  } else {
    testsList.innerHTML = tests.map(t => `
      <div class="test-card">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <b style="font-size:15px; color:#fff;">🧪 ${escapeHtml(t.test_name || 'Unit Test')}</b>
          <span class="pc-badge status-ready">${t.test_type || 'UNIT'}</span>
        </div>
        <div style="font-size:12px; color:var(--text-muted); margin-top:4px;">Target: ${t.target_file || 'Source File'}</div>
        <pre><code>${escapeHtml(t.code || '')}</code></pre>
      </div>
    `).join('');
  }

  // Load comments for this review
  if (state.currentReviewId) loadComments();
}

function setScore(id, val) {
  document.getElementById(`score${id}`).textContent = `${val.toFixed(0)}%`;
  document.getElementById(`bar${id}`).style.width = `${val}%`;
}

function switchReportTab(name) {
  document.querySelectorAll('.rep-tab').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.rep-tab-content').forEach(c => c.classList.add('hidden'));

  event.currentTarget.classList.add('active');
  document.getElementById(`tab${name.charAt(0).toUpperCase() + name.slice(1)}`).classList.remove('hidden');
}

// Modal Handlers
function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
  hideAlert('importAlert');
}

function switchImportTab(type) {
  const titleForm = document.getElementById('titleForm');
  const ghForm = document.getElementById('githubForm');
  const zipForm = document.getElementById('zipForm');
  const titleTab = document.getElementById('importTabTitle');
  const ghTab = document.getElementById('importTabGithub');
  const zipTab = document.getElementById('importTabZip');

  [titleForm, ghForm, zipForm].forEach(f => f && f.classList.add('hidden'));
  [titleTab, ghTab, zipTab].forEach(t => t && t.classList.remove('active'));

  if (type === 'title') {
    if (titleForm) titleForm.classList.remove('hidden');
    if (titleTab) titleTab.classList.add('active');
  } else if (type === 'github') {
    if (ghForm) ghForm.classList.remove('hidden');
    if (ghTab) ghTab.classList.add('active');
  } else if (type === 'zip') {
    if (zipForm) zipForm.classList.remove('hidden');
    if (zipTab) zipTab.classList.add('active');
  }
}

async function handleTitleProjectCreate(e) {
  e.preventDefault();
  const title = document.getElementById('titleProjectTitle').value.trim();
  const description = document.getElementById('titleDescription').value.trim();
  const language = document.getElementById('titleLanguage').value;

  if (!title) return;

  showAlert('importAlert', 'Generating starter codebase & initializing project...', 'success');

  try {
    const res = await fetch(`${API_BASE}/projects/create-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ title, description, language })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Failed to create project from title'));
    }

    closeModal('uploadModal');
    showReport(json.data.id);
  } catch (err) {
    showAlert('importAlert', err.message, 'error');
  }
}

async function handleGithubImport(e) {
  e.preventDefault();
  const github_url = document.getElementById('githubUrl').value.trim();
  const title = document.getElementById('githubTitle').value.trim();

  showAlert('importAlert', 'Cloning & analyzing GitHub repository... Please wait.', 'success');

  try {
    const res = await fetch(`${API_BASE}/projects/github`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ github_url, title })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'GitHub import failed'));
    }

    closeModal('uploadModal');
    showReport(json.data.id);
  } catch (err) {
    showAlert('importAlert', err.message, 'error');
  }
}

async function handleZipUpload(e) {
  e.preventDefault();
  const fileInput = document.getElementById('zipFileInput');
  const title = document.getElementById('zipTitle').value.trim();

  if (!fileInput.files[0]) return;

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  if (title) formData.append('title', title);

  showAlert('importAlert', 'Uploading & extracting ZIP archive... Please wait.', 'success');

  try {
    const res = await fetch(`${API_BASE}/projects/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` },
      body: formData
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'ZIP upload failed'));
    }

    closeModal('uploadModal');
    showReport(json.data.id);
  } catch (err) {
    showAlert('importAlert', err.message, 'error');
  }
}

// AI Error Detector & Solver Handlers
async function handleSolveError() {
  const code = document.getElementById('solverCode').value.trim();
  const error_log = document.getElementById('solverErrorLog').value.trim();
  const language = document.getElementById('solverLang').value;

  if (!code) {
    alert('Please enter or paste a source code snippet to analyze.');
    return;
  }

  const loading = document.getElementById('solverLoading');
  const placeholder = document.getElementById('solverPlaceholder');
  const result = document.getElementById('solverResult');
  const solveBtn = document.getElementById('solveBtn');

  loading.classList.remove('hidden');
  placeholder.classList.add('hidden');
  result.classList.add('hidden');
  solveBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/ai-tools/detect-and-solve-errors`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ code, error_log, language })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Error analysis failed'));
    }

    state.solverResult = json.data;

    document.getElementById('solverSummaryText').textContent = json.data.error_summary || 'Error Solution';
    document.getElementById('solverCause').textContent = json.data.root_cause || json.data.explanation;
    document.getElementById('solverCorrectedCode').textContent = json.data.corrected_code;

    const tipsList = document.getElementById('solverTips');
    tipsList.innerHTML = (json.data.prevention_tips || []).map(tip => `<li><i class="fa-solid fa-check"></i> ${escapeHtml(tip)}</li>`).join('');

    result.classList.remove('hidden');
  } catch (err) {
    alert(`Error: ${err.message}`);
    placeholder.classList.remove('hidden');
  } finally {
    loading.classList.add('hidden');
    solveBtn.disabled = false;
  }
}

function copySolverCode() {
  if (!state.solverResult) return;
  navigator.clipboard.writeText(state.solverResult.corrected_code);
  alert('Corrected code copied to clipboard!');
}

async function createProjectFromSolver() {
  if (!state.solverResult) return;
  const title = prompt('Enter a Title for this fixed project:', 'Fixed Code Project');
  if (!title) return;

  try {
    const res = await fetch(`${API_BASE}/projects/create-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({
        title,
        description: state.solverResult.error_summary,
        language: document.getElementById('solverLang').value
      })
    });
    const json = await res.json();
    if (json.success) {
      alert('Project created successfully!');
      showReport(json.data.id);
    }
  } catch (err) {
    alert(`Failed to save project: ${err.message}`);
  }
}

// AI Code Studio Handlers
async function handleGenerateCode() {
  const promptText = document.getElementById('genPrompt').value.trim();
  const language = document.getElementById('genLang').value;
  const framework = document.getElementById('genFramework').value.trim();

  if (!promptText) {
    alert('Please enter a prompt or project requirement.');
    return;
  }

  const loading = document.getElementById('genLoading');
  const placeholder = document.getElementById('genPlaceholder');
  const result = document.getElementById('genResult');
  const generateBtn = document.getElementById('generateBtn');

  loading.classList.remove('hidden');
  placeholder.classList.add('hidden');
  result.classList.add('hidden');
  generateBtn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/ai-tools/generate-code`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({ prompt: promptText, language, framework })
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Code generation failed'));
    }

    state.generatorResult = json.data;

    document.getElementById('genTitle').textContent = json.data.title || 'Generated Code Solution';
    document.getElementById('genFileTag').textContent = json.data.file_name || 'solution';
    document.getElementById('genOutputCode').textContent = json.data.generated_code;
    document.getElementById('genExplanation').textContent = json.data.explanation;

    result.classList.remove('hidden');
  } catch (err) {
    alert(`Error: ${err.message}`);
    placeholder.classList.remove('hidden');
  } finally {
    loading.classList.add('hidden');
    generateBtn.disabled = false;
  }
}

function copyGenCode() {
  if (!state.generatorResult) return;
  navigator.clipboard.writeText(state.generatorResult.generated_code);
  alert('Generated code copied to clipboard!');
}

async function createProjectFromGenerator() {
  if (!state.generatorResult) return;
  const title = prompt('Enter a Title for this generated project:', state.generatorResult.title || 'Generated Project');
  if (!title) return;

  try {
    const res = await fetch(`${API_BASE}/projects/create-title`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({
        title,
        description: state.generatorResult.explanation,
        language: state.generatorResult.language
      })
    });
    const json = await res.json();
    if (json.success) {
      alert('Project created successfully!');
      showReport(json.data.id);
    }
  } catch (err) {
    alert(`Failed to save project: ${err.message}`);
  }
}

// PDF Bundle Handlers
function handlePdfFilesSelect(evt) {
  const files = evt.target.files;
  if (!files || files.length === 0) return;

  state.selectedPdfFiles = Array.from(files);
  const listEl = document.getElementById('pdfFileList');
  const btn = document.getElementById('pdfSummarizeBtn');

  listEl.innerHTML = state.selectedPdfFiles.map(f => `
    <span class="pdf-file-tag"><i class="fa-solid fa-file-pdf"></i> ${escapeHtml(f.name)} (${(f.size / 1024).toFixed(0)} KB)</span>
  `).join('');

  listEl.classList.remove('hidden');
  btn.disabled = false;
  btn.classList.remove('disabled');
}

async function handleSummarizePdfBundle() {
  if (state.selectedPdfFiles.length === 0) return;

  const loading = document.getElementById('pdfLoading');
  const result = document.getElementById('pdfResult');
  const btn = document.getElementById('pdfSummarizeBtn');

  loading.classList.remove('hidden');
  result.classList.add('hidden');
  btn.disabled = true;

  const formData = new FormData();
  state.selectedPdfFiles.forEach(file => {
    formData.append('files', file);
  });

  try {
    const res = await fetch(`${API_BASE}/pdf/summarize-bundle`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${state.token}` },
      body: formData
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'PDF processing failed'));
    }

    state.pdfResult = json.data;

    document.getElementById('pdfBundleTitle').textContent = json.data.combined_title;
    document.getElementById('pdfBundleMeta').textContent = `${json.data.total_pdfs_processed} PDFs Processed • ${json.data.total_pages} Total Pages`;
    document.getElementById('pdfExecutiveSummary').textContent = json.data.executive_summary;

    // Render High Yield Topics
    const topicsGrid = document.getElementById('pdfTopicsList');
    topicsGrid.innerHTML = (json.data.high_yield_topics || []).map(t => `
      <div class="topic-card">
        <span class="badge-pill ${t.importance?.includes('High') ? 'high' : 'core'}">${escapeHtml(t.importance || '⭐ Core Concept')}</span>
        <h4>${escapeHtml(t.topic)}</h4>
        <p>${escapeHtml(t.summary)}</p>
      </div>
    `).join('');

    // Render Definitions & Formulas
    const defsGrid = document.getElementById('pdfDefsList');
    defsGrid.innerHTML = (json.data.definitions_and_formulas || []).map(d => `
      <div class="def-card">
        <h4 class="text-blue"><i class="fa-solid fa-bookmark"></i> ${escapeHtml(d.term)}</h4>
        <p><strong>Definition:</strong> ${escapeHtml(d.definition)}</p>
        <p style="color: var(--text-muted); font-size: 12px; margin-top: 6px;">💡 <strong>Exam Key Point:</strong> ${escapeHtml(d.key_point)}</p>
      </div>
    `).join('');

    // Render Exam Questions
    const qList = document.getElementById('pdfQuestionsList');
    qList.innerHTML = (json.data.exam_questions || []).map((q, idx) => `
      <div class="question-card">
        <div class="q-header">
          <span class="q-title">Q${idx + 1}: ${escapeHtml(q.question)}</span>
          <span class="q-marks">${escapeHtml(q.marks || '10 Marks')}</span>
        </div>
        <div class="q-ans"><strong>Model Answer:</strong><br>${escapeHtml(q.answer)}</div>
      </div>
    `).join('');

    // Render Cheatsheet
    document.getElementById('pdfCheatsheetMarkdown').textContent = json.data.cheatsheet_markdown;

    result.classList.remove('hidden');
  } catch (err) {
    alert(`Error processing PDF bundle: ${err.message}`);
  } finally {
    loading.classList.add('hidden');
    btn.disabled = false;
  }
}

function switchPdfTab(tabName) {
  document.querySelectorAll('.pdf-tab').forEach(b => b.classList.remove('active'));
  ['Topics', 'Defs', 'Questions', 'Cheatsheet'].forEach(t => {
    const el = document.getElementById(`pdfTab${t}`);
    if (el) el.classList.add('hidden');
  });

  event.currentTarget.classList.add('active');
  const targetId = `pdfTab${tabName.charAt(0).toUpperCase() + tabName.slice(1)}`;
  const target = document.getElementById(targetId);
  if (target) target.classList.remove('hidden');
}

async function downloadMergedPdf() {
  if (!state.pdfResult || !state.pdfResult.bundle_id) {
    alert('No merged PDF bundle available for download.');
    return;
  }

  const btn = document.getElementById('downloadMergedPdfBtn');
  const originalHTML = btn.innerHTML;
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Downloading...';

  try {
    const res = await fetch(`${API_BASE}/pdf/download-merged/${state.pdfResult.bundle_id}`, {
      method: 'GET',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });

    if (!res.ok) {
      const errJson = await res.json().catch(() => null);
      throw new Error(parseErrorMessage(errJson, `Download failed (HTTP ${res.status})`));
    }

    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `merged_study_bundle_${state.pdfResult.bundle_id.slice(0, 8)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert(`Download failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalHTML;
  }
}

// AI Tutor Doubt Assistant Handlers
let chatHistory = [];

function toggleDoubtCodeContext() {
  const wrap = document.getElementById('doubtCodeWrap');
  wrap.classList.toggle('hidden');
}

function sendQuickDoubt(text) {
  document.getElementById('doubtInput').value = text;
  handleSendDoubt();
}

async function handleSendDoubt() {
  const inputEl = document.getElementById('doubtInput');
  const codeCtxEl = document.getElementById('doubtCodeContext');
  const query = inputEl.value.trim();
  const code_context = codeCtxEl ? codeCtxEl.value.trim() : '';

  if (!query) return;

  const thread = document.getElementById('chatThread');
  const sendBtn = document.getElementById('sendDoubtBtn');

  // 1. Add User message bubble
  const userMsgId = `user_msg_${Date.now()}`;
  thread.innerHTML += `
    <div class="chat-msg user" id="${userMsgId}">
      <div class="msg-avatar"><i class="fa-solid fa-user"></i></div>
      <div class="msg-content">
        <p>${escapeHtml(query)}</p>
        ${code_context ? `<pre><code>${escapeHtml(code_context)}</code></pre>` : ''}
      </div>
    </div>
  `;

  // Clear input
  inputEl.value = '';
  sendBtn.disabled = true;

  // 2. Add AI loading bubble
  const aiLoadingId = `ai_loading_${Date.now()}`;
  thread.innerHTML += `
    <div class="chat-msg ai" id="${aiLoadingId}">
      <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
      <div class="msg-content">
        <p><i class="fa-solid fa-spinner fa-spin"></i> Thinking & preparing step-by-step explanation...</p>
      </div>
    </div>
  `;

  thread.scrollTop = thread.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/ai-tools/clear-doubt`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify({
        query,
        code_context,
        chat_history: chatHistory
      })
    });

    // Safe JSON parse — server may return plain-text on 500
    let json;
    const rawText = await res.text();
    try {
      json = JSON.parse(rawText);
    } catch (_) {
      json = { success: false, message: rawText.slice(0, 200) || `Server error (HTTP ${res.status})` };
    }

    const loadingEl = document.getElementById(aiLoadingId);

    if (!res.ok || !json.success) {
      if (loadingEl) loadingEl.remove();
      throw new Error(parseErrorMessage(json, 'Failed to clear doubt'));
    }

    const data = json.data;

    // Track history
    chatHistory.push({ sender: 'user', text: query });
    chatHistory.push({ sender: 'assistant', text: data.answer });

    // Render AI response
    if (loadingEl) {
      loadingEl.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-robot"></i></div>
        <div class="msg-content">
          <div>${formatDoubtAnswer(data.answer)}</div>
          ${data.key_takeaways && data.key_takeaways.length > 0 ? `
            <div class="res-box mt-2">
              <label class="res-label"><i class="fa-solid fa-lightbulb text-warning"></i> Key Takeaways</label>
              <ul class="tips-list">
                ${data.key_takeaways.map(t => `<li>${escapeHtml(t)}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
          ${data.related_topics && data.related_topics.length > 0 ? `
            <div class="chip-row mt-2">
              <span class="res-label" style="width:100%; margin-bottom: 2px;">Ask Follow-up:</span>
              ${data.related_topics.map(topic => `
                <button class="chip-btn" onclick="sendQuickDoubt('Tell me more about ${escapeHtml(topic)}')">💡 ${escapeHtml(topic)}</button>
              `).join('')}
            </div>
          ` : ''}
        </div>
      `;
    }

  } catch (err) {
    const loadingEl = document.getElementById(aiLoadingId);
    if (loadingEl) {
      loadingEl.innerHTML = `
        <div class="msg-avatar"><i class="fa-solid fa-triangle-exclamation text-red"></i></div>
        <div class="msg-content alert-error">
          <p>Sorry, I encountered an error answering your doubt: ${escapeHtml(err.message)}</p>
        </div>
      `;
    }
  } finally {
    sendBtn.disabled = false;
    thread.scrollTop = thread.scrollHeight;
  }
}

function formatDoubtAnswer(text) {
  if (!text) return '';
  let formatted = escapeHtml(text);
  // Format markdown headers
  formatted = formatted.replace(/^### (.*$)/gim, '<h4 style="margin:8px 0 4px; color:#A78BFA;">$1</h4>');
  formatted = formatted.replace(/^## (.*$)/gim, '<h3 style="margin:10px 0 6px; color:#818CF8;">$1</h3>');
  // Format code blocks ```python ... ```
  formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  // Format inline code `code`
  formatted = formatted.replace(/`([^`]+)`/g, '<code style="background:#0F172A; padding:2px 6px; border-radius:4px; color:#A7F3D0;">$1</code>');
  // Format newlines
  formatted = formatted.replace(/\n/g, '<br>');
  return formatted;
}

// Helpers
function showAlert(id, msg, type) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = `alert alert-${type}`;
  el.classList.remove('hidden');
}

function hideAlert(id) {
  document.getElementById(id).classList.add('hidden');
}

function escapeHtml(str) {
  return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ─────────────────────────────────────────────────
//  NOTIFICATIONS
// ─────────────────────────────────────────────────
async function loadNotifications() {
  if (!state.token) return;
  try {
    const res = await fetch(`${API_BASE}/notifications`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();
    if (json.success) {
      state.notifications = json.data || [];
      renderNotifications();
    }
  } catch (err) {
    console.error('Notifications load failed:', err);
  }
}

function renderNotifications() {
  const list = document.getElementById('notifList');
  const badge = document.getElementById('notifBadge');
  const notifs = state.notifications;

  const unreadCount = notifs.filter(n => !n.is_read).length;

  if (unreadCount > 0) {
    badge.textContent = unreadCount > 9 ? '9+' : unreadCount;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }

  if (!notifs.length) {
    list.innerHTML = `<div class="notif-empty"><i class="fa-solid fa-bell-slash"></i>No notifications yet</div>`;
    return;
  }

  const typeIconMap = {
    'REVIEW_COMPLETE': { icon: 'fa-microchip', cls: 'success' },
    'REVIEW_FAILED':   { icon: 'fa-circle-xmark', cls: 'danger' },
    'COMMENT':         { icon: 'fa-comment', cls: '' },
    'SYSTEM':          { icon: 'fa-gear', cls: 'warning' },
  };

  list.innerHTML = notifs.map(n => {
    const meta = typeIconMap[n.notification_type] || { icon: 'fa-bell', cls: '' };
    const timeAgo = formatTimeAgo(n.created_at);
    return `
      <div class="notif-item ${n.is_read ? '' : 'unread'}" onclick="markNotifRead('${n.id}', this)">
        <div class="notif-icon ${meta.cls}"><i class="fa-solid ${meta.icon}"></i></div>
        <div class="notif-body">
          <div class="notif-title">${escapeHtml(n.title || 'Notification')}</div>
          <div class="notif-msg">${escapeHtml(n.message || '')}</div>
          <div class="notif-time"><i class="fa-regular fa-clock"></i> ${timeAgo}</div>
        </div>
      </div>
    `;
  }).join('');
}

function toggleNotifDropdown() {
  const dropdown = document.getElementById('notifDropdown');
  if (dropdown.classList.contains('hidden')) {
    dropdown.classList.remove('hidden');
    loadNotifications(); // refresh on open
  } else {
    dropdown.classList.add('hidden');
  }
}

async function markNotifRead(notifId, itemEl) {
  if (!notifId) return;
  try {
    await fetch(`${API_BASE}/notifications/${notifId}/read`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    // Update local state
    const n = state.notifications.find(x => x.id === notifId);
    if (n) n.is_read = true;
    if (itemEl) itemEl.classList.remove('unread');
    renderNotifications();
  } catch (err) {
    console.error('Mark read failed:', err);
  }
}

async function markAllNotifsRead() {
  const unread = state.notifications.filter(n => !n.is_read);
  for (const n of unread) {
    await markNotifRead(n.id, null);
  }
  renderNotifications();
}

function formatTimeAgo(isoStr) {
  if (!isoStr) return 'just now';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1)  return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

// ─────────────────────────────────────────────────
//  USER PROFILE PAGE
// ─────────────────────────────────────────────────
async function loadProfilePage() {
  if (!state.token) return;

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();
    if (!json.success) return;

    const u = json.data;
    state.user = u;
    localStorage.setItem('auth_user', JSON.stringify(u));

    // Hero
    const initial = (u.username || 'U').charAt(0).toUpperCase();
    document.getElementById('profileAvatar').textContent = initial;
    document.getElementById('profileName').textContent = u.username || 'User';
    document.getElementById('profileEmail').textContent = u.email || '';
    document.getElementById('profileSinceBadge').innerHTML =
      `<i class="fa-solid fa-calendar"></i> Since ${new Date(u.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`;
    if (u.is_superuser) {
      document.getElementById('profileRoleBadge').innerHTML = `<i class="fa-solid fa-crown"></i> Admin`;
    }

    // Prefill form
    document.getElementById('profileUsername').value = u.username || '';
    document.getElementById('profileEmailInput').value = u.email || '';
    document.getElementById('profileNewPassword').value = '';
    document.getElementById('profileConfirmPassword').value = '';

    // Stats - use cached projects
    document.getElementById('statProjects').textContent = state.projects.length || '—';
    document.getElementById('statReviews').textContent = state.projects.filter(p => p.status === 'COMPLETED').length || '—';

  } catch (err) {
    console.error('Profile load error:', err);
  }
}

async function handleProfileUpdate(e) {
  e.preventDefault();
  const alertEl = document.getElementById('profileAlert');
  const saveBtn = document.getElementById('profileSaveBtn');
  alertEl.style.display = 'none';

  const username = document.getElementById('profileUsername').value.trim();
  const email    = document.getElementById('profileEmailInput').value.trim();
  const newPw    = document.getElementById('profileNewPassword').value;
  const confirmPw = document.getElementById('profileConfirmPassword').value;

  if (newPw && newPw !== confirmPw) {
    alertEl.textContent = 'Passwords do not match.';
    alertEl.className = 'profile-alert error';
    alertEl.style.display = 'block';
    return;
  }

  const payload = {};
  if (username) payload.username = username;
  if (email)    payload.email = email;
  if (newPw)    payload.password = newPw;

  saveBtn.disabled = true;
  saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Profile update failed.'));
    }

    state.user = json.data;
    localStorage.setItem('auth_user', JSON.stringify(state.user));
    updateUserUI();

    alertEl.textContent = '✅ Profile updated successfully!';
    alertEl.className = 'profile-alert success';
    alertEl.style.display = 'block';
    document.getElementById('profileNewPassword').value = '';
    document.getElementById('profileConfirmPassword').value = '';

  } catch (err) {
    alertEl.textContent = err.message;
    alertEl.className = 'profile-alert error';
    alertEl.style.display = 'block';
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Save Changes';
  }
}

// ─────────────────────────────────────────────────
//  REVIEW COMMENTS
// ─────────────────────────────────────────────────
async function loadComments() {
  const reviewId = state.currentReviewId;
  if (!reviewId) return;

  const list = document.getElementById('commentsList');
  list.innerHTML = '<div class="comments-empty"><i class="fa-solid fa-spinner fa-spin"></i> Loading comments...</div>';

  try {
    const res = await fetch(`${API_BASE}/reviews/${reviewId}/comments`, {
      headers: { 'Authorization': `Bearer ${state.token}` }
    });
    const json = await res.json();

    if (!json.success) throw new Error('Failed to load comments');

    const comments = json.data || [];
    document.getElementById('commentCount').textContent =
      comments.length ? `(${comments.length})` : '';

    if (comments.length === 0) {
      list.innerHTML = `<div class="comments-empty"><i class="fa-solid fa-comments" style="font-size:24px;opacity:0.3;margin-bottom:8px;display:block;"></i>No comments yet. Be the first to add one!</div>`;
      return;
    }

    list.innerHTML = comments.map(c => {
      const initial = (c.author || c.user_id || 'U').charAt(0).toUpperCase();
      const timeAgo = formatTimeAgo(c.created_at);
      return `
        <div class="comment-item">
          <div class="comment-avatar">${escapeHtml(initial)}</div>
          <div class="comment-body">
            <div class="comment-meta">
              <span class="comment-author">${escapeHtml(c.author || 'User')}</span>
              <span class="comment-time">${timeAgo}</span>
              ${c.file_path ? `<span class="comment-file"><i class="fa-solid fa-file-code"></i> ${escapeHtml(c.file_path)}${c.line_number ? ':' + escapeHtml(c.line_number) : ''}</span>` : ''}
            </div>
            <div class="comment-text">${escapeHtml(c.comment_text)}</div>
          </div>
        </div>
      `;
    }).join('');

  } catch (err) {
    list.innerHTML = `<div class="comments-empty">Failed to load comments: ${escapeHtml(err.message)}</div>`;
  }
}

async function submitComment() {
  const reviewId = state.currentReviewId;
  if (!reviewId) {
    alert('No active review. Please open a project report first.');
    return;
  }

  const text      = document.getElementById('commentText').value.trim();
  const filePath  = document.getElementById('commentFilePath').value.trim();
  const lineNum   = document.getElementById('commentLineNum').value.trim();

  if (!text) {
    alert('Please enter a comment before posting.');
    return;
  }

  const btn = document.getElementById('submitCommentBtn');
  btn.disabled = true;
  btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

  try {
    const payload = { comment_text: text };
    if (filePath) payload.file_path = filePath;
    if (lineNum)  payload.line_number = lineNum;

    const res = await fetch(`${API_BASE}/reviews/${reviewId}/comments`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${state.token}`
      },
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(parseErrorMessage(json, 'Failed to post comment'));
    }

    // Clear inputs
    document.getElementById('commentText').value = '';
    document.getElementById('commentFilePath').value = '';
    document.getElementById('commentLineNum').value = '';

    // Reload comments list
    await loadComments();

    // Bump profile comment stat if visible
    const statEl = document.getElementById('statComments');
    if (statEl) {
      const current = parseInt(statEl.textContent) || 0;
      statEl.textContent = current + 1;
    }

  } catch (err) {
    alert(`Comment failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Post';
  }
}




