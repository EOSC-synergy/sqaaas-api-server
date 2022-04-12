# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "sqaaas_api_server"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion==2.6.0",
    "swagger-ui-bundle==0.0.6",
    "PyGithub>=1.53",
    "python-jenkins>=1.7.0",
    "deepdiff>=5.2.3"
    "GitPython>=3.1.17"
]

setup(
    name=NAME,
    version=VERSION,
    description="SQAaaS API",
    author_email="orviz@ifca.unican.es",
    url="https://github.com/eosc-synergy/sqaaas-api-server",
    keywords=["OpenAPI", "SQAaaS API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'openapi_server': [
        'LICENSE',
        'openapi/openapi.yaml',
        'templates/Jenkinsfile',
        'templates/embed_badge.html',
        'templates/commands_script.sh',
        'templates/pipeline_assessment.json',
        'templates/README',
        '../etc/sqaaas.ini.sample']},
    include_package_data=False,
    entry_points={
        'console_scripts': ['sqaaas_api_server=openapi_server.__main__:main']},
    long_description="""\
    API for the Software and Service Quality Assurance as a Service (SQAaaS) component.
    """
)

