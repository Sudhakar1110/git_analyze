app_name = "git_analyze"
app_title = "Git Analyzer"
app_publisher = "Git Analyzer"
app_description = "Analyze GitHub repositories using Groq API"
app_email = "admin@example.com"
app_license = "MIT"

after_install = "git_analyze.install.after_install"

app_include_css = "/assets/git_analyze/css/git_analyzer.css"
app_include_js = "/assets/git_analyze/js/git_analyzer.js"

doc_events = {
    "Repo Analysis": {
        "on_submit": "git_analyze.api.run_analysis_on_submit",
    },
}

scheduler_events = {
    "hourly": [
        "git_analyze.tasks.cleanup_old_analyses",
    ],
}

website_route_rules = [
    {"from_route": "/git-analyzer", "to_route": "dashboard"},
    {"from_route": "/git-analyzer/new", "to_route": "new-analysis"},
    {"from_route": "/git-analyzer/results", "to_route": "results"},
    {"from_route": "/git-analyzer/history", "to_route": "history"},
    {"from_route": "/git-analyzer/settings", "to_route": "settings"},
]
