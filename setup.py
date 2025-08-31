#!/usr/bin/env python3
"""
Setup script for Multimodal RAG PDF Processing
Fallback setup.py for environments that don't support pyproject.toml
"""

from setuptools import setup, find_packages
import os

# Read requirements from requirements.txt
def read_requirements():
    req_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(req_file):
        with open(req_file, 'r', encoding='utf-8') as f:
            requirements = []
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if line and not line.startswith('#'):
                    # Remove inline comments
                    if ' #' in line:
                        line = line.split(' #')[0].strip()
                    requirements.append(line)
            return requirements
    return []

# Read README for long description
def read_readme():
    readme_file = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_file):
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return "Multimodal RAG system for PDF document parsing and element extraction"

setup(
    name="multimodal-rag-pdf-processing",
    version="1.0.0",
    description="Multimodal RAG system for PDF document parsing and element extraction",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Multimodal RAG Team",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'jupyter>=1.0.0',
            'notebook>=6.5.0',
            'pytest>=7.0.0',
            'black>=23.0.0',
            'isort>=5.12.0',
            'flake8>=6.0.0',
        ],
        'advanced': [
            'unstructured[local-inference]>=0.10.0',
            'torch>=2.0.0',
            'transformers>=4.30.0',
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Markup",
    ],
    keywords="pdf rag multimodal document-processing ocr",
    include_package_data=True,
    zip_safe=False,
)