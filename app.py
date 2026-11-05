import io
import os
import time
import uuid
import logging
from pathlib import Path
from threading import Lock, Thread

from flask import (
    Flask,
    request,
    jsonify,
    render_template_string,
    send_file
)

import main as engine


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ARES_WEB")

# Research runs in a background thread. Use one Gunicorn worker
# because the short-lived job and PDF stores are held in memory.
research_lock = Lock()
jobs_lock = Lock()
JOBS = {}
PDF_REPORTS = {}

JOB_TTL_SECONDS = 60 * 60
MAX_STORED_JOBS = 20

# The current engine still uses SQLite internally while collecting
# source metadata. History is not exposed in the web interface.
engine.initialize_database()


def cleanup_expired_items():
    now = time.time()

    with jobs_lock:
        for job_id in list(JOBS):
            if now - JOBS[job_id].get("created_at", now) > JOB_TTL_SECONDS:
                JOBS.pop(job_id, None)

        for token in list(PDF_REPORTS):
            if now - PDF_REPORTS[token].get("created_at", now) > JOB_TTL_SECONDS:
                PDF_REPORTS.pop(token, None)

        if len(JOBS) > MAX_STORED_JOBS:
            oldest = sorted(
                JOBS.items(),
                key=lambda item: item[1].get("created_at", 0)
            )
            for job_id, _ in oldest[:-MAX_STORED_JOBS]:
                JOBS.pop(job_id, None)


# =========================================================
# HTML + CSS + JAVASCRIPT
# =========================================================

