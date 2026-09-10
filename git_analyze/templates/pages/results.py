import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    user = frappe.session.user
    if user == "Administrator":
        filters = {}
    else:
        filters = {"owner": user}

    context.analyses = frappe.get_all(
        "Repo Analysis",
        filters=filters,
        fields=["name", "repo_name", "github_url", "status", "creation",
                "file_count", "groq_model", "purpose", "tech_stack"],
        order_by="creation desc",
        limit_page_length=50,
    )
