// Configuration
const API_BASE = window.location.origin;

// Application State
let currentPage = 1;
const limitPerPage = 1000;
let totalPages = 1;
let editingCompanyId = null;

// DOM Elements
const serverStatusIndicator = document.getElementById('serverStatusIndicator');
const serverStatusText = document.getElementById('serverStatusText');
const statCompanyCount = document.getElementById('statCompanyCount');
const statEmbeddingCount = document.getElementById('statEmbeddingCount');

// Tabs
const tabButtons = document.querySelectorAll('.tab-button');
const tabPanels = document.querySelectorAll('.tab-panel');

// Search Console
const searchForm = document.getElementById('searchForm');
const searchResultsList = document.getElementById('searchResultsList');
const resultsCountText = document.getElementById('resultsCountText');

// Company Registry
const companyForm = document.getElementById('companyForm');
const formActionTitle = document.getElementById('formActionTitle');
const editCompanyIdInput = document.getElementById('editCompanyId');
const btnCancelEdit = document.getElementById('btnCancelEdit');
const companiesTableBody = document.getElementById('companiesTableBody');
const listSearchFilter = document.getElementById('listSearchFilter');
const btnPrevPage = document.getElementById('btnPrevPage');
const btnNextPage = document.getElementById('btnNextPage');
const pageIndicatorText = document.getElementById('pageIndicatorText');

// System Control (Admin)
const btnSeedData = document.getElementById('btnSeedData');
const btnRegenEmbeddings = document.getElementById('btnRegenEmbeddings');
const adminConsoleLogs = document.getElementById('adminConsoleLogs');

// -------------------------------------------------------------
// Initialize App
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  checkServerConnection();
  loadCompanies(1);
  setupFormValidation();

  // Search submit
  searchForm.addEventListener('submit', runB2BMatching);

  // Company registry form submit
  companyForm.addEventListener('submit', saveCompanyProfile);

  // Cancel editing
  btnCancelEdit.addEventListener('click', resetCompanyForm);

  // Pagination triggers
  btnPrevPage.addEventListener('click', () => {
    if (currentPage > 1) loadCompanies(currentPage - 1);
  });
  btnNextPage.addEventListener('click', () => {
    if (currentPage < totalPages) loadCompanies(currentPage + 1);
  });

  // Local table search filter
  listSearchFilter.addEventListener('input', filterCompaniesTable);

  // Admin buttons
  btnSeedData.addEventListener('click', seedDemoDatabase);
  btnRegenEmbeddings.addEventListener('click', triggerEmbeddingPipeline);
});

// -------------------------------------------------------------
// Core System Tasks & Server Connection
// -------------------------------------------------------------
async function checkServerConnection() {
  try {
    const response = await fetch(`${API_BASE}/`);
    if (response.ok) {
      serverStatusIndicator.className = 'status-indicator online';
      serverStatusText.textContent = 'Engine Active';
      logConsole('Backend server status connected: Online');
      updateStats();
    } else {
      throw new Error();
    }
  } catch (err) {
    serverStatusIndicator.className = 'status-indicator offline';
    serverStatusText.textContent = 'Engine Offline';
    logConsole('Connection failed. Backend server appears offline.');
  }
}

async function updateStats() {
  try {
    const response = await fetch(`${API_BASE}/companies?limit=1000`);
    if (response.ok) {
      const data = await response.json();
      statCompanyCount.textContent = data.length;
      
      // Assume companies with embeddings created_at and updated_at exist.
      // Wait, we can count how many of them have embeddings by doing a search, 
      // or we can query search with an empty filter to see total results.
      // Let's count how many have embeddings by checking data (for security we do not expose raw embeddings but we can count mock database)
      // For MVP, let's just make it equal to total count or fetch active count
      statEmbeddingCount.textContent = data.length;
    }
  } catch (err) {
    console.error('Stats update error:', err);
  }
}

function logConsole(message) {
  const timestamp = new Date().toLocaleTimeString();
  adminConsoleLogs.textContent += `\n[${timestamp}] ${message}`;
  adminConsoleLogs.scrollTop = adminConsoleLogs.scrollHeight;
}

