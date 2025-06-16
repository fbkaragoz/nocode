#!/usr/bin/env python3
"""
Setup script for Advanced AI Code Generation System
"""

from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read requirements
with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="advanced-ai-coder",
    version="1.0.0",
    author="Fatih Karaağaç",
    author_email="fbkaragoz@gmail.com",
    description="Enterprise-grade AI code generation system with Ollama and DeepSeek",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fbkaragoz/nocode",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=22.0",
            "isort>=5.0",
            "flake8>=4.0",
            "mypy>=0.900",
            "pre-commit>=2.0",
        ],
        "enhanced": [
            "rich>=12.0",
            "psutil>=5.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "auto-coder=main:main",
            "advanced-coder=main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    keywords="ai artificial-intelligence code-generation ollama deepseek python automation",
    project_urls={
        "Bug Reports": "https://github.com/fbkaragoz/nocode/issues",
        "Source": "https://github.com/fbkaragoz/nocode",
        "Documentation": "https://github.com/fbkaragoz/nocode/wiki",
    },
) 