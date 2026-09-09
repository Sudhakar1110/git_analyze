import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class AnalysisHistory(Document):
    pass


def log_history(repo_analysis_name, request_type, request_payload=None,
                response_preview=None, token_usage=0, response_time=0,
                status="Success", error_message=None):
    history = frappe.get_doc({
        "doctype": "Analysis History",
        "repo_analysis": repo_analysis_name,
        "request_type": request_type,
        "request_payload": str(request_payload) if request_payload else None,
        "response_preview": response_preview[:500] if response_preview else None,
        "token_usage": token_usage,
        "response_time": response_time,
        "status": status,
        "error_message": error_message,
        "timestamp": now_datetime(),
    })
    history.insert(ignore_permissions=True)
    frappe.db.commit()
    return history.name
