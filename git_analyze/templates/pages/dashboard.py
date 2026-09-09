import frappe

def get_context(context):
    context.active_page = "dashboard"
    context.no_breadcrumbs = 1
    context.no_header = 1

    total = frappe.db.count("Repo Analysis")
    completed = frappe.db.count("Repo Analysis", {"status": "Completed"})
    in_progress = frappe.db.count("Repo Analysis", {"status": "In Progress"})
    failed = frappe.db.count("Repo Analysis", {"status": "Failed"})

    context.total_analyses = total
    context.completed_analyses = completed
    context.in_progress_analyses = in_progress
    context.failed_analyses = failed

    context.recent_analyses = frappe.get_all(
        "Repo Analysis",
        fields=["name", "repo_name", "github_url", "status", "creation"],
        order_by="creation desc",
        limit_page_length=5,
    )

    context.title = "Git Analyzer"
