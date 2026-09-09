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
    # Check which tables exist
    tables = [r[0] for r in frappe.db.sql("SHOW TABLES LIKE 'tabWorkspace%'")]
    print("Workspace tables:", tables)

    # Get columns of tabWorkspace
    columns = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace`")]
    print("Workspace columns:", columns)

    # Check for child table
    has_link_table = "tabWorkspace Link" in tables
    has_shortcut_table = "tabWorkspace Shortcut" in tables
    print("Has link table:", has_link_table, "Has shortcut table:", has_shortcut_table)

    if frappe.db.exists("Workspace", "Git Analyzer"):
        frappe.db.set_value("Workspace", "Git Analyzer", {"public": 1, "is_hidden": 0})
        frappe.db.commit()
        print("Workspace updated to public")
        # Still need to add links
        _add_workspace_links(has_link_table, has_shortcut_table)
        return

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

    if "category" in columns:
        data["category"] = "Modules"

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

    if "links" in columns:
        data["links"] = json.dumps(links)
    if "shortcuts" in columns:
        data["shortcuts"] = json.dumps(shortcuts)

    cols = ", ".join(["`{}`".format(c) for c in data.keys()])
    placeholders = ", ".join(["%s"] * len(data))

    frappe.db.sql(
        "INSERT INTO `tabWorkspace` ({}) VALUES ({})".format(cols, placeholders),
        list(data.values())
    )
    frappe.db.commit()
    print("Workspace created")

    _add_workspace_links(has_link_table, has_shortcut_table)


def _add_workspace_links(has_link_table, has_shortcut_table):
    if has_link_table:
        # Delete existing links for this workspace
        frappe.db.sql("DELETE FROM `tabWorkspace Link` WHERE parent = 'Git Analyzer'")

        links = [
            {"type": "Card Break", "label": "Repo Analysis", "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 1},
            {"type": "Link", "link_type": "DocType", "doc_type": "Repo Analysis", "label": "Repo Analysis", "onboard": 1, "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 2},
            {"type": "Link", "link_type": "DocType", "doc_type": "Analysis History", "label": "Analysis History", "onboard": 0, "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 3},
            {"type": "Card Break", "label": "Settings", "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 4},
            {"type": "Link", "link_type": "DocType", "doc_type": "Analysis Settings", "label": "Analysis Settings", "onboard": 1, "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 5},
        ]

        # Get actual columns of the link table
        link_cols = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Link`")]
        print("Link table columns:", link_cols)

        for link in links:
            filtered = {k: v for k, v in link.items() if k in link_cols}
            cols = ", ".join(["`{}`".format(c) for c in filtered.keys()])
            placeholders = ", ".join(["%s"] * len(filtered))
            frappe.db.sql(
                "INSERT INTO `tabWorkspace Link` ({}) VALUES ({})".format(cols, placeholders),
                list(filtered.values())
            )
        frappe.db.commit()
        print("Workspace links added:", len(links))

    if has_shortcut_table:
        frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'Git Analyzer'")

        shortcuts = [
            {"type": "Shortcut", "link_type": "DocType", "doc_type": "Repo Analysis", "label": "New Repo Analysis", "color": "#589CFF", "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 1},
            {"type": "Shortcut", "link_type": "DocType", "doc_type": "Analysis Settings", "label": "Analysis Settings", "color": "#589CFF", "parent": "Git Analyzer", "parenttype": "Workspace", "idx": 2},
        ]

        shortcut_cols = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Shortcut`")]
        print("Shortcut table columns:", shortcut_cols)

        for sc in shortcuts:
            filtered = {k: v for k, v in sc.items() if k in shortcut_cols}
            cols = ", ".join(["`{}`".format(c) for c in filtered.keys()])
            placeholders = ", ".join(["%s"] * len(filtered))
            frappe.db.sql(
                "INSERT INTO `tabWorkspace Shortcut` ({}) VALUES ({})".format(cols, placeholders),
                list(filtered.values())
            )
        frappe.db.commit()
        print("Workspace shortcuts added:", len(shortcuts))
