# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest

from openapi_server.controllers import utils

supported_git_platform = {"github": "https://github.com"}
expected_git_platform = [
    ("https://github.com/foo/bar", "github"),
    ("http://github.com/foo/bar", "github"),
    ("http://github.com/foo/bar.git", "github"),
]


@pytest.mark.parametrize("repo_url,expected", expected_git_platform)
def test_supported_git_platform(repo_url, expected):
    repo_url = utils.supported_git_platform(repo_url, supported_git_platform)
    assert repo_url == expected


expected_repo_name = [
    (
        "https://github.com:443/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "https://github.com:443/eoscsynergy/sqaaas-api-server",
        True,
        "github.com:443/eoscsynergy/sqaaas-api-server",
    ),
    (
        "https://github.com/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "https://github.com/eoscsynergy/sqaaas-api-server",
        True,
        "github.com/eoscsynergy/sqaaas-api-server",
    ),
    (
        "http://github.com:443/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "http://github.com:443/eoscsynergy/sqaaas-api-server",
        True,
        "github.com:443/eoscsynergy/sqaaas-api-server",
    ),
    (
        "http://github.com/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "http://github.com/eoscsynergy/sqaaas-api-server",
        True,
        "github.com/eoscsynergy/sqaaas-api-server",
    ),
    (
        "github.com:443/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "github.com:443/eoscsynergy/sqaaas-api-server",
        True,
        "github.com:443/eoscsynergy/sqaaas-api-server",
    ),
    (
        "github.com/eoscsynergy/sqaaas-api-server",
        False,
        "eoscsynergy/sqaaas-api-server",
    ),
    (
        "github.com/eoscsynergy/sqaaas-api-server",
        True,
        "github.com/eoscsynergy/sqaaas-api-server",
    ),
]


@pytest.mark.parametrize("repo_url,include_host,expected", expected_repo_name)
def test_get_short_repo_name(repo_url, include_host, expected):
    registry_url = utils.get_short_repo_name(repo_url, include_host=include_host)
    assert registry_url == expected


expected_registry_url = [
    (
        "https://mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0",
        "https://mydockerregistry.example.com:8080",
    ),
    (
        "https://mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0",
        "https://mydockerregistry.example.com",
    ),
    (
        "http://mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0",
        "http://mydockerregistry.example.com:8080",
    ),
    (
        "http://mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0",
        "http://mydockerregistry.example.com",
    ),
    (
        "mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0",
        "mydockerregistry.example.com:8080",
    ),
    (
        "mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0",
        "mydockerregistry.example.com",
    ),
]


@pytest.mark.parametrize("image_name,expected", expected_registry_url)
def test_get_registry_from_image(image_name, expected):
    registry_url = utils.get_registry_from_image(image_name)
    assert registry_url == expected
