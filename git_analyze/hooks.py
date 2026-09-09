app_name = "git_analyze"
app_title = "Git Analyzer"
app_publisher = "Git Analyzer"
app_description = "Analyze GitHub repositories using Groq API"
app_email = "admin@example.com"
app_license = "MIT"

after_install = "git_analyze.install.after_install"

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