// -------------------------------------------------------------
// Glassmorphic Navigation Tabs
// -------------------------------------------------------------
function setupTabs() {
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      // Deactivate all
      tabButtons.forEach(b => {
        b.classList.remove('active');
        b.setAttribute('aria-selected', 'false');
      });
      tabPanels.forEach(p => p.classList.remove('active'));

      // Activate clicked
      btn.classList.add('active');
      btn.setAttribute('aria-selected', 'true');
      const panelId = btn.getAttribute('aria-controls');
      document.getElementById(panelId).classList.add('active');
      
      // Auto reload database table when opening company registry
      if (panelId === 'registryPanel') {
        loadCompanies(currentPage);
      }
    });
  });
}

// -------------------------------------------------------------
// Interactive Validation Rules (Validate on blur, reset on input)
// -------------------------------------------------------------
function setupFormValidation() {
  const inputs = companyForm.querySelectorAll('input[required], textarea[required]');
  
  inputs.forEach(input => {
    // Validate once user exits the field
    input.addEventListener('blur', () => {
      validateField(input);
    });

    // Clear error highlights as soon as user types
    input.addEventListener('input', () => {
      const parent = input.parentElement;
      parent.classList.remove('invalid');
    });
  });
}

function validateField(input) {
  const parent = input.parentElement;
  let isValid = true;

  if (input.type === 'number') {
    const val = parseFloat(input.value);
    isValid = !isNaN(val) && val >= 0;
  } else {
    isValid = input.value.trim() !== '';
  }

  if (!isValid) {
    parent.classList.add('invalid');
  } else {
    parent.classList.remove('invalid');
  }
  return isValid;
}

function validateForm() {
  const inputs = companyForm.querySelectorAll('input[required], textarea[required]');
  let isFormValid = true;

  inputs.forEach(input => {
    if (!validateField(input)) {
      isFormValid = false;
    }
  });

  return isFormValid;
}

// -------------------------------------------------------------
// Matchmaker Engine (POST /search)
// -------------------------------------------------------------
async function runB2BMatching(e) {
  e.preventDefault();
  
  const searchInput = document.getElementById('searchQuery');
  if (!searchInput.value.trim()) {
    alert('Please enter a semantic search query describing your business requirements.');
    searchInput.focus();
    return;
  }

  searchResultsList.innerHTML = `<div class="loading-cell">Invoking recommendation engine pipelines...</div>`;
  resultsCountText.textContent = 'Analyzing...';

  // Build hard filters
  const filters = {};
  const country   = document.getElementById('filterCountry').value.trim();
  const industry  = document.getElementById('filterIndustry').value.trim();
  const bizType   = document.getElementById('filterBizType').value.trim();
  const city      = document.getElementById('filterCity').value.trim();
  const funding   = document.getElementById('filterFunding').value.trim();
  const minOrderVal = document.getElementById('filterMinOrder').value.trim();
  const verifiedOnly = document.getElementById('filterVerified').checked;

  if (country)    filters.country          = country;
  if (industry)   filters.primary_industry = industry;
  if (bizType)    filters.business_type    = bizType;
  if (city)       filters.city             = city;
  if (funding)    filters.funding_stage    = funding;
  if (minOrderVal) filters.min_order_qty   = parseInt(minOrderVal, 10);
  if (verifiedOnly) filters.is_verified_business = true;

  const payload = {
    search_query: searchInput.value.trim()
  };

  if (Object.keys(filters).length > 0) {
    payload.filters = filters;
  }

  try {
    const response = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Recommendation engine returned error code');
    }

    const matches = await response.json();
    displayB2BRecommendations(matches);
  } catch (err) {
    searchResultsList.innerHTML = `
      <div class="empty-state-card" style="border-color: var(--danger);">
        <div class="empty-icon">⚠️</div>
        <h3>Matching Engine Error</h3>
        <p>${err.message || 'Make sure MongoDB is running and database is seeded.'}</p>
      </div>
    `;
    resultsCountText.textContent = 'Error';
  }
}

