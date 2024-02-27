# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only


async def test_get_criteria(mocker, client):
    """Test case for get_criteria.

    Returns data about criteria
    """
    mocker.patch(
        "openapi_server.controllers.default_controller._get_tooling_metadata",
        return_value={"mock_key": "mock_response"},
    )
    mocker.patch(
        "openapi_server.controllers.default_controller._sort_tooling_by_criteria",
        return_value={"mock_key": "mock_response"},
    )

    params = [("criterion_id", "criterion_id_example")]
    headers = {
        "Accept": "application/json",
    }
    response = await client.request(
        method="GET",
        path="/v1/criteria",
        headers=headers,
        params=params,
    )
    assert response.status == 200, "Response body is : " + (
        await response.read()
    ).decode("utf-8")
