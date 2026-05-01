const API = '';
let currentFilename = null;

// DOM refs
const fileInput = document.getElementById('file-input');
const uploadZone = document.getElementById('upload-zone');
const dropzone = document.getElementById('upload-dropzone');
const fileBanner = document.getElementById('file-banner');
const dashGrid = document.getElementById('dashboard-grid');
const loading = document.getElementById('loading');
const progressBar = document.getElementById('progress-bar');
const progressText = document.getElementById('progress-text');

// Color map for forgery types (matches backend)
const TYPE_COLORS = {
    'Partial Modification': '#ef4444',
    'Overwritten Text': '#3b82f6',
    'Copy-Paste Forgery': '#10b981',
    'Content Removed': '#eab308',
    'Added Content': '#a855f7',
    'Watermark Removed': '#92400e',
    'Spacing Anomaly': '#14b8a6',
    'Merged Document': '#6b7280',
    'AI Generated Approximation': '#f97316'
};

// ═══ NAV ═══
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        const page = item.dataset.page;
        if (page === 'upload') fileInput.click();
        if (page === 'verify' && currentFilename) runVerify();
    });
});

// ═══ UPLOAD ═══
document.getElementById('btn-browse').addEventListener('click', e => {
    e.stopPropagation();
    fileInput.click();
});
dropzone.addEventListener('click', () => fileInput.click());

// Drag & drop
['dragenter','dragover'].forEach(ev => {
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.add('drag-over'); });
});
['dragleave','drop'].forEach(ev => {
    dropzone.addEventListener(ev, e => { e.preventDefault(); dropzone.classList.remove('drag-over'); });
});
dropzone.addEventListener('drop', e => {
    const files = e.dataTransfer.files;
    if (files.length) handleFile(files[0]);
});

fileInput.addEventListener('change', e => {
    if (e.target.files[0]) handleFile(e.target.files[0]);
});

