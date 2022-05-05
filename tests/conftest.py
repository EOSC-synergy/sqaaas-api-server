import logging
import pytest
import os

import connexion

from openapi_server import config


CONF = config.init('etc/sqaaas.ini.sample')


class MockGitHubUtils:
    @staticmethod
    def get_file(*args, **kwargs):
        return "file content"

        
@pytest.fixture
def client(monkeypatch, loop, aiohttp_client):
    def mock_init_utils():
        return (None, MockGitHubUtils, None, None)

    monkeypatch.setattr("openapi_server.controllers.init_utils", mock_init_utils)

    logging.getLogger('connexion.operation').setLevel('ERROR')
    options = {
        "swagger_ui": True
        }
    specification_dir = os.path.join(os.path.dirname(__file__), '..',
                                     'openapi_server',
                                     'openapi')
    app = connexion.AioHttpApp(__name__, specification_dir=specification_dir,
                               options=options)
    app.add_api('openapi.yaml', pythonic_params=True,
                pass_context_arg_name='request')
    return loop.run_until_complete(aiohttp_client(app.app))
