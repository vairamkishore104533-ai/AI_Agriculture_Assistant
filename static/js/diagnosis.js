var currentCrop = "";
var currentSymptoms = [];
var currentResult = null;

function initCropSelect() {
    var sel = document.getElementById("crop-select");
    if (sel) {
        sel.addEventListener("change", function () {
            onCropSelected(this.value);
        });
    }
}

function onCropSelected(crop) {
    if (!crop) return;
    currentCrop = crop;
    currentSymptoms = [];

    var s1i = document.getElementById("step-1-indicator");
    var s2i = document.getElementById("step-2-indicator");
    var s1 = document.getElementById("step-1");
    var s3 = document.getElementById("step-3");
    var dr = document.getElementById("diag-result");
    if (s1i) { s1i.classList.add("completed"); s1i.classList.remove("active"); }
    if (s2i) { s2i.classList.add("active"); }
    if (s1) { s1.style.display = "none"; }
    if (s3) { s3.style.display = "none"; }
    if (dr) { dr.style.display = "none"; }

    loadSymptoms(crop);
}

function loadSymptoms(crop) {
    var grid = document.getElementById("symptom-grid");
    var step2 = document.getElementById("step-2");
    if (!grid || !step2) return;
    grid.innerHTML = '<div class="diag-loading">Loading symptoms...</div>';
    step2.style.display = "block";

    fetch("/api/diagnosis/symptoms/" + encodeURIComponent(crop))
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (!res.success || !res.symptoms || res.symptoms.length === 0) {
                grid.innerHTML = '<div class="diag-empty">No symptoms available for this crop.</div>';
                return;
            }
            var html = "";
            for (var i = 0; i < res.symptoms.length; i++) {
                var s = res.symptoms[i];
                html += '<div class="diag-symptom-card" data-symptom="' + s.replace(/'/g, "&#39;") + '"><span class="diag-symptom-check">☐</span><span class="diag-symptom-text">' + s + '</span></div>';
            }
            grid.innerHTML = html;
            var cards = grid.querySelectorAll(".diag-symptom-card");
            for (var i = 0; i < cards.length; i++) {
                cards[i].addEventListener("click", function () {
                    toggleSymptom(this);
                });
            }
            var sc = document.getElementById("selected-count");
            if (sc) sc.textContent = "0 selected";
        })
        .catch(function () {
            grid.innerHTML = '<div class="diag-empty">Failed to load symptoms. Please try again.</div>';
        });
}

function toggleSymptom(el) {
    var symptom = el.getAttribute("data-symptom");
    if (!symptom) return;
    var idx = currentSymptoms.indexOf(symptom);
    if (idx >= 0) {
        currentSymptoms.splice(idx, 1);
        el.classList.remove("selected");
        var check = el.querySelector(".diag-symptom-check");
        if (check) check.textContent = "☐";
    } else {
        currentSymptoms.push(symptom);
        el.classList.add("selected");
        var check = el.querySelector(".diag-symptom-check");
        if (check) check.textContent = "☑";
    }
    var count = currentSymptoms.length;
    var sc = document.getElementById("selected-count");
    if (sc) sc.textContent = count + " selected";
    var s3 = document.getElementById("step-3");
    if (s3) s3.style.display = count > 0 ? "block" : "none";
}

function filterSymptoms(q) {
    var cards = document.querySelectorAll(".diag-symptom-card");
    var lower = q.toLowerCase();
    for (var i = 0; i < cards.length; i++) {
        var textEl = cards[i].querySelector(".diag-symptom-text");
        var text = textEl ? textEl.textContent.toLowerCase() : "";
        cards[i].style.display = text.indexOf(lower) >= 0 ? "flex" : "none";
    }
}

function selectAllSymptoms() {
    var cards = document.querySelectorAll(".diag-symptom-card");
    currentSymptoms = [];
    for (var i = 0; i < cards.length; i++) {
        var symptom = cards[i].getAttribute("data-symptom");
        if (symptom) {
            currentSymptoms.push(symptom);
            cards[i].classList.add("selected");
            var check = cards[i].querySelector(".diag-symptom-check");
            if (check) check.textContent = "☑";
        }
    }
    var sc = document.getElementById("selected-count");
    if (sc) sc.textContent = currentSymptoms.length + " selected";
    var s3 = document.getElementById("step-3");
    if (s3) s3.style.display = currentSymptoms.length > 0 ? "block" : "none";
}

