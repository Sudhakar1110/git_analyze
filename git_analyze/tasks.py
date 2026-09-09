import frappe


def cleanup_old_analyses():
    frappe.db.sql(
        "DELETE FROM `tabAnalysis History` WHERE creation < DATE_SUB(NOW(), INTERVAL 90 DAY)"
    )
    frappe.db.commit()
