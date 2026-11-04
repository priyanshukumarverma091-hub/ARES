# ARES — AI Research & Exploration System

### Don't just search. Discover.

ARES is an AI-powered research automation system designed to transform research questions into structured, evidence-driven insights.

Instead of manually searching through multiple websites, collecting articles, extracting information, and preparing reports, ARES brings these stages together into a unified research workflow.

It discovers relevant sources, extracts meaningful content, uses AI to synthesize information, and generates structured research reports.

---

## Overview

Research is more than finding information. It involves discovering reliable sources, understanding different perspectives, connecting evidence, and presenting meaningful conclusions.

ARES aims to simplify this process through an automated research pipeline.

**The core idea:**

Turn a research question into an organized research report with traceable sources.

## Research Pipeline

ARES follows a four-stage research workflow:

| Stage | Process    | Description                                                       |
| ----- | ---------- | ----------------------------------------------------------------- |
| 01    | Discovery  | Finds relevant web and academic sources.                          |
| 02    | Extraction | Collects and extracts meaningful article content.                 |
| 03    | Analysis   | Uses AI to synthesize information and generate research insights. |
| 04    | Reporting  | Generates structured PDF research reports.                        |

## Key Features

* **Automated Research:** Initiate research using a natural-language topic.
* **Web Discovery:** Search for relevant information across online sources.
* **Academic Discovery:** Include academic research sources in the discovery process.
* **Content Extraction:** Extract readable content from discovered webpages.
* **AI-Powered Analysis:** Generate structured research findings using an LLM.
* **Source Transparency:** Display discovered sources alongside research findings.
* **Research Statistics:** Present corpus-level statistics for collected research material.
* **PDF Report Generation:** Export research findings into downloadable PDF reports.
* **Research History:** Maintain a record of previous research activities.
* **Persistent Storage:** Use SQLite for storing research-related data.

## Technology Stack

| Technology               | Purpose                                |
| ------------------------ | -------------------------------------- |
| Python                   | Core application and research pipeline |
| Flask                    | Web application and API layer          |
| OpenAI SDK               | AI-powered research synthesis          |
| DuckDuckGo Search (DDGS) | Web discovery                          |
| Trafilatura              | Web content extraction                 |
| Playwright               | Browser automation                     |
| SQLite                   | Persistent data storage                |
| ReportLab                | PDF report generation                  |
| HTML, CSS, JavaScript    | Frontend interface                     |
| Vercel                   | Deployment configuration               |

## Project Structure

```text
ARES/
│
├── app.py              # Flask web application and interface
├── main.py             # Core research engine
├── requirements.txt    # Python dependencies
├── vercel.json         # Vercel deployment configuration
├── .gitignore          # Git exclusions
│
├── reports/            # Generated research reports
├── logs/               # Application logs
└── ares.db             # Local research database
```

*Note: Runtime directories and the local database are generated during execution and are not committed to the repository.*

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/priyanshukumarverma091-hub/ARES.git
```

```bash
cd ARES
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root.

Add the required configuration:

```env
OPENAI_API_KEY=your_api_key_here
```

Keep your API keys private. Never commit your `.env` file.

### 5. Run ARES

```bash
python app.py
```

Open the local application in your browser using the address displayed by Flask.

## How to Use

1. Open the ARES research interface.
2. Enter a research topic or question.
3. Start the research process.
4. Allow ARES to discover and extract relevant information.
5. Review the generated research findings.
6. Explore the discovered sources.
7. Download the research report as a PDF.

## Design Philosophy

ARES is built around three principles:

**Evidence First**
Research findings should be supported by discoverable sources.

**Structured Understanding**
Information should be organized into meaningful insights rather than presented as disconnected search results.

**Research Automation**
Reduce repetitive research work so more time can be spent understanding, questioning, and investigating ideas.

## Current Development

ARES is an actively developing research automation project.

The focus is on improving source discovery, extraction quality, research synthesis, and report generation.

## Responsible Use

ARES is intended for research, learning, and information exploration.

AI-generated findings should be independently verified. Users should consult original sources before relying on research conclusions.

## Author

**Priyanshu Kumar Verma**

AI/ML Researcher | Deep Learning | Generative AI

GitHub: [@priyanshukumarverma091-hub](https://github.com/priyanshukumarverma091-hub)

---

<p align="center">
  <strong>ARES — Research with evidence. Think independently.</strong>
</p>
