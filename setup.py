"""Setup script for the basketcase package."""
from setuptools import find_packages, setup

setup(
    name="basketcase",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
        "schedule>=1.2.1",
        "click>=8.1.7",
        "tabulate>=0.9.0",
        "pandas>=2.1.4",
        "matplotlib>=3.8.2",
        "SQLAlchemy>=2.0.25",
        "alembic>=1.13.1",
        "pywin32>=306",
    ],
    entry_points={
        "console_scripts": [
            "basketcase=basketcase.cli:cli",
        ],
    },
    python_requires=">=3.8",
    author="Your Name",
    author_email="your.email@example.com",
    description="Track grocery prices and calculate inflation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/basketcase",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
