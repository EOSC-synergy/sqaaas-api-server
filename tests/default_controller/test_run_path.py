import pytest


async def test_run_pipeline_response_204(mocker, client, mock_db, mock_jepl_utils):
    """Test case for checking 204 responses in run_pipeline."""
    mocker.patch('openapi_server.controllers.utils.db', mock_db)
    mocker.patch('openapi_server.controllers.default_controller.db', mock_db)
    mocker.patch('openapi_server.controllers.default_controller.JePLUtils', mock_jepl_utils)
    mocker.patch('openapi_server.controllers.default_controller._update_status', return_value=True)

    params = [('issue_badge', 'False'),
              ('repo_url', 'repo_url_example'),
              ('repo_branch', 'repo_branch_example')]
    headers = {
        'Accept': 'application/json',
    }
    response = await client.request(
        method='POST',
        path='/v1/pipeline/{pipeline_id}/run'.format(pipeline_id='dd7d8481-81a3-407f-95f0-a2f1cb382a4b'),
        headers=headers,
        # params=params,
    )
    assert response.status == 204, 'Response body is : ' + (await response.read()).decode('utf-8')
