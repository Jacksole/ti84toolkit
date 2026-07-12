from setuptools import find_packages, setup

setup(
    name="ti84toolkit",
    version="1.0.0",
    description="TI-84 Embedded Systems Toolkit, ported to a Python CLI",
    py_modules=["cli"],
    packages=find_packages(include=["core", "core.*", "modules", "modules.*"]),
    install_requires=[
        "typer>=0.12.0",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "toolkit=cli:app",
        ],
    },
    python_requires=">=3.9",
)
