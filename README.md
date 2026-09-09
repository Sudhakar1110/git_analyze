# Git Analyzer - Frappe Custom App

Analyze GitHub repositories using Groq API and display workflow analysis within ERPNext v15.

## Features

- **Repository Analysis**: Analyze GitHub repositories for purpose, tech stack, architecture, and more
- **Groq API Integration**: Uses Groq's free tier with llama3-8b-8192 model
- **Follow-up Questions**: Ask additional questions about analyzed repositories
- **Export Options**: Save analysis to ERPNext or export as Markdown
- **Multi-language Support**: Output analysis in multiple languages

## Installation

### Prerequisites

- Frappe Framework v15
- ERPNext v15
- Python 3.10+
- Groq API key (free tier available)

### Install the App

```bash
# Navigate to your frappe-bench directory
cd frappe-bench

# Get the app
bench get-app https://github.com/Sudhakar1110/git_analyze.git

# Install the app on your site
bench --site your-site.local install-app git_analyze

# Run migrations
bench --site your-site.local migrate

# Build assets
bench build
```

## Configuration

1. Go to **Analysis Settings** in your Frappe desk
2. Enter your **Groq API Key** (get one free at https://console.groq.com)
3. Select your preferred **Groq Model** (default: llama3-8b-8192)
4. Configure **Max Files Limit** (default: 50)
5. Set **Output Language** (default: English)
6. Optionally add a **GitHub Token** for private repositories

## Usage

### Analyze a Repository

1. Navigate to **Repo Analyzer** page in Frappe desk
2. Enter a GitHub repository URL (e.g., `https://github.com/frappe/frappe`)
3. Enter the branch name (default: main)
4. Click **Analyze**
5. View the analysis results in tabbed sections

### Ask Follow-up Questions

1. After analyzing a repository, scroll to the **Follow-up Question** section
2. Enter your question about the repository
3. Click **Ask**
4. View the AI-generated response

### Export Analysis

- **Save to ERPNext**: Analysis is automatically saved as a Repo Analysis document
- **Export as Markdown**: Download the analysis as a .md file

## DocTypes

### Repo Analysis
Stores GitHub URL, branch, analysis status, and full workflow output including:
- Project Purpose
- Tech Stack
- Architecture
- Entry Points
- Key Modules
- Data Flow
- API Endpoints
- Database Models
- Dependencies
- How to Run

### Analysis Settings (Singleton)
Configuration for the Groq API integration:
- Groq API Key
- Model Selection
- Max Files Limit
- Output Language
- GitHub Token (optional)
- Skip Patterns

### Analysis History
Logs all API requests and token usage for tracking and debugging.

## API Methods

The following whitelisted API methods are available:

- `analyze_repo(github_url, branch)` - Analyze a repository
- `ask_followup(repo_analysis_name, question)` - Ask follow-up question
- `export_as_markdown(repo_analysis_name)` - Export as Markdown
- `get_analysis_status(repo_analysis_name)` - Get analysis status
- `get_analysis_results(repo_analysis_name)` - Get full results
- `get_analysis_history(repo_analysis_name)` - Get API history

## License

MIT License
