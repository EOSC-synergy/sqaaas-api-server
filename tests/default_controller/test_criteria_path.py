async def test_get_criteria(monkeypatch, client):
    """Test case for get_criteria

    Returns data about criteria
    """
    async def mock_get_tooling_metadata(*args, **kwargs):
        return {"mock_key": "mock_response"}

    monkeypatch.setattr("openapi_server.controllers.default_controller._get_tooling_metadata", mock_get_tooling_metadata)
    monkeypatch.setattr("openapi_server.controllers.default_controller._sort_tooling_by_criteria", mock_get_tooling_metadata)

    params = [('criterion_id', 'criterion_id_example')]
    headers = {
        'Accept': 'application/json',
    }
    response = await client.request(
        method='GET',
        path='/v1/criteria',
        headers=headers,
        params=params,
        )
    assert response.status == 200, 'Response body is : ' + (await response.read()).decode('utf-8')
