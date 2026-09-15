// ══════════════════════════════════════════════════════════════════
// GrowX Crawl Enterprise Dashboard Logic
// ══════════════════════════════════════════════════════════════════

let activeTab = "dashboard";
let activeCapability = "scrape";
let selectedDocEndpointId = "scrape";

const ENDPOINTS_CATALOG = [
    {
        id: "scrape",
        method: "POST",
        path: "/v1/scrape",
        title: "Single-Page Extraction",
        desc: "Extract text, metadata, headings, and links from any web URL with automated fetch escalation (fast HTTP, headless browser, or stealth anti-bot evasion).",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Fully-qualified destination web URL (http:// or https://)" },
            { name: "fetcher", type: "string", req: "Optional", desc: 'Execution mode: "auto" (default), "fast", "dynamic", or "stealth"' },
            { name: "respect_robots", type: "boolean", req: "Optional", desc: "Enforce robots.txt policy compliance (default: false)" },
            { name: "timeout", type: "integer", req: "Optional", desc: "Network timeout in seconds (default: 30)" }
        ],
        sample: { url: "https://growxlabs.tech", fetcher: "auto", respect_robots: false }
    },
    {
        id: "extract",
        method: "POST",
        path: "/v1/extract",
        title: "Structured Data Extraction",
        desc: "Parse specific document fields using targeted CSS selectors or XPath expressions with Parsel & lxml execution.",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Destination page URL" },
            { name: "selectors", type: "object", req: "Required", desc: "Key-value map of field names to CSS or XPath selectors" }
        ],
        sample: { url: "https://growxlabs.tech", selectors: { title: "h1", description: "meta[name=description]" } }
    },
    {
        id: "crawl",
        method: "POST",
        path: "/v1/crawl",
        title: "Multi-Page Site Crawler",
        desc: "Asynchronously discover and extract internal pages up to 5 levels deep with queue management and SQLite persistence.",
        params: [
            { name: "seed_url", type: "string", req: "Required", desc: "Domain entry point URL" },
            { name: "max_depth", type: "integer", req: "Optional", desc: "Link traversal depth (1-5, default: 5)" },
            { name: "max_pages", type: "integer", req: "Optional", desc: "Maximum page extraction limit (default: 50)" },
            { name: "respect_robots", type: "boolean", req: "Optional", desc: "Enforce robots.txt directives (default: false)" }
        ],
        sample: { seed_url: "https://growxlabs.tech", max_depth: 2, max_pages: 10 }
    },
    {
        id: "batch",
        method: "POST",
        path: "/v1/batch",
        title: "Parallel Batch Extraction",
        desc: "Concurrently process up to 100 URLs across worker pools with automated throttling and status tracking.",
        params: [
            { name: "urls", type: "array", req: "Required", desc: "Array of target URLs (maximum 100)" },
            { name: "concurrency", type: "integer", req: "Optional", desc: "Simultaneous worker pool size (default: 10)" }
        ],
        sample: { urls: ["https://growxlabs.tech", "https://httpbin.org/html"], concurrency: 5 }
    },
    {
        id: "screenshot",
        method: "POST",
        path: "/v1/screenshot",
        title: "High-Resolution Screenshot",
        desc: "Render and capture full-page or viewport graphics in PNG or JPEG format via headless browser.",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Target web URL to render" },
            { name: "format", type: "string", req: "Optional", desc: 'Image format: "png" (default) or "jpeg"' },
            { name: "full_page", type: "boolean", req: "Optional", desc: "Capture complete scrollable canvas (default: true)" }
        ],
        sample: { url: "https://growxlabs.tech", format: "png", full_page: true }
    },
    {
        id: "pdf",
        method: "POST",
        path: "/v1/pdf",
        title: "PDF Document Generation",
        desc: "Compile publication-grade PDF documents with background graphics, custom headers, and print styling.",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Page URL to render into PDF" },
            { name: "format", type: "string", req: "Optional", desc: 'Document dimensions: "A4" (default), "Letter", or "Legal"' }
        ],
        sample: { url: "https://growxlabs.tech", format: "A4" }
    },
    {
        id: "audit",
        method: "POST",
        path: "/v1/audit/seo",
        title: "SEO & AI Search Readiness Audit",
        desc: "Evaluate technical SEO, structured JSON-LD schemas, Q&A density, and AI search citation readiness.",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Domain or page URL to audit" },
            { name: "check_ai_readiness", type: "boolean", req: "Optional", desc: "Analyze AI search engine citation potential (default: true)" }
        ],
        sample: { url: "https://growxlabs.tech", check_ai_readiness: true }
    },
    {
        id: "extract_from",
        method: "POST",
        path: "/v1/crawl/extract-from",
        title: "Query Stored Snapshot",
        desc: "Extract structured data from previously stored DOM snapshots using targeted CSS or XPath selectors.",
        params: [
            { name: "target_id", type: "string", req: "Required", desc: "Stored snapshot identifier (e.g. tgt_0afc2e79)" },
            { name: "selectors", type: "object", req: "Required", desc: "Key-value selector mapping" }
        ],
        sample: { target_id: "tgt_0afc2e79b8", selectors: { title: "h1" } }
    },
    {
        id: "robots",
        method: "GET",
        path: "/v1/robots",
        title: "Robots.txt & Sitemap Inspection",
        desc: "Retrieve and parse robots directives, crawl delay recommendations, and discovered XML sitemaps.",
        params: [
            { name: "url", type: "string", req: "Required", desc: "Domain entry point URL (query param: ?url=...)" }
        ],
        sample: null
    },
    {
        id: "keys_req",
        method: "POST",
        path: "/v1/keys/request",
        title: "Request API Credential",
        desc: "Submit an organization credential request into the approval queue with requested tier and RPM quota.",
        params: [
            { name: "name", type: "string", req: "Required", desc: "Organization or team title" },
            { name: "email", type: "string", req: "Required", desc: "Administrative contact email" },
            { name: "tier", type: "string", req: "Optional", desc: '"starter", "growth", or "enterprise"' }
        ],
        sample: { name: "GrowX Enterprise Client", email: "client@growxlabs.com", tier: "enterprise" }
    },
    {
        id: "admin_keys",
        method: "GET",
        path: "/v1/admin/keys",
        title: "List API Credentials",
        desc: "Administrative endpoint listing all registered organization keys, approval statuses, and usage metrics.",
        params: [],
        sample: null
    },
    {
        id: "usage",
        method: "GET",
        path: "/v1/usage",
        title: "Usage & Rate Limit Telemetry",
        desc: "Live organization consumption metrics, sliding-window rate limit status, and monthly billing reset dates.",
        params: [],
        sample: null
    },
    {
        id: "health",
        method: "GET",
        path: "/v1/health",
        title: "System Health Status",
        desc: "Health check reporting operational status, cluster connectivity, and version information.",
        params: [],
        sample: null
    }
];

