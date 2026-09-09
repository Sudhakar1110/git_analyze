import frappe


def get_context(context):
    context.no_cache = 1
    context.title = "New Analysis - Git Analyzer"
    context.active_page = "new-analysis"
    context.show_dashboard_sidebar = True
    context.analyses = []
    context.current_user = frappe.session.user
    context.is_authenticated = frappe.session.user != "Guest"
