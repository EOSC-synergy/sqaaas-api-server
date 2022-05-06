import pytest


async def test_run_pipeline(mocker, client):
    """Test case for run_pipeline

    Runs pipeline.
    """
    mocker.patch("openapi_server.controllers.utils.validate_request", lambda f: f)

    params = [('issue_badge', 'False'),
              ('repo_url', 'repo_url_example'),
              ('repo_branch', 'repo_branch_example')]
    headers = {
        'Accept': 'application/json',
    }
    response = await client.request(
        method='POST',
        path='/v1/pipeline/{pipeline_id}/run'.format(pipeline_id='pipeline_id'),
        headers=headers,
        params=params,
    )
    assert response.status == 200, 'Response body is : ' + (await response.read()).decode('utf-8')