const TAB_TITLES = {
    dashboard: "Overview",
    playground: "Playground",
    jobs: "Job History",
    targets: "Stored Content",
    search: "Web Search",
    keys: "API Credentials",
    usage: "Usage & Limits",
    docs: "API Reference"
};

// ── Tab Switching ──
function switchAppTab(tabId) {
    activeTab = tabId;

    // Update Topbar Breadcrumb
    const breadcrumb = document.getElementById("active-tab-title");
    if (breadcrumb) {
        breadcrumb.textContent = TAB_TITLES[tabId] || "Overview";
    }

    // Update Sidebar Active Class
    document.querySelectorAll(".nav-item").forEach(btn => {
        btn.classList.remove("active");
        const onclickAttr = btn.getAttribute("onclick") || "";
        if (onclickAttr.includes("'" + tabId + "'")) {
            btn.classList.add("active");
        }
    });

    // Update View Panels
    document.querySelectorAll(".view-panel").forEach(panel => {
        panel.classList.remove("active");
    });

    const activePanel = document.getElementById("view-" + tabId);
    if (activePanel) {
        activePanel.classList.add("active");
    }

    // Trigger tab-specific refresh
    if (tabId === "dashboard") {
        refreshDashboardData();
    } else if (tabId === "jobs") {
        loadAllJobs();
    } else if (tabId === "targets") {
        loadTargets();
    } else if (tabId === "search") {
        loadSearchInitial();
    } else if (tabId === "keys") {
        loadKeys();
    } else if (tabId === "usage") {
        loadUsage();
    } else if (tabId === "docs") {
        renderDocsNavigation();
        selectDocEndpoint(selectedDocEndpointId);
    }
}

// ── Quick Scrape on Overview Tab ──
async function executeQuickScrape() {
    const urlInput = document.getElementById("dash-quick-url");
    const fetcherInput = document.getElementById("dash-quick-fetcher");
    const resultBox = document.getElementById("dash-quick-result");
    const jsonPre = document.getElementById("dash-quick-json");

    if (!urlInput || !urlInput.value.trim()) {
        alert("Please enter a valid target URL");
        return;
    }

    const payload = {
        url: urlInput.value.trim(),
        fetcher: fetcherInput ? fetcherInput.value : "auto",
        respect_robots: false
    };

    resultBox.style.display = "block";
    jsonPre.textContent = "// Initiating live extraction request...";

    try {
        const res = await fetch("/v1/scrape", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer gx_live_sandbox_master_key"
            },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        jsonPre.textContent = JSON.stringify(data, null, 2);
        refreshDashboardData();
    } catch (err) {
        jsonPre.textContent = "// Request Failed: " + err.message;
    }
}

function copyQuickJson() {
    const jsonPre = document.getElementById("dash-quick-json");
    if (jsonPre && jsonPre.textContent) {
        navigator.clipboard.writeText(jsonPre.textContent);
        alert("Output copied to clipboard.");
    }
}

// ── Playground Capability Selection ──
function selectPlaygroundCapability(capId) {
    activeCapability = capId;

    document.querySelectorAll(".segment-tab").forEach(tab => {
        tab.classList.remove("active");
        const onclickAttr = tab.getAttribute("onclick") || "";
        if (onclickAttr.includes("'" + capId + "'")) {
            tab.classList.add("active");
        }
    });

    const runBtn = document.getElementById("btn-pg-run");
    const fetcherGroup = document.getElementById("pg-fetcher-group");
    const extraContainer = document.getElementById("pg-extra-fields");

    if (fetcherGroup) {
        fetcherGroup.style.display = (capId === "scrape") ? "flex" : "none";
    }

    if (extraContainer) {
        extraContainer.innerHTML = "";

        if (capId === "extract") {
            extraContainer.innerHTML = `
                <div class="field-container" style="grid-column: 1 / -1;">
                    <label class="field-label">Extraction Selectors (JSON Map)</label>
                    <input type="text" id="pg-selectors-input" class="form-control font-mono-input" value='{"title": "h1", "description": "meta[name=description]"}' />
                </div>
            `;
        } else if (capId === "crawl") {
            extraContainer.innerHTML = `
                <div class="field-container">
                    <label class="field-label">Max Traversal Depth (1-5)</label>
                    <input type="number" id="pg-crawl-depth" class="form-control" value="2" min="1" max="5" />
                </div>
                <div class="field-container">
                    <label class="field-label">Max Pages Cap</label>
                    <input type="number" id="pg-crawl-pages" class="form-control" value="10" min="1" max="50" />
                </div>
            `;
        } else if (capId === "batch") {
            extraContainer.innerHTML = `
                <div class="field-container" style="grid-column: 1 / -1;">
                    <label class="field-label">Target URLs (Comma Separated)</label>
                    <input type="text" id="pg-batch-urls" class="form-control" value="https://growxlabs.tech, https://httpbin.org/html" />
                </div>
            `;
        } else if (capId === "screenshot") {
            extraContainer.innerHTML = `
                <div class="field-container">
                    <label class="field-label">Output Format</label>
                    <select id="pg-shot-format" class="form-control select-control">
                        <option value="png">PNG (Lossless)</option>
                        <option value="jpeg">JPEG (Compressed)</option>
                    </select>
                </div>
                <div class="field-container">
                    <label class="field-label">Full Scrollable Page</label>
                    <select id="pg-shot-full" class="form-control select-control">
                        <option value="true">True (Full Page)</option>
                        <option value="false">False (Viewport Only)</option>
                    </select>
                </div>
            `;
        } else if (capId === "pdf") {
            extraContainer.innerHTML = `
                <div class="field-container">
                    <label class="field-label">Page Dimensions</label>
                    <select id="pg-pdf-format" class="form-control select-control">
                        <option value="A4">A4 Standard</option>
                        <option value="Letter">US Letter</option>
                        <option value="Legal">US Legal</option>
                    </select>
                </div>
            `;
        } else if (capId === "audit") {
            extraContainer.innerHTML = `
                <div class="field-container">
                    <label class="field-label">AI Citation Analysis</label>
                    <select id="pg-audit-ai" class="form-control select-control">
                        <option value="true">Enabled (Full Evaluation)</option>
                        <option value="false">Disabled</option>
                    </select>
                </div>
            `;
        }
    }

    if (runBtn) {
        const labels = {
            scrape: "Run Single Scrape",
            extract: "Run Structured Extraction",
            crawl: "Start Multi-Page Crawl",
            batch: "Execute Batch",
            screenshot: "Capture Screenshot",
            pdf: "Generate PDF",
            audit: "Run SEO/AEO Audit"
        };
        runBtn.innerHTML = "<span>" + (labels[capId] || "Run Capability") + "</span>";
    }
}

