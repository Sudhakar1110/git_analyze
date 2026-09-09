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
        frappe.db.set_value("Workspace", "Git Analyzer", {"public": 1, "is_hidden": 0})
        frappe.db.commit()
        print("Workspace updated to public")
    else:
        print("ERROR: Workspace 'Git Analyzer' does not exist. Run migrate first.")
        return

    # Get link table columns
    link_cols = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Link`")]
    shortcut_cols = [row[0] for row in frappe.db.sql("SHOW COLUMNS FROM `tabWorkspace Shortcut`")]
    print("Link columns:", link_cols)
    print("Shortcut columns:", shortcut_cols)

    _add_links(link_cols)
    _add_shortcuts(shortcut_cols)


def _add_links(link_cols):
    frappe.db.sql("DELETE FROM `tabWorkspace Link` WHERE parent = 'Git Analyzer'")

    count = frappe.db.sql("SELECT MAX(CAST(SUBSTRING(name, 7) AS UNSIGNED)) FROM `tabWorkspace Link` WHERE name LIKE 'WSLink%%'")[0][0] or 0

    links = [
        {"type": "Card Break", "label": "Repo Analysis"},
        {"type": "Link", "link_type": "DocType", "link_to": "Repo Analysis", "label": "Repo Analysis", "onboard": 1},
        {"type": "Link", "link_type": "DocType", "link_to": "Analysis History", "label": "Analysis History", "onboard": 0},
        {"type": "Card Break", "label": "Settings"},
        {"type": "Link", "link_type": "DocType", "link_to": "Analysis Settings", "label": "Analysis Settings", "onboard": 1},
    ]

    for i, link in enumerate(links):
        count += 1
        name = "WSLink{:04d}".format(count)
        data = {
            "name": name,
            "parent": "Git Analyzer",
            "parentfield": "links",
            "parenttype": "Workspace",
            "idx": i + 1,
            "owner": "Administrator",
            "modified_by": "Administrator",
        }
        for k, v in link.items():
            if k in link_cols:
                data[k] = v

        cols = ", ".join(["`{}`".format(c) for c in data.keys()])
        placeholders = ", ".join(["%s"] * len(data))
        frappe.db.sql(
            "INSERT INTO `tabWorkspace Link` ({}) VALUES ({})".format(cols, placeholders),
            list(data.values())
        )

    frappe.db.commit()
    print("Workspace links added:", len(links))


def _add_shortcuts(shortcut_cols):
    frappe.db.sql("DELETE FROM `tabWorkspace Shortcut` WHERE parent = 'Git Analyzer'")

    count = frappe.db.sql("SELECT MAX(CAST(SUBSTRING(name, 9) AS UNSIGNED)) FROM `tabWorkspace Shortcut` WHERE name LIKE 'WSShortcut%%'")[0][0] or 0

    shortcuts = [
        {"type": "Shortcut", "link_type": "DocType", "link_to": "Repo Analysis", "label": "New Repo Analysis", "color": "#589CFF"},
        {"type": "Shortcut", "link_type": "DocType", "link_to": "Analysis Settings", "label": "Analysis Settings", "color": "#589CFF"},
    ]

    for i, sc in enumerate(shortcuts):
        count += 1
        name = "WSShortcut{:04d}".format(count)
        data = {
            "name": name,
            "parent": "Git Analyzer",
            "parentfield": "shortcuts",
            "parenttype": "Workspace",
            "idx": i + 1,
            "owner": "Administrator",
            "modified_by": "Administrator",
        }
        for k, v in sc.items():
            if k in shortcut_cols:
                data[k] = v

        cols = ", ".join(["`{}`".format(c) for c in data.keys()])
        placeholders = ", ".join(["%s"] * len(data))
        frappe.db.sql(
            "INSERT INTO `tabWorkspace Shortcut` ({}) VALUES ({})".format(cols, placeholders),
            list(data.values())
        )

    frappe.db.commit()
    print("Workspace shortcuts added:", len(shortcuts))
