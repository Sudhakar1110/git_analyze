import frappe
import json


def after_install():
    create_module_def()
    create_workspace()


def setup_workspace():
    """Run: bench --site ga.ogascale.com execute git_analyze.install.setup_workspace"""
    create_module_def()
    create_workspace()
    print("Done! Run: bench build --force")


def create_module_def():
    if frappe.db.exists("Module Def", "Git Analyzer"):
        return
    frappe.get_doc({
        "doctype": "Module Def",
        "module_name": "Git Analyzer",
        "app_name": "git_analyze",
        "label": "Git Analyzer",
        "color": "#589CFF",
        "icon": "octicon octicon-mark-github",
    }).insert(ignore_permissions=True)
    frappe.db.commit()


def create_workspace():
    if frappe.db.exists("Workspace", "Git Analyzer"):
        frappe.db.set_value("Workspace", "Git Analyzer", {
            "public": 1,
            "is_hidden": 0,
        })
        frappe.db.commit()
        print("Workspace updated to public")
        return

    # Get actual columns of tabWorkspace
    columns = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace`")]
    print("Available columns:", columns)

    now = frappe.utils.now_datetime()

    data = {
        "name": "Git Analyzer",
        "label": "Git Analyzer",
        "title": "Git Analyzer",
        "module": "Git Analyzer",
        "icon": "octicon octicon-mark-github",
        "is_hidden": 0,
        "public": 1,
        "owner": "Administrator",
        "modified_by": "Administrator",
        "creation": now,
        "modified": now,
    }

    links = [
        {"type": "Card Break", "label": "Repo Analysis"},
        {"type": "Link", "link_type": "DocType", "doc_type": "Repo Analysis", "label": "Repo Analysis", "onboard": 1},
        {"type": "Link", "link_type": "DocType", "doc_type": "Analysis History", "label": "Analysis History", "onboard": 0},
        {"type": "Card Break", "label": "Settings"},
        {"type": "Link", "link_type": "DocType", "doc_type": "Analysis Settings", "label": "Analysis Settings", "onboard": 1},
    ]

    shortcuts = [
        {"type": "Shortcut", "link_type": "DocType", "doc_type": "Repo Analysis", "label": "New Repo Analysis", "color": "#589CFF"},
        {"type": "Shortcut", "link_type": "DocType", "doc_type": "Analysis Settings", "label": "Analysis Settings", "color": "#589CFF"},
    ]

    # Only add JSON fields if the columns exist
    if "links" in columns:
        data["links"] = json.dumps(links)
    if "shortcuts" in columns:
        data["shortcuts"] = json.dumps(shortcuts)
    if "category" in columns:
        data["category"] = "Modules"

    cols = ", ".join(["`{}`".format(c) for c in data.keys()])
    placeholders = ", ".join(["%s"] * len(data))

    frappe.db.sql(
        "INSERT INTO `tabWorkspace` ({}) VALUES ({})".format(cols, placeholders),
        list(data.values())
    )
    frappe.db.commit()
    print("Workspace created")