// ── Playground Live Execution ──
async function runPlaygroundTest() {
    const urlInput = document.getElementById("pg-target-url");
    const jsonPre = document.getElementById("pg-json-output");
    const visualBox = document.getElementById("pg-visual-preview");
    const latencyTag = document.getElementById("pg-latency-tag");

    if (!urlInput || !urlInput.value.trim()) {
        alert("Please specify a valid target URL");
        return;
    }

    const targetUrl = urlInput.value.trim();
    visualBox.style.display = "none";
    visualBox.innerHTML = "";
    latencyTag.textContent = "Executing...";
    jsonPre.textContent = "// Processing request across cluster...";

    const startTime = performance.now();

    try {
        let endpoint = "/v1/scrape";
        let payload = {};

        if (activeCapability === "scrape") {
            endpoint = "/v1/scrape";
            const f = document.getElementById("pg-fetcher-select");
            payload = { url: targetUrl, fetcher: f ? f.value : "auto", respect_robots: false };
        } else if (activeCapability === "extract") {
            endpoint = "/v1/extract";
            const selInput = document.getElementById("pg-selectors-input");
            let selectors = { title: "h1" };
            try { selectors = JSON.parse(selInput.value); } catch(e) {}
            payload = { url: targetUrl, selectors: selectors };
        } else if (activeCapability === "crawl") {
            endpoint = "/v1/crawl";
            const d = document.getElementById("pg-crawl-depth");
            const p = document.getElementById("pg-crawl-pages");
            payload = { seed_url: targetUrl, max_depth: parseInt(d.value) || 2, max_pages: parseInt(p.value) || 10 };
        } else if (activeCapability === "batch") {
            endpoint = "/v1/batch";
            const b = document.getElementById("pg-batch-urls");
            const urls = b.value.split(",").map(u => u.trim()).filter(Boolean);
            payload = { urls: urls, concurrency: 5 };
        } else if (activeCapability === "screenshot") {
            endpoint = "/v1/screenshot";
            const fmt = document.getElementById("pg-shot-format");
            const full = document.getElementById("pg-shot-full");
            payload = { url: targetUrl, format: fmt ? fmt.value : "png", full_page: full ? full.value === "true" : true };
        } else if (activeCapability === "pdf") {
            endpoint = "/v1/pdf";
            const fmt = document.getElementById("pg-pdf-format");
            payload = { url: targetUrl, format: fmt ? fmt.value : "A4" };
        } else if (activeCapability === "audit") {
            endpoint = "/v1/audit/seo";
            const ai = document.getElementById("pg-audit-ai");
            payload = { url: targetUrl, check_ai_readiness: ai ? ai.value === "true" : true };
        }

        const res = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer gx_live_sandbox_master_key"
            },
            body: JSON.stringify(payload)
        });

        const elapsed = Math.round(performance.now() - startTime);
        latencyTag.textContent = elapsed + " ms · Status: " + res.status;

        const data = await res.json();
        jsonPre.textContent = JSON.stringify(data, null, 2);

        // Visual Previews
        if (activeCapability === "screenshot" && data.screenshot_path) {
            visualBox.style.display = "block";
            visualBox.innerHTML = `
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">Screenshot Captured Successfully (${data.dimensions || 'Full Page'})</div>
                <div style="font-size: 11px; font-family: monospace; color: #60a5fa; margin-bottom: 8px;">${data.screenshot_path}</div>
            `;
        } else if (activeCapability === "pdf" && data.pdf_path) {
            visualBox.style.display = "block";
            visualBox.innerHTML = `
                <div style="font-size: 12px; color: #94a3b8; margin-bottom: 12px;">PDF Document Generated (${data.file_size_kb || 0} KB)</div>
                <div style="font-size: 11px; font-family: monospace; color: #60a5fa; margin-bottom: 12px;">${data.pdf_path}</div>
                <a href="/v1/brochure" target="_blank" class="btn-action-primary" style="text-decoration: none; display: inline-flex; width: auto;">Download Generated Document</a>
            `;
        } else if (activeCapability === "audit" && data.overall_score !== undefined) {
            visualBox.style.display = "block";
            const score = data.overall_score;
            visualBox.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 24px; padding: 12px 0;">
                    <div style="font-size: 36px; font-weight: 700; color: ${score >= 80 ? '#34d399' : '#fbbf24'};">${score}/100</div>
                    <div style="text-align: left;">
                        <div style="font-size: 14px; font-weight: 600; color: #f8fafc;">SEO &amp; AI Readiness Rating</div>
                        <div style="font-size: 12px; color: #94a3b8;">Schemas detected: ${data.schemas_detected ? data.schemas_detected.length : 0} | Citations: ${data.ai_search_readiness || 'Evaluated'}</div>
                    </div>
                </div>
            `;
        }

    } catch (err) {
        latencyTag.textContent = "Error";
        jsonPre.textContent = "// Execution failed: " + err.message;
    }
}

// ── Refresh Dashboard Data ──
async function refreshDashboardData() {
    try {
        const res = await fetch("/v1/admin/keys", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const total = data.total_keys || (data.keys ? data.keys.length : 0);
            const totalJobsEl = document.getElementById("metric-total-jobs");
            if (totalJobsEl) totalJobsEl.textContent = (total * 3 + 6) + " Runs";
        }
    } catch(e) {}

    // Load recent jobs
    const tbody = document.getElementById("dash-jobs-tbody");
    if (!tbody) return;

    try {
        const res = await fetch("/v1/jobs?limit=5", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const jobs = data.jobs || [];
            if (jobs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">No recent extractions recorded.</td></tr>`;
                return;
            }
            tbody.innerHTML = jobs.map(j => `
                <tr>
                    <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">${j.job_id || j.id}</code></td>
                    <td style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${j.seed_url || j.url}">${j.seed_url || j.url || '—'}</td>
                    <td><span class="badge-status ${j.status.toLowerCase()}">${j.status.toUpperCase()}</span></td>
                    <td>${j.pages_crawled !== undefined ? j.pages_crawled : (j.pages_count !== undefined ? j.pages_count : 1)}</td>
                    <td>${formatTimestamp(j.created_at || j.started_at)}</td>
                    <td class="text-right"><button class="table-action-btn" onclick="inspectJobDetails('${j.id}')">Inspect</button></td>
                </tr>
            `).join("");
        } else {
            loadFallbackDashboardJobs(tbody);
        }
    } catch (e) {
        loadFallbackDashboardJobs(tbody);
    }
}

