const state = {
    apiBase: "/api",
    busy: false,
    messages: [],
    hierarchy: null,
    lastAnswer: "",
    clinicalPanel: null,
    activeClinicalTab: "evidence",
};

const dom = {
    statusPill: document.getElementById("status-pill"),
    modelLabel: document.getElementById("model-label"),
    prompt: document.getElementById("doctor-prompt"),
    send: document.getElementById("send-prompt"),
    clear: document.getElementById("clear-chat"),
    copyLast: document.getElementById("copy-last-answer"),
    messageList: document.getElementById("message-list"),
    runState: document.getElementById("run-state"),
    agentMap: document.getElementById("agent-map"),
    traceList: document.getElementById("trace-list"),
    patientChip: document.getElementById("patient-chip"),
    demoMetrics: document.getElementById("demo-metrics"),
    impactStrip: document.getElementById("impact-strip"),
    dataQualityCard: document.getElementById("data-quality-card"),
    tabButtons: document.querySelectorAll("[data-tab]"),
    tabPanes: document.querySelectorAll("[data-pane]"),
    evidenceList: document.getElementById("evidence-list"),
    riskCards: document.getElementById("risk-cards"),
    timelineList: document.getElementById("timeline-list"),
    reportPreview: document.getElementById("report-preview"),
    downloadMd: document.getElementById("download-md"),
    downloadPdf: document.getElementById("download-pdf"),
};

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function renderMarkdown(text) {
    const lines = String(text || "").split(/\r?\n/);
    const out = [];
    let inList = false;
    let inCode = false;
    let codeLines = [];

    const closeList = () => {
        if (inList) {
            out.push("</ul>");
            inList = false;
        }
    };

    for (const rawLine of lines) {
        const line = rawLine.trimEnd();
        if (line.trim().startsWith("```")) {
            if (inCode) {
                out.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
                codeLines = [];
                inCode = false;
            } else {
                closeList();
                inCode = true;
            }
            continue;
        }

        if (inCode) {
            codeLines.push(line);
            continue;
        }

        if (!line.trim()) {
            closeList();
            continue;
        }

        const heading = line.match(/^(#{1,3})\s+(.+)$/);
        if (heading) {
            closeList();
            const level = Math.min(3, heading[1].length);
            out.push(`<h${level}>${escapeHtml(heading[2])}</h${level}>`);
            continue;
        }

        const bullet = line.match(/^[-*]\s+(.+)$/);
        if (bullet) {
            if (!inList) {
                out.push("<ul>");
                inList = true;
            }
            out.push(`<li>${formatInline(bullet[1])}</li>`);
            continue;
        }

        closeList();
        out.push(`<p>${formatInline(line)}</p>`);
    }

    closeList();
    if (inCode) {
        out.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    }
    return out.join("");
}

function formatInline(text) {
    return escapeHtml(text)
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/`([^`]+)`/g, "<code>$1</code>");
}

async function api(path, options = {}) {
    const response = await fetch(`${state.apiBase}${path}`, {
        headers: { "Content-Type": "application/json", ...(options.headers || {}) },
        ...options,
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
        const detail = payload.detail || payload.message || `HTTP ${response.status}`;
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return payload;
}

function setRunState(label, mode = "idle") {
    dom.runState.textContent = label;
    dom.runState.className = `run-state ${mode}`;
}

function addMessage(role, content) {
    state.messages.push({ role, content });
    const item = document.createElement("article");
    item.className = `message ${role}`;
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = role === "user" ? "Doktor" : role === "error" ? "Sistem" : "DataMedX";
    const body = document.createElement("div");
    body.className = "message-body";
    body.innerHTML = role === "assistant" ? renderMarkdown(content) : escapeHtml(content);
    item.append(meta, body);
    dom.messageList.appendChild(item);
    dom.messageList.scrollTop = dom.messageList.scrollHeight;
}

function resetConversation() {
    state.messages = [];
    state.lastAnswer = "";
    state.clinicalPanel = null;
    dom.messageList.innerHTML = "";
    addMessage("assistant", "Direkt klinik isteğini yaz. Hasta ID, tanı, ilaç, lab, metastaz veya kohort sorgusunu aynı prompt içinde kullanabilirsin.");
    dom.traceList.innerHTML = '<div class="trace-empty">Henüz çalışma yok.</div>';
    dom.copyLast.disabled = true;
    renderClinicalPanel();
    activateClinicalTab("evidence");
    setRunState("Hazır", "idle");
}

function renderStatus(system) {
    const online = system?.status === "Online";
    dom.statusPill.textContent = online ? "Online" : "Offline";
    dom.statusPill.className = `status-pill ${online ? "online" : "offline"}`;
    dom.modelLabel.textContent = system?.model ? `Base: ${system.model}` : "Model bekleniyor";
}

function renderAgentMap(hierarchy) {
    state.hierarchy = hierarchy;
    const agents = hierarchy?.submodels || [];
    dom.agentMap.innerHTML = "";
    if (!agents.length) {
        dom.agentMap.innerHTML = '<div class="trace-empty">Agent listesi yüklenemedi.</div>';
        return;
    }
    for (const agent of agents) {
        const item = document.createElement("div");
        item.className = "agent-item";
        const text = document.createElement("div");
        const name = document.createElement("strong");
        name.textContent = agent.name;
        const meta = document.createElement("span");
        meta.textContent = `${agent.model || "model yok"} • ${agent.tool_count ?? 0} tool`;
        text.append(name, meta);
        const badge = document.createElement("div");
        badge.className = "agent-badge";
        badge.title = agent.active ? "Aktif" : "Pasif";
        if (!agent.active) {
            badge.style.background = "#cbd5e1";
        }
        item.append(text, badge);
        dom.agentMap.appendChild(item);
    }
}

function renderTrace(payload) {
    const traces = [];
    for (const text of payload.direct_texts || []) {
        traces.push({ title: "Adım", text });
    }
    const logs = (payload.logs || []).slice(-5);
    for (const log of logs) {
        traces.push({ title: log.type || "log", text: log.message || "" });
    }
    dom.traceList.innerHTML = "";
    if (!traces.length) {
        dom.traceList.innerHTML = '<div class="trace-empty">Bu çalışmada iz kaydı yok.</div>';
        return;
    }
    for (const trace of traces.slice(-8)) {
        const item = document.createElement("div");
        item.className = "trace-item";
        item.innerHTML = `<strong>${escapeHtml(trace.title)}</strong>${escapeHtml(trace.text)}`;
        dom.traceList.appendChild(item);
    }
}

function activateClinicalTab(tab) {
    state.activeClinicalTab = tab;
    dom.tabButtons.forEach((button) => {
        const active = button.dataset.tab === tab;
        button.classList.toggle("active", active);
        button.setAttribute("aria-selected", active ? "true" : "false");
    });
    dom.tabPanes.forEach((pane) => {
        pane.classList.toggle("active", pane.dataset.pane === tab);
    });
}

function renderClinicalPanel(panel = {}) {
    const status = panel?.status || "empty";
    state.clinicalPanel = panel || {};

    if (status === "ready") {
        const summary = panel.risk_summary || {};
        dom.patientChip.textContent = `${panel.patient_id || "Hasta"} • ${summary.red || 0} kırmızı / ${summary.yellow || 0} sarı / ${summary.green || 0} yeşil`;
        dom.patientChip.className = "patient-chip ready";
    } else {
        dom.patientChip.textContent = panel?.message || "Hasta ID bekleniyor";
        dom.patientChip.className = status === "error" || status === "not_found" ? "patient-chip error" : "patient-chip";
    }

    renderEvidence(panel?.evidence || []);
    renderRiskCards(panel?.risk_cards || []);
    renderTimeline(panel?.timeline || []);
    renderReport(panel?.report_markdown || "");
    renderDemoMetrics(panel?.demo_metrics || []);
    renderImpact(panel?.impact || {});
    renderDataQuality(panel?.data_quality || {});
}

function renderDemoMetrics(metrics) {
    const fallback = [
        { label: "Kanıt", value: "0", note: "kaynak/snippet" },
        { label: "Risk", value: "0", note: "klinik uyarı" },
        { label: "Timeline", value: "0", note: "olay" },
        { label: "Rapor", value: "-", note: "tek tık" },
    ];
    const items = metrics.length ? metrics : fallback;
    dom.demoMetrics.innerHTML = "";
    for (const item of items.slice(0, 4)) {
        const card = document.createElement("div");
        card.className = "metric-card";
        card.innerHTML = `
            <strong>${escapeHtml(item.value || "0")}</strong>
            <span>${escapeHtml(item.label || "Metrik")}</span>
            <small>${escapeHtml(item.note || "")}</small>
        `;
        dom.demoMetrics.appendChild(card);
    }
}

function renderImpact(impact) {
    const before = impact.before || "Manuel dosya okuma: 10-15 dk";
    const after = impact.after || "DataMedX: kanıtlı özet, risk ve rapor tek akışta";
    dom.impactStrip.innerHTML = `
        <div>
            <span>Önce</span>
            <strong>${escapeHtml(before)}</strong>
        </div>
        <div>
            <span>Sonra</span>
            <strong>${escapeHtml(after)}</strong>
        </div>
    `;
}

function renderDataQuality(quality) {
    const status = quality.status || "empty";
    const items = quality.items || [];
    dom.dataQualityCard.className = `data-quality-card ${status}`;
    const itemHtml = items.length
        ? `<div class="quality-list">${items.map((item) => `
            <div class="quality-item">
                <div>
                    <strong>${escapeHtml(item.metric || "Lab")}</strong>
                    <span>${escapeHtml(item.value || "")}</span>
                </div>
                <p>${escapeHtml(item.reason || "Doğrulama önerilir.")}</p>
                <small>${escapeHtml(item.source || "")}</small>
            </div>
        `).join("")}</div>`
        : "";
    dom.dataQualityCard.innerHTML = `
        <div class="quality-header">
            <span>Veri Kalitesi</span>
            <strong>${escapeHtml(quality.title || "Hasta kaydı bekleniyor")}</strong>
        </div>
        <p>${escapeHtml(quality.summary || "Hasta kaydı doğrulanınca uç değer ve tutarsızlık kontrolü yapılır.")}</p>
        ${itemHtml}
    `;
}

function renderEvidence(items) {
    dom.evidenceList.innerHTML = "";
    if (!items.length) {
        dom.evidenceList.innerHTML = '<div class="trace-empty">Hasta kaydı doğrulanınca kaynak/snippet satırları burada görünür.</div>';
        return;
    }

    for (const item of items) {
        const row = document.createElement("div");
        row.className = `evidence-item ${item.tone || "info"}`;
        row.innerHTML = `
            <div class="evidence-title">${escapeHtml(item.title || "Kanıt")}</div>
            <div class="evidence-source">${escapeHtml(item.source || "kaynak yok")}</div>
            <div class="evidence-snippet">${escapeHtml(item.snippet || "")}</div>
        `;
        dom.evidenceList.appendChild(row);
    }
}

function renderRiskCards(items) {
    dom.riskCards.innerHTML = "";
    if (!items.length) {
        dom.riskCards.innerHTML = '<div class="trace-empty">Risk sinyali için hasta kaydı bekleniyor.</div>';
        return;
    }

    for (const item of items) {
        const card = document.createElement("div");
        card.className = `risk-card ${item.tone || "green"}`;
        card.innerHTML = `
            <div class="risk-card-top">
                <span>${escapeHtml(item.label || item.level || "Bilgi")}</span>
                <strong>${escapeHtml(item.signal || "Risk sinyali")}</strong>
            </div>
            <p>${escapeHtml(item.evidence || "Kanıt yok")}</p>
        `;
        dom.riskCards.appendChild(card);
    }
}

function renderTimeline(items) {
    dom.timelineList.innerHTML = "";
    if (!items.length) {
        dom.timelineList.innerHTML = '<div class="trace-empty">Hasta yolculuğu için timeline verisi bekleniyor.</div>';
        return;
    }

    for (const item of items) {
        const row = document.createElement("div");
        row.className = "timeline-item";
        row.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
                <div class="timeline-date">${escapeHtml(item.date || "Tarih yok")}</div>
                <strong>${escapeHtml(item.title || "Olay")}</strong>
                <span>${escapeHtml(item.category || "kategori")} • ${escapeHtml(item.source || "kaynak")}</span>
            </div>
        `;
        dom.timelineList.appendChild(row);
    }
}

