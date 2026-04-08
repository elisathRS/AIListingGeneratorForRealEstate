/* ============================================================
   ListPro — app.js
   Handles: form submission, results display, copy, downloads,
            Instagram posting, video generation polling.
   ============================================================ */

const API_BASE = '';           // same origin — FastAPI serves everything
const LS_KEY   = 'listpro_result';

/* ── Utilities ─────────────────────────────────────────────── */

function showToast(message, type = 'default', duration = 3000) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = message;
  toast.className = `toast show${type !== 'default' ? ' ' + type : ''}`;
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => {
    toast.className = 'toast';
  }, duration);
}

function showSpinner() {
  const el = document.getElementById('spinnerOverlay');
  if (el) el.classList.add('active');
}

function hideSpinner() {
  const el = document.getElementById('spinnerOverlay');
  if (el) el.classList.remove('active');
}

function showError(message) {
  const banner = document.getElementById('errorBanner');
  if (!banner) return;
  banner.textContent = message;
  banner.style.display = 'block';
  banner.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
  const banner = document.getElementById('errorBanner');
  if (banner) banner.style.display = 'none';
}

/* ── Copy to Clipboard ─────────────────────────────────────── */

function copyText(elementId, buttonId) {
  const el  = document.getElementById(elementId);
  const btn = document.getElementById(buttonId);
  if (!el || !btn) return;

  const text = el.innerText || el.textContent;

  navigator.clipboard.writeText(text).then(() => {
    btn.textContent = '✓ Copied!';
    btn.classList.add('copied');
    showToast('Copied to clipboard!', 'success');
    setTimeout(() => {
      btn.textContent = 'Copy';
      btn.classList.remove('copied');
    }, 2000);
  }).catch(() => {
    // Fallback for older browsers
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showToast('Copied to clipboard!', 'success');
  });
}

/* ── File Input Labels ─────────────────────────────────────── */

function wireFileZone(inputId, zoneId, labelId, multi) {
  const input = document.getElementById(inputId);
  const zone  = document.getElementById(zoneId);
  const label = document.getElementById(labelId);
  if (!input || !zone || !label) return;

  // Clicking anywhere on the zone triggers the hidden file input
  zone.addEventListener('click', (e) => {
    if (e.target !== input) input.click();
  });

  input.addEventListener('change', () => {
    const count = input.files.length;
    if (count > 0) {
      label.textContent = multi && count > 1 ? `${count} files selected` : input.files[0].name;
      zone.classList.add('has-file');
    } else {
      label.textContent = multi ? 'No files selected' : 'No file selected';
      zone.classList.remove('has-file');
    }
  });

  // Drag-and-drop support
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('has-file'); });
  zone.addEventListener('dragleave', () => { if (!input.files.length) zone.classList.remove('has-file'); });
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    const dt = e.dataTransfer;
    if (!dt.files.length) return;
    // Assign dropped files to the input via DataTransfer
    try {
      const transfer = new DataTransfer();
      Array.from(dt.files).forEach(f => transfer.items.add(f));
      input.files = transfer.files;
      input.dispatchEvent(new Event('change'));
    } catch (_) {
      // Fallback: just update the label visually
      label.textContent = dt.files.length > 1 ? `${dt.files.length} files selected` : dt.files[0].name;
      zone.classList.add('has-file');
    }
  });
}

function initFileInputs() {
  wireFileZone('cover_photo',        'coverDropZone',      'coverFileName',       false);
  wireFileZone('additional_photos',  'additionalDropZone', 'additionalFileNames', true);
}

/* ── Form Validation ───────────────────────────────────────── */

function validateForm(form) {
  const errors = [];

  const requiredSelects = ['property_type', 'state'];
  requiredSelects.forEach(name => {
    const el = form.querySelector(`[name="${name}"]`);
    if (el && !el.value) errors.push(`Please select a ${name.replace('_', ' ')}.`);
  });

  const operation = form.querySelector('input[name="operation"]:checked');
  if (!operation) errors.push('Please select an operation: Sale or Rent.');

  const requiredInputs = ['address', 'city', 'price', 'bedrooms', 'bathrooms', 'built_area', 'parking', 'agent_name', 'agent_phone', 'agent_email'];
  requiredInputs.forEach(name => {
    const el = form.querySelector(`[name="${name}"]`);
    if (el && !el.value.trim()) errors.push(`${name.replace(/_/g, ' ')} is required.`);
  });

  const coverPhoto = form.querySelector('[name="cover_photo"]');
  if (coverPhoto && coverPhoto.files.length === 0) errors.push('A cover photo is required.');

  return errors;
}

/* ── Form Submission ───────────────────────────────────────── */