HTML = r"""
<!DOCTYPE html>
<html lang="en">

<head>

<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>ARES — Research Beyond Search</title>

<link rel="preconnect" href="https://fonts.googleapis.com">

<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Playfair+Display:wght@500;600;700&display=swap"
rel="stylesheet">

<style>

:root {
    --bg: #f7f8fa;
    --surface: #ffffff;
    --text: #182438;
    --muted: #8791a2;
    --blue: #315ce8;
    --border: #e9edf2;
    --navy: #17243b;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    min-height: 100vh;
}

nav {
    height: 76px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 7%;
    background: white;
    border-bottom: 1px solid var(--border);
}

.logo {
    font-size: 25px;
    font-weight: 800;
    letter-spacing: 3px;
}

.logo span {
    color: var(--blue);
}

.nav-right {
    display: flex;
    align-items: center;
    gap: 9px;
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 1px;
}

.status-dot {
    height: 7px;
    width: 7px;
    border-radius: 50%;
    background: #20b981;
}

.hero {
    max-width: 1000px;
    margin: 85px auto 55px;
    padding: 0 25px;
    text-align: center;
}

.eyebrow {
    color: var(--blue);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    margin-bottom: 22px;
}

h1 {
    font-family: 'Playfair Display', serif;
    font-size: clamp(40px, 6vw, 68px);
    line-height: 1.12;
    font-weight: 500;
    letter-spacing: -2px;
}

h1 span {
    color: var(--blue);
}

.subtitle {
    color: var(--muted);
    font-size: 15px;
    margin-top: 22px;
    line-height: 1.8;
}

.search-box {
    background: white;
    max-width: 760px;
    margin: 42px auto 0;
    border: 1px solid var(--border);
    border-radius: 17px;
    padding: 12px;
    box-shadow: 0 15px 45px rgba(25,40,70,.06);
    transition: .25s;
}

.search-box:focus-within {
    border-color: var(--blue);
    box-shadow: 0 15px 45px rgba(49,92,232,.10);
}

textarea {
    width: 100%;
    min-height: 110px;
    border: none;
    outline: none;
    resize: vertical;
    padding: 17px;
    font-family: inherit;
    font-size: 16px;
    color: var(--text);
}

textarea::placeholder {
    color: #a8b0bc;
}

.search-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px 5px;
}

.search-hint {
    font-size: 11px;
    color: var(--muted);
}

button {
    border: none;
    cursor: pointer;
    font-family: inherit;
}

.research-btn {
    background: var(--blue);
    color: white;
    padding: 14px 24px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 700;
    transition: .2s;
}

.research-btn:hover {
    background: #2149ce;
    transform: translateY(-2px);
}

.research-btn:disabled {
    opacity: .5;
    cursor: wait;
}

.examples {
    margin-top: 25px;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}

.example {
    border: 1px solid var(--border);
    background: white;
    color: #697589;
    border-radius: 30px;
    padding: 10px 15px;
    font-size: 11px;
    transition: .2s;
}

.example:hover {
    border-color: var(--blue);
    color: var(--blue);
}


/* WORKSPACE */

.workspace {
    max-width: 1050px;
    margin: 30px auto 100px;
    padding: 0 25px;
    display: none;
}

.progress-card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 25px;
}

.progress-title {
    font-weight: 700;
    font-size: 14px;
    margin-bottom: 18px;
}

.progress-bar {
    height: 5px;
    background: #edf0f5;
    border-radius: 10px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    width: 0%;
    background: var(--blue);
    transition: width .5s;
}

.progress-text {
    font-size: 12px;
    color: var(--muted);
    margin-top: 15px;
}


/* PIPELINE */

.pipeline {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin: 20px 0 30px;
}

.pipeline-item {
    background: white;
    border: 1px solid var(--border);
    border-radius: 11px;
    padding: 15px;
}

.pipeline-item.active {
    border-color: var(--blue);
    background: #f4f7ff;
}

.pipeline-item.done {
    border-color: #b7e5d0;
}

.pipeline-item strong {
    display: block;
    font-size: 12px;
    margin-bottom: 6px;
}

.pipeline-item small {
    font-size: 10px;
    color: var(--muted);
}


/* RESULTS */

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 35px 0 20px;
    gap: 15px;
}

.result-header h2 {
    font-family: 'Playfair Display', serif;
    font-size: 29px;
    font-weight: 500;
}

.export-btn {
    background: var(--navy);
    color: white;
    padding: 12px 17px;
    border-radius: 9px;
    font-size: 12px;
}

.card {
    background: white;
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 28px;
    margin-bottom: 20px;
}

.card-label {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 2px;
    color: var(--blue);
    margin-bottom: 20px;
}

.findings {
    line-height: 1.85;
    font-size: 14px;
    color: #465268;
    overflow-wrap: anywhere;
}

.findings h1,
.findings h2,
.findings h3 {
    font-family: 'DM Sans', sans-serif;
    font-size: 16px;
    font-weight: 700;
    margin: 22px 0 10px;
    letter-spacing: 0;
}

.findings p {
    margin-bottom: 13px;
}

.findings ul,
.findings ol {
    padding-left: 22px;
    margin-bottom: 15px;
}

.source {
    display: block;
    padding: 17px 0;
    border-bottom: 1px solid var(--border);
    text-decoration: none;
    color: var(--text);
}

.source:last-child {
    border: none;
}

.source strong {
    font-size: 13px;
    display: block;
    margin-bottom: 7px;
}

.source small {
    color: var(--muted);
    font-size: 11px;
    overflow-wrap: anywhere;
}

.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
}

.stat {
    background: #f8f9fc;
    padding: 20px;
    border-radius: 10px;
}

.stat strong {
    display: block;
    font-size: 23px;
    margin-bottom: 5px;
}

.stat small {
    font-size: 10px;
    color: var(--muted);
}

.history-item {
    padding: 15px 0;
    border-bottom: 1px solid var(--border);
}

.history-item strong {
    display: block;
    font-size: 13px;
    margin-bottom: 5px;
}

.history-item small {
    color: var(--muted);
    font-size: 11px;
}

.error {
    background: #fff0f0;
    border: 1px solid #ffd4d4;
    color: #c33;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
    font-size: 13px;
    display: none;
}

footer {
    text-align: center;
    color: #a2aab6;
    font-size: 11px;
    padding: 35px;
    border-top: 1px solid var(--border);
}

@media(max-width:650px) {

    nav {
        padding: 0 20px;
    }

    .hero {
        margin-top: 60px;
    }

    .nav-right {
        display: none;
    }

    .pipeline {
        grid-template-columns: repeat(2, 1fr);
    }

    .stats-grid {
        grid-template-columns: repeat(2, 1fr);
    }

    .result-header {
        flex-direction: column;
        align-items: flex-start;
    }

}

</style>
</head>


<body>

<nav>

    <div class="logo">AR<span>E</span>S</div>

    <div class="nav-right">
        <div class="status-dot"></div>
        RESEARCH ENGINE ONLINE
    </div>

</nav>


<section class="hero">

    <div class="eyebrow">
        AI RESEARCH & EXPLORATION SYSTEM
    </div>

    <h1>
        Don't just search.<br>
        <span>Discover.</span>
    </h1>

    <p class="subtitle">
        Turn complex questions into structured research.<br>
        Explore sources, uncover insights and build understanding.
    </p>

    <div class="search-box">

        <textarea
            id="topic"
            maxlength="500"
            placeholder="What would you like to investigate today?"
        ></textarea>

        <div class="search-bottom">

            <div class="search-hint">
                ARES Research Engine v0.3
            </div>

            <button
                class="research-btn"
                id="researchBtn"
                onclick="startResearch()"
            >
                Start Research →
            </button>

        </div>

    </div>


    <div class="examples">

        <button class="example"
        onclick="setTopic('Recent advances in artificial intelligence')">
            Artificial Intelligence
        </button>

        <button class="example"
        onclick="setTopic('Deep learning research challenges')">
            Deep Learning
        </button>

        <button class="example"
        onclick="setTopic('Climate change and extreme weather prediction')">
            Climate Research
        </button>

        <button class="example"
        onclick="setTopic('Recent advances in quantum computing')">
            Quantum Computing
        </button>

    </div>

</section>


<section class="workspace" id="workspace">

    <div class="error" id="error"></div>

    <div class="progress-card">

        <div class="progress-title" id="progressTitle">
            Preparing research engine...
        </div>

        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>

        <div class="progress-text" id="progressText">
            Initializing ARES...
        </div>

    </div>


    <div class="pipeline">

        <div class="pipeline-item" id="stage1">
            <strong>01 / Discovery</strong>
            <small>Web + Academic Search</small>
        </div>

        <div class="pipeline-item" id="stage2">
            <strong>02 / Extraction</strong>
            <small>Content Collection</small>
        </div>

        <div class="pipeline-item" id="stage3">
            <strong>03 / Analysis</strong>
            <small>AI Research Synthesis</small>
        </div>

        <div class="pipeline-item" id="stage4">
            <strong>04 / Reporting</strong>
            <small>PDF Generation</small>
        </div>

    </div>


    <div id="results" style="display:none">

        <div class="result-header">

            <h2>Research Findings</h2>

            <button
                class="export-btn"
                onclick="exportPDF()"
            >
                ↓ Download Research PDF
            </button>

        </div>


        <div class="card">

            <div class="card-label">
                RESEARCH OVERVIEW
            </div>

            <div id="researchTopic"></div>

        </div>


        <div class="card">

            <div class="card-label">
                CORPUS STATISTICS
            </div>

            <div class="stats-grid" id="stats"></div>

        </div>


        <div class="card">

            <div class="card-label">
                RESEARCH ANALYSIS
            </div>

            <div class="findings" id="findings"></div>

        </div>


        <div class="card">

            <div class="card-label">
                DISCOVERED SOURCES
            </div>

            <div id="sources"></div>

        </div>

    </div>


</section>


<footer>
    ARES © 2026 · Research with evidence. Think independently.
</footer>


<script>

let researchData = null;


function setTopic(topic) {

    document.getElementById("topic").value = topic;
    document.getElementById("topic").focus();

}


function setProgress(value, title, description) {

    document.getElementById("progressFill").style.width =
        value + "%";

    document.getElementById("progressTitle").textContent =
        title;

    document.getElementById("progressText").textContent =
        description;

}


function setStage(active) {

    for (let i = 1; i <= 4; i++) {

        const element = document.getElementById("stage" + i);

        element.classList.remove("active", "done");

        if (i < active) {
            element.classList.add("done");
        }

        if (i === active) {
            element.classList.add("active");
        }

    }

}


function escapeHTML(value) {

    return String(value ?? "").replace(
        /[&<>"']/g,
        char => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        })[char]
    );

}


// Basic Markdown renderer

function renderMarkdown(text) {

    const lines = String(text || "").split("\n");

    let output = "";
    let listOpen = false;

    for (const raw of lines) {

        const line = raw.trim();

        if (!line) {

            if (listOpen) {
                output += "</ul>";
                listOpen = false;
            }

            continue;
        }

        if (line.startsWith("# ")) {

            output += "<h1>" +
                escapeHTML(line.slice(2)) +
                "</h1>";

            continue;
        }

        if (line.startsWith("## ")) {

            output += "<h2>" +
                escapeHTML(line.slice(3)) +
                "</h2>";

            continue;
        }

        if (line.startsWith("### ")) {

            output += "<h3>" +
                escapeHTML(line.slice(4)) +
                "</h3>";

            continue;
        }

        if (line.startsWith("- ") || line.startsWith("* ")) {

            if (!listOpen) {
                output += "<ul>";
                listOpen = true;
            }

            output += "<li>" +
                escapeHTML(line.slice(2)) +
                "</li>";

            continue;
        }

        if (listOpen) {
            output += "</ul>";
            listOpen = false;
        }

        output += "<p>" +
            escapeHTML(line) +
            "</p>";

    }

    if (listOpen) {
        output += "</ul>";
    }

    return output;

}


// =========================================================
// START RESEARCH
// =========================================================

async function readJSONResponse(response) {
    const raw = await response.text();

    if (!raw) {
        throw new Error(`Server returned an empty response (HTTP ${response.status}).`);
    }

    try {
        return JSON.parse(raw);
    } catch (error) {
        throw new Error(`Server returned an invalid response (HTTP ${response.status}).`);
    }
}


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


async function startResearch() {
    const topic = document.getElementById("topic").value.trim();

    if (!topic) {
        alert("Please enter a research topic.");
        return;
    }

    if (topic.length > 500) {
        alert("Research topic must be under 500 characters.");
        return;
    }

    const button = document.getElementById("researchBtn");
    const workspace = document.getElementById("workspace");
    const results = document.getElementById("results");
    const error = document.getElementById("error");

    workspace.style.display = "block";
    results.style.display = "none";
    error.style.display = "none";
    researchData = null;

    button.disabled = true;
    button.textContent = "Researching...";
    workspace.scrollIntoView({ behavior: "smooth" });

    const stages = [
        [12, 1, "Searching the web", "Discovering relevant web and academic sources..."],
        [35, 2, "Extracting information", "Collecting article content..."],
        [65, 3, "Analyzing research", "Summarizing and synthesizing evidence..."],
        [88, 4, "Preparing report", "Finalizing your research results..."]
    ];

    let stageIndex = 0;
    setProgress(5, "Starting ARES", "Submitting your research topic...");
    setStage(1);

    const timer = setInterval(() => {
        const stage = stages[Math.min(stageIndex, stages.length - 1)];
        setProgress(stage[0], stage[2], stage[3]);
        setStage(stage[1]);
        stageIndex = Math.min(stageIndex + 1, stages.length - 1);
    }, 5000);

    try {
        const startResponse = await fetch("/api/research", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ topic })
        });

        const startData = await readJSONResponse(startResponse);

        if (!startResponse.ok) {
            throw new Error(startData.error || "Could not start research.");
        }

        if (!startData.job_id) {
            throw new Error("The server did not return a research job ID.");
        }

        let completedData = null;

        while (true) {
            await sleep(2000);

            const statusResponse = await fetch(
                `/api/research/${encodeURIComponent(startData.job_id)}`,
                { cache: "no-store" }
            );

            const statusData = await readJSONResponse(statusResponse);

            if (!statusResponse.ok) {
                throw new Error(statusData.error || "Could not check research status.");
            }

            if (statusData.status === "failed") {
                throw new Error(statusData.error || "Research failed.");
            }

            if (statusData.status === "completed") {
                completedData = statusData.result;
                break;
            }
        }

        if (!completedData || !Array.isArray(completedData.articles)) {
            throw new Error("Research finished but returned incomplete results.");
        }

        if (!completedData.stats || typeof completedData.stats !== "object") {
            throw new Error("Research statistics are missing from the response.");
        }

        researchData = completedData;

        for (let i = 1; i <= 4; i++) {
            const element = document.getElementById("stage" + i);
            element.classList.remove("active");
            element.classList.add("done");
        }

        setProgress(
            100,
            "Research completed",
            `${completedData.articles.length} sources analyzed in ${completedData.duration} seconds.`
        );

        displayResults(completedData);
    } catch (err) {
        error.textContent = err.message || "An unexpected research error occurred.";
        error.style.display = "block";
        setProgress(0, "Research interrupted", "Please review the error and try again.");
    } finally {
        clearInterval(timer);
        button.disabled = false;
        button.textContent = "Start Research →";
    }
}


// =========================================================
// DISPLAY RESULTS
// =========================================================

function displayResults(data) {

    document.getElementById("results").style.display = "block";

    const pdfButton = document.querySelector(".export-btn");
    if (pdfButton) {
        pdfButton.style.display = data.pdf_token ? "inline-block" : "none";
    }

    document.getElementById("researchTopic").textContent =
        data.topic || "Untitled research";


    document.getElementById("findings").innerHTML =
        renderMarkdown(data.summary || "No summary available.");


    const stats = data.stats || {};


    const statItems = [

        ["Sources", stats.total_sources ?? 0],

        ["Academic", stats.academic_sources ?? 0],

        ["Web Sources", stats.web_sources ?? 0],

        [
            "Relevance",
            Number(stats.average_relevance ?? 0).toFixed(1) + "/100"
        ]

    ];


    document.getElementById("stats").innerHTML =

        statItems.map(item => `

            <div class="stat">

                <strong>${escapeHTML(item[1])}</strong>

                <small>${escapeHTML(item[0])}</small>

            </div>

        `).join("");


    const container = document.getElementById("sources");

    container.replaceChildren();


    if (!data.articles.length) {

        container.textContent = "No sources available.";

    }


    data.articles.forEach((article, index) => {

        const link = document.createElement("a");

        link.className = "source";


        // Only allow HTTP/HTTPS external links.

        try {

            const parsedURL = new URL(article.url);

            if (
                parsedURL.protocol === "http:" ||
                parsedURL.protocol === "https:"
            ) {

                link.href = parsedURL.href;
                link.target = "_blank";
                link.rel = "noopener noreferrer";

            }

        } catch (e) {

            link.removeAttribute("href");

        }


        const title = document.createElement("strong");

        title.textContent =
            `[S${index + 1}] ${article.title || "Untitled source"}`;


        const details = document.createElement("small");

        details.textContent =

            `${article.domain || "Unknown domain"} · ` +

            `${article.source_type || "web"} · ` +

            `Relevance ${article.relevance_score ?? 0}/100`;


        link.append(title, details);

        container.appendChild(link);

    });


    document.getElementById("results").scrollIntoView({
        behavior: "smooth"
    });

}


// =========================================================
// PDF EXPORT
// =========================================================

async function exportPDF() {
    if (!researchData || !researchData.pdf_token) {
        alert("No downloadable PDF is available for this research.");
        return;
    }

    const button = document.querySelector(".export-btn");
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Preparing PDF...";

    try {
        const response = await fetch(
            `/api/export/${encodeURIComponent(researchData.pdf_token)}`
        );

        if (!response.ok) {
            const data = await readJSONResponse(response);
            throw new Error(data.error || "PDF download failed.");
        }

        const blob = await response.blob();

        if (!blob.size) {
            throw new Error("The generated PDF is empty.");
        }

        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "ARES_Research_Report.pdf";

        document.body.appendChild(link);
        link.click();
        link.remove();

        setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
        alert(err.message || "PDF download failed.");
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}


// =========================================================
// KEYBOARD SHORTCUT
// =========================================================

document.getElementById("topic").addEventListener(
    "keydown",
    function(event) {

        if (
            event.key === "Enter" &&
            !event.shiftKey
        ) {

            event.preventDefault();

            startResearch();

        }

    }
);



</script>

</body>
</html>
"""