function renderReport(markdown) {
    dom.reportPreview.textContent = markdown || "Rapor için hasta ID içeren bir prompt gönder.";
    dom.downloadMd.disabled = !markdown;
    dom.downloadPdf.disabled = !markdown;
}

function reportFilename(extension) {
    const rawId = state.clinicalPanel?.patient_id || "hasta";
    const safeId = String(rawId).replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 48) || "hasta";
    const date = new Date().toISOString().slice(0, 10);
    return `datamedx-${safeId}-${date}.${extension}`;
}

function downloadMarkdownReport() {
    const markdown = state.clinicalPanel?.report_markdown || "";
    if (!markdown) return;
    const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = reportFilename("md");
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

function printPdfReport() {
    const markdown = state.clinicalPanel?.report_markdown || "";
    if (!markdown) return;
    const printWindow = window.open("", "_blank", "width=900,height=1100");
    if (!printWindow) {
        addMessage("error", "PDF penceresi açılamadı. Tarayıcı popup iznini kontrol et.");
        return;
    }
    printWindow.document.write(`
        <!DOCTYPE html>
        <html lang="tr">
        <head>
            <meta charset="UTF-8">
            <title>${escapeHtml(reportFilename("pdf"))}</title>
            <style>
                body { font-family: Arial, sans-serif; color: #10211f; margin: 32px; line-height: 1.5; }
                h1, h2, h3 { color: #0f766e; margin: 18px 0 8px; }
                ul { padding-left: 20px; }
                li { margin: 5px 0; }
                code, pre { background: #eef3f1; border: 1px solid #d8e2df; border-radius: 6px; padding: 2px 5px; }
                pre { padding: 10px; white-space: pre-wrap; }
                @page { margin: 18mm; }
            </style>
        </head>
        <body>${renderMarkdown(markdown)}</body>
        </html>
    `);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 250);
}