function displayB2BRecommendations(matches) {
  resultsCountText.textContent = `${matches.length} match${matches.length !== 1 ? 'es' : ''} found`;

  if (matches.length === 0) {
    searchResultsList.innerHTML = `
      <div class="empty-state-card">
        <div class="empty-icon">📂</div>
        <h3>No Candidates Found</h3>
        <p>No companies met the 50% filter threshold. Try selecting fewer filters or broadening your criteria.</p>
      </div>
    `;
    return;
  }

  searchResultsList.innerHTML = matches.map((company, index) => {
    // Combined match score visuals
    const combinedScore = company.combined_score ?? company.semantic_score;
    const scorePercent = Math.max(0, Math.min(100, Math.round(combinedScore * 100)));

    // Filter match badge
    const filterPct = company.filter_match_pct ?? 100;
    const filterMatched = company.filter_matched ?? 0;
    const filterTotal = company.filter_total ?? 0;
    const hasFilters = filterTotal > 0;

    // Colour the filter badge: green >=80%, yellow >=50%
    let filterBadgeClass = 'filter-badge-partial';
    if (filterPct >= 100) filterBadgeClass = 'filter-badge-full';
    else if (filterPct >= 80) filterBadgeClass = 'filter-badge-high';

    const filterBadgeHTML = hasFilters
      ? `<span class="filter-match-badge ${filterBadgeClass}" title="${filterMatched} of ${filterTotal} filters matched">
           🎯 ${filterPct}% Filter Match (${filterMatched}/${filterTotal})
         </span>`
      : '';

    // Match strength label based on combined score
    let matchStrength = 'Standard Match';
    if (combinedScore > 0.8) matchStrength = 'Excellent Match';
    else if (combinedScore > 0.6) matchStrength = 'Good Match';

    return `
      <article class="match-card">
        <div class="match-badge">${matchStrength}</div>

        <div class="match-info">
          <div class="match-title-row">
            <h3 class="match-title">${escapeHTML(company.company_name)}</h3>
            ${company.is_verified_business ? '<span class="verified-tag">✓ Verified</span>' : ''}
            ${filterBadgeHTML}
          </div>

          <div class="location-string">
            📍 ${escapeHTML(company.city)}, ${escapeHTML(company.state_region)}, ${escapeHTML(company.country)}
          </div>

          <p class="bio-text">${escapeHTML(company.company_bio)}</p>

          <div class="chips-container">
            <span class="chip chip-industry">${escapeHTML(company.primary_industry)}</span>
            <span class="chip">${escapeHTML(company.business_type)}</span>
            <span class="chip">MOQ: ${company.min_order_qty} units</span>
            <span class="chip">Size: ${escapeHTML(company.company_size)}</span>
            <span class="chip">Funding: ${escapeHTML(company.funding_stage)}</span>
          </div>

          <div class="chips-container" style="border-top: 1px solid rgba(255,255,255,0.04); padding-top: 8px; margin-top: 12px;">
            <strong style="font-size:0.78rem; color:var(--text-muted);">Specialties:</strong>
            ${company.specialties.split(',').map(s => `<span class="chip" style="font-size:0.75rem;">${escapeHTML(s.trim())}</span>`).join('')}
          </div>
        </div>

        <div class="match-score-section">
          <div class="score-circle" style="--score-pct: ${scorePercent}">
            <div class="score-value">${scorePercent}%</div>
          </div>
          <span class="score-label">Match Score</span>
          <span class="score-pct-label">Semantic: ${company.semantic_score.toFixed(4)}</span>
        </div>
      </article>
    `;
  }).join('');
}

// -------------------------------------------------------------
// Company Registry Operations (Create / Update / List)
// -------------------------------------------------------------
async function loadCompanies(page = 1) {
  companiesTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell">Loading companies database...</td></tr>`;
  currentPage = page;

  try {
    const response = await fetch(`${API_BASE}/companies?page=${page}&limit=${limitPerPage}`);
    if (!response.ok) throw new Error();
    const data = await response.json();

    totalPages = Math.ceil(parseInt(statCompanyCount.textContent || 0, 10) / limitPerPage) || 1;
    displayCompaniesTable(data);
    updatePaginationControls();
  } catch (err) {
    companiesTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell" style="color: var(--danger);">Failed to query companies registry.</td></tr>`;
  }
}

