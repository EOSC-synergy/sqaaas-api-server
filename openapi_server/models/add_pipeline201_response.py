# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class AddPipeline201Response(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id: str = None):
        """AddPipeline201Response - a model defined in OpenAPI

        :param id: The id of this AddPipeline201Response.
        """
        self.openapi_types = {"id": str}

        self.attribute_map = {"id": "id"}

        self._id = id

    @classmethod
    def from_dict(cls, dikt: dict) -> "AddPipeline201Response":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The add_pipeline_201_response of this AddPipeline201Response.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this AddPipeline201Response.

        UUID identifying the pipeline

        :return: The id of this AddPipeline201Response.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this AddPipeline201Response.

        UUID identifying the pipeline

        :param id: The id of this AddPipeline201Response.
        :type id: str
        """

        self._id = id