function initForm() {
  const form = document.getElementById('listingForm');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    hideError();

    const errors = validateForm(form);
    if (errors.length > 0) {
      showError(errors[0]);
      return;
    }

    // Build FormData manually so multiple files are appended as separate entries
    const fd = new FormData(form);

    // Amenities: replace checkbox entries with a single comma-separated string
    const checked = [...form.querySelectorAll('input[name="amenities"]:checked')].map(cb => cb.value);
    fd.delete('amenities');
    fd.append('amenities', checked.join(','));

    // Additional photos: delete the auto-entry and re-append each file individually
    // so FastAPI receives them as a proper List[UploadFile]
    const addInput = document.getElementById('additional_photos');
    fd.delete('additional_photos');
    if (addInput && addInput.files.length > 0) {
      Array.from(addInput.files).forEach(file => fd.append('additional_photos', file));
    }

    showSpinner();

    try {
      const res = await fetch(`${API_BASE}/api/generate`, {
        method: 'POST',
        body: fd,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error (${res.status})`);
      }

      const data = await res.json();
      localStorage.setItem(LS_KEY, JSON.stringify(data));
      window.location.href = '/results';

    } catch (err) {
      hideSpinner();
      showError(`Failed to generate listing: ${err.message}`);
    }
  });
}

/* ── Results Page ──────────────────────────────────────────── */

function formatPrice(price) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(price);
}

function initResults() {
  // Only run on the results page — bail out if key elements are absent
  const noDataWarning = document.getElementById('noDataWarning');
  const resultsGrid   = document.getElementById('resultsGrid');
  if (!noDataWarning || !resultsGrid) return;

  const raw = localStorage.getItem(LS_KEY);

  if (!raw) {
    noDataWarning.style.display = 'block';
    resultsGrid.style.display   = 'none';
    return;
  }

  const data = JSON.parse(raw);
  const pd   = data.property_data || {};

  // Property title
  const op      = pd.operation === 'Sale' ? 'For Sale' : 'For Rent';
  const title   = `${pd.bedrooms}-Bed ${pd.property_type} ${op}`;
  const subtitle = `${pd.address}, ${pd.city}, ${pd.state} · ${formatPrice(pd.price)}`;

  const titleEl    = document.getElementById('propertyTitle');
  const subtitleEl = document.getElementById('propertySubtitle');
  if (titleEl)    titleEl.textContent    = title;
  if (subtitleEl) subtitleEl.textContent = subtitle;

  document.title = `ListPro — ${title}`;

  // Description
  const descEl = document.getElementById('descriptionText');
  if (descEl) descEl.textContent = data.description || 'No description generated.';

  // Instagram caption
  const capEl = document.getElementById('captionText');
  if (capEl) capEl.textContent = data.instagram_caption || 'No caption generated.';

  // Store listing_id for action buttons
  window._listingId = data.listing_id;
}

/* ── Asset Downloads ───────────────────────────────────────── */

function downloadAsset(type) {
  const id = window._listingId;
  if (!id) { showToast('No listing found.', 'error'); return; }
  window.open(`${API_BASE}/api/${type}/${id}`, '_blank');
}

/* ── Instagram Posting ─────────────────────────────────────── */

async function postToInstagram() {
  const id  = window._listingId;
  const btn = document.getElementById('instagramBtn');
  const status = document.getElementById('instagramStatus');

  if (!id) { showToast('No listing found.', 'error'); return; }

  if (!confirm('Post this listing to Instagram?')) return;

  btn.disabled   = true;
  btn.textContent = 'Posting…';
  if (status) { status.textContent = ''; status.className = 'instagram-status'; }

  try {
    const res  = await fetch(`${API_BASE}/api/instagram/${id}`, { method: 'POST' });
    const data = await res.json();

    if (data.success) {
      if (status) { status.textContent = '✓ Posted to Instagram!'; status.className = 'instagram-status success'; }
      showToast('Posted to Instagram successfully!', 'success');
      btn.textContent = '✓ Posted';
    } else {
      if (status) { status.textContent = data.message || 'Failed to post.'; status.className = 'instagram-status error'; }
      showToast(data.message || 'Failed to post.', 'error');
      btn.disabled = false;
      btn.textContent = 'Post to Instagram';
    }
  } catch (err) {
    if (status) { status.textContent = 'Network error. Please try again.'; status.className = 'instagram-status error'; }
    showToast('Network error.', 'error');
    btn.disabled = false;
    btn.textContent = 'Post to Instagram';
  }
}

/* ── Video Generation ──────────────────────────────────────── */

let _videoPollTimer = null;

async function generateVideo() {
  const id       = window._listingId;
  const btn      = document.getElementById('videoBtn');
  const progress = document.getElementById('videoProgress');
  const download = document.getElementById('videoDownload');
  const dlLink   = document.getElementById('videoDownloadLink');

  if (!id) { showToast('No listing found.', 'error'); return; }

  btn.disabled = true;
  btn.textContent = 'Rendering…';
  if (progress) progress.style.display = 'block';
  if (download) download.style.display = 'none';

  try {
    await fetch(`${API_BASE}/api/video/${id}`, { method: 'POST' });
    _pollVideoStatus(id, btn, progress, download, dlLink);
  } catch (err) {
    showToast('Failed to start video render.', 'error');
    btn.disabled = false;
    btn.textContent = 'Generate Video';
    if (progress) progress.style.display = 'none';
  }
}

function _pollVideoStatus(id, btn, progress, download, dlLink) {
  clearInterval(_videoPollTimer);
  _videoPollTimer = setInterval(async () => {
    try {
      const res  = await fetch(`${API_BASE}/api/video/status/${id}`);
      const data = await res.json();

      if (data.status === 'done') {
        clearInterval(_videoPollTimer);
        if (progress)  progress.style.display  = 'none';
        if (download)  download.style.display  = 'block';
        if (dlLink)    dlLink.href = `${API_BASE}/api/video/download/${id}`;
        btn.textContent = '✓ Video Ready';
        showToast('Your video reel is ready!', 'success');
      } else if (data.status === 'error') {
        clearInterval(_videoPollTimer);
        if (progress) progress.style.display = 'none';
        btn.disabled = false;
        btn.textContent = 'Generate Video';
        showToast('Video rendering failed. Please try again.', 'error');
      }
      // 'rendering' or 'pending' — keep polling
    } catch (err) {
      clearInterval(_videoPollTimer);
      if (progress) progress.style.display = 'none';
      btn.disabled = false;
      btn.textContent = 'Generate Video';
    }
  }, 3000);
}

/* ── Init ──────────────────────────────────────────────────── */

document.addEventListener('DOMContentLoaded', () => {
  initFileInputs();
  initForm();
  initResults();
});
