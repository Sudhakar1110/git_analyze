import frappe
from frappe import _
import time
from frappe.utils import now_datetime, cint


def has_permission(doc, user):
    if user == "Administrator":
        return True
    return frappe.has_permission(doc.doctype, "read", user=user)


def run_analysis_on_submit(doc, method):
    pass


@frappe.whitelist()
def analyze_repo(github_url, branch="main", depth="medium", questions=""):
    if not github_url:
        frappe.throw(_("GitHub URL is required"))
    if "github.com" not in github_url:
        frappe.throw(_("Please enter a valid GitHub URL"))

    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")
    if not settings.groq_api_key:
        frappe.throw(_("Please configure Groq API key in Analysis Settings"))

    max_files = {"shallow": 50, "medium": 100, "deep": 200}.get(depth, 100)

    from git_analyze.github_fetcher import GitHubFetcher
    fetcher_temp = GitHubFetcher()
    owner, repo_name = fetcher_temp.parse_github_url(github_url)

    repo_analysis = frappe.get_doc({
        "doctype": "Repo Analysis",
        "github_url": github_url,
        "repo_name": f"{owner}/{repo_name}",
        "branch": branch,
        "status": "In Progress",
    })
    repo_analysis.insert(ignore_permissions=True)
    frappe.db.commit()

    try:
        run_analysis(repo_analysis.name, github_url, branch, max_files)
        repo_analysis.reload()
        return {
            "status": "success",
            "repo_analysis": repo_analysis.name,
            "name": repo_analysis.name,
        }


@frappe.whitelist()
def save_settings(groq_api_key=None, groq_model=None, max_files_limit=None, output_language=None, github_token=None):
    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")

    if groq_api_key is not None:
        settings.groq_api_key = groq_api_key
    if groq_model is not None:
        settings.groq_model = groq_model
    if max_files_limit is not None:
        settings.max_files_limit = int(max_files_limit)
    if output_language is not None:
        settings.output_language = output_language
    if github_token is not None:
        settings.github_token = github_token

    settings.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success"}


def run_analysis(repo_analysis_name, github_url, branch="main", max_files=100):
    start_time = time.time()
    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")

    try:
        from git_analyze.github_fetcher import GitHubFetcher
        from git_analyze.groq_client import GroqClient

        fetcher = GitHubFetcher(github_token=settings.get_github_token())
        repo_data = fetcher.fetch_repository(
            github_url=github_url,
            branch=branch,
            max_files=max_files,
            skip_patterns=settings.get_skip_patterns(),
        )

        if not repo_data.get("files"):
            frappe.db.set_value("Repo Analysis", repo_analysis_name, "status", "Failed")
            frappe.db.set_value("Repo Analysis", repo_analysis_name, "full_output", "No files found. Check the URL and branch.")
            frappe.db.commit()
            return

        groq_client = GroqClient(
            api_key=settings.get_groq_api_key(),
            model=settings.groq_model,
        )

        result = groq_client.analyze_repository(
            repo_name=f"{repo_data['owner']}/{repo_data['repo']}",
            branch=repo_data["branch"],
            file_structure=repo_data["structure"],
            file_contents=repo_data["files"],
            language=settings.output_language,
        )

        sections = groq_client.parse_analysis_sections(result["content"])
        analysis_time = time.time() - start_time

        repo_analysis = frappe.get_doc("Repo Analysis", repo_analysis_name)
        repo_analysis.status = "Completed"
        repo_analysis.analysis_date = now_datetime()
        repo_analysis.purpose = sections.get("purpose", "")
        repo_analysis.tech_stack = sections.get("tech_stack", "")
        repo_analysis.architecture = sections.get("architecture", "")
        repo_analysis.entry_points = sections.get("entry_points", "")
        repo_analysis.key_modules = sections.get("key_modules", "")
        repo_analysis.data_flow = sections.get("data_flow", "")
        repo_analysis.api_endpoints = sections.get("api_endpoints", "")
        repo_analysis.database_models = sections.get("database_models", "")
        repo_analysis.dependencies = sections.get("dependencies", "")
        repo_analysis.how_to_run = sections.get("how_to_run", "")
        repo_analysis.full_output = result["content"]
        repo_analysis.groq_model = result["model"]
        repo_analysis.token_usage = result["token_usage"]["total_tokens"]
        repo_analysis.analysis_time = analysis_time
        repo_analysis.file_count = repo_data["analyzed_files"]
        repo_analysis.save(ignore_permissions=True)
        frappe.db.commit()

    except Exception as e:
        error_msg = str(e)
        frappe.db.set_value("Repo Analysis", repo_analysis_name, "status", "Failed")
        frappe.db.set_value("Repo Analysis", repo_analysis_name, "full_output", f"Error: {error_msg}")
        frappe.db.commit()
        frappe.log_error(f"Analysis failed for {repo_analysis_name}: {error_msg}")


