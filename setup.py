from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="elitetools",
    version="0.0.1",
    author="John Kominetz",
    description="Elite Dangerous Data Tools",
    url="https://github.com/kominetz/elite-tools",
    packages=find_packages(),
    python_requires='>=3.7',
)