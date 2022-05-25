import pytest


expected_response =  [
    (
        {
            "repo_code": {"repo": "https://example.org", "branch": "main"},
            "repo_docs": {"repo": "https://example.org", "branch": "main"}
        }, 201
    ),
    (
        {
            "repo_code": {"repo": "https://example.org", "branch": "main"}
        }, 201
    ),
    (
        {
            "repo_docs": {"repo": "https://example.org", "branch": "main"}
        }, 400
    ),
    (
        {}, 400
    ),
]

@pytest.mark.parametrize('body,expected', expected_response)
async def test_add_pipeline_for_assessment(mocker, client, body, expected):
    """Test case for add_pipeline_for_assessment

    Creates a pipeline for assessment (QAA module).
    """
    mocker.patch("openapi_server.controllers.default_controller._get_tooling_for_assessment", return_value=('a', 'b'))
    mocker.patch("openapi_server.controllers.default_controller._add_pipeline_to_db", return_value='pipeline_id')
    mocker.patch("openapi_server.controllers.db.add_assessment_data", return_value=None)

    params = [('optional_tools', 'optional_tools_example')]
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    response = await client.request(
        method='POST',
        path='/v1/pipeline/assessment',
        headers=headers,
        json=body,
        params=params,
    )
    assert response.status == expected, 'Response body is : ' + (await response.read()).decode('utf-8')


