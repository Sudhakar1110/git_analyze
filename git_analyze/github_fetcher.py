import frappe
import requests
import re
from typing import Dict, List, Optional, Tuple


class GitHubFetcher:
    GITHUB_API_BASE = "https://api.github.com"
    GITHUB_RAW_BASE = "https://raw.githubusercontent.com"

    KEY_FILES = [
        "README.md", "package.json", "setup.py", "pyproject.toml",
        "requirements.txt", "Makefile", "Dockerfile", "docker-compose.yml",
        "config.py", "settings.py", "manage.py", "app.py", "main.py",
        "index.py", "server.js", "app.js", "index.js",
    ]

    def __init__(self, github_token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Git-Analyzer-Frappe",
        })
        if github_token:
            self.session.headers["Authorization"] = f"token {github_token}"

    def parse_github_url(self, url: str) -> Tuple[str, str]:
        url = url.strip().rstrip("/")
        match = re.search(r"github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
        if match:
            return match.group(1), match.group(2)
        frappe.throw(f"Invalid GitHub URL: {url}")

    def get_file_tree(self, owner: str, repo: str, branch: str = "main",
                      max_files: int = 50) -> List[Dict]:
        url = f"{self.GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
        try:
            response = self.session.get(url, params={"recursive": 1})
            response.raise_for_status()
            return [
                {"path": item["path"], "size": item.get("size", 0), "type": item["type"]}
                for item in response.json().get("tree", [])
                if item["type"] == "blob"
            ]
        except requests.exceptions.RequestException as e:
            frappe.throw(f"Failed to fetch repository tree: {str(e)}")

    def should_skip_file(self, path: str) -> bool:
        skip_dirs = [
            "node_modules", "venv", "__pycache__", ".git", "dist",
            "build", ".next", ".nuxt", "vendor", "bower_components",
        ]
        for part in path.split("/")[:-1]:
            if part in skip_dirs:
                return True
        skip_ext = [
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff",
            ".woff2", ".ttf", ".eot", ".pdf", ".zip", ".tar", ".gz",
            ".rar", ".pyc", ".pyo", ".pyd", ".so", ".dll",
        ]
        if any(path.lower().endswith(ext) for ext in skip_ext):
            return True
        if ".min." in path:
            return True
        return False

    def get_file_content(self, owner: str, repo: str, path: str,
                         branch: str = "main") -> Optional[str]:
        url = f"{self.GITHUB_RAW_BASE}/{owner}/{repo}/{branch}/{path}"
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException:
            return None

    def fetch_repository(self, github_url: str, branch: str = "main",
                         max_files: int = 50,
                         skip_patterns: Optional[List[str]] = None,
                         **kwargs) -> Dict:
        owner, repo = self.parse_github_url(github_url)
        files = self.get_file_tree(owner, repo, branch, max_files)
        filtered = [f for f in files if not self.should_skip_file(f["path"])]

        key_files = [
            f for f in filtered
            if any(f["path"].endswith(k) for k in self.KEY_FILES)
        ]
        other_files = [f for f in filtered if f not in key_files]
        files_to_fetch = (key_files + other_files)[:max_files]

        file_contents = {}
        for f in files_to_fetch:
            content = self.get_file_content(owner, repo, f["path"], branch)
            if content:
                file_contents[f["path"]] = content

        structure = "\n".join([f["path"] for f in filtered[:100]])

        return {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "total_files": len(files),
            "analyzed_files": len(file_contents),
            "structure": structure,
            "files": file_contents,
        }
