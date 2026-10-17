from setuptools import setup, find_packages

setup(
    name="invariantq",
    version="1.0.0",
    description="INVARIANTQ: A Research-Grade Quantum Computing Platform",
    author="InvariantQ Team",
    packages=find_packages(),
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "pytest>=7.0.0",
    ],
    entry_points={
        "console_scripts": [
            "invariantq=invariantq.cli:main",
        ],
    },
    package_data={
        "invariantq.core": ["libinvariantq.so"],
    },
    include_package_data=True,
    python_requires=">=3.9",
)