# =========================================================
# HOME
# =========================================================

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML)


# =========================================================
# BACKGROUND RESEARCH WORKER
# =========================================================

def run_research_job(job_id, topic):
    try:
        logger.info("Research job %s started: %s", job_id, topic)

        result = engine.run_research(topic)

        if not isinstance(result, dict):
            raise RuntimeError(
                "The research engine did not return a structured result."
            )

        result = dict(result)

        # Capture the engine-generated PDF in memory and remove its
        # temporary disk copy. The download route serves the bytes.
        report_path = result.pop("report_path", None)
        pdf_bytes = None

        if report_path:
            report_file = Path(report_path).resolve()
            if report_file.is_file():
                pdf_bytes = report_file.read_bytes()
                try:
                    report_file.unlink()
                except OSError:
                    logger.warning("Could not remove temporary PDF: %s", report_file)

        result.pop("research_id", None)
        result.pop("sources_saved", None)

        result.setdefault("articles", [])
        result.setdefault("stats", {})
        result.setdefault("summary", "")
        result.setdefault("duration", 0)

        if not isinstance(result["articles"], list):
            result["articles"] = []
        if not isinstance(result["stats"], dict):
            result["stats"] = {}

        pdf_token = None
        if pdf_bytes:
            pdf_token = uuid.uuid4().hex
            with jobs_lock:
                PDF_REPORTS[pdf_token] = {
                    "bytes": pdf_bytes,
                    "created_at": time.time()
                }

        result["report_ready"] = bool(pdf_token)
        result["pdf_token"] = pdf_token

        with jobs_lock:
            JOBS[job_id]["status"] = "completed"
            JOBS[job_id]["result"] = result
            JOBS[job_id]["completed_at"] = time.time()

        logger.info(
            "Research job %s completed. Sources=%s PDF=%s",
            job_id, len(result["articles"]), bool(pdf_token)
        )

    except Exception as exc:
        logger.exception("Research job %s failed", job_id)
        with jobs_lock:
            if job_id in JOBS:
                JOBS[job_id]["status"] = "failed"
                JOBS[job_id]["error"] = str(exc) or "Research failed."
                JOBS[job_id]["completed_at"] = time.time()

    finally:
        research_lock.release()


