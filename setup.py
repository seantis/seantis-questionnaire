import os
import sys
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="seantis-questionnaire",
    version="2.0.1",
    description="A Django application for creating online questionnaires/surveys.",
    long_description=read("README.md"),
    author="Seantis GmbH",
    author_email="info@seantis.ch",
    license="BSD",
    url="https://github.com/seantis/seantis-questionnaire",
    packages=find_packages(exclude=["example"]),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        "Framework :: Django",
    ],
    zip_safe=False,
    install_requires=[
        'django',
        'django-transmeta',
        'django-compat',
        'pyyaml',
        'pyparsing'
    ],
    setup_requires=[
        'versiontools >= 1.6',
    ],
)

