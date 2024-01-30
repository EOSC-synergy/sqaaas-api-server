# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class InlineResponse2005(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, pull_request_url: str = None):
        """InlineResponse2005 - a model defined in OpenAPI

        :param pull_request_url: The pull_request_url of this InlineResponse2005.
        """
        self.openapi_types = {"pull_request_url": str}

        self.attribute_map = {"pull_request_url": "pull_request_url"}

        self._pull_request_url = pull_request_url

    @classmethod
    def from_dict(cls, dikt: dict) -> "InlineResponse2005":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The inline_response_200_5 of this InlineResponse2005.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def pull_request_url(self):
        """Gets the pull_request_url of this InlineResponse2005.


        :return: The pull_request_url of this InlineResponse2005.
        :rtype: str
        """
        return self._pull_request_url

    @pull_request_url.setter
    def pull_request_url(self, pull_request_url):
        """Sets the pull_request_url of this InlineResponse2005.


        :param pull_request_url: The pull_request_url of this InlineResponse2005.
        :type pull_request_url: str
        """

        self._pull_request_url = pull_request_url
