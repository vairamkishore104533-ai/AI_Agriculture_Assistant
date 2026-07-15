console.log("fertilizer.js loading...");

var fertState = {
    currentStep: 1,
    season: "",
    crop: "",
    growthStage: "",
    irrigation: "",
    recommendation: null,
    seasonName: "",
    cropName: "",
    growthStageName: "",
    irrigationName: "",
};

function fertInit() {
    console.log("fertInit called");

    document.querySelectorAll(".fert-select-item").forEach(function (el) {
        el.addEventListener("click", function () {
            var parent = this.closest(".fert-select-grid");
            if (!parent) return;
            var name = parent.getAttribute("data-name");
            if (!name) return;
            var value = this.getAttribute("data-value") || "";
            var labelEl = this.querySelector(".fert-select-label");
            var displayName = labelEl ? labelEl.textContent.trim() : value;

            parent.querySelectorAll(".fert-select-item").forEach(function (c) {
                c.classList.remove("selected");
            });
            this.classList.add("selected");

            fertState[name] = value;
            if (name === "season") fertState.seasonName = displayName;
            else if (name === "growthStage") fertState.growthStageName = displayName;
            else if (name === "irrigation") fertState.irrigationName = displayName;

            console.log("selected " + name + ":", value, "(", displayName + ")");
            onFertSelect(name);
        });
    });

    var cropSelect = document.getElementById("fert-crop-select");
    if (cropSelect) {
        cropSelect.addEventListener("change", function () {
            onFertCropSelect(this.value);
        });
    }

    var searchInput = document.getElementById("fert-history-search-input");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            loadFertHistory();
        });
    }

    var seasonFilter = document.getElementById("fert-season-filter");
    if (seasonFilter) {
        seasonFilter.addEventListener("change", function () {
            loadFertHistory();
        });
    }
}

function onFertStepClick(n) {
    console.log("Step clicked:", n);
    if (n === fertState.currentStep) return;

    var firstIncomplete = getFertFirstIncompleteStep();
    if (n > firstIncomplete) {
        var labels = ["", "Season", "Crop", "Growth Stage", "Irrigation", "Generate"];
        showFertToast("Please complete " + labels[firstIncomplete] + " first.", "error");
        return;
    }
    goToFertStep(n);
}

function getFertFirstIncompleteStep() {
    if (!fertState.season) return 1;
    if (!fertState.crop) return 2;
    if (!fertState.growthStage) return 3;
    if (!fertState.irrigation) return 4;
    return 5;
}

function isFertStepCompleted(n) {
    switch (n) {
        case 1: return fertState.season !== "";
        case 2: return fertState.crop !== "";
        case 3: return fertState.growthStage !== "";
        case 4: return fertState.irrigation !== "";
        default: return false;
    }
}

function goToFertStep(n) {
    console.log("goToFertStep:", n);
    fertState.currentStep = n;

    for (var i = 1; i <= 5; i++) {
        var indicator = document.getElementById("fert-step-" + i + "-indicator");
        var panel = document.getElementById("fert-step-" + i);
        var numEl = indicator ? indicator.querySelector(".fert-step-num") : null;

        if (indicator) {
            indicator.classList.remove("active", "completed");
            if (i < n && isFertStepCompleted(i)) {
                indicator.classList.add("completed");
                if (numEl) numEl.textContent = "\u2713";
            } else if (i === n) {
                indicator.classList.add("active");
                if (numEl) numEl.textContent = i;
            } else {
                if (numEl) numEl.textContent = i;
            }
        }

        if (panel) {
            if (i === n) {
                panel.classList.add("active");
                panel.style.display = "block";
            } else {
                panel.classList.remove("active");
                panel.style.display = "none";
            }
        }
    }

    updateFertStepLabels();

    if (n === 5) {
        var genBtn = document.getElementById("fert-generate-btn");
        var allFilled = fertState.season && fertState.crop && fertState.growthStage && fertState.irrigation;
        if (genBtn) genBtn.disabled = !allFilled;
    }
}