function clearSymptoms() {
    var cards = document.querySelectorAll(".diag-symptom-card");
    currentSymptoms = [];
    for (var i = 0; i < cards.length; i++) {
        cards[i].classList.remove("selected");
        var check = cards[i].querySelector(".diag-symptom-check");
        if (check) check.textContent = "☐";
    }
    var sc = document.getElementById("selected-count");
    if (sc) sc.textContent = "0 selected";
    var s3 = document.getElementById("step-3");
    if (s3) s3.style.display = "none";
}

function analyzeDiagnosis() {
    if (!currentCrop || currentSymptoms.length === 0) {
        console.warn("analyzeDiagnosis: skipped — no crop or symptoms", { crop: currentCrop, symCount: currentSymptoms.length });
        showDiagToast("Please select a crop and symptoms first.", "error");
        return;
    }

    console.log("[Diagnosis] Sending request...", {
        crop: currentCrop,
        symptoms: currentSymptoms,
        symptomCount: currentSymptoms.length,
    });

    var btn = document.getElementById("diagnose-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Analyzing..."; }
    var dr = document.getElementById("diag-result");
    if (dr) dr.style.display = "none";

    fetch("/api/diagnosis/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            crop: currentCrop,
            symptoms: currentSymptoms,
        }),
    })
    .then(function (r) {
        if (!r.ok) {
            return r.text().then(function (text) {
                console.error("[Diagnosis] HTTP " + r.status + " response:", text);
                try {
                    var j = JSON.parse(text);
                    showDiagToast(j.error || j.message || "Server error (" + r.status + ")", "error");
                } catch (e) {
                    showDiagToast("Server error (" + r.status + "): " + text.substring(0, 200), "error");
                }
                hideLoading();
          if (btn) { btn.disabled = false; btn.textContent = "\uD83D\uDD2C Diagnose Crop"; }
                return null;
            });
        }
        return r.json();
    })
    .then(function (res) {
        hideLoading();
          if (btn) { btn.disabled = false; btn.textContent = "\uD83D\uDD2C Diagnose Crop"; }
        if (!res) return;

        console.log("[Diagnosis] Response received:", res);

        if (!res.success) {
            var errMsg = res.error || res.message || "Failed to analyze";
            console.error("[Diagnosis] Server returned error:", errMsg);
            showDiagToast(errMsg, "error");
            return;
        }

        if (res.diagnosis) {
            window.currentDiagnosisRaw = res.diagnosis;
        } else {
            window.currentDiagnosisRaw = null;
        }

        if (res.result === null || res.result === undefined) {
            if (res.diagnosis) {
                console.log("[Diagnosis] No structured result, using raw diagnosis text");
                currentResult = null;
                displayRawDiagnosis(res.diagnosis);
                return;
            }
            showDiagToast("No diagnosis returned from AI service.", "error");
            return;
        }

        currentResult = res.result;
        displayResult(res.result);
        console.log("[Diagnosis] Diagnosis rendered successfully");
    })
    .catch(function (err) {
        console.error("[Diagnosis] Network/fetch error:", err);
        hideLoading();
          if (btn) { btn.disabled = false; btn.textContent = "\uD83D\uDD2C Diagnose Crop"; }
        showDiagToast("Network error: " + (err.message || "Please try again."), "error");
    });
}

