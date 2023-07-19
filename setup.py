# Always prefer setuptools over distutils
from setuptools import setup, find_packages

# To use a consistent encoding
from codecs import open
from os import path

from dailyreleases import __author__, __version__, __licence__

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="dailyreleases",
    version=__version__,
    description="A reddit bot that consolidates scene releases",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={"Source": "https://github.com/amir16yp/dailyreleases"},
    author=__author__,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
    ],
    python_requires=">=3.7",
    license=__licence__,
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    package_data={"dailyreleases": ["*.default"]},
    install_requires=["praw", "beautifulsoup4==4.7.1", 'discord-webhook', 'epicstore_api'],
    entry_points={"console_scripts": ["dailyreleases = dailyreleases.main:main"]},
)