async function loadBootstrap() {
    try {
        const [system, hierarchy] = await Promise.all([
            api("/system/status"),
            api("/hierarchy"),
        ]);
        renderStatus(system);
        renderAgentMap(hierarchy);
    } catch (error) {
        renderStatus({ status: "Offline" });
        dom.agentMap.innerHTML = `<div class="trace-empty">${escapeHtml(error.message)}</div>`;
    }
}

async function sendPrompt() {
    if (state.busy) return;
    const prompt = dom.prompt.value.trim();
    if (!prompt) {
        addMessage("error", "Doktor prompt'u boş olamaz.");
        return;
    }

    state.busy = true;
    dom.send.disabled = true;
    setRunState("Agentlar çalışıyor", "running");
    addMessage("user", prompt);

    try {
        const payload = await api("/doctor/chat", {
            method: "POST",
            body: JSON.stringify({
                patient_id: "",
                prompt,
                output_style: "doctor_panel",
            }),
        });
        renderStatus(payload.system);
        renderAgentMap(payload.hierarchy);
        renderTrace(payload);
        renderClinicalPanel(payload.clinical_panel || {});
        state.lastAnswer = payload.answer || "Yanıt üretilemedi.";
        dom.copyLast.disabled = !state.lastAnswer;
        addMessage("assistant", state.lastAnswer);
        setRunState("Tamamlandı", "idle");
    } catch (error) {
        addMessage("error", error.message);
        setRunState("Hata", "error");
    } finally {
        state.busy = false;
        dom.send.disabled = false;
    }
}

function bindEvents() {
    dom.send.addEventListener("click", sendPrompt);
    dom.clear.addEventListener("click", resetConversation);
    dom.tabButtons.forEach((button) => {
        button.addEventListener("click", () => activateClinicalTab(button.dataset.tab));
    });
    dom.downloadMd.addEventListener("click", downloadMarkdownReport);
    dom.downloadPdf.addEventListener("click", printPdfReport);
    dom.copyLast.addEventListener("click", async () => {
        if (!state.lastAnswer) return;
        try {
            await navigator.clipboard.writeText(state.lastAnswer);
            setRunState("Kopyalandı", "idle");
        } catch (error) {
            addMessage("error", `Cevap kopyalanamadı: ${error.message}`);
        }
    });
    dom.prompt.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            event.preventDefault();
            sendPrompt();
        }
    });
}

bindEvents();
renderClinicalPanel();
loadBootstrap();
setInterval(loadBootstrap, 15000);