function updateFertStepLabels() {
    if (!window._fertOrigLabels) {
        window._fertOrigLabels = {};
        for (var i = 1; i <= 4; i++) {
            var el = document.getElementById("fert-step-" + i + "-indicator");
            if (el) {
                var labelEl = el.querySelector(".fert-step-label");
                if (labelEl) window._fertOrigLabels[i] = labelEl.textContent;
            }
        }
    }

    var mappings = [
        { step: 1, val: fertState.seasonName },
        { step: 2, val: fertState.cropName },
        { step: 3, val: fertState.growthStageName },
        { step: 4, val: fertState.irrigationName },
    ];

    for (var i = 0; i < mappings.length; i++) {
        var el = document.getElementById("fert-step-" + mappings[i].step + "-indicator");
        if (!el) continue;
        var labelEl = el.querySelector(".fert-step-label");
        if (!labelEl) continue;
        if (mappings[i].val) {
            labelEl.textContent = mappings[i].val;
        } else if (window._fertOrigLabels[mappings[i].step]) {
            labelEl.textContent = window._fertOrigLabels[mappings[i].step];
        }
    }
}

function onFertSelect(name) {
    console.log("onFertSelect:", name);

    if (name === "season" && fertState.season) {
        goToFertStep(2);
    } else if (name === "growthStage" && fertState.growthStage) {
        goToFertStep(4);
    } else if (name === "irrigation" && fertState.irrigation) {
        goToFertStep(5);
    }
}

function onFertCropSelect(value) {
    console.log("Crop selected:", value);
    var nextBtn = document.getElementById("fert-crop-next");
    if (value) {
        fertState.crop = value;
        var select = document.getElementById("fert-crop-select");
        if (select) {
            var opt = select.options[select.selectedIndex];
            fertState.cropName = opt ? opt.textContent.trim() : value;
        }
        if (nextBtn) nextBtn.disabled = false;
    } else {
        fertState.crop = "";
        fertState.cropName = "";
        if (nextBtn) nextBtn.disabled = true;
    }
}

function onFertCropNext() {
    console.log("Crop Next clicked, crop:", fertState.crop);
    if (fertState.crop) {
        goToFertStep(3);
    } else {
        showFertToast("Please select a crop first.", "error");
    }
}

function fertBack() {
    console.log("fertBack from:", fertState.currentStep);
    if (fertState.currentStep > 1) {
        goToFertStep(fertState.currentStep - 1);
    }
}

function generateFertilizer() {
    console.log("Generate clicked");
    console.log("Season:", fertState.season);
    console.log("Crop selected:", fertState.crop);
    console.log("Growth selected:", fertState.growthStage);
    console.log("Irrigation selected:", fertState.irrigation);

    if (!fertState.season || !fertState.crop || !fertState.growthStage || !fertState.irrigation) {
        showFertToast("Please complete all steps first.", "error");
        return;
    }

    var btn = document.getElementById("fert-generate-btn");
    var resultSection = document.getElementById("fert-result-section");
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="fert-spinner"></span> Generating...'; }
    if (resultSection) resultSection.style.display = "none";

    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation: fertState.irrigation,
    };

    console.log("Calling /api/fertilizer/recommend", JSON.stringify(payload));

    fetch("/api/fertilizer/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) {
        if (!r.ok) {
            return r.text().then(function (text) {
                console.error("Recommend HTTP error:", r.status, text);
                try { var j = JSON.parse(text); throw new Error(j.error || "Server error"); }
                catch (e) { throw new Error("Server error (" + r.status + ")"); }
            });
        }
        return r.json();
    })
    .then(function (res) {
        console.log("Recommendation generated, success:", res.success);
        if (btn) { btn.disabled = false; btn.innerHTML = "Get Recommendation"; }
        if (!res.success) {
            showFertToast(res.error || "Failed to generate.", "error");
            return;
        }
        fertState.recommendation = res;
        displayFertResult(res);
        autoSaveFertilizer(res);
    })
    .catch(function (err) {
        console.error("Generate error:", err);
        if (btn) { btn.disabled = false; btn.innerHTML = "Get Recommendation"; }
        showFertToast("Error: " + (err.message || "Something went wrong"), "error");
    });
}

function autoSaveFertilizer(res) {
    console.log("Auto-saving to MongoDB...");
    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation_method: fertState.irrigation,
        recommendation: res.recommendation,
        language: document.documentElement.getAttribute("data-lang") || "en",
    };

    fetch("/api/fertilizer/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            console.log("Saved to MongoDB:", res.message);
            showFertToast("Recommendation saved!", "success");
            loadFertHistory();
            updateFertStats();
        } else {
            console.warn("Auto-save failed:", res.error);
        }
    })
    .catch(function (err) {
        console.warn("Auto-save error:", err);
    });
}

