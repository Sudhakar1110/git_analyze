import frappe
from frappe.model.document import Document


class RepoAnalysis(Document):
    def validate(self):
        if self.github_url and "github.com" not in self.github_url:
            frappe.throw("Please enter a valid GitHub URL")
        if self.github_url and not self.repo_name:
            parts = self.github_url.rstrip("/").split("/")
            if len(parts) >= 2:
                self.repo_name = f"{parts[-2]}/{parts[-1]}"
