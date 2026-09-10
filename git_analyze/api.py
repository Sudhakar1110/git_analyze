import frappe
from frappe import _
import time
import threading
import traceback
import json
import base64
from frappe.utils import now_datetime, cint

DECOMMISSIONED_MODELS = [
    "llama3-8b-8192", "llama-3.1-8b-instant", "llama3-70b-8192",
    "llama-3.3-70b-versatile", "mixtral-8x7b-32768", "gemma2-9b-it",
]

ANALYSIS_LOCK = threading.Lock()


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

    site_name = frappe.conf.site_name or frappe.local.site

    t = threading.Thread(
        target=_bg_run,
        args=(site_name, repo_analysis.name, github_url, branch, max_files),
        daemon=True,
        name=f"analysis-{repo_analysis.name}",
    )
    t.start()

    return {"status": "success", "repo_analysis": repo_analysis.name, "name": repo_analysis.name}


def _bg_run(site, name, url, branch, max_files):
    try:
        frappe.init(site=site, force=True)
        frappe.connect()
        frappe.set_user("Administrator")
        _do_analysis(name, url, branch, max_files)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        try:
            frappe.db.set_value("Repo Analysis", name, "status", "Failed")
            frappe.db.set_value("Repo Analysis", name, "full_output", error_msg)
            frappe.db.commit()
        except Exception:
            pass
        try:
            frappe.log_error(f"BG Analysis failed for {name}: {error_msg}\n{traceback.format_exc()}")
        except Exception:
            pass
    finally:
        try:
            frappe.db.close()
        except Exception:
            pass
        try:
            frappe.destroy()
        except Exception:
            pass