function displayFertResult(res) {
    var section = document.getElementById("fert-result-section");
    if (!section) return;
    section.style.display = "block";

    var meta = res.metadata || {};
    setFertText("fert-result-crop", meta.crop || fertState.cropName || fertState.crop);
    setFertText("fert-result-season", meta.season || fertState.seasonName || fertState.season);
    setFertText("fert-result-stage", meta.growth_stage || fertState.growthStageName || fertState.growthStage);
    setFertText("fert-result-irrigation", meta.irrigation || fertState.irrigationName || fertState.irrigation);

    var confidenceVal = "High";
    var confidenceClass = "high";
    if (res.confidence) {
        var c = ("" + res.confidence).toLowerCase();
        if (c.indexOf("low") >= 0) { confidenceVal = "Low"; confidenceClass = "low"; }
        else if (c.indexOf("medium") >= 0 || c.indexOf("moderate") >= 0) { confidenceVal = "Medium"; confidenceClass = "medium"; }
    }
    var badge = document.getElementById("fert-confidence-badge");
    if (badge) {
        badge.textContent = confidenceVal;
        badge.className = "fert-confidence-badge " + confidenceClass;
    }

    var body = document.getElementById("fert-result-body");
    if (body) {
        body.innerHTML = '<div class="fert-markdown fert-fade-in">' + renderFertMarkdown(res.recommendation) + "</div>";
    }

    var saveBtn = document.getElementById("fert-save-btn");
    if (saveBtn) saveBtn.style.display = "inline-flex";
    var exportGroup = document.getElementById("fert-export-group");
    if (exportGroup) exportGroup.style.display = "inline-flex";

    section.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setFertText(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val || "-";
}

function saveFertilizer() {
    if (!fertState.recommendation) {
        showFertToast("No recommendation to save. Generate one first.", "error");
        return;
    }
    var btn = document.getElementById("fert-save-btn");
    if (btn) { btn.disabled = true; btn.textContent = "Saving..."; }

    var payload = {
        season: fertState.season,
        crop: fertState.crop,
        growth_stage: fertState.growthStage,
        irrigation_method: fertState.irrigation,
        recommendation: fertState.recommendation.recommendation,
        language: document.documentElement.getAttribute("data-lang") || "en",
    };

    fetch("/api/fertilizer/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (btn) { btn.disabled = false; btn.innerHTML = "Save"; }
        if (res.success) {
            showFertToast("Recommendation saved!", "success");
            loadFertHistory();
            updateFertStats();
        } else {
            showFertToast(res.error || "Failed to save.", "error");
        }
    })
    .catch(function () {
        if (btn) { btn.disabled = false; btn.innerHTML = "Save"; }
        showFertToast("Save failed.", "error");
    });
}

function loadFertHistory() {
    var q = "";
    var searchInput = document.getElementById("fert-history-search-input");
    if (searchInput) q = searchInput.value.trim();

    var seasonFilter = document.getElementById("fert-season-filter");
    var seasonVal = seasonFilter ? seasonFilter.value : "";

    var url = "/api/fertilizer/history?";
    var params = [];
    if (q) params.push("search=" + encodeURIComponent(q));
    else if (seasonVal) params.push("season=" + encodeURIComponent(seasonVal));
    url += params.join("&");

    fetch(url)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        var list = document.getElementById("fert-history-list");
        if (!list) return;
        if (!res.success || !res.history || res.history.length === 0) {
            list.innerHTML = '<div class="fert-empty">No recommendations yet.</div>';
            return;
        }
        var html = "";
        for (var i = 0; i < res.history.length; i++) {
            var h = res.history[i];
            var dateStr = h.created_at ? h.created_at.substring(0, 10) : "";
            html += '<div class="fert-history-item" data-id="' + h.id + '">';
            html += '<div class="fert-history-left">';
            html += '<span class="fert-history-crop">' + htmlEscape(h.crop) + "</span>";
            html += '<div class="fert-history-meta"><span>' + htmlEscape(h.season || "") + "</span><span>" + htmlEscape(h.growth_stage || "") + "</span><span>" + htmlEscape(h.irrigation_method || "") + "</span></div>';
            html += '<span class="fert-history-date">' + dateStr + "</span></div>";
            html += '<div class="fert-history-right">';
            html += '<button class="fert-btn-icon" title="View" onclick="viewFertHistory(\'' + h.id + '\')">\uD83D\uDC41</button>';
            html += '<div class="fert-export-dropdown" style="position:relative;display:inline-block">';
            html += '<button class="fert-btn-icon" title="Export" onclick="toggleExportMenu(this)">\uD83D\uDCC4</button>';
            html += '<div class="fert-export-menu" style="display:none;position:absolute;right:0;top:100%;background:var(--fert-card-bg);border:1px solid var(--fert-border);border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:100;min-width:90px;overflow:hidden">';
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','txt');fertCloseMenus()">TXT</button>";
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','pdf');fertCloseMenus()">PDF</button>";
            html += '<button class="fert-export-option" style="display:block;width:100%;padding:8px 14px;border:none;background:transparent;cursor:pointer;font-size:0.8rem;text-align:left;font-family:inherit" onclick="exportFertilizer(\'' + h.id + "','csv');fertCloseMenus()">CSV</button>";
            html += "</div></div>";
            html += '<button class="fert-btn-icon" title="Delete" onclick="deleteFertilizer(\'' + h.id + '\')">\uD83D\uDDD1</button>';
            html += "</div></div>";
        }
        list.innerHTML = html;
    });
}

