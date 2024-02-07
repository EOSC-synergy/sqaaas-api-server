# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from setuptools import find_packages, setup

NAME = "sqaaas_api_server"
VERSION = "3.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion==2.14.2",
    "swagger-ui-bundle==0.0.9",
    "PyGithub>=1.53",
    "python-jenkins>=1.7.0",
    "deepdiff>=5.2.3",
    "GitPython>=3.1.17",
]

setup(
    name=NAME,
    version=VERSION,
    description="SQAaaS API",
    author="Pablo Orviz",
    author_email="orviz@ifca.unican.es",
    url="https://github.com/eosc-synergy/sqaaas-api-server",
    keywords=["OpenAPI", "SQAaaS API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={
        "openapi_server": [
            "LICENSE",
            "openapi/openapi.yaml",
            "templates/Jenkinsfile",
            "templates/embed_badge.html",
            "templates/commands_script.sh",
            "templates/commands_script_im.sh",
            "templates/pipeline_assessment.json",
            "templates/README",
            "templates/jenkins/credentials.xml",
            "../etc/sqaaas.ini.sample",
        ]
    },
    include_package_data=False,
    entry_points={
        "console_scripts": ["sqaaas_api_server=openapi_server.__main__:main"]
    },
    long_description="""\
    API for the Software and Service Quality Assurance as a Service (SQAaaS) component.
    """,
)
