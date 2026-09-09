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
            "title": "Git Analyzer",
        })
        frappe.db.commit()
        print("Workspace updated to public")
        return

    now = frappe.utils.now_datetime()
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
    frappe.db.sql("""
        INSERT INTO `tabWorkspace`
        (name, label, title, module, icon, is_hidden, public, owner, modified_by, creation, modified, links, shortcuts)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'Administrator', 'Administrator', %s, %s, %s, %s)
    """, ('Git Analyzer', 'Git Analyzer', 'Git Analyzer', 'Git Analyzer', 'octicon octicon-mark-github', 0, 1, now, now, json.dumps(links), json.dumps(shortcuts)))
    frappe.db.commit()
    print("Workspace created")
