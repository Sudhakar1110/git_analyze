import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    user = frappe.session.user
    if user == "Administrator":
        analysis_names = frappe.get_all("Repo Analysis", pluck="name")
    else:
        analysis_names = frappe.get_all(
            "Repo Analysis",
            filters={"owner": user},
            pluck="name",
        )

    if analysis_names:
        context.history = frappe.get_all(
            "Analysis History",
            filters={"repo_analysis": ["in", analysis_names]},
            fields=["name", "repo_analysis", "request_type", "status",
                    "token_usage", "response_time", "timestamp"],
            order_by="timestamp desc",
            limit_page_length=100,
        )
    else:
        context.history = []
