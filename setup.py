from setuptools import setup, find_packages

with open("requirements.txt") as f:
    install_requires = f.read().strip().split("\n")

setup(
    name="git_analyze",
    version="1.0.0",
    description="Analyze GitHub repositories using Groq API",
    author="Git Analyzer",
    author_email="admin@example.com",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=install_requires,
)
