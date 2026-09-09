import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    context.history = frappe.get_all(
        "Analysis History",
        fields=["name", "repo_analysis", "request_type", "status",
                "token_usage", "response_time", "timestamp"],
        order_by="timestamp desc",
        limit_page_length=100,
    )