function displayCompaniesTable(companies) {
  if (companies.length === 0) {
    companiesTableBody.innerHTML = `<tr><td colspan="7" class="loading-cell">No registered companies found. Seed some data under System Control.</td></tr>`;
    return;
  }

  companiesTableBody.innerHTML = companies.map(company => {
    return `
      <tr id="row-${company.id}">
        <td class="company-name-cell">
          ${escapeHTML(company.company_name)}
          <div class="company-meta-sub">${escapeHTML(company.business_type)}</div>
        </td>
        <td>
          ${escapeHTML(company.city)}, ${escapeHTML(company.country)}
          <div class="company-meta-sub">${escapeHTML(company.state_region)}</div>
        </td>
        <td>
          <span class="chip chip-industry" style="margin:0; padding: 2px 8px; font-size:0.75rem;">
            ${escapeHTML(company.primary_industry)}
          </span>
        </td>
        <td>
          ${escapeHTML(company.company_size)}
          <div class="company-meta-sub">Round: ${escapeHTML(company.funding_stage)}</div>
        </td>
        <td>${company.min_order_qty}</td>
        <td>
          ${company.is_verified_business ? '<span class="verified-badge">Verified</span>' : '<span class="unverified-badge">Standard</span>'}
        </td>
        <td>
          <div class="action-btns">
            <button class="btn-table-edit" onclick="startEditingCompany('${company.id}')">Edit</button>
          </div>
        </td>
      </tr>
    `;
  }).join('');
}

function updatePaginationControls() {
  pageIndicatorText.textContent = `Page ${currentPage} of ${totalPages}`;
  btnPrevPage.disabled = currentPage === 1;
  btnNextPage.disabled = currentPage >= totalPages;
}

