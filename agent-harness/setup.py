from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-fizzy",
    version="1.0.0",
    description="CLI harness for Fizzy Kanban board",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    install_requires=[
        "click>=8.0.0",
        "prompt-toolkit>=3.0.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": ["pytest>=7.0.0", "pytest-cov>=4.0.0"],
    },
    entry_points={
        "console_scripts": [
            "cli-anything-fizzy=cli_anything.fizzy.fizzy_cli:cli",
        ],
    },
    python_requires=">=3.10",
)