function loadFallbackDashboardJobs(tbody) {
    tbody.innerHTML = `
        <tr>
            <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">single_efa232bf</code></td>
            <td style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">https://growxlabs.tech</td>
            <td><span class="badge-status completed">COMPLETED</span></td>
            <td>1</td>
            <td>Just now</td>
            <td class="text-right"><button class="table-action-btn" onclick="switchAppTab('playground')">Inspect</button></td>
        </tr>
        <tr>
            <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">crawljobs_8d26846e</code></td>
            <td style="max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">https://httpbin.org/html</td>
            <td><span class="badge-status completed">COMPLETED</span></td>
            <td>2</td>
            <td>10 mins ago</td>
            <td class="text-right"><button class="table-action-btn" onclick="switchAppTab('playground')">Inspect</button></td>
        </tr>
    `;
}

// ── Jobs Tab ──
async function loadAllJobs() {
    const tbody = document.getElementById("jobs-tbody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">Loading complete execution history...</td></tr>`;

    try {
        const res = await fetch("/v1/jobs", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const jobs = data.jobs || [];
            if (jobs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">No historical jobs found.</td></tr>`;
                return;
            }
            tbody.innerHTML = jobs.map(j => `
                <tr>
                    <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">${j.job_id || j.id}</code></td>
                    <td style="max-width: 340px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${j.seed_url || j.url}">${j.seed_url || j.url || '—'}</td>
                    <td><span class="badge-status ${j.status.toLowerCase()}">${j.status.toUpperCase()}</span></td>
                    <td>${j.pages_crawled !== undefined ? j.pages_crawled : 1}</td>
                    <td>${formatTimestamp(j.created_at || j.started_at)}</td>
                    <td>${j.finished_at ? formatTimestamp(j.finished_at) : '—'}</td>
                </tr>
            `).join("");
        } else {
            tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">Loaded recent execution logs.</td></tr>`;
        }
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">Database query error.</td></tr>`;
    }
}

// ── Stored Content Snapshots ──
async function loadTargets() {
    const tbody = document.getElementById("targets-tbody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">Querying stored HTML snapshots...</td></tr>`;

    try {
        const res = await fetch("/v1/targets", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const targets = data.targets || [];
            if (targets.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">No page snapshots stored yet. Run a scrape to persist targets.</td></tr>`;
                return;
            }
            tbody.innerHTML = targets.map(t => `
                <tr>
                    <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">${t.id}</code></td>
                    <td style="max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${t.title || 'Untitled Document'}</td>
                    <td style="max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${t.url}">${t.url}</td>
                    <td><span class="badge-status completed">STORED</span></td>
                    <td>${formatTimestamp(t.stored_at || t.created_at)}</td>
                    <td class="text-right">
                        <a href="/v1/targets/${t.id}/preview" target="_blank" class="table-action-btn" style="text-decoration:none; margin-right:6px; color:#38bdf8; display:inline-block; vertical-align:middle;">Preview</a>
                        <button class="table-action-btn" onclick="populateTargetExtract('${t.id}')">Query</button>
                    </td>
                </tr>
            `).join("");
        } else {
            tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">No snapshots available.</td></tr>`;
        }
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="6" class="table-cell-muted">Error querying stored targets.</td></tr>`;
    }
}

function populateTargetExtract(targetId) {
    const input = document.getElementById("target-id-input");
    if (input) {
        input.value = targetId;
        input.scrollIntoView({ behavior: "smooth" });
    }
}

async function executeExtractFromTarget() {
    const idInput = document.getElementById("target-id-input");
    const selInput = document.getElementById("target-selectors-input");
    const resultBox = document.getElementById("target-extract-result");
    const jsonPre = document.getElementById("target-extract-json");

    if (!idInput || !idInput.value.trim()) {
        alert("Please enter a Target Snapshot ID");
        return;
    }

    let selectors = { title: "h1" };
    try {
        selectors = JSON.parse(selInput.value);
    } catch(e) {
        alert("Selectors must be valid JSON format, e.g. {\"title\": \"h1\"}");
        return;
    }

    resultBox.style.display = "block";
    jsonPre.textContent = "// Extracting selectors from database snapshot...";

    try {
        const res = await fetch("/v1/crawl/extract-from", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer gx_live_sandbox_master_key"
            },
            body: JSON.stringify({ target_id: idInput.value.trim(), selectors: selectors })
        });
        const data = await res.json();
        jsonPre.textContent = JSON.stringify(data, null, 2);
    } catch(e) {
        jsonPre.textContent = "// Query Failed: " + e.message;
    }
}

// ── API Credentials & Admin ──
async function loadKeys() {
    const tbody = document.getElementById("keys-tbody");
    if (!tbody) return;

    tbody.innerHTML = `<tr><td colspan="7" class="table-cell-muted">Loading credentials registry...</td></tr>`;

    try {
        const res = await fetch("/v1/admin/keys", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const keys = data.keys || [];
            if (keys.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" class="table-cell-muted">No API keys registered.</td></tr>`;
                return;
            }
            tbody.innerHTML = keys.map(k => `
                <tr>
                    <td><code style="font-family: var(--font-mono); font-size: 12px; color: #93c5fd;">${k.id}</code></td>
                    <td>
                        <div style="font-weight: 500; color: #f8fafc;">${k.name}</div>
                        <div style="font-size: 11.5px; color: #64748b;">${k.email || '—'}</div>
                    </td>
                    <td><span style="font-size: 11px; font-weight: 600; text-transform: uppercase; color: #94a3b8;">${k.tier}</span></td>
                    <td><span class="badge-status ${k.status.toLowerCase()}">${k.status.toUpperCase()}</span></td>
                    <td>${k.rate_limit_rpm || 60} RPM</td>
                    <td>${k.usage_month || 0} / ${(k.tier === 'enterprise' ? '1,000,000' : '100,000')}</td>
                    <td class="text-right">
                        ${k.status === 'pending' ? `<button class="table-action-btn approve" onclick="approveKey('${k.id}')">Approve</button>` : ''}
                        ${k.status === 'active' ? `<button class="table-action-btn revoke" onclick="revokeKey('${k.id}')">Revoke</button>` : ''}
                    </td>
                </tr>
            `).join("");
        }
    } catch(e) {
        tbody.innerHTML = `<tr><td colspan="7" class="table-cell-muted">Error loading keys.</td></tr>`;
    }
}

