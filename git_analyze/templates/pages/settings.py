import frappe

def get_context(context):
    context.active_page = "settings"
    context.no_breadcrumbs = 1
    context.no_header = 1
    context.title = "Settings - Git Analyzer"

    settings = frappe.get_single_doc("Analysis Settings")
    context.settings = settings

    if settings and settings.groq_api_key:
        try:
            context.groq_key = settings.get_password("groq_api_key")
        except Exception:
            context.groq_key = ""
    else:
        context.groq_key = ""

    if settings and settings.github_token:
        try:
            context.github_token = settings.get_password("github_token")
        except Exception:
            context.github_token = ""
    else:
        context.github_token = ""
