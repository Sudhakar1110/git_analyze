# Git Analyzer

## Intelligent Repository Analysis Platform

An AI-powered Frappe application that analyzes GitHub repositories, generates comprehensive technical reports, and exports them in professional formats.

---

## Table of Contents

- [Application Overview](#application-overview)
- [Workflow — Start to End](#workflow--start-to-end)
- [Features](#features)
- [Architecture](#architecture)
- [Export Formats](#export-formats)
- [User Roles & Permissions](#user-roles--permissions)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

---

## Application Overview

Git Analyzer connects to GitHub, fetches repository files, sends them to an AI model via the Groq API, and produces a structured technical analysis covering architecture, dependencies, data flow, and deployment instructions.

```
┌─────────────────────────────────────────────────────────────────┐
│                        GIT ANALYZER                             │
│                  Repository Analysis Platform                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│   │  GitHub   │───▶│   Groq   │───▶│ Frappe   │───▶│ Export  │ │
│   │  API      │    │   API    │    │ Database │    │ Engine  │ │
│   └──────────┘    └──────────┘    └──────────┘    └─────────┘ │
│        │               │               │               │       │
│        ▼               ▼               ▼               ▼       │
│   Fetch Files    AI Analysis    Store Results    PDF/DOCX/HTML │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Workflow — Start to End

### Phase 1: User Initiates Analysis

```
 User Action                     System Response
 ─────────────                   ───────────────
 1. User opens New Analysis  ──▶  Form loads with URL input,
    page                          branch selector, depth picker

 2. User enters GitHub URL   ──▶  System validates URL format
    e.g. github.com/owner/repo    (must contain github.com)

 3. User selects branch      ──▶  Default: main
    (main, develop, etc.)

 4. User selects depth       ──▶  Shallow: 50 files
                                  Medium:  100 files
                                  Deep:    200 files

 5. User clicks "Start       ──▶  Request sent to server
    Analysis"                      via fetch API with CSRF token
```

### Phase 2: System Creates Analysis Record

```
┌─────────────────────────────────────────────────────────────┐
│ 1. validate_github_url()                                    │
│    ├── Check URL contains "github.com"                      │
│    ├── Parse owner and repo name from URL                   │
│    └── Throw error if invalid                               │
│                                                             │
│ 2. load_settings()                                          │
│    ├── Fetch Analysis Settings singleton                    │
│    ├── Verify Groq API key exists                           │
│    └── Throw error if not configured                        │
│                                                             │
│ 3. create_record()                                          │
│    ├── Create "Repo Analysis" document                      │
│    ├── Set status = "In Progress"                           │
│    ├── Set owner = current logged-in user                   │
│    ├── Save to database                                     │
│    └── Return analysis ID to frontend                       │
│                                                             │
│ 4. start_background_thread()                                │
│    ├── Initialize Frappe context in new thread              │
│    ├── Connect to database                                  │
│    └── Begin analysis pipeline                              │
└─────────────────────────────────────────────────────────────┘
```

### Phase 3: Frontend Polls for Status

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Spinner Overlay                                           │
│   ┌─────────────────────────────┐                           │
│   │      ⟳ Analyzing...        │                           │
│   │                             │                           │
│   │  "Fetching repository       │  ◀── Status text updates  │
│   │   files..."                 │      from DB every 3s     │
│   │                             │                           │
│   └─────────────────────────────┘                           │
│                                                             │
│   Every 3 seconds:                                          │
│   ├── POST /api/method/git_analyze.api.get_analysis_status  │
│   ├── Check status field in database                        │
│   ├── Update spinner text with progress                     │
│   └── If "Completed" → redirect to Results page             │
│       If "Failed" → show error, redirect after 3s           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Phase 4: Background Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND THREAD EXECUTION                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Step 1: FETCH REPOSITORY FILES                                    │
│  ─────────────────────────────                                     │
│  ├── Connect to GitHub API (api.github.com)                        │
│  ├── GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1     │
│  ├── Parse file tree → filter out:                                  │
│  │   ├── node_modules, venv, __pycache__, .git, dist, build       │
│  │   ├── Binary files (.png, .jpg, .pdf, .zip, etc.)              │
│  │   └── Minified files (.min.js, .min.css)                        │
│  ├── Prioritize key files:                                         │
│  │   ├── README.md, package.json, setup.py, pyproject.toml        │
│  │   ├── requirements.txt, Dockerfile, docker-compose.yml         │
│  │   ├── manage.py, app.py, main.py, index.js                     │
│  │   └── config.py, settings.py                                    │
│  ├── Fetch file contents (raw.githubusercontent.com)               │
│  ├── Limit: {depth} files max                                      │
│  └── Update status: "Fetching repository files..."                 │
│                                                                     │
│  Step 2: PREPARE ANALYSIS                                          │
│  ────────────────────────                                          │
│  ├── Build file structure string (directory tree)                  │
│  ├── Build file contents string (code snippets)                    │
│  ├── Truncate: structure ≤ 3000 chars, contents ≤ 15000 chars     │
│  ├── Limit: 20 files, 5000 chars per file                          │
│  ├── Update status: "Analyzing {N} files with AI..."              │
│  └── Initialize Groq API client                                    │
│                                                                     │
│  Step 3: AI ANALYSIS                                               │
│  ─────────────────                                                 │
│  ├── POST to api.groq.com/openai/v1/chat/completions              │
│  ├── Model: openai/gpt-oss-20b (or configured model)              │
│  ├── System prompt: "You are an expert software engineer..."       │
│  ├── User prompt: Full analysis request with:                      │
│  │   ├── Repository name and branch                                │
│  │   ├── File structure                                            │
│  │   ├── File contents                                             │
│  │   └── Request for 10 specific sections                          │
│  ├── Timeout: 120 seconds                                          │
│  └── Parse AI response into structured sections                    │
│                                                                     │
│  Step 4: PARSE & STORE RESULTS                                     │
│  ─────────────────────────────                                     │
│  ├── Extract 10 sections from AI output:                           │
│  │   ├── Executive Summary (purpose)                               │
│  │   ├── Technology Stack (tech_stack)                             │
│  │   ├── System Architecture (architecture)                        │
│  │   ├── Entry Points (entry_points)                               │
│  │   ├── Core Modules (key_modules)                                │
│  │   ├── Data Flow (data_flow)                                     │
│  │   ├── API Endpoints (api_endpoints)                             │
│  │   ├── Data Models (database_models)                             │
│  │   ├── Dependencies (dependencies)                               │
│  │   └── Deployment Guide (how_to_run)                             │
│  ├── Calculate analysis time                                       │
│  ├── Update status = "Completed"                                   │
│  ├── Save all fields to database                                   │
│  └── Commit transaction                                            │
│                                                                     │
│  ERROR HANDLING:                                                    │
│  ├── If any step fails → status = "Failed"                         │
│  ├── Store error message in full_output field                      │
│  ├── Log error to frappe.log_error()                               │
│  └── Cleanup: close DB connection, destroy Frappe context          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 5: Results Display

```
┌─────────────────────────────────────────────────────────────┐
│  Results Page                                               │
│  ─────────────                                              │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Repository        │ Status    │ Files │ Model │ Date │    │
│  ├───────────────────┼───────────┼───────┼───────┼──────┤    │
│  │ owner/repo-name   │ Completed │  42   │ gpt.. │ Sep  │    │
│  │                   │           │       │       │      │    │
│  │ owner/other-repo  │ In Progress│  --  │ gpt.. │ Sep  │    │
│  │                   │  ⟳        │       │       │      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Tabs: All | Completed | In Progress | Failed               │
│  Search: [________________] 🔍                              │
│                                                             │
│  Actions per row:                                           │
│  ├── [Export] button (only for Completed)                   │
│  └── Auto-refresh for In Progress items (every 5s)          │
│                                                             │
│  Export Modal:                                              │
│  ┌─────────────────────────────────────────┐                │
│  │  Export Analysis                        │                │
│  │                                         │                │
│  │  ┌──────┐ ┌──────┐ ┌──────┐            │                │
│  │  │  📝  │ │  📄  │ │  📑  │            │                │
│  │  │  MD  │ │ PDF  │ │ DOCX │            │                │
│  │  └──────┘ └──────┘ └──────┘            │                │
│  │  ┌──────┐ ┌──────┐                     │                │
│  │  │  🌐  │ │  📊  │                     │                │
│  │  │ HTML │ │ JSON │                     │                │
│  │  └──────┘ └──────┘                     │                │
│  │                                         │                │
│  │  [Cancel]              [Download]       │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Phase 6: Report Export

```
┌─────────────────────────────────────────────────────────────┐
│  PROFESSIONAL REPORT STRUCTURE                               │
│  ─────────────────────────────                               │
│                                                             │
│  ┌─────────────────────────────────────────┐                │
│  │          COVER PAGE                     │                │
│  │  ┌─────────────────────────────────┐    │                │
│  │  │  GIT ANALYZER                   │    │                │
│  │  │  Repository Analysis Report     │    │                │
│  │  │                                 │    │                │
│  │  │  owner/repo-name — main branch  │    │                │
│  │  │                                 │    │                │
│  │  │  ┌─────┐ ┌─────┐ ┌─────┐       │    │                │
│  │  │  │ 42  │ │ gpt │ │ 3.2k│       │    │                │
│  │  │  │files│ │model│ │tokens│      │    │                │
│  │  │  └─────┘ └─────┘ └─────┘       │    │                │
│  │  └─────────────────────────────────┘    │                │
│  └─────────────────────────────────────────┘                │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────┐                │
│  │       TABLE OF CONTENTS                 │                │
│  │  01. Executive Summary          ▸       │                │
│  │  02. Technology Stack           ▸       │                │
│  │  03. System Architecture        ▸       │                │
│  │  04. Entry Points               ▸       │                │
│  │  05. Core Modules               ▸       │                │
│  │  06. Data Flow                  ▸       │                │
│  │  07. API Endpoints              ▸       │                │
│  │  08. Data Models                ▸       │                │
│  │  09. Dependencies               ▸       │                │
│  │  10. Deployment Guide           ▸       │                │
│  └─────────────────────────────────────────┘                │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────┐                │
│  │       10 NUMBERED SECTIONS              │                │
│  │  ┌─────────────────────────────────┐    │                │
│  │  │ [01] Executive Summary          │    │                │
│  │  │ ────────────────────────────────│    │                │
│  │  │ [analysis content here]         │    │                │
│  │  │ [with formatted text, bullets,  │    │                │
│  │  │  code blocks, tables]           │    │                │
│  │  └─────────────────────────────────┘    │                │
│  │  ┌─────────────────────────────────┐    │                │
│  │  │ [02] Technology Stack           │    │                │
│  │  │ ────────────────────────────────│    │                │
│  │  │ [Python] [React] [PostgreSQL]   │    │                │
│  │  │ [Docker] [Redis] [Nginx]        │    │                │
│  │  └─────────────────────────────────┘    │                │
│  │  ... (sections 03-10)                   │                │
│  └─────────────────────────────────────────┘                │
│                         │                                   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────┐                │
│  │       APPENDIX                          │                │
│  │  Full AI Analysis Output                │                │
│  │  (raw markdown in collapsible block)    │                │
│  └─────────────────────────────────────────┘                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Features

### Core Analysis Features

| Feature | Description |
|---------|-------------|
| **AI-Powered Analysis** | Uses Groq LLM to analyze code structure, architecture, and patterns |
| **GitHub Integration** | Fetches files directly from GitHub API — no clone required |
| **Smart File Selection** | Prioritizes key files (README, package.json, config) over bulk files |
| **Binary Filtering** | Automatically skips images, fonts, compiled files, minified code |
| **Configurable Depth** | Shallow (50), Medium (100), Deep (200) file limits |
| **Branch Selection** | Analyze any branch — main, develop, feature branches |
| **Token Tracking** | Records tokens consumed per analysis |
| **Complexity Scoring** | Auto-calculated 0-100 score based on file count, content depth |

### Report Generation Features

| Feature | Description |
|---------|-------------|
| **Cover Page** | Professional gradient header with repo name and metadata cards |
| **Table of Contents** | Numbered section list with clickable anchors |
| **10 Analysis Sections** | Structured sections with numbered badges |
| **Tech Stack Badges** | Parsed technologies displayed as colored pills |
| **Complexity Score** | Visual score indicator based on analysis metrics |
| **Full Output Appendix** | Complete raw AI output in collapsible block |
| **Multiple Formats** | PDF, DOCX, HTML, JSON, Markdown — one click download |

### Export Format Details

| Format | Features |
|--------|----------|
| **PDF** | A4 page size, zero margins (full bleed), cover page, section breaks, styled headings |
| **DOCX** | Cover page, TOC page, section headings, list bullets, monospace appendix, page breaks |
| **HTML** | Standalone styled page, gradient header, meta cards, responsive layout, tech badges |
| **JSON** | Structured data with report metadata, repository info, analysis metrics, all sections |
| **Markdown** | Metadata table, numbered TOC, section headers, collapsible appendix |

### User Interface Features

| Feature | Description |
|---------|-------------|
| **Dark Sidebar Navigation** | Fixed sidebar with green accent, active state indicators |
| **Dashboard** | Stats cards (total, completed, in-progress, failed) + recent analyses |
| **New Analysis Form** | URL input, branch selector, depth picker, optional questions |
| **Live Progress Spinner** | Real-time status updates during analysis ("Fetching files...", "Analyzing...") |
| **Results Table** | Sortable, searchable, filterable by status tabs |
| **Auto-Refresh** | In-progress items poll every 5 seconds, completed items trigger page reload |
| **Format Picker Modal** | 5 format cards with selection highlighting and download button |
| **Toast Notifications** | Success/error messages with slide-in animation |
| **Export Blob Download** | Direct browser download — no server file storage needed |

### Backend Features

| Feature | Description |
|---------|-------------|
| **Background Threading** | Analysis runs in daemon thread — no HTTP timeout |
| **Thread-Safe HTTP** | Fresh requests.Session per thread — no connection sharing |
| **Frappe Context Init** | Proper `frappe.init()` / `frappe.connect()` / `frappe.destroy()` lifecycle |
| **Owner-Based Filtering** | Users see only their analyses; Administrator sees all |
| **Page Cache Bypass** | `context.no_cache = 1` on all portal pages |
| **CSRF Protection** | All API calls include Frappe CSRF token |
| **Error Handling** | Try/catch at every layer, error stored in DB, logged to frappe.log_error() |
| **Model Auto-Replacement** | Decommissioned Groq models auto-replaced with current default |

### Settings & Configuration

| Feature | Description |
|---------|-------------|
| **Groq API Key** | Encrypted storage via `get_password()` |
| **Model Selection** | Choose from available Groq models (GPT OSS 20B/120B, Qwen) |
| **Max Files Override** | Global limit on files per analysis |
| **Output Language** | English, Spanish, French, German, Chinese, Japanese |
| **GitHub Token** | Optional PAT for private repository access |
| **Test Connection** | One-click API connectivity verification |

### Security Features

| Feature | Description |
|---------|-------------|
| **Permission Control** | System Manager + Website User roles on all doctypes |
| **Owner Isolation** | Non-admin users only see their own analyses |
| **API Key Masking** | Password fields masked in settings form |
| **CSRF Tokens** | All state-changing API calls require valid token |
| **No Server File Storage** | Exports generate in-memory, download directly to browser |

### Workflow Summary

```
┌────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│   USER     │     │   SERVER   │     │   GITHUB   │     │   GROQ     │
│            │     │            │     │    API     │     │    API     │
└─────┬──────┘     └─────┬──────┘     └─────┬──────┘     └─────┬──────┘
      │                  │                  │                  │
      │  1. Submit URL   │                  │                  │
      │─────────────────▶│                  │                  │
      │                  │                  │                  │
      │  2. Create doc   │                  │                  │
      │  3. Start thread │                  │                  │
      │◀─────────────────│                  │                  │
      │                  │                  │                  │
      │  4. Poll status  │  5. Fetch tree   │                  │
      │─────────────────▶│─────────────────▶│                  │
      │                  │                  │                  │
      │                  │  6. Get files    │                  │
      │                  │─────────────────▶│                  │
      │                  │                  │                  │
      │                  │  7. Send to AI   │                  │
      │                  │─────────────────────────────────────▶
      │                  │                  │                  │
      │                  │  8. AI response  │                  │
      │                  │◀─────────────────────────────────────
      │                  │                  │                  │
      │                  │  9. Store results│                  │
      │                  │  10. Status=Done │                  │
      │                  │                  │                  │
      │  11. Redirect    │                  │                  │
      │◀─────────────────│                  │                  │
      │                  │                  │                  │
      │  12. View results│                  │                  │
      │─────────────────▶│                  │                  │
      │                  │                  │                  │
      │  13. Click Export│                  │                  │
      │─────────────────▶│                  │                  │
      │                  │  14. Generate    │                  │
      │                  │      report      │                  │
      │  15. Download    │                  │                  │
      │◀─────────────────│                  │                  │
      │                  │                  │                  │
```

---

## Architecture

### Doctypes

| Doctype | Type | Purpose |
|---------|------|---------|
| **Repo Analysis** | Standard | Stores each analysis result (autoname: ANALYSIS-{####}) |
| **Analysis Settings** | Singleton | API keys, model selection, preferences |
| **Analysis History** | Standard | Audit log of all API interactions |

### Portal Pages

| Page | Route | Purpose |
|------|-------|---------|
| Dashboard | `/git-analyzer/dashboard` | Stats overview, recent analyses |
| New Analysis | `/git-analyzer/new-analysis` | Submit URL, start analysis |
| Results | `/git-analyzer/results` | View all analyses, export |
| History | `/git-analyzer/history` | API call audit log |
| Settings | `/git-analyzer/settings` | Configure API keys, preferences |

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `analyze_repo` | POST | Create analysis, start background thread |
| `get_analysis_status` | POST | Poll status during analysis |
| `get_analysis_results` | POST | Fetch full results |
| `save_settings` | POST | Save API keys and preferences |
| `test_groq_connection` | POST | Verify Groq API connectivity |
| `ask_followup` | POST | Ask follow-up questions |
| `export_as_markdown` | POST | Generate Markdown report |
| `export_as_html` | POST | Generate HTML report |
| `export_as_pdf` | POST | Generate PDF report |
| `export_as_docx` | POST | Generate Word document |
| `export_as_json` | POST | Generate JSON data |

---

## Configuration

### Analysis Settings Singleton

| Field | Type | Description |
|-------|------|-------------|
| `groq_api_key` | Password | Groq API key (encrypted) |
| `groq_model` | Select | AI model for analysis |
| `max_files_limit` | Int | Default max files per analysis |
| `output_language` | Select | Language for generated reports |
| `github_token` | Password | GitHub PAT for private repos |

### Available Groq Models

| Model | Description |
|-------|-------------|
| `openai/gpt-oss-20b` | Fast, cost-effective (default) |
| `openai/gpt-oss-120b` | More powerful, slower |
| `qwen/qwen3.6-27b` | Qwen 3.6 27B |
| `qwen/qwen3.8-27b` | Qwen 3.8 27B |

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Analysis stays "In Progress" | Background thread failed | Check `frappe.log_error()` for "BG Analysis failed" |
| Export fails with "python-docx not installed" | Missing dependency | Install: `bench pip install python-docx` |
| Portal shows stale data | Browser cache | Hard refresh: Ctrl+Shift+R |
| "No files found" error | Wrong URL or branch | Verify URL and branch name |
| Groq API connection error | Firewall/network | Ensure port 443 to api.groq.com is open |
| Rate limit error | Too many requests | Wait 1 minute, or add GitHub token |
| "Decommissioned model" error | Old model selected | App auto-replaces with default model |

---

## License

MIT