function toggleExportMenu(btn) {
    fertCloseMenus();
    var menu = btn.nextElementSibling;
    if (menu) menu.style.display = menu.style.display === "block" ? "none" : "block";
}

function fertCloseMenus() {
    document.querySelectorAll(".fert-export-menu").forEach(function (m) { m.style.display = "none"; });
}

document.addEventListener("click", function (e) {
    if (!e.target.closest(".fert-export-dropdown")) {
        document.querySelectorAll(".fert-export-menu").forEach(function (m) { m.style.display = "none"; });
    }
});

function viewFertHistory(id) {
    fetch("/api/fertilizer/history")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        var found = null;
        if (res.history) {
            for (var i = 0; i < res.history.length; i++) {
                if (res.history[i].id === id) { found = res.history[i]; break; }
            }
        }
        if (!found) { showFertToast("Recommendation not found.", "error"); return; }
        var body = document.getElementById("fert-view-modal-body");
        if (!body) return;
        var html =
            '<div class="fert-view-field"><span class="fert-view-label">Crop</span><span class="fert-view-val">' + htmlEscape(found.crop) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">Season</span><span class="fert-view-val">' + htmlEscape(found.season) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">Growth Stage</span><span class="fert-view-val">' + htmlEscape(found.growth_stage) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">Irrigation</span><span class="fert-view-val">' + htmlEscape(found.irrigation_method) + "</span></div>" +
            '<div class="fert-view-field"><span class="fert-view-label">Date</span><span class="fert-view-val">' + (found.created_at ? found.created_at.substring(0, 10) : "") + "</span></div>";
        if (found.recommendation) {
            html += '<div class="fert-view-field" style="margin-top:12px"><span class="fert-view-label">Recommendation</span><div class="fert-markdown" style="font-size:0.85rem;line-height:1.6;margin-top:4px">' + renderFertMarkdown(found.recommendation) + "</div></div>";
        }
        body.innerHTML = html;
        document.getElementById("fert-view-modal").style.display = "flex";
    });
}

function closeFertViewModal() {
    document.getElementById("fert-view-modal").style.display = "none";
}

function deleteFertilizer(id) {
    if (!confirm("Delete this recommendation?")) return;
    fetch("/api/fertilizer/" + id, { method: "DELETE" })
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) {
            showFertToast("Recommendation deleted!", "success");
            loadFertHistory();
            if (res.stats) updateFertStatsFromServer(res.stats);
        } else {
            showFertToast(res.error || "Failed to delete.", "error");
        }
    });
}

function exportFertilizer(id, fmt) {
    fetch("/api/fertilizer/export/" + id + "?format=" + fmt)
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) { downloadFertFile(res); }
        else { showFertToast(res.error || "Export failed.", "error"); }
    });
}

function downloadFertFile(res) {
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
    a.download = res.filename || "fertilizer_export.txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showFertToast("Exported!", "success");
}