def _do_analysis(name, github_url, branch, max_files):
    start_time = time.time()
    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")

    frappe.db.set_value("Repo Analysis", name, "full_output", "Fetching repository files...")
    frappe.db.commit()

    from git_analyze.github_fetcher import GitHubFetcher
    fetcher = GitHubFetcher(github_token=settings.get_github_token())
    repo_data = fetcher.fetch_repository(
        github_url=github_url,
        branch=branch,
        max_files=max_files,
        skip_patterns=settings.get_skip_patterns(),
    )

    if not repo_data.get("files"):
        frappe.db.set_value("Repo Analysis", name, "status", "Failed")
        frappe.db.set_value("Repo Analysis", name, "full_output", "No files found. Check URL and branch.")
        frappe.db.commit()
        return

    groq_model = settings.groq_model or "openai/gpt-oss-20b"
    if groq_model in DECOMMISSIONED_MODELS:
        groq_model = "openai/gpt-oss-20b"
        frappe.db.set_value("Analysis Settings", "Analysis Settings", "groq_model", groq_model)
        frappe.db.commit()

    frappe.db.set_value("Repo Analysis", name, "full_output", f"Analyzing {repo_data['analyzed_files']} files with AI...")
    frappe.db.commit()

    from git_analyze.groq_client import GroqClient
    groq_client = GroqClient(
        api_key=settings.get_groq_api_key(),
        model=groq_model,
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

    frappe.db.set_value("Repo Analysis", name, "status", "Completed")
    frappe.db.set_value("Repo Analysis", name, "analysis_date", now_datetime())
    frappe.db.set_value("Repo Analysis", name, "purpose", sections.get("purpose", ""))
    frappe.db.set_value("Repo Analysis", name, "tech_stack", sections.get("tech_stack", ""))
    frappe.db.set_value("Repo Analysis", name, "architecture", sections.get("architecture", ""))
    frappe.db.set_value("Repo Analysis", name, "entry_points", sections.get("entry_points", ""))
    frappe.db.set_value("Repo Analysis", name, "key_modules", sections.get("key_modules", ""))
    frappe.db.set_value("Repo Analysis", name, "data_flow", sections.get("data_flow", ""))
    frappe.db.set_value("Repo Analysis", name, "api_endpoints", sections.get("api_endpoints", ""))
    frappe.db.set_value("Repo Analysis", name, "database_models", sections.get("database_models", ""))
    frappe.db.set_value("Repo Analysis", name, "dependencies", sections.get("dependencies", ""))
    frappe.db.set_value("Repo Analysis", name, "how_to_run", sections.get("how_to_run", ""))
    frappe.db.set_value("Repo Analysis", name, "full_output", result["content"])
    frappe.db.set_value("Repo Analysis", name, "groq_model", result["model"])
    frappe.db.set_value("Repo Analysis", name, "token_usage", result["token_usage"]["total_tokens"])
    frappe.db.set_value("Repo Analysis", name, "analysis_time", analysis_time)
    frappe.db.set_value("Repo Analysis", name, "file_count", repo_data["analyzed_files"])
    frappe.db.commit()


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


def _get_analysis_data(repo_analysis_name):
    r = frappe.get_doc("Repo Analysis", repo_analysis_name)
    if r.status != "Completed" or not r.full_output:
        frappe.throw(_("Analysis is not completed yet. Export is available only for completed analyses."))
    return r


def _get_report_html(r):
    sections_html = ""
    section_map = [
        ("Project Purpose", r.purpose),
        ("Tech Stack", r.tech_stack),
        ("Architecture", r.architecture),
        ("Entry Points", r.entry_points),
        ("Key Modules", r.key_modules),
        ("Data Flow", r.data_flow),
        ("API Endpoints", r.api_endpoints),
        ("Database Models", r.database_models),
        ("Dependencies", r.dependencies),
        ("How to Run", r.how_to_run),
    ]
    for title, content in section_map:
        if content:
            escaped = frappe.utils.escape_html(content).replace("\n", "<br>")
            sections_html += f"""
            <div style="margin-bottom:24px;">
                <h2 style="color:#0f172a;font-size:18px;font-weight:600;margin-bottom:8px;padding-bottom:6px;border-bottom:2px solid #10b981;">{title}</h2>
                <div style="color:#334155;font-size:14px;line-height:1.7;">{escaped}</div>
            </div>"""

    full_escaped = frappe.utils.escape_html(r.full_output or "").replace("\n", "<br>")

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #1e293b; line-height: 1.6; }}
.header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: white; padding: 32px; border-radius: 12px; margin-bottom: 32px; }}
.header h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
.header p {{ margin: 4px 0; opacity: 0.85; font-size: 14px; }}
.meta-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 16px; margin-bottom: 32px; }}
.meta-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; text-align: center; }}
.meta-card .label {{ font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
.meta-card .value {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-top: 4px; }}
.section {{ margin-bottom: 24px; }}
.section h2 {{ color: #0f172a; font-size: 18px; font-weight: 600; margin-bottom: 8px; padding-bottom: 6px; border-bottom: 2px solid #10b981; }}
.section-content {{ color: #334155; font-size: 14px; line-height: 1.7; }}
.full-output {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 24px; margin-top: 32px; }}
.full-output h2 {{ border-bottom-color: #6366f1; }}
.footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 40px; padding-top: 16px; border-top: 1px solid #e2e8f0; }}
</style>
</head>
<body>
<div class="header">
    <h1>Repository Analysis: {r.repo_name}</h1>
    <p><strong>URL:</strong> {r.github_url} &nbsp;|&nbsp; <strong>Branch:</strong> {r.branch} &nbsp;|&nbsp; <strong>Status:</strong> {r.status}</p>
    <p><strong>Generated by:</strong> Git Analyzer &nbsp;|&nbsp; <strong>Date:</strong> {r.analysis_date or r.creation}</p>
</div>
<div class="meta-grid">
    <div class="meta-card"><div class="label">Files Analyzed</div><div class="value">{r.file_count or 0}</div></div>
    <div class="meta-card"><div class="label">AI Model</div><div class="value" style="font-size:14px;">{r.groq_model or 'default'}</div></div>
    <div class="meta-card"><div class="label">Tokens Used</div><div class="value">{r.token_usage or 0}</div></div>
    <div class="meta-card"><div class="label">Time Taken</div><div class="value">{r.analysis_time or 0}s</div></div>
</div>
{sections_html}
<div class="full-output">
    <h2>Full AI Output</h2>
    <div class="section-content">{full_escaped}</div>
</div>
<div class="footer">Generated by Git Analyzer &mdash; {now_datetime()}</div>
</body>
</html>"""


def _get_report_markdown(r):
    md = f"# Repository Analysis: {r.repo_name}\n\n"
    md += f"| Field | Value |\n|-------|-------|\n"
    md += f"| **URL** | {r.github_url} |\n"
    md += f"| **Branch** | {r.branch} |\n"
    md += f"| **Status** | {r.status} |\n"
    md += f"| **Files Analyzed** | {r.file_count or 0} |\n"
    md += f"| **AI Model** | {r.groq_model or 'default'} |\n"
    md += f"| **Tokens Used** | {r.token_usage or 0} |\n"
    md += f"| **Time Taken** | {r.analysis_time or 0}s |\n"
    md += f"| **Generated** | {r.analysis_date or r.creation} |\n\n"
    md += "---\n\n"
    section_map = [
        ("Project Purpose", r.purpose), ("Tech Stack", r.tech_stack),
        ("Architecture", r.architecture), ("Entry Points", r.entry_points),
        ("Key Modules", r.key_modules), ("Data Flow", r.data_flow),
        ("API Endpoints", r.api_endpoints), ("Database Models", r.database_models),
        ("Dependencies", r.dependencies), ("How to Run", r.how_to_run),
    ]
    for title, content in section_map:
        if content:
            md += f"## {title}\n\n{content}\n\n"
    md += "---\n\n## Full AI Output\n\n```\n{r.full_output}\n```\n\n"
    md += f"*Generated by Git Analyzer on {now_datetime()}*\n"
    return md


def _get_report_json(r):
    return {
        "repository": {
            "name": r.repo_name,
            "url": r.github_url,
            "branch": r.branch,
            "status": r.status,
            "files_analyzed": r.file_count or 0,
        },
        "analysis": {
            "date": str(r.analysis_date or r.creation),
            "model": r.groq_model or "default",
            "tokens_used": r.token_usage or 0,
            "time_seconds": r.analysis_time or 0,
        },
        "sections": {
            "purpose": r.purpose or "",
            "tech_stack": r.tech_stack or "",
            "architecture": r.architecture or "",
            "entry_points": r.entry_points or "",
            "key_modules": r.key_modules or "",
            "data_flow": r.data_flow or "",
            "api_endpoints": r.api_endpoints or "",
            "database_models": r.database_models or "",
            "dependencies": r.dependencies or "",
            "how_to_run": r.how_to_run or "",
        },
        "full_output": r.full_output or "",
        "generated_by": "Git Analyzer",
        "generated_at": str(now_datetime()),
    }


@frappe.whitelist()
def export_as_markdown(repo_analysis_name):
    r = _get_analysis_data(repo_analysis_name)
    return {"content": _get_report_markdown(r), "filename": f"{r.repo_name.replace('/', '_')}_analysis.md"}


@frappe.whitelist()
def export_as_html(repo_analysis_name):
    r = _get_analysis_data(repo_analysis_name)
    return {"content": _get_report_html(r), "filename": f"{r.repo_name.replace('/', '_')}_analysis.html"}


@frappe.whitelist()
def export_as_json(repo_analysis_name):
    r = _get_analysis_data(repo_analysis_name)
    data = _get_report_json(r)
    return {"content": json.dumps(data, indent=2), "filename": f"{r.repo_name.replace('/', '_')}_analysis.json"}


@frappe.whitelist()
def export_as_pdf(repo_analysis_name):
    r = _get_analysis_data(repo_analysis_name)
    html = _get_report_html(r)
    try:
        from frappe.utils.pdf import get_pdf
        pdf = get_pdf(html, options={"page-size": "A4", "margin-top": "15mm", "margin-bottom": "15mm"})
        b64 = base64.b64encode(pdf).decode("utf-8")
        return {
            "content": b64,
            "filename": f"{r.repo_name.replace('/', '_')}_analysis.pdf",
            "is_base64": True,
        }
    except Exception as e:
        frappe.throw(_("PDF generation failed: {0}. Ensure wkhtmltopdf is installed.").format(str(e)))


@frappe.whitelist()
def export_as_docx(repo_analysis_name):
    r = _get_analysis_data(repo_analysis_name)
    try:
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        import io

        doc = Document()

        style = doc.styles["Normal"]
        style.font.name = "Calibri"
        style.font.size = Pt(11)

        title = doc.add_heading(f"Repository Analysis: {r.repo_name}", level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        table = doc.add_table(rows=8, cols=2, style="Light Grid Accent 1")
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        meta = [
            ("Repository URL", r.github_url),
            ("Branch", r.branch),
            ("Status", r.status),
            ("Files Analyzed", str(r.file_count or 0)),
            ("AI Model", r.groq_model or "default"),
            ("Tokens Used", str(r.token_usage or 0)),
            ("Time Taken", f"{r.analysis_time or 0}s"),
            ("Generated", str(r.analysis_date or r.creation)),
        ]
        for i, (k, v) in enumerate(meta):
            table.rows[i].cells[0].text = k
            table.rows[i].cells[1].text = v
            for cell in table.rows[i].cells:
                for p in cell.paragraphs:
                    p.style.font.size = Pt(10)

        doc.add_paragraph("")

        section_map = [
            ("Project Purpose", r.purpose), ("Tech Stack", r.tech_stack),
            ("Architecture", r.architecture), ("Entry Points", r.entry_points),
            ("Key Modules", r.key_modules), ("Data Flow", r.data_flow),
            ("API Endpoints", r.api_endpoints), ("Database Models", r.database_models),
            ("Dependencies", r.dependencies), ("How to Run", r.how_to_run),
        ]
        for title_text, content in section_map:
            if content:
                doc.add_heading(title_text, level=1)
                for para in content.split("\n"):
                    if para.strip():
                        doc.add_paragraph(para.strip())

        doc.add_heading("Full AI Output", level=1)
        for para in (r.full_output or "").split("\n"):
            if para.strip():
                doc.add_paragraph(para.strip())

        doc.add_paragraph("")
        footer = doc.add_paragraph(f"Generated by Git Analyzer on {now_datetime()}")
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in footer.runs:
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(148, 163, 184)

        buf = io.BytesIO()
        doc.save(buf)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode("utf-8")
        return {
            "content": b64,
            "filename": f"{r.repo_name.replace('/', '_')}_analysis.docx",
            "is_base64": True,
        }
    except ImportError:
        frappe.throw(_("python-docx library is not installed. Contact your server admin to run: bench pip install python-docx"))
    except Exception as e:
        frappe.throw(_("DOCX generation failed: {0}").format(str(e)))


@frappe.whitelist()
def test_groq_connection():
    import requests as req
    settings = frappe.get_doc("Analysis Settings", "Analysis Settings")
    if not settings.groq_api_key:
        return {"status": "error", "error": "No Groq API key configured"}

    try:
        api_key = settings.get_groq_api_key()
        model = settings.groq_model or "openai/gpt-oss-20b"
        if model in DECOMMISSIONED_MODELS:
            model = "openai/gpt-oss-20b"
            frappe.db.set_value("Analysis Settings", "Analysis Settings", "groq_model", model)
            frappe.db.commit()
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5}
        r = req.post(url, json=payload, headers=headers, timeout=30)
        if r.status_code != 200:
            error_detail = r.json().get("error", {}).get("message", r.text[:200])
            return {"status": "error", "error": f"Groq API error ({r.status_code}): {error_detail}"}
        data = r.json()
        return {"status": "ok", "model": model, "response": data["choices"][0]["message"]["content"]}
    except req.exceptions.ConnectionError:
        return {"status": "error", "error": "Cannot reach api.groq.com - server firewall or network issue. Contact your server admin to allow outbound HTTPS to api.groq.com:443"}
    except req.exceptions.Timeout:
        return {"status": "error", "error": "Connection timed out - api.groq.com is too slow or blocked"}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {str(e)}"}
