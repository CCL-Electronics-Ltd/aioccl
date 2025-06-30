"""Setup module for aioCCL."""

from pathlib import Path
from setuptools import find_packages, setup

VERSION = "2025.6.5"

ROOT_DIR = Path(__file__).parent.resolve()

setup(
  name = "aioccl",
  packages=find_packages(exclude=["tests", "misc"]),
  version=VERSION,
  license="Apache License, Version 2.0",
  description="A Python library for CCL API server",
  long_description=(ROOT_DIR / "README.md").read_text(encoding="utf-8"),
  long_description_content_type="text/markdown",
  author="fkiscd",
  author_email="fkiscd@gmail.com",
  url="https://github.com/CCL-Electronics-Ltd/aioccl",
  download_url="https://github.com/CCL-Electronics-Ltd/aioccl",
  install_requires=[
          "aiohttp>3"
      ],
  include_package_data=True,
  classifiers=[
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Natural Language :: English",
    "License :: OSI Approved :: Apache Software License",
    "Topic :: Home Automation",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.12",
  ],
)
