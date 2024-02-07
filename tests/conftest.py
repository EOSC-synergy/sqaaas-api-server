# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
import os

import connexion
import pytest

from openapi_server import config

CONF = config.init("etc/sqaaas.ini.sample")


pytest_plugins = [
    "tests.fixtures.db",
    "tests.fixtures.github",
    "tests.fixtures.jepl",
    "tests.fixtures.jenkins",
]


@pytest.fixture
def client(monkeypatch, loop, aiohttp_client, mock_github_utils, mock_jenkins_utils):
    def mock_init_utils():
        return (None, mock_github_utils, mock_jenkins_utils, None)

    monkeypatch.setattr("openapi_server.controllers.init_utils", mock_init_utils)

    logging.getLogger("connexion.operation").setLevel("ERROR")
    options = {"swagger_ui": True}
    specification_dir = os.path.join(
        os.path.dirname(__file__), "..", "openapi_server", "openapi"
    )
    app = connexion.AioHttpApp(
        __name__, specification_dir=specification_dir, options=options
    )
    app.add_api("openapi.yaml", pythonic_params=True, pass_context_arg_name="request")
    return loop.run_until_complete(aiohttp_client(app.app))