function displayResult(r) {
    var setText = function (id, val) {
        var el = document.getElementById(id);
        if (el) el.textContent = val || "\u2014";
    };
    setText("result-disease", r.disease);
    setText("result-confidence", r.confidence);
    setText("result-severity", r.severity);
    setText("result-description", r.description);
    setText("result-causes", r.causes);
    setText("result-spread", r.spread);
    setText("result-immediate", r.treatment_immediate);
    setText("result-organic", r.treatment_organic);
    setText("result-chemical", r.treatment_chemical);
    setText("result-prevention", r.prevention);
    setText("result-related", r.related_diseases);
    setText("result-recovery", r.recovery_time);
    setText("result-success", r.success_rate);

    var severity = (r.severity || "").toLowerCase();
    var badge = document.getElementById("severity-badge");
    if (badge) {
        badge.textContent = r.severity || "Medium";
        badge.className = "diag-disease-badge";
        if (severity === "low") badge.classList.add("severity-low");
        else if (severity === "medium") badge.classList.add("severity-medium");
        else if (severity === "high") badge.classList.add("severity-high");
        else if (severity === "critical") badge.classList.add("severity-critical");
    }

    var emergencyCard = document.getElementById("emergency-card");
    var emergencyText = document.getElementById("result-emergency");
    if (emergencyCard && emergencyText) {
        if (r.emergency && (severity === "high" || severity === "critical")) {
            emergencyText.textContent = r.emergency;
            emergencyCard.style.display = "block";
        } else {
            emergencyCard.style.display = "none";
        }
    }

    var rawSection = document.getElementById("result-diagnosis-raw-section");
    var rawContent = document.getElementById("result-diagnosis-raw");
    if (rawSection && rawContent && window.currentDiagnosisRaw) {
        rawContent.innerHTML = renderMarkdown(window.currentDiagnosisRaw);
        rawSection.style.display = "block";
    } else if (rawSection) {
        rawSection.style.display = "none";
    }

    var s2i = document.getElementById("step-2-indicator");
    var s3i = document.getElementById("step-3-indicator");
    if (s2i) { s2i.classList.add("completed"); s2i.classList.remove("active"); }
    if (s3i) { s3i.classList.add("active"); }

    var dr = document.getElementById("diag-result");
    if (dr) {
        dr.style.display = "block";
        dr.scrollIntoView({ behavior: "smooth", block: "start" });
    }
}

function saveDiagnosis() {
    if (!currentResult) {
        showDiagToast("No diagnosis to save.", "error");
        return;
    }

    var payload = {
        crop: currentCrop,
        symptoms: currentSymptoms,
        disease: currentResult.disease,
        severity: currentResult.severity,
        confidence: currentResult.confidence,
        description: currentResult.description,
        causes: currentResult.causes,
        spread: currentResult.spread,
        treatment_immediate: currentResult.treatment_immediate,
        treatment_organic: currentResult.treatment_organic,
        treatment_chemical: currentResult.treatment_chemical,
        prevention: currentResult.prevention,
        emergency: currentResult.emergency,
        related_diseases: currentResult.related_diseases,
        recovery_time: currentResult.recovery_time,
        success_rate: currentResult.success_rate,
    };

    if (window.currentDiagnosisRaw) {
        payload.diagnosis = window.currentDiagnosisRaw;
    }

    console.log("[Diagnosis] Saving...", payload);

    fetch("/api/diagnosis/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) {
        if (!r.ok) {
            return r.text().then(function (text) { throw new Error("HTTP " + r.status + ": " + text.substring(0, 200)); });
        }
        return r.json();
    })
    .then(function (res) {
        if (res.success) {
            showDiagToast("Diagnosis saved!", "success");
            loadHistory();
            updateStats();
        } else {
            showDiagToast(res.message || "Failed to save", "error");
        }
    })
    .catch(function (err) {
        console.error("[Diagnosis] Save error:", err);
        showDiagToast("Save failed: " + err.message, "error");
    });
}

function loadHistory() {
    var searchInput = document.getElementById("history-search");
    var q = searchInput ? searchInput.value.trim() : "";
    var url = "/api/diagnosis/history" + (q ? "?search=" + encodeURIComponent(q) : "");
    fetch(url)
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var list = document.getElementById("history-list");
            if (!list) return;
            if (!res.success || !res.diagnoses || res.diagnoses.length === 0) {
                list.innerHTML = '<div class="diag-empty">No previous diagnoses.</div>';
                return;
            }
            var html = "";
            for (var i = 0; i < res.diagnoses.length; i++) {
                var d = res.diagnoses[i];
                var sev = (d.severity || "medium").toLowerCase();
                var dateStr = d.created_at ? d.created_at.substring(0, 10) : "";
                html += '<div class="diag-history-item" data-id="' + d.id + '">';
                html += '<div class="diag-history-left">';
                html += '<span class="diag-history-crop">' + d.crop + "</span>";
                html += '<span class="diag-history-disease">' + d.disease + "</span>";
                html += '<span class="diag-history-date">' + dateStr + "</span></div>";
                html += '<div class="diag-history-right">';
                html += '<span class="severity-tag severity-' + sev + '">' + d.severity + "</span>";
                html += '<button class="diag-btn-icon" title="View" onclick="viewHistory(\'' + d.id + '\')">\uD83D\uDC41</button>';
                html += '<button class="diag-btn-icon" title="Export" onclick="exportDiagnosisById(\'' + d.id + '\', \'txt\')">\uD83D\uDCC4</button>';
                html += '<button class="diag-btn-icon" title="Delete" onclick="deleteDiagnosis(\'' + d.id + '\')">\uD83D\uDDD1</button>';
                html += "</div></div>";
            }
            list.innerHTML = html;
        });
}