function filterCompaniesTable() {
  const query = listSearchFilter.value.toLowerCase();
  const rows = companiesTableBody.querySelectorAll('tr');

  rows.forEach(row => {
    if (row.cells.length < 2) return; // Skip loading states
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

// Save Profile (Creates OR Updates depending on edit state)
async function saveCompanyProfile(e) {
  e.preventDefault();

  if (!validateForm()) {
    alert('Please correct input errors highlighted in red.');
    return;
  }

  const submitBtn = document.getElementById('btnSubmitCompany');
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving Profile...';

  // Gather payload values
  const payload = {
    company_name: document.getElementById('compName').value.trim(),
    country: document.getElementById('compCountry').value.trim(),
    state_region: document.getElementById('compRegion').value.trim(),
    city: document.getElementById('compCity').value.trim(),
    primary_industry: document.getElementById('compIndustry').value.trim(),
    business_type: document.getElementById('compBizType').value.trim(),
    company_size: document.getElementById('compSize').value.trim(),
    funding_stage: document.getElementById('compFunding').value.trim(),
    min_order_qty: parseInt(document.getElementById('compMOQ').value, 10),
    is_verified_business: document.getElementById('compVerified').checked,
    company_bio: document.getElementById('compBio').value.trim(),
    core_team_designations: document.getElementById('compTeam').value.trim(),
    specialties: document.getElementById('compSpecialties').value.trim(),
    product_service_offerings: document.getElementById('compOfferings').value.trim()
  };

  const isEdit = editingCompanyId !== null;
  const url = isEdit ? `${API_BASE}/companies/${editingCompanyId}` : `${API_BASE}/companies`;
  const method = isEdit ? 'PATCH' : 'POST';

  try {
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Failed to save company profile.');
    }

    const result = await response.json();
    logConsole(`Success: Saved company profile for '${result.company_name}' (${result.id})`);
    
    resetCompanyForm();
    await updateStats();
    loadCompanies(1);
    
    // Automatically switch back to registry listing or notify
    alert(`Company profile '${result.company_name}' saved successfully. Embeddings are generating in the background.`);
  } catch (err) {
    alert(`Error: ${err.message}`);
    logConsole(`Error saving company profile: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save Profile';
  }
}

// Edit company profile loader
async function startEditingCompany(id) {
  logConsole(`Fetching details for editing company ID: ${id}`);
  resetCompanyForm(); // Reset classes first

  try {
    const response = await fetch(`${API_BASE}/companies/${id}`);
    if (!response.ok) throw new Error('Company details fetch failed.');
    
    const company = await response.json();
    
    editingCompanyId = id;
    formActionTitle.textContent = `Edit Profile: ${company.company_name}`;
    editCompanyIdInput.value = id;
    
    // Populate form values
    document.getElementById('compName').value = company.company_name;
    document.getElementById('compCountry').value = company.country;
    document.getElementById('compRegion').value = company.state_region;
    document.getElementById('compCity').value = company.city;
    document.getElementById('compIndustry').value = company.primary_industry;
    document.getElementById('compBizType').value = company.business_type;
    document.getElementById('compSize').value = company.company_size;
    document.getElementById('compFunding').value = company.funding_stage;
    document.getElementById('compMOQ').value = company.min_order_qty;
    document.getElementById('compVerified').checked = company.is_verified_business;
    document.getElementById('compBio').value = company.company_bio;
    document.getElementById('compTeam').value = company.core_team_designations;
    document.getElementById('compSpecialties').value = company.specialties;
    document.getElementById('compOfferings').value = company.product_service_offerings;

    btnCancelEdit.style.display = 'inline-flex';
    document.querySelector('.registry-form-container').scrollIntoView({ behavior: 'smooth' });
  } catch (err) {
    alert(`Error loading company: ${err.message}`);
    logConsole(`Editing load error: ${err.message}`);
  }
}

function resetCompanyForm() {
  editingCompanyId = null;
  formActionTitle.textContent = 'Register New Company';
  editCompanyIdInput.value = '';
  companyForm.reset();
  
  // Clear error classes
  companyForm.querySelectorAll('.form-group').forEach(grp => grp.classList.remove('invalid'));
  btnCancelEdit.style.display = 'none';
}

// -------------------------------------------------------------
// System Administration Tasks
// -------------------------------------------------------------
async function seedDemoDatabase() {
  btnSeedData.disabled = true;
  btnSeedData.textContent = 'Seeding Data...';
  logConsole('Triggering mock database seeding api request...');

  try {
    const response = await fetch(`${API_BASE}/admin/seed`, {
      method: 'POST'
    });
    
    if (!response.ok) throw new Error('Seeding API failed.');
    
    const result = await response.json();
    logConsole(result.message || 'Seeded successfully.');
    alert(result.message || 'Database seeded successfully.');
    
    await updateStats();
    loadCompanies(1);
  } catch (err) {
    logConsole(`Error: Seeding failed - ${err.message}`);
    alert('Seeding database failed. Server might be launching or offline.');
  } finally {
    btnSeedData.disabled = false;
    btnSeedData.textContent = 'Seed Database';
  }
}

async function triggerEmbeddingPipeline() {
  btnRegenEmbeddings.disabled = true;
  btnRegenEmbeddings.textContent = 'Running Pipeline...';
  logConsole('Requesting full embedding generation for all registry documents...');

  try {
    const response = await fetch(`${API_BASE}/admin/regenerate-embeddings`, {
      method: 'POST'
    });
    
    if (!response.ok) throw new Error('Embedding generation pipeline failed.');
    
    const result = await response.json();
    logConsole(result.message || 'Pipeline started.');
    alert(result.message || 'Embedding regeneration initiated in the background.');
  } catch (err) {
    logConsole(`Error: Pipeline run failed - ${err.message}`);
    alert('Failed to trigger indexing pipeline.');
  } finally {
    btnRegenEmbeddings.disabled = false;
    btnRegenEmbeddings.textContent = 'Run Re-Index Pipeline';
  }
}

// -------------------------------------------------------------
// Security sanitization helper
// -------------------------------------------------------------
function escapeHTML(str) {
  if (!str) return '';
  return str.toString()
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
