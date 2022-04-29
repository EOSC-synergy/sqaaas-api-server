from openapi_server.controllers import utils


def test_get_registry_from_image():
    image_name = 'mydockerregistry.example.com:8080/eoscsynergy/sqaaas-api-server:2.1.0'
    expected_result = 'mydockerregistry.example.com:8080'
    result = utils.get_registry_from_image(image_name)
    assert result == expected_result