# =========================================================
# START RESEARCH API
# =========================================================

@app.route("/api/research", methods=["POST"])
def research():
    data = request.get_json(silent=True) or {}
    topic = str(data.get("topic", "")).strip()

    if not topic:
        return jsonify({"error": "Research topic is required."}), 400
    if len(topic) > 500:
        return jsonify({"error": "Topic must be under 500 characters."}), 400

    if not research_lock.acquire(blocking=False):
        return jsonify({
            "error": "Another research task is already running. Please wait."
        }), 409

    cleanup_expired_items()
    job_id = uuid.uuid4().hex

    with jobs_lock:
        JOBS[job_id] = {
            "status": "running",
            "created_at": time.time(),
            "result": None,
            "error": None
        }

    try:
        Thread(
            target=run_research_job,
            args=(job_id, topic),
            daemon=True
        ).start()
    except Exception:
        research_lock.release()
        with jobs_lock:
            JOBS.pop(job_id, None)
        logger.exception("Could not start research background thread")
        return jsonify({"error": "Could not start the research worker."}), 500

    return jsonify({"job_id": job_id, "status": "running"}), 202


# =========================================================
# RESEARCH STATUS API
# =========================================================

@app.route("/api/research/<job_id>", methods=["GET"])
def research_status(job_id):
    with jobs_lock:
        job = JOBS.get(job_id)

        if not job:
            return jsonify({
                "error": "Research job not found or expired. Please start again."
            }), 404

        if job["status"] == "completed":
            return jsonify({
                "status": "completed",
                "result": job.get("result")
            })

        if job["status"] == "failed":
            return jsonify({
                "status": "failed",
                "error": job.get("error") or "Research failed."
            })

        return jsonify({"status": "running"})


# =========================================================
# IN-MEMORY PDF DOWNLOAD
# =========================================================

@app.route("/api/export/<token>", methods=["GET"])
def export_pdf(token):
    with jobs_lock:
        report = PDF_REPORTS.get(token)

    if not report:
        return jsonify({
            "error": "This PDF is no longer available. Run the research again."
        }), 404

    pdf_stream = io.BytesIO(report["bytes"])
    pdf_stream.seek(0)

    return send_file(
        pdf_stream,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="ARES_Research_Report.pdf",
        max_age=0
    )


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "application": "ARES",
        "version": getattr(engine, "VERSION", "unknown"),
        "status": "online"
    })


# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(413)
def request_too_large(error):
    return jsonify({"error": "Request payload is too large."}), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found."}), 404


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        debug=False,
        threaded=True
    )