function viewHistory(id) {
    fetch("/api/diagnosis/history")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            var found = null;
            if (res.diagnoses) {
                for (var i = 0; i < res.diagnoses.length; i++) {
                    if (res.diagnoses[i].id === id) { found = res.diagnoses[i]; break; }
                }
            }
            if (!found) { showDiagToast("Diagnosis not found", "error"); return; }
            var body = document.getElementById("view-modal-body");
            if (!body) return;
            var sev = (found.severity || "medium").toLowerCase();
            var html =
                '<div class="view-field"><span class="view-label">Crop</span><span class="view-val">' + found.crop + "</span></div>" +
                '<div class="view-field"><span class="view-label">Disease</span><span class="view-val">' + (found.disease || "\u2014") + "</span></div>" +
                '<div class="view-field"><span class="view-label">Severity</span><span class="view-val"><span class="severity-tag severity-' + sev + '">' + (found.severity || "\u2014") + "</span></span></div>" +
                '<div class="view-field"><span class="view-label">Confidence</span><span class="view-val">' + (found.confidence || "\u2014") + "</span></div>" +
                '<div class="view-field-full"><span class="view-label">Symptoms</span><span class="view-val">' + (found.symptoms ? found.symptoms.join(", ") : "\u2014") + "</span></div>" +
                '<div class="view-field-full"><span class="view-label">Causes</span><span class="view-val">' + (found.causes || "\u2014") + "</span></div>" +
                '<div class="view-field-full"><span class="view-label">Treatment</span><span class="view-val">' + (found.treatment_immediate || "\u2014") + "</span></div>" +
                '<div class="view-field-full"><span class="view-label">Prevention</span><span class="view-val">' + (found.prevention || "\u2014") + "</span></div>" +
                '<div class="view-field"><span class="view-label">Date</span><span class="view-val">' + (found.created_at ? found.created_at.substring(0, 10) : "") + "</span></div>";
            if (found.diagnosis) {
                html += '<div class="view-field-full" style="margin-top:12px"><span class="view-label">Full Diagnosis</span><div class="diag-markdown" style="font-size:0.85rem;line-height:1.6;margin-top:4px">' + renderMarkdown(found.diagnosis) + '</div></div>';
            }
            body.innerHTML = html;
            var modal = document.getElementById("view-modal");
            if (modal) modal.style.display = "flex";
        });
}

function deleteDiagnosis(id) {
    if (!confirm("Delete this diagnosis?")) return;
    fetch("/api/diagnosis/" + id, { method: "DELETE" })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) {
                showDiagToast("Diagnosis deleted!", "success");
                loadHistory();
                if (res.stats) updateStatsFromServer(res.stats);
            } else {
                showDiagToast(res.message || "Failed to delete", "error");
            }
        });
}

