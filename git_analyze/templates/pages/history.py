import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    analysis_names = frappe.get_all(
        "Repo Analysis",
        filters={"owner": frappe.session.user},
        pluck="name",
    )

    context.history = frappe.get_all(
        "Analysis History",
        filters={"repo_analysis": ["in", analysis_names]} if analysis_names else {},
        fields=["name", "repo_analysis", "request_type", "status",
                "token_usage", "response_time", "timestamp"],
        order_by="timestamp desc",
        limit_page_length=100,
    )
