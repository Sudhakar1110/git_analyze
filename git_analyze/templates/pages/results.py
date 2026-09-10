import frappe


def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1
    context.no_cache = 1

    user = frappe.session.user
    if user == "Administrator":
        filters = {}
    else:
        filters = {"owner": user}

    try:
        analyses = frappe.get_all(
            "Repo Analysis",
            filters=filters,
            fields=["name", "repo_name", "github_url", "status", "creation",
                    "file_count", "groq_model", "purpose", "tech_stack"],
            order_by="creation desc",
            limit=50,
        )
    except Exception:
        analyses = []

    for a in analyses:
        if a.get("status") == "Failed":
            try:
                val = frappe.db.get_value("Repo Analysis", a["name"], "full_output")
                a["full_output"] = val or ""
            except Exception:
                a["full_output"] = ""
        else:
            a["full_output"] = ""

    context.analyses = analyses
