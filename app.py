import os
import logging
from pathlib import Path
from threading import Lock

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
REPORT_DIR = (BASE_DIR / "reports").resolve()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("ARES_WEB")

research_lock = Lock()


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

engine.initialize_database()


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


    <div class="card" id="historyCard">

        <div class="card-label">
            RECENT RESEARCH
        </div>

        <div id="history">
            Loading research history...
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

    workspace.scrollIntoView({
        behavior: "smooth"
    });


    const stages = [

        [12, 1, "Searching the web",
            "Discovering relevant web and academic sources..."],

        [35, 2, "Extracting information",
            "Collecting article content..."],

        [65, 3, "Analyzing research",
            "Summarizing and synthesizing evidence..."],

        [90, 4, "Preparing report",
            "Generating your research PDF..."]

    ];


    let stageIndex = 0;

    const timer = setInterval(() => {

        if (stageIndex < stages.length) {

            const stage = stages[stageIndex];

            setProgress(
                stage[0],
                stage[2],
                stage[3]
            );

            setStage(stage[1]);

            stageIndex++;

        }

    }, 4000);


    try {

        const response = await fetch("/api/research", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                topic: topic
            })

        });


        const data = await response.json();


        if (!response.ok) {

            throw new Error(
                data.error || "Research failed."
            );

        }


        // FIX: Backend sends report_ready instead of
        // exposing the absolute report_path.

        if (!data.report_ready) {

            throw new Error(
                "Research completed, but PDF report was not generated."
            );

        }


        if (!Array.isArray(data.articles)) {
            throw new Error("Invalid research sources received.");
        }

        if (!data.stats || typeof data.stats !== "object") {
            throw new Error("Research statistics are missing.");
        }


        researchData = data;

        clearInterval(timer);


        setProgress(
            100,
            "Research completed",
            `${data.articles.length} sources analyzed in ${data.duration} seconds.`
        );


        for (let i = 1; i <= 4; i++) {

            const element = document.getElementById("stage" + i);

            element.classList.remove("active");
            element.classList.add("done");

        }


        displayResults(data);

        loadHistory();

    }

    catch (err) {

        clearInterval(timer);

        error.textContent = err.message;
        error.style.display = "block";

        setProgress(
            0,
            "Research interrupted",
            "Please review the error and try again."
        );

    }

    finally {

        button.disabled = false;
        button.textContent = "Start Research →";

    }

}


// =========================================================
// DISPLAY RESULTS
// =========================================================

function displayResults(data) {

    document.getElementById("results").style.display = "block";

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

    if (!researchData || !researchData.research_id) {
        alert("No completed research report available.");
        return;
    }

    try {

        const response = await fetch("/api/export", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                research_id: researchData.research_id
            })

        });


        if (!response.ok) {

            let message = "PDF download failed.";

            try {
                const data = await response.json();
                message = data.error || message;
            } catch (e) {}

            throw new Error(message);

        }


        const blob = await response.blob();

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = url;
        link.download = "ARES_Research_Report.pdf";

        document.body.appendChild(link);

        link.click();

        link.remove();

        URL.revokeObjectURL(url);

    }

    catch (err) {

        alert(err.message);

    }

}


// =========================================================
// RESEARCH HISTORY
// =========================================================