function exportDiagnosis(fmt) {
    if (!currentResult) return;
    var lines = [];
    lines.push("CROP DIAGNOSIS REPORT");
    lines.push("=".repeat(50));
    lines.push("Crop: " + currentCrop);
    lines.push("Symptoms: " + currentSymptoms.join(", "));
    lines.push("");
    lines.push("Disease: " + currentResult.disease);
    lines.push("Confidence: " + currentResult.confidence);
    lines.push("Severity: " + currentResult.severity);
    lines.push("Description: " + currentResult.description);
    lines.push("Causes: " + currentResult.causes);
    lines.push("Spread: " + currentResult.spread);
    lines.push("");
    lines.push("TREATMENT");
    lines.push("-".repeat(50));
    lines.push("Immediate: " + currentResult.treatment_immediate);
    lines.push("Organic: " + currentResult.treatment_organic);
    lines.push("Chemical: " + currentResult.treatment_chemical);
    lines.push("Prevention: " + currentResult.prevention);
    lines.push("");
    lines.push("Recovery Time: " + currentResult.recovery_time);
    lines.push("Success Rate: " + currentResult.success_rate);
    lines.push("Related Diseases: " + currentResult.related_diseases);
    var text = lines.join("\n");

    if (fmt === "pdf") {
        fetch("/api/diagnosis/export/temp", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ crop: currentCrop, symptoms: currentSymptoms, result: currentResult, format: fmt }),
        })
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) downloadFile(res);
            else showDiagToast("Export failed", "error");
        });
    } else {
        var blob = new Blob([text], { type: "text/plain" });
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url;
        a.download = "diagnosis_" + currentCrop.toLowerCase() + ".txt";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showDiagToast("Exported!", "success");
    }
}

function exportDiagnosisById(id, fmt) {
    window.location.href = "/api/diagnosis/export/" + id + "?format=" + fmt;
}

function downloadFile(res) {
    var content = res.export;
    var mimeType = res.mime;
    if (res.encoding === "base64") {
        var binary = atob(content);
        var array = new Uint8Array(binary.length);
        for (var i = 0; i < binary.length; i++) { array[i] = binary.charCodeAt(i); }
        content = array;
    }
    var blob = new Blob([content], { type: mimeType });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = res.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showDiagToast("Exported!", "success");
}

function updateStats() {
    fetch("/api/diagnosis/stats")
        .then(function (r) { return r.json(); })
        .then(function (res) {
            if (res.success) updateStatsFromServer(res.stats);
        });
}

function updateStatsFromServer(stats) {
    var setText = function (id, val) {
        var el = document.getElementById(id);
        if (el) el.textContent = val;
    };
    setText("stat-total", stats.total);
    setText("stat-healthy", stats.healthy);
    setText("stat-diseases", stats.diseases_detected);
    setText("stat-critical", stats.critical);
}

function displayRawDiagnosis(diagnosis) {
    var dr = document.getElementById("diag-result");
    if (!dr) return;
    dr.style.display = "block";
    dr.innerHTML = '<div class="diag-result-header glass"><h2>Diagnosis Report</h2><div class="diag-markdown">' + renderMarkdown(diagnosis) + '</div></div><div class="diag-actions-bar glass"><button class="diag-btn diag-btn-primary" onclick="saveDiagnosis()">💾 Save Diagnosis</button><button class="diag-btn diag-btn-secondary" onclick="exportDiagnosis(\'txt\')">📄 Export TXT</button></div>';
    dr.scrollIntoView({ behavior: "smooth", block: "start" });

    var s2i = document.getElementById("step-2-indicator");
    var s3i = document.getElementById("step-3-indicator");
    if (s2i) { s2i.classList.add("completed"); s2i.classList.remove("active"); }
    if (s3i) { s3i.classList.add("active"); }

    console.log("[Diagnosis] Raw diagnosis displayed");
}

function renderMarkdown(text) {
    if (!text) return "";
    var html = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/^- (.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
    html = html.replace(/\n\n/g, "</p><p>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<\/ul><p><ul>/g, "");
    html = html.replace(/<\/p>\n?<li>/g, "<li>");
    html = html.replace(/<\/li>\n?<\/p>/g, "</li>");
    html = html.replace(/<p><ul>/g, "<ul>");
    html = html.replace(/<\/ul><\/p>/g, "</ul>");
    return html;
}

function showDiagToast(msg, type) {
    var toast = document.getElementById("diag-toast");
    if (!toast) return;
    toast.textContent = msg;
    toast.className = "diag-toast " + (type || "");
    toast.style.display = "block";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.style.display = "none"; }, 3000);
}

initCropSelect();


