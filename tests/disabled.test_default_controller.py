# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

import json

import pytest
from aiohttp import web

from openapi_server.models.assessment_output import AssessmentOutput
from openapi_server.models.badge import Badge
from openapi_server.models.criterion import Criterion
from openapi_server.models.criterion_output_addl_props_inner import \
    CriterionOutputAddlPropsInner
from openapi_server.models.inline_object import InlineObject
from openapi_server.models.inline_response200 import InlineResponse200
from openapi_server.models.inline_response201 import InlineResponse201
from openapi_server.models.inline_response2001 import InlineResponse2001
from openapi_server.models.inline_response2002 import InlineResponse2002
from openapi_server.models.inline_response2003 import InlineResponse2003
from openapi_server.models.inline_response2004 import InlineResponse2004
from openapi_server.models.inline_response2005 import InlineResponse2005
from openapi_server.models.je_pl_composer import JePLComposer
from openapi_server.models.je_pl_config import JePLConfig
from openapi_server.models.je_pl_jenkinsfile import JePLJenkinsfile
from openapi_server.models.pipeline import Pipeline
from openapi_server.models.pipeline_assessment import PipelineAssessment
from openapi_server.models.upstream_error import UpstreamError


async def test_add_pipeline(client):
    """Test case for add_pipeline

    Creates a pipeline.
    """
    body = {
        "config_data": [
            {
                "environment": {
                    "JPL_IGNOREFAILURES": "defined",
                    "JPL_DOCKERPUSH": "docs service1 service4",
                },
                "sqa_criteria": {
                    "key": {
                        "repos": [
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                        ],
                        "when": {
                            "building_tag": true,
                            "branch": {
                                "comparator": "GLOB",
                                "pattern": "release-\\\\d+",
                            },
                        },
                    }
                },
                "config": {
                    "project_repos": [
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                    ],
                    "credentials": [
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                    ],
                },
                "timeout": 1,
            },
            {
                "environment": {
                    "JPL_IGNOREFAILURES": "defined",
                    "JPL_DOCKERPUSH": "docs service1 service4",
                },
                "sqa_criteria": {
                    "key": {
                        "repos": [
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                        ],
                        "when": {
                            "building_tag": true,
                            "branch": {
                                "comparator": "GLOB",
                                "pattern": "release-\\\\d+",
                            },
                        },
                    }
                },
                "config": {
                    "project_repos": [
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                    ],
                    "credentials": [
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                    ],
                },
                "timeout": 1,
            },
        ],
        "composer_data": {
            "services": {
                "key": {
                    "image": {
                        "registry": {
                            "push": true,
                            "credential_id": "my-dockerhub-cred",
                        },
                        "name": "eoscsynergy/sqaaas-api-spec:1.0.0",
                    },
                    "hostname": "sqaaas-host",
                    "environment": {
                        "JPL_IGNOREFAILURES": "defined",
                        "JPL_DOCKERPUSH": "docs service1 service4",
                    },
                    "build": {
                        "args": {"key": "args"},
                        "dockerfile": "Dockerfile-alternate",
                        "context": "./dir",
                    },
                    "volumes": [
                        {"source": "./", "type": "bind", "target": "./sqaaas-build"},
                        {"source": "./", "type": "bind", "target": "./sqaaas-build"},
                    ],
                    "oneshot": true,
                    "command": "sleep 600000",
                }
            },
            "version": "3.7",
        },
        "name": "sqaaas-api-spec",
        "id": "dd7d8481-81a3-407f-95f0-a2f1cb382a4b",
        "jenkinsfile_data": {
            "stages": [
                {
                    "pipeline_config": {
                        "credentials_id": "userpass_dockerhub",
                        "base_branch": "https://github.com/eosc-synergy/sqaaas-api-spec",
                        "base_repository": "master",
                        "jepl_validator_docker_image": "eoscsynergy/jpl-validator:1.1.0",
                        "config_file": "./.sqa/config.yml",
                    },
                    "when": {"branches": ["master", "master"]},
                },
                {
                    "pipeline_config": {
                        "credentials_id": "userpass_dockerhub",
                        "base_branch": "https://github.com/eosc-synergy/sqaaas-api-spec",
                        "base_repository": "master",
                        "jepl_validator_docker_image": "eoscsynergy/jpl-validator:1.1.0",
                        "config_file": "./.sqa/config.yml",
                    },
                    "when": {"branches": ["master", "master"]},
                },
            ]
        },
    }
    params = [("report_to_stdout", False)]
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = await client.request(
        method="POST",
        path="/v1/pipeline",
        headers=headers,
        json=body,
        params=params,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_create_pull_request(client):
    """Test case for create_pull_request

    Creates pull request with JePL files.
    """
    body = openapi_server.InlineObject()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = await client.request(
        method="POST",
        path="/v1/pipeline/{pipeline_id}/pull_request".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
        json=body,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_delete_pipeline_by_id(client):
    """Test case for delete_pipeline_by_id

    Delete pipeline by ID
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="DELETE",
        path="/v1/pipeline/{pipeline_id}".format(pipeline_id="pipeline_id_example"),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_badge(client):
    """Test case for get_badge

    Gets badge data associated with the given pipeline
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/badge".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_compressed_files(client):
    """Test case for get_compressed_files

    Get JePL files in compressed format.
    """
    headers = {
        "Accept": "application/zip",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/compressed_files".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_output_for_assessment(client):
    """Test case for get_output_for_assessment

    Get the assessment output (QAA module)
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/assessment/{pipeline_id}/output".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_by_id(client):
    """Test case for get_pipeline_by_id

    Find pipeline by ID
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}".format(pipeline_id="pipeline_id_example"),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_commands_scripts(client):
    """Test case for get_pipeline_commands_scripts

    Gets the commands builder scripts
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/config/scripts".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_composer(client):
    """Test case for get_pipeline_composer

    Gets composer configuration used by the pipeline.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/composer".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_composer_jepl(client):
    """Test case for get_pipeline_composer_jepl

    Gets JePL composer configuration for the given pipeline.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/composer/jepl".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_config(client):
    """Test case for get_pipeline_config

    Gets pipeline's main configuration.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/config".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_config_jepl(client):
    """Test case for get_pipeline_config_jepl

    Gets JePL config configuration for the given pipeline.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/config/jepl".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_jenkinsfile(client):
    """Test case for get_pipeline_jenkinsfile

    Gets Jenkins pipeline definition used by the pipeline.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/jenkinsfile".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_jenkinsfile_jepl(client):
    """Test case for get_pipeline_jenkinsfile_jepl

    Gets Jenkins configuration for the given pipeline.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/jenkinsfile/jepl".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_output(client):
    """Test case for get_pipeline_output

    Get output from pipeline execution
    """
    params = [("validate", False)]
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/output".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
        params=params,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipeline_status(client):
    """Test case for get_pipeline_status

    Get pipeline status.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline/{pipeline_id}/status".format(
            pipeline_id="pipeline_id_example"
        ),
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_get_pipelines(client):
    """Test case for get_pipelines

    Gets pipeline IDs.
    """
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/pipeline",
        headers=headers,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")


async def test_update_pipeline_by_id(client):
    """Test case for update_pipeline_by_id

    Update pipeline by ID
    """
    body = {
        "config_data": [
            {
                "environment": {
                    "JPL_IGNOREFAILURES": "defined",
                    "JPL_DOCKERPUSH": "docs service1 service4",
                },
                "sqa_criteria": {
                    "key": {
                        "repos": [
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                        ],
                        "when": {
                            "building_tag": true,
                            "branch": {
                                "comparator": "GLOB",
                                "pattern": "release-\\\\d+",
                            },
                        },
                    }
                },
                "config": {
                    "project_repos": [
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                    ],
                    "credentials": [
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                    ],
                },
                "timeout": 1,
            },
            {
                "environment": {
                    "JPL_IGNOREFAILURES": "defined",
                    "JPL_DOCKERPUSH": "docs service1 service4",
                },
                "sqa_criteria": {
                    "key": {
                        "repos": [
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                            {
                                "container": "testing",
                                "repo_url": "https://github.com/eosc-synergy/sqaaas-api-spec",
                                "tox": {"tox_file": "tox.ini", "testenv": ["cover"]},
                                "commands": ["mvn checkstyle:check"],
                                "tool": {
                                    "args": [
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                        {
                                            "summary": "summary",
                                            "args": [null, null],
                                            "repeatable": false,
                                            "selectable": true,
                                            "format": "string",
                                            "description": "Detect the license of the given project",
                                            "type": "subcommand",
                                            "value": "detect",
                                            "option": "option",
                                        },
                                    ],
                                    "docs": "https://openapi-generator.tech",
                                    "name": "name",
                                    "lang": "lang",
                                    "jepl_support": true,
                                    "executable": "executable",
                                    "docker": {
                                        "image": "image",
                                        "dockerfile": "dockerfile",
                                        "reviewed": "2000-01-23",
                                        "oneshot": true,
                                    },
                                },
                            },
                        ],
                        "when": {
                            "building_tag": true,
                            "branch": {
                                "comparator": "GLOB",
                                "pattern": "release-\\\\d+",
                            },
                        },
                    }
                },
                "config": {
                    "project_repos": [
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                        {
                            "repo": "https://github.com/eosc-synergy/sqaaas-api-spec",
                            "branch": "master",
                        },
                    ],
                    "credentials": [
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                        {
                            "password_var": "GIT_PASS",
                            "username_var": "GIT_USER",
                            "id": "my-dockerhub-token",
                            "type": "username_password",
                        },
                    ],
                },
                "timeout": 1,
            },
        ],
        "composer_data": {
            "services": {
                "key": {
                    "image": {
                        "registry": {
                            "push": true,
                            "credential_id": "my-dockerhub-cred",
                        },
                        "name": "eoscsynergy/sqaaas-api-spec:1.0.0",
                    },
                    "hostname": "sqaaas-host",
                    "environment": {
                        "JPL_IGNOREFAILURES": "defined",
                        "JPL_DOCKERPUSH": "docs service1 service4",
                    },
                    "build": {
                        "args": {"key": "args"},
                        "dockerfile": "Dockerfile-alternate",
                        "context": "./dir",
                    },
                    "volumes": [
                        {"source": "./", "type": "bind", "target": "./sqaaas-build"},
                        {"source": "./", "type": "bind", "target": "./sqaaas-build"},
                    ],
                    "oneshot": true,
                    "command": "sleep 600000",
                }
            },
            "version": "3.7",
        },
        "name": "sqaaas-api-spec",
        "id": "dd7d8481-81a3-407f-95f0-a2f1cb382a4b",
        "jenkinsfile_data": {
            "stages": [
                {
                    "pipeline_config": {
                        "credentials_id": "userpass_dockerhub",
                        "base_branch": "https://github.com/eosc-synergy/sqaaas-api-spec",
                        "base_repository": "master",
                        "jepl_validator_docker_image": "eoscsynergy/jpl-validator:1.1.0",
                        "config_file": "./.sqa/config.yml",
                    },
                    "when": {"branches": ["master", "master"]},
                },
                {
                    "pipeline_config": {
                        "credentials_id": "userpass_dockerhub",
                        "base_branch": "https://github.com/eosc-synergy/sqaaas-api-spec",
                        "base_repository": "master",
                        "jepl_validator_docker_image": "eoscsynergy/jpl-validator:1.1.0",
                        "config_file": "./.sqa/config.yml",
                    },
                    "when": {"branches": ["master", "master"]},
                },
            ]
        },
    }
    params = [("report_to_stdout", False)]
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = await client.request(
        method="PUT",
        path="/v1/pipeline/{pipeline_id}".format(pipeline_id="pipeline_id_example"),
        headers=headers,
        json=body,
        params=params,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")
