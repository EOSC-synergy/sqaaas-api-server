# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class GetPipelineStatus200Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, build_url: str=None, build_status: str=None, openbadge_id: str=None):
        """GetPipelineStatus200Response - a model defined in OpenAPI

        :param build_url: The build_url of this GetPipelineStatus200Response.
        :param build_status: The build_status of this GetPipelineStatus200Response.
        :param openbadge_id: The openbadge_id of this GetPipelineStatus200Response.
        """
        self.openapi_types = {
            'build_url': str,
            'build_status': str,
            'openbadge_id': str
        }

        self.attribute_map = {
            'build_url': 'build_url',
            'build_status': 'build_status',
            'openbadge_id': 'openbadge_id'
        }

        self._build_url = build_url
        self._build_status = build_status
        self._openbadge_id = openbadge_id

    @classmethod
    def from_dict(cls, dikt: dict) -> 'GetPipelineStatus200Response':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The get_pipeline_status_200_response of this GetPipelineStatus200Response.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def build_url(self):
        """Gets the build_url of this GetPipelineStatus200Response.


        :return: The build_url of this GetPipelineStatus200Response.
        :rtype: str
        """
        return self._build_url

    @build_url.setter
    def build_url(self, build_url):
        """Sets the build_url of this GetPipelineStatus200Response.


        :param build_url: The build_url of this GetPipelineStatus200Response.
        :type build_url: str
        """

        self._build_url = build_url

    @property
    def build_status(self):
        """Gets the build_status of this GetPipelineStatus200Response.


        :return: The build_status of this GetPipelineStatus200Response.
        :rtype: str
        """
        return self._build_status

    @build_status.setter
    def build_status(self, build_status):
        """Sets the build_status of this GetPipelineStatus200Response.


        :param build_status: The build_status of this GetPipelineStatus200Response.
        :type build_status: str
        """
        allowed_values = ["success", "failure", "aborted", "not_built", "unstable", "waiting_scan_org"]  # noqa: E501
        if build_status not in allowed_values:
            raise ValueError(
                "Invalid value for `build_status` ({0}), must be one of {1}"
                .format(build_status, allowed_values)
            )

        self._build_status = build_status

    @property
    def openbadge_id(self):
        """Gets the openbadge_id of this GetPipelineStatus200Response.


        :return: The openbadge_id of this GetPipelineStatus200Response.
        :rtype: str
        """
        return self._openbadge_id

    @openbadge_id.setter
    def openbadge_id(self, openbadge_id):
        """Sets the openbadge_id of this GetPipelineStatus200Response.


        :param openbadge_id: The openbadge_id of this GetPipelineStatus200Response.
        :type openbadge_id: str
        """

        self._openbadge_id = openbadge_id