var diagLoadingMessages = [
    t("Analyzing crop data...", "பயிர்களை பகுப்பாய்வு செய்கிறது..."),
    t("Identifying symptoms...", "அறிகுறிகளை சரிபார்க்கிறது..."),
    t("Consulting database...", "தரவுத்தளத்துடன் இணைக்கிறது..."),
    t("Generating diagnosis...", "முடிவுகளை உருவாக்குகிறது...")
];
function showLoading() {
    var overlay = document.getElementById("diag-loading-overlay");
    var text = document.getElementById("diag-loading-text");
    if (!overlay || !text) return;
    overlay.style.display = "flex";
    var msgIdx = 0;
    window.diagLoadingInterval = setInterval(function() {
        msgIdx = (msgIdx + 1) % diagLoadingMessages.length;
        text.textContent = diagLoadingMessages[msgIdx];
    }, 2000);
}
function hideLoading() {
    var overlay = document.getElementById("diag-loading-overlay");
    if (overlay) overlay.style.display = "none";
    if (window.diagLoadingInterval) clearInterval(window.diagLoadingInterval);
}


// --- Live Crops Integration ---
function filterLiveCrops(q) {
    var lower = q.toLowerCase();
    var items = document.querySelectorAll('.diag-live-crop-item');
    var count = 0;
    var list = document.getElementById('live-crop-dropdown-list');
    var backdrop = document.getElementById('floating-crop-picker-backdrop');
    
    // Auto-open if typing
    if (q.length > 0 && list && list.style.display === 'none') {
        openLiveCropDropdown();
    }
    
    items.forEach(function(item) {
        var cropName = item.getAttribute('data-crop');
        if (cropName.indexOf(lower) >= 0) {
            item.style.display = 'block';
            count++;
        } else {
            item.style.display = 'none';
        }
    });
}

function openLiveCropDropdown() {
    var btn = document.getElementById('live-crop-dropdown-btn');
    var list = document.getElementById('live-crop-dropdown-list');
    var backdrop = document.getElementById('floating-crop-picker-backdrop');
    
    if (!btn || !list) return;
    
    if (window.innerWidth <= 768) {
        // Mobile bottom sheet style
        list.style.top = 'auto';
        list.style.bottom = '20px';
        list.style.left = '5%';
        list.style.width = '90%';
        list.style.maxHeight = '50vh';
        if (backdrop) {
            backdrop.style.background = 'rgba(0,0,0,0.4)';
        }
    } else {
        // Desktop floating panel relative to viewport
        var rect = btn.getBoundingClientRect();
        list.style.left = rect.left + 'px';
        list.style.width = rect.width + 'px';
        
        var spaceBelow = window.innerHeight - rect.bottom;
        if (spaceBelow < 250) { // If less than 250px below, open upwards
            list.style.top = 'auto';
            list.style.bottom = (window.innerHeight - rect.top + 4) + 'px';
        } else {
            list.style.top = (rect.bottom + 4) + 'px';
            list.style.bottom = 'auto';
        }
        if (backdrop) {
            backdrop.style.background = 'transparent';
        }
    }
    
    list.style.display = 'block';
    if(backdrop) backdrop.style.display = 'block';
}

function closeLiveCropDropdown() {
    var list = document.getElementById('live-crop-dropdown-list');
    var backdrop = document.getElementById('floating-crop-picker-backdrop');
    if (list) list.style.display = 'none';
    if (backdrop) backdrop.style.display = 'none';
}

function toggleLiveCropDropdown(e) {
    if (e) e.stopPropagation();
    var list = document.getElementById('live-crop-dropdown-list');
    if (list && list.style.display === 'block') {
        closeLiveCropDropdown();
    } else {
        openLiveCropDropdown();
    }
}

function selectLiveCrop(cropName) {
    var btn = document.getElementById('live-crop-dropdown-btn');
    if (btn) btn.innerHTML = '🌱 <strong>' + escapeHtml(cropName) + '</strong> <span>▼</span>';
    
    closeLiveCropDropdown();
    
    // Connect to existing Diagnose Your Crop block
    var cropSelect = document.getElementById('crop-select');
    if (cropSelect) {
        cropSelect.value = cropName;
        cropSelect.dispatchEvent(new Event('change'));
        showDiagToast(cropName + ' selected for diagnosis', 'success');
    }
}

// Window resize handling
window.addEventListener('resize', function() {
    var list = document.getElementById('live-crop-dropdown-list');
    if (list && list.style.display === 'block') {
        openLiveCropDropdown(); // reposition
    }
});


document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeLiveCropDropdown();
    }
});
