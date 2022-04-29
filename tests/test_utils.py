import pytest

from openapi_server.controllers import utils


expected_registry_url = [
    ('https://mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0', 'https://mydockerregistry.example.com:8080'),
    ('https://mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0', 'https://mydockerregistry.example.com'),
    ('http://mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0', 'http://mydockerregistry.example.com:8080'),
    ('http://mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0', 'http://mydockerregistry.example.com'),
    ('mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0', 'mydockerregistry.example.com:8080'),
    ('mydockerregistry.example.com/eoscsynergy/sqaaas-api-server:2.1.0', 'mydockerregistry.example.com')
]

@pytest.mark.parametrize('image_name,expected', expected_registry_url)
def test_get_registry_from_image(image_name, expected):
    registry_url = utils.get_registry_from_image(image_name)
    assert registry_url == expected