@frappe.whitelist()
def ask_followup(repo_analysis_name, question):
    if not repo_analysis_name or not question:
        frappe.throw(_("Both repo_analysis_name and question are required"))

    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")
    repo_analysis = frappe.get_doc("Repo Analysis", repo_analysis_name)

    from git_analyze.groq_client import GroqClient
    groq_client = GroqClient(api_key=settings.get_groq_api_key(), model=settings.groq_model)

    result = groq_client.ask_followup(
        repo_name=repo_analysis.repo_name,
        question=question,
        previous_analysis=repo_analysis.full_output or "",
        language=settings.output_language,
    )

    return {"status": "success", "answer": result["content"]}


@frappe.whitelist()
def get_analysis_status(repo_analysis_name):
    repo_analysis = frappe.get_doc("Repo Analysis", repo_analysis_name)
    return {
        "status": repo_analysis.status,
        "repo_name": repo_analysis.repo_name,
        "token_usage": repo_analysis.token_usage,
        "analysis_time": repo_analysis.analysis_time,
        "file_count": repo_analysis.file_count,
        "full_output": repo_analysis.full_output,
    }


@frappe.whitelist()
def get_analysis_results(repo_analysis_name):
    r = frappe.get_doc("Repo Analysis", repo_analysis_name)
    return {
        "name": r.name,
        "github_url": r.github_url,
        "repo_name": r.repo_name,
        "branch": r.branch,
        "status": r.status,
        "purpose": r.purpose,
        "tech_stack": r.tech_stack,
        "architecture": r.architecture,
        "entry_points": r.entry_points,
        "key_modules": r.key_modules,
        "data_flow": r.data_flow,
        "api_endpoints": r.api_endpoints,
        "database_models": r.database_models,
        "dependencies": r.dependencies,
        "how_to_run": r.how_to_run,
        "full_output": r.full_output,
        "groq_model": r.groq_model,
        "token_usage": r.token_usage,
        "analysis_time": r.analysis_time,
        "file_count": r.file_count,
    }


@frappe.whitelist()
def export_as_markdown(repo_analysis_name):
    r = frappe.get_doc("Repo Analysis", repo_analysis_name)

    if r.status != "Completed" or not r.full_output:
        return {"error": "Analysis is not completed yet. Export is available only for completed analyses."}

    md = f"# Repository Analysis: {r.repo_name}\n\n"
    md += f"**URL:** {r.github_url}\n**Branch:** {r.branch}\n\n"
    for title, content in [
        ("Project Purpose", r.purpose), ("Tech Stack", r.tech_stack),
        ("Architecture", r.architecture), ("Entry Points", r.entry_points),
        ("Key Modules", r.key_modules), ("Data Flow", r.data_flow),
        ("API Endpoints", r.api_endpoints), ("Database Models", r.database_models),
        ("Dependencies", r.dependencies), ("How to Run", r.how_to_run),
    ]:
        if content:
            md += f"## {title}\n\n{content}\n\n"

    md += f"## Full Output\n\n{r.full_output}\n\n"

    filename = f"{r.repo_name.replace('/', '_')}_analysis.md"

    return {"content": md, "filename": filename}
