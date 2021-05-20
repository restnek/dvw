from distutils.core import setup

from setuptools import find_namespace_packages

with open("requirements.txt") as f:
    required = f.read().splitlines()

setup(
    name="dvw",
    version="0.0.1",
    author="restnek",
    description="Digital Video Watermarking (DVW) tool",
    python_requires=">=3.6",
    install_requires=required,
    packages=find_namespace_packages(),
    entry_points={"console_scripts": ["dvw = dvw.cli:main"]},
    license="MIT",
)