function exportCurrentResult(fmt) {
    if (!fertState.recommendation) {
        showFertToast("No result to export.", "error");
        return;
    }
    var lines = [];
    lines.push("FERTILIZER RECOMMENDATION REPORT");
    lines.push("=".repeat(50));
    lines.push("Crop: " + (fertState.cropName || fertState.crop));
    lines.push("Season: " + (fertState.seasonName || fertState.season));
    lines.push("Growth Stage: " + (fertState.growthStageName || fertState.growthStage));
    lines.push("Irrigation: " + (fertState.irrigationName || fertState.irrigation));
    lines.push("");
    lines.push(fertState.recommendation.recommendation);

    if (fmt === "csv") {
        var csv = "Field,Value\n";
        csv += "Crop," + (fertState.cropName || fertState.crop) + "\n";
        csv += "Season," + (fertState.seasonName || fertState.season) + "\n";
        csv += "Growth Stage," + (fertState.growthStageName || fertState.growthStage) + "\n";
        csv += "Irrigation," + (fertState.irrigationName || fertState.irrigation) + "\n";
        downloadFertBlob(csv, "text/csv", "fertilizer_current.csv");
    } else {
        downloadFertBlob(lines.join("\n"), "text/plain", "fertilizer_current.txt");
    }
}

function downloadFertBlob(content, mime, filename) {
    var blob = new Blob([content], { type: mime });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showFertToast("Exported!", "success");
}

function updateFertStats() {
    fetch("/api/fertilizer/stats")
    .then(function (r) { return r.json(); })
    .then(function (res) {
        if (res.success) updateFertStatsFromServer(res.stats);
    });
}

function updateFertStatsFromServer(stats) {
    var el = document.getElementById("fert-stat-total");
    if (el) el.textContent = stats.total || 0;
}

function renderFertMarkdown(text) {
    if (!text) return "";
    var html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    html = html.replace(/^### (.+)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.+)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.+)$/gm, "<h1>$1</h1>");
    html = html.replace(/^-\s\*\*(.+?)\*\*:\s*(.+)$/gm, "<li><strong>$1</strong>: $2</li>");
    html = html.replace(/^-\s(.+)$/gm, "<li>$1</li>");
    html = html.replace(/(<li>.*<\/li>\n?)+/g, "<ul>$&</ul>");
    html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    html = html.replace(/(\d+\.\s+)(.+)/gm, function (m, num, text) {
        return "<li>" + num + text + "</li>";
    });
    html = html.replace(/\n\n/g, "</p><p>");
    html = "<p>" + html + "</p>";
    html = html.replace(/<\/ul><p><ul>/g, "");
    html = html.replace(/<\/p>\n?<li>/g, "<li>");
    html = html.replace(/<\/li>\n?<\/p>/g, "</li>");
    html = html.replace(/<p><ul>/g, "<ul>");
    html = html.replace(/<\/ul><\/p>/g, "</ul>");
    return html;
}

function htmlEscape(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function showFertToast(msg, type) {
    var toast = document.getElementById("fert-toast");
    if (!toast) { alert(msg); return; }
    toast.textContent = msg;
    toast.className = "fert-toast " + (type || "");
    toast.style.display = "block";
    clearTimeout(toast._timer);
    toast._timer = setTimeout(function () { toast.style.display = "none"; }, 3000);
}

window.onFertStepClick = onFertStepClick;
window.onFertCropSelect = onFertCropSelect;
window.onFertCropNext = onFertCropNext;
window.fertBack = fertBack;
window.generateFertilizer = generateFertilizer;
window.saveFertilizer = saveFertilizer;
window.toggleExportMenu = toggleExportMenu;
window.fertCloseMenus = fertCloseMenus;
window.exportCurrentResult = exportCurrentResult;
window.viewFertHistory = viewFertHistory;
window.exportFertilizer = exportFertilizer;
window.deleteFertilizer = deleteFertilizer;
window.closeFertViewModal = closeFertViewModal;
window.downloadFertFile = downloadFertFile;
window.showFertToast = showFertToast;

console.log("fertilizer.js loaded, onFertStepClick=" + (typeof window.onFertStepClick));

document.addEventListener("DOMContentLoaded", function () {
    console.log("DOMContentLoaded firing");
    try {
        fertInit();
    } catch (e) {
        console.error("fertInit error:", e);
        showFertToast("JS init error: " + e.message, "error");
    }
    try {
        goToFertStep(1);
    } catch (e) {
        console.error("goToFertStep error:", e);
    }
    try {
        loadFertHistory();
    } catch (e) {
        console.error("loadFertHistory error:", e);
    }
    try {
        updateFertStats();
    } catch (e) {
        console.error("updateFertStats error:", e);
    }
});