async function loadHistory() {

    try {

        const response = await fetch("/api/history");

        if (!response.ok) {
            throw new Error("History request failed.");
        }

        const history = await response.json();

        const container = document.getElementById("history");

        container.replaceChildren();


        if (!Array.isArray(history) || !history.length) {

            container.textContent = "No previous research yet.";

            return;

        }


        history.forEach(item => {

            const div = document.createElement("div");

            div.className = "history-item";


            const title = document.createElement("strong");

            title.textContent = item.topic || "Untitled research";


            const date = document.createElement("small");

            date.textContent = item.created_at || "";


            div.append(title, date);

            container.appendChild(div);

        });

    }

    catch (err) {

        console.error("History loading failed:", err);

        document.getElementById("history").textContent =
            "Could not load research history.";

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


loadHistory();

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
# RESEARCH API
# =========================================================

@app.route("/api/research", methods=["POST"])
def research():

    data = request.get_json(silent=True) or {}

    topic = str(data.get("topic", "")).strip()

    if not topic:

        return jsonify({
            "error": "Research topic is required."
        }), 400

    if len(topic) > 500:

        return jsonify({
            "error": "Topic must be under 500 characters."
        }), 400


    if not research_lock.acquire(blocking=False):

        return jsonify({
            "error": (
                "Another research task is already running. "
                "Please wait."
            )
        }), 409


    try:

        logger.info("Research started: %s", topic)

        result = engine.run_research(topic)


        if not isinstance(result, dict):

            logger.error(
                "Invalid engine response type: %s",
                type(result).__name__
            )

            return jsonify({
                "error": (
                    "The research engine did not return "
                    "a structured result. Check main.py."
                )
            }), 500


        # Create a separate response object.
        # Do not expose the local PDF file path.

        result = dict(result)

        report_path = result.get("report_path")

        result["report_ready"] = bool(report_path)

        result.pop("report_path", None)


        # Ensure expected frontend fields exist.

        result.setdefault("articles", [])

        result.setdefault("stats", {})

        result.setdefault("summary", "")

        result.setdefault("duration", 0)


        logger.info(
            "Research completed: ID=%s, PDF=%s",
            result.get("research_id"),
            result["report_ready"]
        )


        return jsonify(result)


    except Exception as e:

        logger.exception("Research failed")

        return jsonify({
            "error": str(e)
        }), 500


    finally:

        research_lock.release()


# =========================================================
# PDF DOWNLOAD
# =========================================================

@app.route("/api/export", methods=["POST"])
def export():

    data = request.get_json(silent=True) or {}

    research_id = data.get("research_id")


    if (
        not isinstance(research_id, int)
        or isinstance(research_id, bool)
        or research_id <= 0
    ):

        return jsonify({
            "error": "Invalid research ID."
        }), 400


    try:

        with engine.get_db() as conn:

            row = conn.execute(
                """
                SELECT report_path
                FROM research
                WHERE id = ?
                """,
                (research_id,)
            ).fetchone()


        if not row or not row[0]:

            return jsonify({
                "error": "Research report not found."
            }), 404


        filepath = Path(row[0]).resolve()


        # Security: PDF must be inside the reports directory.

        if filepath.parent != REPORT_DIR:

            logger.warning(
                "Rejected report path outside report directory: %s",
                filepath
            )

            return jsonify({
                "error": "Invalid report location."
            }), 403


        if not filepath.is_file():

            return jsonify({
                "error": "PDF file does not exist."
            }), 404


        return send_file(
            filepath,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filepath.name
        )


    except Exception:

        logger.exception("PDF export failed")

        return jsonify({
            "error": "Could not download report."
        }), 500


# =========================================================
# RESEARCH HISTORY
# =========================================================

@app.route("/api/history", methods=["GET"])
def history():

    try:

        with engine.get_db() as conn:

            rows = conn.execute(
                """
                SELECT
                    id,
                    topic,
                    created_at,
                    report_path
                FROM research
                ORDER BY id DESC
                LIMIT 20
                """
            ).fetchall()


        return jsonify([

            {
                "id": row[0],
                "topic": row[1],
                "created_at": row[2],
                "has_report": bool(row[3])
            }

            for row in rows

        ])


    except Exception:

        logger.exception("History loading failed")

        return jsonify({
            "error": "Could not load research history."
        }), 500


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

    return jsonify({
        "error": "Request payload is too large."
    }), 413


@app.errorhandler(404)
def not_found(error):

    return jsonify({
        "error": "Endpoint not found."
    }), 404


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", 5000)),
        debug=False,
        threaded=True
    )