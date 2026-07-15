let pieChart;
let barChart;
let trendChart;
let latestResults = [];

const titleMap = {
    dashboard: "Dashboard",
    manual: "Manual Comment Analysis",
    scanner: "Instagram Scanner",
    reports: "Reports",
};

document.querySelectorAll(".nav-link").forEach((button) => {
    button.addEventListener("click", () => {
        document.querySelectorAll(".nav-link").forEach((item) => item.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
        document.getElementById("pageTitle").textContent = titleMap[button.dataset.tab];
    });
});

document.getElementById("themeToggle").addEventListener("click", () => {
    const isDark = document.body.classList.toggle("dark");
    localStorage.setItem("cybershield-theme", isDark ? "dark" : "light");
});

const currentTheme = localStorage.getItem("cybershield-theme");
if (currentTheme === "light") {
    document.body.classList.remove("dark");
} else {
    document.body.classList.add("dark");
}

document.getElementById("analyzeBtn").addEventListener("click", async () => {
    const comment = document.getElementById("manualComment").value.trim();
    if (!comment) return;
    const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comment }),
    });
    const data = await response.json();
    document.getElementById("manualResult").innerHTML = resultMarkup(data);
});

document.getElementById("startBtn").addEventListener("click", async () => {
    const reelUrl = document.getElementById("reelUrl").value.trim();
    if (!reelUrl) return;
    document.getElementById("scannerHint").textContent = "Starting monitor...";
    const response = await fetch(`/start_monitoring?reel_url=${encodeURIComponent(reelUrl)}`);
    const data = await response.json();
    document.getElementById("scannerHint").textContent = data.message || data.error;
    refreshResults();
});

document.getElementById("stopBtn").addEventListener("click", async () => {
    const response = await fetch("/stop_monitoring");
    const data = await response.json();
    document.getElementById("scannerHint").textContent = data.message;
    refreshResults();
});

document.getElementById("csvBtn").addEventListener("click", () => downloadReport("csv"));
document.getElementById("pdfBtn").addEventListener("click", () => downloadReport("pdf"));

async function downloadReport(type) {
    const response = await fetch("/export_report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type }),
    });
    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        document.getElementById("reportHint").textContent = data.error || "Report export failed.";
        return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `cybershield_report.${type}`;
    anchor.click();
    URL.revokeObjectURL(url);
    document.getElementById("reportHint").textContent = `${type.toUpperCase()} report downloaded.`;
}

async function refreshResults() {
    const response = await fetch("/results");
    const data = await response.json();
    latestResults = data.results || [];
    renderSummary(data.summary);
    renderTable("resultsBody", latestResults);
    renderTable("scannerBody", latestResults);
    renderCharts(data.summary, latestResults);
}

function renderSummary(summary) {
    document.getElementById("totalComments").textContent = summary.total;
    document.getElementById("bullyingComments").textContent = summary.bullying;
    document.getElementById("safeComments").textContent = summary.safe;
    document.getElementById("bullyingRate").textContent = `${summary.bullying_percentage}%`;
    const modelEl = document.getElementById("modelStatus");
    if (modelEl) {
        modelEl.textContent = summary.model_status;
    }
    document.getElementById("scannerStatus").textContent = summary.status || "Idle";
    document.getElementById("visibleComments").textContent = summary.visible_comments || 0;
    document.getElementById("analyzedComments").textContent = summary.analyzed_comments || 0;
    document.getElementById("lastCommentHint").textContent = summary.last_comment
        ? `Latest: ${summary.last_comment}`
        : "";
    const monitorStatus = document.getElementById("monitorStatus");
    monitorStatus.textContent = summary.monitoring ? "Live monitoring" : "Idle";
    monitorStatus.classList.toggle("live", summary.monitoring);
    if (summary.last_error) {
        document.getElementById("scannerHint").textContent = summary.last_error;
    }
}

function renderTable(targetId, results) {
    const body = document.getElementById(targetId);
    body.innerHTML = "";
    if (!results.length) {
        const row = document.createElement("tr");
        row.innerHTML = `<td class="empty-row" colspan="6">No analyzed comments yet.</td>`;
        body.appendChild(row);
        return;
    }
    results.forEach((item) => {
        const row = document.createElement("tr");
        const userDisplay = item.profile_url 
            ? `<a href="${escapeHtml(item.profile_url)}" target="_blank" class="user-profile-link">${escapeHtml(item.username)}</a>` 
            : escapeHtml(item.username);
        row.innerHTML = `
            <td>${userDisplay}</td>
            <td>${escapeHtml(item.comment)}</td>
            <td><span class="badge ${item.prediction.toLowerCase().replace(" ", "-")}">${item.prediction}</span></td>
            <td>${item.confidence}%</td>
            <td>${escapeHtml((item.reason || []).join("; "))}</td>
            <td>
                <button class="action-btn copy-user">Copy User</button>
                <button class="action-btn copy-comment">Copy Comment</button>
            </td>
        `;
        row.querySelector(".copy-user").addEventListener("click", () => copyUsername(item.username));
        row.querySelector(".copy-comment").addEventListener("click", () => {
            navigator.clipboard.writeText(item.comment);
        });
        body.appendChild(row);
    });
}

function renderCharts(summary, results) {
    const pieData = [summary.bullying, summary.safe];
    const labels = ["Bullying", "Non-Bullying"];
    const colors = ["#d93f5b", "#1f9d68"];
    if (!pieChart) {
        pieChart = new Chart(document.getElementById("pieChart"), {
            type: "doughnut",
            data: { labels, datasets: [{ data: pieData, backgroundColor: colors }] },
        });
        barChart = new Chart(document.getElementById("barChart"), {
            type: "bar",
            data: { labels, datasets: [{ label: "Comments", data: pieData, backgroundColor: colors }] },
            options: { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
        });
        trendChart = new Chart(document.getElementById("trendChart"), {
            type: "line",
            data: trendData(results),
            options: { scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } },
        });
        return;
    }
    pieChart.data.datasets[0].data = pieData;
    barChart.data.datasets[0].data = pieData;
    trendChart.data = trendData(results);
    pieChart.update();
    barChart.update();
    trendChart.update();
}

function trendData(results) {
    const buckets = {};
    [...results].reverse().forEach((item) => {
        const key = (item.timestamp || "").slice(11, 16) || "Manual";
        buckets[key] = (buckets[key] || 0) + 1;
    });
    return {
        labels: Object.keys(buckets),
        datasets: [{ label: "Comments analyzed", data: Object.values(buckets), borderColor: "#246bfe", tension: 0.35 }],
    };
}

function resultMarkup(data) {
    return `
        <strong>${data.prediction}</strong>
        <p>Confidence: ${data.confidence}%</p>
        <p>${escapeHtml((data.reason || []).join("; "))}</p>
    `;
}

function copyUsername(username) {
    navigator.clipboard.writeText(username);
}

function openProfile(url) {
    if (url) window.open(url, "_blank", "noopener");
}

function openReports() {
    document.querySelector('[data-tab="reports"]').click();
}

function escapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

refreshResults();
setInterval(refreshResults, 1000);
