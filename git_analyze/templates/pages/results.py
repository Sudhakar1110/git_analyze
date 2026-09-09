import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    context.analyses = frappe.get_all(
        "Repo Analysis",
        filters={"owner": frappe.session.user},
        fields=["name", "repo_name", "github_url", "status", "creation",
                "file_count", "groq_model", "purpose", "tech_stack"],
        order_by="creation desc",
        limit_page_length=50,
    )