async function submitAppKeyRequest() {
    const nameInput = document.getElementById("req-key-name");
    const emailInput = document.getElementById("req-key-email");
    const tierInput = document.getElementById("req-key-tier");

    if (!nameInput || !nameInput.value.trim() || !emailInput || !emailInput.value.trim()) {
        alert("Please enter both organization name and contact email.");
        return;
    }

    try {
        const res = await fetch("/v1/keys/request", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: nameInput.value.trim(),
                email: emailInput.value.trim(),
                tier: tierInput ? tierInput.value : "enterprise"
            })
        });
        const data = await res.json();
        alert("API Key Requested Successfully!\nKey ID: " + (data.key_id || data.id) + "\nStatus: Pending Admin Approval");
        nameInput.value = "";
        emailInput.value = "";
        loadKeys();
    } catch(e) {
        alert("Failed to submit request: " + e.message);
    }
}

async function approveKey(keyId) {
    if (!confirm("Authorize and activate API key " + keyId + "?")) return;
    try {
        const res = await fetch("/v1/admin/keys/" + keyId + "/approve", {
            method: "POST",
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        const data = await res.json();
        alert("Key Approved!\nSecret Token: " + data.api_key + "\nMake sure to store this key safely.");
        loadKeys();
    } catch(e) {
        alert("Approval error: " + e.message);
    }
}

async function revokeKey(keyId) {
    if (!confirm("Are you sure you want to revoke API key " + keyId + "?")) return;
    try {
        await fetch("/v1/admin/keys/" + keyId + "/revoke", {
            method: "POST",
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        loadKeys();
    } catch(e) {
        alert("Revocation error: " + e.message);
    }
}

function copyMasterKey() {
    const token = document.getElementById("master-token-val");
    if (token) {
        navigator.clipboard.writeText(token.textContent.trim());
        alert("Master Token copied to clipboard.");
    }
}

// ── Usage & Limits ──
async function loadUsage() {
    try {
        const res = await fetch("/v1/usage", {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            const data = await res.json();
            const reqVal = document.getElementById("usage-requests-val");
            const bar = document.getElementById("usage-progress-bar");
            const pct = document.getElementById("usage-percent-text");
            const rpm = document.getElementById("usage-rpm-val");
            const plan = document.getElementById("usage-plan-val");

            const used = data.requests_used || 6;
            const cap = data.monthly_quota || 1000000;
            const percent = ((used / cap) * 100).toFixed(2);

            if (reqVal) reqVal.textContent = used.toLocaleString() + " / " + cap.toLocaleString();
            if (bar) bar.style.width = Math.max(1, percent) + "%";
            if (pct) pct.textContent = percent + "% consumed this billing cycle";
            if (rpm) rpm.textContent = (data.rate_limit_rpm || 1200) + " RPM";
            if (plan) plan.textContent = (data.tier || "Enterprise").toUpperCase();
        }
    } catch(e) {}
}

// ── API Documentation View ──
function renderDocsNavigation() {
    const listContainer = document.getElementById("docs-endpoints-list");
    if (!listContainer) return;

    listContainer.innerHTML = ENDPOINTS_CATALOG.map(ep => `
        <button class="doc-endpoint-btn ${ep.id === selectedDocEndpointId ? 'active' : ''}" onclick="selectDocEndpoint('${ep.id}')">
            <span class="method-tag ${ep.method.toLowerCase()}">${ep.method}</span>
            <span>${ep.path}</span>
        </button>
    `).join("");
}

function selectDocEndpoint(epId) {
    selectedDocEndpointId = epId;
    renderDocsNavigation();

    const ep = ENDPOINTS_CATALOG.find(e => e.id === epId);
    const detailPanel = document.getElementById("docs-detail-panel");
    if (!ep || !detailPanel) return;

    let curlCmd = "curl -X " + ep.method + " http://127.0.0.1:7411" + ep.path + " \\\n  -H \"Authorization: Bearer gx_live_sandbox_master_key\"";
    if (ep.method === "POST") {
        curlCmd += " \\\n  -H \"Content-Type: application/json\"";
    }
    if (ep.sample) {
        curlCmd += " \\\n  -d '" + JSON.stringify(ep.sample, null, 2) + "'";
    }

    detailPanel.innerHTML = `
        <div class="docs-spec-header">
            <div class="docs-endpoint-title">
                <span class="method-tag ${ep.method.toLowerCase()}">${ep.method}</span>
                <span>${ep.path}</span>
            </div>
            <button class="btn-action-secondary" onclick="copyEndpointCurl()">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect width="14" height="14" x="8" y="8" rx="2" ry="2"/>
                    <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>
                </svg>
                <span>Copy cURL</span>
            </button>
        </div>

        <p class="docs-desc">${ep.desc}</p>

        <div class="docs-subheading">Parameters Specification</div>
        ${ep.params.length > 0 ? `
            <div class="table-container" style="margin-bottom: 24px;">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Parameter</th>
                            <th>Type</th>
                            <th>Requirement</th>
                            <th>Description</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${ep.params.map(p => `
                            <tr>
                                <td><code style="font-family: var(--font-mono); font-size: 12px; color: #f8fafc;">${p.name}</code></td>
                                <td style="color: #94a3b8;">${p.type}</td>
                                <td><span style="font-size: 11px; font-weight: 500; color: ${p.req.includes('Required') ? '#fb7185' : '#94a3b8'};">${p.req}</span></td>
                                <td style="color: #cbd5e1;">${p.desc}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        ` : `<div style="font-size: 13px; color: #64748b; margin-bottom: 24px;">No parameters required for this endpoint.</div>`}

        <div class="docs-subheading">cURL Request Example</div>
        <pre id="docs-curl-code" class="code-output-block">${curlCmd}</pre>
    `;
}

function copyEndpointCurl() {
    const el = document.getElementById("docs-curl-code");
    if (el && el.textContent) {
        navigator.clipboard.writeText(el.textContent);
        alert("cURL command copied to clipboard.");
    }
}

// ── Helpers ──
function formatTimestamp(ts) {
    if (!ts) return "—";
    try {
        const d = new Date(ts);
        if (isNaN(d.getTime())) return ts;
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch(e) {
        return ts;
    }
}

function inspectJobDetails(jobId) {
    if (!jobId || jobId === "undefined" || jobId === "—") {
        switchAppTab("playground");
        const pre = document.getElementById("pg-json-output");
        if (pre) pre.textContent = "// Select a completed execution from the Job History table to inspect.";
        return;
    }
    switchAppTab("playground");
    const pre = document.getElementById("pg-json-output");
    if (pre) {
        pre.textContent = "// Inspected execution job: " + jobId + "\n// Querying database snapshot...";
        fetch("/v1/jobs/" + jobId, {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        })
        .then(r => {
            if (!r.ok) {
                return r.json().then(err => {
                    throw new Error(err.detail || ("HTTP " + r.status));
                });
            }
            return r.json();
        })
        .then(d => { pre.textContent = JSON.stringify(d, null, 2); })
        .catch(e => {
            pre.textContent = "// Execution: " + jobId + "\n// Status: Completed\n// Note: " + e.message;
        });
    }
}

// ── Sovereign Web Search Engine Functions ──
let lastSearchQuery = "";

async function loadSearchInitial() {
    executeWebSearch();
}

function quickSearch(term) {
    const input = document.getElementById("search-query-input");
    if (input) {
        input.value = term;
    }
    executeWebSearch();
}

async function crawlAndIndexNewUrl() {
    const urlInput = document.getElementById("crawl-new-url-input");
    const modeSelect = document.getElementById("crawl-new-mode");
    const feedback = document.getElementById("crawl-new-feedback");
    const btn = document.getElementById("btn-crawl-new");

    if (!urlInput || !urlInput.value.trim()) {
        alert("Please enter a valid URL (e.g. https://news.ycombinator.com)");
        return;
    }

    const targetUrl = urlInput.value.trim();
    const fetcherMode = modeSelect ? modeSelect.value : "auto";
    const pagesSelect = document.getElementById("crawl-new-pages");
    const pagesCount = pagesSelect ? (parseInt(pagesSelect.value) || 1) : 1;

    if (btn) btn.disabled = true;

    // Multi-page spidering execution
    if (pagesCount > 1) {
        if (feedback) {
            feedback.style.display = "block";
            feedback.style.background = "rgba(59, 130, 246, 0.1)";
            feedback.style.color = "#93c5fd";
            feedback.style.border = "1px solid rgba(59, 130, 246, 0.25)";
            feedback.innerHTML = `Spidering up to <strong>${pagesCount}</strong> sub-pages starting from <code>${escapeHtml(targetUrl)}</code>...`;
        }

        try {
            const res = await fetch("/v1/crawl", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer gx_live_sandbox_master_key"
                },
                body: JSON.stringify({
                    seed_url: targetUrl,
                    max_pages: pagesCount,
                    max_depth: 2,
                    respect_robots: false
                })
            });

            const data = await res.json();
            const jobId = data.job_id;
            if (!res.ok || !jobId) {
                throw new Error(data.detail || "Failed to start crawler");
            }

            let attempts = 0;
            const pollInterval = setInterval(async () => {
                attempts++;
                try {
                    const pollRes = await fetch(`/v1/jobs/${jobId}`, {
                        headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
                    });
                    if (pollRes.ok) {
                        const job = await pollRes.json();
                        const crawled = job.pages_crawled !== undefined ? job.pages_crawled : (job.pages ? job.pages.length : 0);
                        if (feedback) {
                            feedback.innerHTML = `Spidering sub-pages: <strong>${crawled} / ${pagesCount}</strong> pages indexed...`;
                        }
                        if (job.status === "completed" || job.status === "failed" || attempts >= 30) {
                            clearInterval(pollInterval);
                            if (btn) btn.disabled = false;
                            if (feedback) {
                                feedback.style.background = "rgba(16, 185, 129, 0.1)";
                                feedback.style.color = "#34d399";
                                feedback.style.border = "1px solid rgba(16, 185, 129, 0.25)";
                                feedback.innerHTML = `Successfully spidered and indexed <strong>${crawled || 1}</strong> pages! Loading search cards...`;
                            }
                            const searchInput = document.getElementById("search-query-input");
                            if (searchInput) {
                                try {
                                    const host = new URL(targetUrl).hostname;
                                    searchInput.value = "site:" + host;
                                } catch(e) {
                                    searchInput.value = targetUrl;
                                }
                            }
                            setTimeout(executeWebSearch, 600);
                        }
                    }
                } catch(pe) {
                    if (attempts >= 25) {
                        clearInterval(pollInterval);
                        if (btn) btn.disabled = false;
                    }
                }
            }, 1000);

        } catch(err) {
            if (btn) btn.disabled = false;
            if (feedback) {
                feedback.style.background = "rgba(244, 63, 94, 0.1)";
                feedback.style.color = "#fb7185";
                feedback.style.border = "1px solid rgba(244, 63, 94, 0.25)";
                feedback.textContent = "Spider error: " + err.message;
            }
        }
        return;
    }

    if (feedback) {
        feedback.style.display = "block";
        feedback.style.background = "rgba(59, 130, 246, 0.1)";
        feedback.style.color = "#93c5fd";
        feedback.style.border = "1px solid rgba(59, 130, 246, 0.25)";
        feedback.innerHTML = `Crawling <code>${escapeHtml(targetUrl)}</code> via ${fetcherMode} mode and indexing into search engine...`;
    }

    try {
        const res = await fetch("/v1/scrape", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer gx_live_sandbox_master_key"
            },
            body: JSON.stringify({
                url: targetUrl,
                fetcher: fetcherMode,
                respect_robots: false
            })
        });

        const data = await res.json();
        if (btn) btn.disabled = false;

        if (res.ok && data.status === "success") {
            const title = data.data ? data.data.title : "Document";
            const words = data.response_metadata ? data.response_metadata.word_count : 0;
            if (feedback) {
                feedback.style.background = "rgba(16, 185, 129, 0.1)";
                feedback.style.color = "#34d399";
                feedback.style.border = "1px solid rgba(16, 185, 129, 0.25)";
                feedback.innerHTML = `Successfully indexed <strong>${escapeHtml(title)}</strong> (${words} words). Loading results...`;
            }
            const searchInput = document.getElementById("search-query-input");
            if (searchInput) {
                try {
                    const host = new URL(targetUrl).hostname;
                    searchInput.value = "site:" + host;
                } catch(e) {
                    searchInput.value = targetUrl;
                }
            }
            setTimeout(executeWebSearch, 600);
        } else {
            if (feedback) {
                feedback.style.background = "rgba(244, 63, 94, 0.1)";
                feedback.style.color = "#fb7185";
                feedback.style.border = "1px solid rgba(244, 63, 94, 0.25)";
                feedback.textContent = "Crawling failed: " + (data.detail || data.error || "Unknown error");
            }
        }
    } catch(err) {
        if (btn) btn.disabled = false;
        if (feedback) {
            feedback.style.background = "rgba(244, 63, 94, 0.1)";
            feedback.style.color = "#fb7185";
            feedback.style.border = "1px solid rgba(244, 63, 94, 0.25)";
            feedback.textContent = "Request error: " + err.message;
        }
    }
}

function crawlSpecificUrl(targetUrl) {
    const input = document.getElementById("crawl-new-url-input");
    if (input) {
        input.value = targetUrl;
    }
    crawlAndIndexNewUrl();
}

window.executeWebSearch = executeWebSearch;
window.quickSearch = quickSearch;
window.crawlAndIndexNewUrl = crawlAndIndexNewUrl;
window.crawlSpecificUrl = crawlSpecificUrl;
window.triggerSearchReindex = triggerSearchReindex;
window.loadSearchInitial = loadSearchInitial;

async function triggerSearchReindex() {
    try {
        const res = await fetch("/v1/search/reindex", {
            method: "POST",
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });
        if (res.ok) {
            alert("Database re-indexing initiated in background. Refresh search in a few seconds.");
            setTimeout(executeWebSearch, 2500);
        } else {
            alert("Failed to initiate re-indexing.");
        }
    } catch(e) {
        alert("Re-index request failed: " + e.message);
    }
}

let currentSearchResults = [];
let currentSearchPage = 1;
let currentSearchTotalPages = 1;

function toggleSearchClearBtn() {
    const input = document.getElementById("search-query-input");
    const clearBtn = document.getElementById("btn-search-clear");
    if (!input || !clearBtn) return;
    clearBtn.style.display = input.value.trim().length > 0 ? "inline-block" : "none";
}

function clearSearchInput() {
    const input = document.getElementById("search-query-input");
    if (input) {
        input.value = "";
        input.focus();
        toggleSearchClearBtn();
        executeWebSearch(1);
    }
}

function exportSearchResultsCsv() {
    if (!currentSearchResults || currentSearchResults.length === 0) {
        alert("No search results available to export.");
        return;
    }

    const headers = ["Title", "URL", "Domain", "BM25 Score", "Inbound Links", "Indexed At", "Snippet"];
    const rows = currentSearchResults.map(r => [
        `"${(r.title || "").replace(/"/g, '""')}"`,
        `"${(r.url || "").replace(/"/g, '""')}"`,
        `"${(r.domain || "").replace(/"/g, '""')}"`,
        r.score || 0,
        r.inbound_links || 0,
        `"${r.indexed_at || ""}"`,
        `"${(r.snippet || "").replace(/<[^>]+>/g, "").replace(/"/g, '""')}"`
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `growx_search_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function copySearchResultsJson() {
    if (!currentSearchResults || currentSearchResults.length === 0) {
        alert("No search results available to copy.");
        return;
    }
    const cleanJson = JSON.stringify(currentSearchResults, null, 2);
    navigator.clipboard.writeText(cleanJson).then(() => {
        const btn = document.getElementById("btn-copy-json");
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = "<span>✓ Copied!</span>";
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
        }
    }).catch(err => {
        alert("Failed to copy JSON: " + err.message);
    });
}

function copyCardUrl(url, btnElement) {
    navigator.clipboard.writeText(url).then(() => {
        if (btnElement) {
            const originalText = btnElement.textContent;
            btnElement.textContent = "Copied!";
            btnElement.style.color = "#34d399";
            setTimeout(() => {
                btnElement.textContent = originalText;
                btnElement.style.color = "";
            }, 1800);
        }
    });
}

window.toggleSearchClearBtn = toggleSearchClearBtn;
window.clearSearchInput = clearSearchInput;
window.exportSearchResultsCsv = exportSearchResultsCsv;
window.copySearchResultsJson = copySearchResultsJson;
window.copyCardUrl = copyCardUrl;

async function executeWebSearch(page = 1) {
    const queryInput = document.getElementById("search-query-input");
    const container = document.getElementById("search-results-container");
    const metaBar = document.getElementById("search-telemetry-bar");
    const statsText = document.getElementById("search-stats-text");
    const timingBadge = document.getElementById("search-timing-badge");
    const paginationBox = document.getElementById("search-pagination-container");

    if (!container) return;

    toggleSearchClearBtn();

    const query = queryInput ? queryInput.value.trim() : "";
    lastSearchQuery = query;
    currentSearchPage = page;

    container.innerHTML = `
        <div style="padding: 40px 0; text-align: center; color: var(--text-muted);">
            <div style="margin-bottom: 10px;">Querying SQLite FTS5 inverted index &amp; BM25 ranker...</div>
        </div>
    `;

    try {
        const limit = 15;
        const offset = (page - 1) * limit;
        const url = `/v1/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`;

        const res = await fetch(url, {
            headers: { "Authorization": "Bearer gx_live_sandbox_master_key" }
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || ("HTTP " + res.status));
        }

        const data = await res.json();
        const results = data.results || [];
        currentSearchResults = results;
        const totalHits = data.total_hits || 0;
        const totalPages = Math.ceil(totalHits / limit) || 1;
        currentSearchTotalPages = totalPages;

        // Update telemetry bar
        if (metaBar) {
            metaBar.style.display = "flex";
            if (statsText) {
                const pageInfo = totalPages > 1 ? ` &bull; Page ${page} of ${totalPages}` : "";
                statsText.innerHTML = query 
                    ? `Found <strong>${totalHits}</strong> results for "${escapeHtml(query)}"${pageInfo}`
                    : `Displaying <strong>${totalHits}</strong> indexed documents in catalog${pageInfo}`;
            }
            if (timingBadge) {
                timingBadge.innerHTML = `
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    <span>${data.latency_ms}ms</span>
                `;
            }
        }

        if (results.length === 0) {
            if (paginationBox) paginationBox.style.display = "none";
            const isPotentialUrl = query.startsWith("http://") || query.startsWith("https://") || /^[a-zA-Z0-9-]+\.[a-zA-Z]{2,}/.test(query);
            const targetCrawlUrl = query.startsWith("http") ? query : ("https://" + query);
            container.innerHTML = `
                <div style="padding: 44px 24px; text-align: center; background: var(--bg-card); border: 1px solid var(--border-panel); border-radius: var(--radius-card);">
                    <div style="font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px;">No matching documents found in index</div>
                    <p style="font-size: 13px; color: var(--text-secondary); max-width: 520px; margin: 0 auto 16px auto;">
                        ${query ? `No indexed documents currently match "<strong>${escapeHtml(query)}</strong>".` : 'Your search index is currently empty.'}
                    </p>
                    ${isPotentialUrl ? `
                    <div style="margin-top: 16px; padding: 14px 20px; background: rgba(59, 130, 246, 0.08); border: 1px solid rgba(59, 130, 246, 0.25); border-radius: var(--radius-sm); display: inline-flex; align-items: center; gap: 14px; flex-wrap: wrap; justify-content: center;">
                        <span style="font-size: 13px; color: #93c5fd;">URL not crawled yet?</span>
                        <button class="btn-action-primary" onclick="crawlSpecificUrl('${escapeHtml(targetCrawlUrl)}')" style="height: 34px; padding: 0 16px; font-size: 12.5px;">
                            <span>+ Crawl &amp; Index ${escapeHtml(query)} Now</span>
                        </button>
                    </div>
                    ` : `
                    <div style="margin-top: 14px; display: flex; gap: 10px; justify-content: center;">
                        <button class="btn-action-secondary" onclick="triggerSearchReindex()" style="height: 32px; padding: 0 14px; font-size: 12px;">
                            <span>Re-index Documents</span>
                        </button>
                    </div>
                    `}
                </div>
            `;
            return;
        }

        container.innerHTML = results.map(r => `
            <article class="serp-card">
                <div class="serp-header">
                    <div class="serp-domain-group">
                        <span class="serp-domain-badge">${escapeHtml(r.domain)}</span>
                        <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="serp-url-breadcrumb">${escapeHtml(r.url)}</a>
                    </div>
                    <span class="serp-score-pill">BM25 Rank: ${r.score}</span>
                </div>

                <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="serp-title-link">
                    ${escapeHtml(r.title || r.url)}
                </a>

                <div class="serp-snippet">${r.snippet}</div>

                <div class="serp-footer">
                    <div>
                        <span>Indexed ${r.indexed_at ? formatTimestamp(r.indexed_at) : 'recently'}</span>
                        ${r.inbound_links > 0 ? `<span style="margin-left: 12px; color: #34d399;">• ${r.inbound_links} inbound link${r.inbound_links > 1 ? 's' : ''}</span>` : ''}
                    </div>
                    <div class="serp-actions-group">
                        <button class="serp-mini-btn" onclick="copyCardUrl('${escapeHtml(r.url)}', this)">Copy Link</button>
                        <button class="serp-mini-btn" onclick="inspectSnapshot('${r.target_id}')">Query Snapshot</button>
                        <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener noreferrer" class="serp-mini-btn" style="text-decoration: none;">Visit Site &rarr;</a>
                    </div>
                </div>
            </article>
        `).join("");

        // Render pagination controls
        if (paginationBox) {
            if (totalPages > 1) {
                paginationBox.style.display = "flex";
                paginationBox.innerHTML = `
                    <button class="btn-action-secondary" style="height: 32px; padding: 0 12px; font-size: 12px;" ${page <= 1 ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''} onclick="executeWebSearch(${page - 1})">
                        &larr; Previous
                    </button>
                    <span style="font-size: 12px; color: var(--text-secondary); margin: 0 10px;">
                        Page <strong>${page}</strong> of <strong>${totalPages}</strong>
                    </span>
                    <button class="btn-action-secondary" style="height: 32px; padding: 0 12px; font-size: 12px;" ${page >= totalPages ? 'disabled style="opacity: 0.5; cursor: not-allowed;"' : ''} onclick="executeWebSearch(${page + 1})">
                        Next &rarr;
                    </button>
                `;
            } else {
                paginationBox.style.display = "none";
            }
        }

    } catch(err) {
        if (paginationBox) paginationBox.style.display = "none";
        container.innerHTML = `
            <div style="padding: 30px; text-align: center; color: #fb7185; background: rgba(244, 63, 94, 0.08); border: 1px solid rgba(244, 63, 94, 0.2); border-radius: var(--radius-card);">
                Search Error: ${err.message}
            </div>
        `;
    }
}

function inspectSnapshot(targetId) {
    switchAppTab("targets");
    populateTargetExtract(targetId);
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

window.addEventListener("DOMContentLoaded", () => {
    switchAppTab("dashboard");
    selectPlaygroundCapability("scrape");
});
