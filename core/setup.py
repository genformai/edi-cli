#!/usr/bin/env python3
"""
Setup script for EDI Core library.
"""

from setuptools import setup, find_packages
import os

# Read README
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as fh:
            return fh.read()
    return "EDI Core Library - Shared parsing and validation engine"

# Read requirements
def read_requirements():
    req_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8") as fh:
            return [line.strip() for line in fh if line.strip() and not line.startswith("#")]
    return []

setup(
    name="edi-core",
    version="0.4.0",
    author="EDI CLI Contributors",
    author_email="contributors@edi-cli.dev",
    description="Core library for EDI parsing, validation, and analysis",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/edi-cli",
    project_urls={
        "Bug Tracker": "https://github.com/your-org/edi-cli/issues",
        "Documentation": "https://edi-cli.readthedocs.io/",
        "Source Code": "https://github.com/your-org/edi-cli",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Office/Business :: Financial",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
            "black>=23.0",
            "mypy>=1.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-mock>=3.10",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yml", "*.yaml", "*.json"],
    },
    zip_safe=False,
    keywords=[
        "edi", "x12", "healthcare", "parsing", "validation", 
        "claims", "hipaa", "library", "core"
    ],
)