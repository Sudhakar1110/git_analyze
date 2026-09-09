import frappe

def get_context(context):
    context.no_breadcrumbs = 1
    context.no_header = 1

    try:
        settings = frappe.get_doc("Analysis Settings", "Analysis Settings")
    except Exception:
        settings = None

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
