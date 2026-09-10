import frappe
import time
from typing import Dict, Optional
from groq import Groq


class GroqClient:
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
        self.client = Groq(api_key=api_key, timeout=120.0)
        self.model = model

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

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert software engineer. Analyze code repositories thoroughly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=4096,
        )

        content = response.choices[0].message.content
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens,
        }
        return {"content": content, "token_usage": token_usage, "model": self.model}

    def ask_followup(self, repo_name: str, question: str,
                     previous_analysis: str,
                     language: str = "English") -> Dict:
        prompt = f"""Based on analysis of {repo_name}, answer this question: {question}

Previous analysis:
{previous_analysis[:5000]}

Provide a detailed answer in {language}:"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Answer questions about code repositories."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=2048,
        )

        return {
            "content": response.choices[0].message.content,
            "token_usage": {"total_tokens": response.usage.total_tokens},
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
