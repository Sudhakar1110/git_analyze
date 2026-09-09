import frappe

def get_context(context):
    context.active_page = "new"
    context.no_breadcrumbs = 1
    context.no_header = 1
    context.title = "New Analysis - Git Analyzer"
