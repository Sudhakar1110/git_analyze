# Git Analyzer — Deployment & User Guide

## Overview

Git Analyzer is a Frappe v15 custom app that performs AI-powered analysis of GitHub repositories. It uses the Groq API to analyze code structure, architecture, dependencies, and workflows, then generates professional reports in multiple formats.

---

## Features

- **AI-Powered Analysis**: Analyzes any public GitHub repository using Groq LLM
- **Multi-Format Export**: Download reports as PDF, Word (DOCX), HTML, JSON, or Markdown
- **Professional Reports**: Cover page, table of contents, numbered sections, complexity scoring
- **Background Processing**: Analysis runs in background threads — no page timeout
- **Real-Time Status**: Live progress updates during analysis
- **Portal UI**: Modern dark sidebar dashboard accessible from the web

---

## Installation

### Prerequisites

- Frappe v15 running on your server
- Site name (e.g., `ga.ogascale.com`)
- SSH access to the server as the `frappe` user

### Step 1: Get the Code

```bash
cd ~/frappe-bench-v15/apps
git clone https://github.com/Sudhakar1110/git_analyze.git
```

### Step 2: Install Dependencies

```bash
cd ~/frappe-bench-v15
bench pip install python-docx
```

### Step 3: Install the App on Your Site

```bash
bench --site ga.ogascale.com install-app git_analyze
```

This runs the `after_install` hook which:
- Creates the Workspace with sidebar links
- Sets up default Analysis Settings

### Step 4: Build Assets

```bash
bench build --app git_analyze
```

### Step 5: Restart

```bash
bench restart
```

---

## Post-Installation Setup

### 1. Access the Portal

Navigate to: `https://ga.ogascale.com/git-analyzer`

You should see the dark sidebar with: Dashboard, New Analysis, Results, History, Settings.

### 2. Configure API Keys

Go to **Settings** page:

1. Enter your **Groq API Key** (starts with `gsk_...`)
   - Get one free at: https://console.groq.com/keys
2. Select the **AI Model** (default: `openai/gpt-oss-20b`)
3. Optionally add a **GitHub Personal Access Token** for private repos
   - Generate at: https://github.com/settings/tokens
4. Click **Save Settings**
5. Click **Test Connection** to verify

### 3. Grant Access to Users

By default, only Administrator can see all analyses. To allow other users:

1. Go to **Desk** → **User** → select the user
2. Under **Roles**, add **Website User**
3. The user can now access the portal and see their own analyses

---

## Usage

### Running an Analysis

1. Click **New Analysis** in the sidebar
2. Enter a GitHub repository URL (e.g., `https://github.com/owner/repo`)
3. Select branch (default: `main`)
4. Choose analysis depth:
   - **Shallow**: Quick scan — up to 50 files
   - **Medium**: Recommended — up to 100 files
   - **Deep**: Full analysis — up to 200 files
5. Click **Start Analysis**
6. Wait for the spinner to complete (typically 1-3 minutes)
7. You'll be redirected to Results automatically

### Viewing Results

Go to **Results** page:
- See all analyses with status, file count, model used
- Use tabs to filter: All, Completed, In Progress, Failed
- Search by repository name or keywords
- Click **Refresh** to reload the page
- In-progress items auto-refresh every 5 seconds

### Exporting Reports

On any **Completed** analysis, click the **Export** button:

A format picker modal appears with 5 options:

| Format | Description | Best For |
|--------|-------------|----------|
| **Markdown** | `.md` file with tables and sections | GitHub READMEs, documentation |
| **PDF** | `.pdf` A4 report with cover page | Sharing with stakeholders, printing |
| **Word** | `.docx` editable document | Editing, adding comments |
| **HTML** | `.html` standalone styled page | Viewing in browser, sharing via email |
| **JSON** | `.json` structured data | Programmatic import, APIs |

All exports include:
- Cover page with repository metadata
- Table of contents
- 10 numbered analysis sections
- Complexity score
- Full AI output appendix

### Understanding the Report Sections

1. **Executive Summary** — What the project does and its purpose
2. **Technology Stack** — Languages, frameworks, tools used
3. **System Architecture** — Overall structure and design patterns
4. **Entry Points & Boot Sequence** — How the application starts
5. **Core Modules & Components** — Key components and their roles
6. **Data Flow & Pipeline** — How data moves through the application
7. **API Endpoints & Contracts** — REST APIs, routes, endpoints
8. **Data Models & Schema** — Database models and schemas
9. **Dependency Matrix** — External libraries and services
10. **Deployment & Setup Guide** — How to run locally

---

## Troubleshooting

### Analysis stays "In Progress" forever

- Check server logs: `tail -f ~/frappe-bench-v15/logs/frappe.log`
- Look for "BG Analysis failed" entries
- Common causes: GitHub rate limiting, Groq API timeout

### Export fails with "python-docx not installed"

```bash
cd ~/frappe-bench-v15
bench pip install python-docx
bench restart
```

### Portal page shows cached/stale data

The app sets `context.no_cache = 1` on all pages. If you still see stale data:
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Clear browser cache

### Groq API errors

- **Rate limit**: Wait a minute and retry, or add a GitHub token in Settings
- **Decommissioned model**: The app auto-replaces old models with `openai/gpt-oss-20b`
- **Connection error**: Check if your server can reach `api.groq.com` on port 443

### Analysis shows "No files found"

- Verify the repository URL is correct
- Check that the branch name is correct (default: `main`)
- Try with a GitHub token for private repos

---

## File Structure

```
git_analyze/
├── api.py                    # All API endpoints (analyze, export, settings)
├── github_fetcher.py         # GitHub API integration
├── groq_client.py            # Groq API integration (uses requests)
├── hooks.py                  # Frappe hooks and route rules
├── install.py                # After-install setup (workspace)
├── tasks.py                  # Scheduled tasks
├── patches.txt               # Frappe patches
├── modules.txt               # Module definition
├── requirements.txt          # Python dependencies
└── templates/
    └── pages/
        ├── dashboard.html    # Dashboard page
        ├── dashboard.py      # Dashboard context
        ├── new-analysis.html # New analysis form
        ├── new-analysis.py   # New analysis context
        ├── results.html      # Results table with export modal
        ├── results.py        # Results context
        ├── history.html      # History page
        ├── history.py        # History context
        ├── settings.html     # Settings form
        └── settings.py       # Settings context
```

---

## API Endpoints

All endpoints are accessible via `POST /api/method/git_analyze.api.{function_name}`

| Endpoint | Description |
|----------|-------------|
| `analyze_repo` | Start a new analysis (github_url, branch, depth) |
| `get_analysis_status` | Poll analysis status |
| `get_analysis_results` | Get full results for an analysis |
| `save_settings` | Save API keys and preferences |
| `test_groq_connection` | Test Groq API connectivity |
| `ask_followup` | Ask follow-up questions about an analysis |
| `export_as_markdown` | Export as Markdown |
| `export_as_html` | Export as HTML |
| `export_as_pdf` | Export as PDF |
| `export_as_docx` | Export as Word document |
| `export_as_json` | Export as JSON |

---

## Updating the App

```bash
cd ~/frappe-bench-v15/apps/git_analyze
git pull origin main
bench build --app git_analyze
bench restart
```

---

## License

MIT
