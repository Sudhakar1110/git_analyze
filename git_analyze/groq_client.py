import frappe
import time
import requests
from typing import Dict, Optional


class GroqClient:
    GROQ_API_BASE = "https://api.groq.com/openai/v1"

    ANALYSIS_PROMPT = """Analyze this GitHub repository and provide a comprehensive analysis.

Repository: {repo_name}
Branch: {branch}

File Structure:
{file_structure}

File Contents:
{file_contents}

Provide a detailed analysis covering:
1. Project Purpose: What does this project do?
2. Tech Stack: Languages, frameworks, and tools used
3. Architecture: Overall structure and design patterns
4. Entry Points: Main files and how the app starts
5. Key Modules: Important components and their roles
6. Data Flow: How data moves through the application
7. API Endpoints: REST APIs, routes, and endpoints
8. Database Models: Data models and schemas
9. Dependencies: External libraries and services
10. How to Run: Instructions to set up and run locally

Provide the analysis in {language} language.
Format the output in clean Markdown with proper sections."""

    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _chat_completion(self, messages, temperature=0.3, max_tokens=4096):
        url = f"{self.GROQ_API_BASE}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        response = self.session.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()

    def analyze_repository(self, repo_name: str, branch: str,
                           file_structure: str, file_contents: Dict[str, str],
                           language: str = "English") -> Dict:
        contents = ""
        for path, content in list(file_contents.items())[:20]:
            if len(content) > 5000:
                content = content[:5000] + "\n...[truncated]"
            contents += f"\n### {path}\n```\n{content}\n```\n"

        prompt = self.ANALYSIS_PROMPT.format(
            repo_name=repo_name,
            branch=branch,
            file_structure=file_structure[:3000],
            file_contents=contents[:15000],
            language=language,
        )

        data = self._chat_completion(
            messages=[
                {"role": "system", "content": "You are an expert software engineer. Analyze code repositories thoroughly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )

        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        token_usage = {
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }
        return {"content": content, "token_usage": token_usage, "model": self.model}

    def ask_followup(self, repo_name: str, question: str,
                     previous_analysis: str,
                     language: str = "English") -> Dict:
        prompt = f"""Based on analysis of {repo_name}, answer this question: {question}

Previous analysis:
{previous_analysis[:5000]}

Provide a detailed answer in {language}:"""

        data = self._chat_completion(
            messages=[
                {"role": "system", "content": "Answer questions about code repositories."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2048,
        )

        return {
            "content": data["choices"][0]["message"]["content"],
            "token_usage": {"total_tokens": data.get("usage", {}).get("total_tokens", 0)},
            "model": self.model,
        }

    def parse_analysis_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        current_section = None
        current_content = []

        section_map = {
            "purpose": "purpose",
            "tech stack": "tech_stack",
            "architecture": "architecture",
            "entry point": "entry_points",
            "key module": "key_modules",
            "data flow": "data_flow",
            "api endpoint": "api_endpoints",
            "database model": "database_models",
            "dependencies": "dependencies",
            "how to run": "how_to_run",
        }

        for line in content.split("\n"):
            line_lower = line.lower().strip()
            found = None
            for keyword, section_name in section_map.items():
                if keyword in line_lower and (line.startswith("#") or line.startswith("**")):
                    found = section_name
                    break
            if found:
                if current_section and current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = found
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section and current_content:
            sections[current_section] = "\n".join(current_content).strip()

        return sections
