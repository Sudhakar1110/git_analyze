import frappe


def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1
    context.no_cache = 1
    context.title = "Git Analyzer"

    user = frappe.session.user
    if user == "Administrator":
        filters = {}
    else:
        filters = {"owner": user}

    try:
        context.total_analyses = frappe.db.count("Repo Analysis", filters)
        context.completed_analyses = frappe.db.count("Repo Analysis", {**filters, "status": "Completed"})
        context.in_progress_analyses = frappe.db.count("Repo Analysis", {**filters, "status": "In Progress"})
        context.failed_analyses = frappe.db.count("Repo Analysis", {**filters, "status": "Failed"})
    except Exception:
        context.total_analyses = 0
        context.completed_analyses = 0
        context.in_progress_analyses = 0
        context.failed_analyses = 0

    try:
        context.recent_analyses = frappe.get_all(
            "Repo Analysis",
            filters=filters,
            fields=["name", "repo_name", "github_url", "status", "creation"],
            order_by="creation desc",
            limit=5,
        )
    except Exception:
        context.recent_analyses = []
