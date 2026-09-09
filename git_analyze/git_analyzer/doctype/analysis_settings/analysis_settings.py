import frappe
from frappe.model.document import Document


class AnalysisSettings(Document):
    def get_groq_api_key(self):
        return self.get_password("groq_api_key") if self.groq_api_key else None

    def get_github_token(self):
        return self.get_password("github_token") if self.github_token else None

    def get_skip_patterns(self):
        return ["node_modules", "venv", "__pycache__", ".git", "dist", "build", ".next"]