async function handleFile(file) {
    const valid = ['image/jpeg','image/png','image/jpg','application/pdf'];
    if (!valid.includes(file.type)) {
        showToast('Invalid file type. Use JPG, PNG, or PDF.', 'error');
        return;
    }
    if (file.size > 16 * 1024 * 1024) {
        showToast('File too large. Maximum 16MB.', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showLoading('Uploading document...');
    try {
        const res = await fetch(`${API}/upload`, { method: 'POST', body: formData });
        const data = await res.json();
        if (data.success) {
            currentFilename = data.filename;
            // Show file banner
            document.getElementById('file-name').textContent = file.name;
            document.getElementById('file-size').textContent = formatSize(file.size);
            uploadZone.style.display = 'none';
            fileBanner.style.display = 'flex';
            dashGrid.style.display = 'grid';

            // Show original
            document.getElementById('original-view').innerHTML =
                `<img src="${API}${data.url}" alt="Original Document">`;
            document.getElementById('analyzed-view').innerHTML =
                '<div class="placeholder-content"><i class="fas fa-microscope fa-3x"></i><p>Click "Run Forensic Analysis"</p></div>';

            resetStats();
            showToast('Document uploaded successfully!', 'success');
            updateQuickStats();
        } else {
            showToast('Upload failed: ' + (data.error || 'Unknown error'), 'error');
        }
    } catch (err) {
        showToast('Upload failed: ' + err.message, 'error');
    } finally {
        hideLoading();
    }
}

// ═══ VERIFY ═══
document.getElementById('btn-verify').addEventListener('click', runVerify);

async function runVerify() {
    if (!currentFilename) {
        showToast('Please upload a document first.', 'error');
        return;
    }

    showLoading('Initializing modules...');
    simulateProgress();

    try {
        const res = await fetch(`${API}/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: currentFilename })
        });
        const data = await res.json();

        if (data.error) {
            showToast('Analysis error: ' + data.error, 'error');
        } else {
            progressBar.style.width = '100%';
            progressText.textContent = 'Complete!';
            setTimeout(() => {
                hideLoading();
                updateDashboard(data);
                showToast('Forensic analysis complete!', 'success');
            }, 400);
            return;
        }
    } catch (err) {
        showToast('Analysis failed: ' + err.message, 'error');
    }
    hideLoading();
}

// ═══ REMOVE ═══
document.getElementById('btn-remove').addEventListener('click', () => {
    currentFilename = null;
    fileBanner.style.display = 'none';
    dashGrid.style.display = 'none';
    uploadZone.style.display = 'flex';
    fileInput.value = '';
    resetStats();
});

// ═══ UPDATE DASHBOARD ═══
function updateDashboard(data) {
    // Analyzed image
    document.getElementById('analyzed-view').innerHTML =
        `<img src="${API}${data.output_image}" alt="Analyzed Document">`;
    attachZoom();

    // Status
    const sd = document.getElementById('status-display');
    if (data.status === 'Forged') {
        sd.className = 'status-indicator status-forged';
        sd.innerHTML = '<div class="status-icon-wrap"><i class="fas fa-times-circle"></i></div><div class="status-text"><strong>FORGED DOCUMENT</strong><span>Tampering Detected</span></div>';
    } else if (data.status === 'Suspicious') {
        sd.className = 'status-indicator status-suspicious';
        sd.innerHTML = '<div class="status-icon-wrap"><i class="fas fa-exclamation-triangle"></i></div><div class="status-text"><strong>SUSPICIOUS</strong><span>Anomalies Found</span></div>';
    } else {
        sd.className = 'status-indicator status-genuine';
        sd.innerHTML = '<div class="status-icon-wrap"><i class="fas fa-check-circle"></i></div><div class="status-text"><strong>GENUINE DOCUMENT</strong><span>No Tampering Detected</span></div>';
    }

    // Gauge
    updateGauge(data.confidence);
    document.getElementById('confidence-label').textContent =
        data.confidence > 80 ? 'High Confidence' : data.confidence > 50 ? 'Medium Confidence' : 'Low Confidence';

    // Types
    const tl = document.getElementById('types-list');
    const counts = data.type_counts || {};
    if (Object.keys(counts).length) {
        tl.innerHTML = Object.entries(counts).map(([type, count]) =>
            `<div class="type-row" style="background:${TYPE_COLORS[type]||'#6b7280'}">
                <span>${type}</span><div class="type-count">${count}</div>
            </div>`
        ).join('');
    } else {
        tl.innerHTML = '<div class="empty-state-small"><p>No forgery types detected</p></div>';
    }

    // Explanations
    const el = document.getElementById('explanation-list');
    if (data.issues && data.issues.length) {
        el.innerHTML = data.issues.map((issue, i) =>
            `<div class="explanation-item">
                <div class="badge-num" style="background:${TYPE_COLORS[issue.type]||'#6b7280'}">${i+1}</div>
                <div class="exp-text"><strong>${issue.type}:</strong> ${issue.explanation}</div>
            </div>`
        ).join('');
    } else {
        el.innerHTML = '<div class="empty-state-small"><i class="fas fa-check-circle"></i><p>No issues detected.</p></div>';
    }

    // Conclusion
    const cs = document.getElementById('conclusion-section');
    const fc = document.getElementById('final-conclusion');
    cs.style.display = 'block';
    fc.textContent = data.conclusion || '';
    fc.className = 'conclusion-alert ' + (data.status === 'Forged' ? 'forged' : data.status === 'Suspicious' ? 'suspicious' : 'genuine');

    // Summary
    if (data.summary) {
        document.getElementById('sum-issues').textContent = data.summary.total_issues;
        document.getElementById('sum-pages').textContent = data.summary.pages_analyzed;
        document.getElementById('sum-time').textContent = data.summary.time_taken;
        document.getElementById('sum-type').textContent = data.summary.file_type;
    }

    // Quick stats
    updateQuickStats();
}

function updateGauge(pct) {
    const circumference = 2 * Math.PI * 52; // r=52
    const offset = circumference - (circumference * pct / 100);
    const circle = document.getElementById('gauge-circle');
    circle.style.strokeDasharray = circumference;
    circle.style.strokeDashoffset = offset;
    // Animate number
    const el = document.getElementById('gauge-text');
    let cur = 0;
    const step = Math.ceil(pct / 30);
    const timer = setInterval(() => {
        cur = Math.min(cur + step, pct);
        el.textContent = cur + '%';
        if (cur >= pct) clearInterval(timer);
    }, 30);
}

function resetStats() {
    const sd = document.getElementById('status-display');
    sd.className = 'status-indicator status-pending';
    sd.innerHTML = '<div class="status-icon-wrap"><i class="fas fa-hourglass-half"></i></div><div class="status-text"><strong>Ready</strong><span>Click verify to start analysis</span></div>';
    document.getElementById('gauge-circle').style.strokeDashoffset = 2 * Math.PI * 52;
    document.getElementById('gauge-text').textContent = '0%';
    document.getElementById('confidence-label').textContent = 'No Analysis Performed';
    document.getElementById('types-list').innerHTML = '<div class="empty-state-small"><p>No detections yet</p></div>';
    document.getElementById('explanation-list').innerHTML = '<div class="empty-state-small"><i class="fas fa-info-circle"></i><p>Detailed explanations will appear here after analysis.</p></div>';
    document.getElementById('conclusion-section').style.display = 'none';
    ['sum-issues','sum-pages'].forEach(id => document.getElementById(id).textContent = '0');
    document.getElementById('sum-time').textContent = '0s';
    document.getElementById('sum-type').textContent = '—';
}

// ═══ ZOOM ═══
function attachZoom() {
    document.querySelectorAll('.image-display img').forEach(img => {
        img.addEventListener('mousemove', e => {
            const r = img.getBoundingClientRect();
            const x = ((e.clientX - r.left) / r.width) * 100;
            const y = ((e.clientY - r.top) / r.height) * 100;
            img.style.transformOrigin = `${x}% ${y}%`;
        });
        img.addEventListener('mouseenter', () => { img.style.transform = 'scale(2)'; });
        img.addEventListener('mouseleave', () => { img.style.transform = 'scale(1)'; });
    });
}

// ═══ LOADING ═══
let progressInterval;
function showLoading(msg) {
    loading.style.display = 'flex';
    progressBar.style.width = '0%';
    if (msg) progressText.textContent = msg;
}
function hideLoading() {
    loading.style.display = 'none';
    clearInterval(progressInterval);
}
function simulateProgress() {
    let pct = 0;
    const steps = ['Preprocessing image...', 'Running copy-paste detection...', 'Analyzing overwriting patterns...',
        'Checking for added content...', 'Scanning for removed content...', 'Evaluating document merge indicators...',
        'Checking watermark integrity...', 'Analyzing spacing patterns...', 'Detecting partial edits...',
        'Running AI-pattern approximation...', 'Aggregating results...'];
    let si = 0;
    progressInterval = setInterval(() => {
        pct = Math.min(pct + 3 + Math.random() * 5, 92);
        progressBar.style.width = pct + '%';
        if (si < steps.length && pct > (si + 1) * 8) {
            progressText.textContent = steps[si++];
        }
    }, 300);
}

// ═══ TOAST ═══
function showToast(msg, type = 'info') {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = 'toast ' + type;
    t.innerHTML = `<i class="fas fa-${type==='success'?'check-circle':type==='error'?'exclamation-circle':'info-circle'}"></i><span>${msg}</span>`;
    c.appendChild(t);
    setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(30px)'; setTimeout(() => t.remove(), 300); }, 3500);
}

// ═══ HELPERS ═══
function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

async function updateQuickStats() {
    try {
        const res = await fetch(`${API}/history`);
        const history = await res.json();
        document.getElementById('qs-scanned').textContent = history.length;
        document.getElementById('qs-forged').textContent = history.filter(h => h.status === 'Forged').length;
        document.getElementById('qs-genuine').textContent = history.filter(h => h.status === 'Genuine').length;
        document.getElementById('qs-pending').textContent = '0';
    } catch(e) { /* ignore */ }
}

// Sidebar toggle
document.getElementById('sidebar-toggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('collapsed');
});

// Download result
document.getElementById('btn-download-result').addEventListener('click', () => {
    const img = document.querySelector('#analyzed-view img');
    if (img) {
        const a = document.createElement('a');
        a.href = img.src;
        a.download = 'medverify_result.png';
        a.click();
    }
});

// Init
updateQuickStats();
attachZoom();
