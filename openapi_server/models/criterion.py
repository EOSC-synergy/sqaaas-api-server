# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_description import CriterionDescription
from openapi_server.models.tool import Tool


class Criterion(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        id: str = None,
        type: str = None,
        description: CriterionDescription = None,
        tools: List[Tool] = None,
    ):
        """Criterion - a model defined in OpenAPI

        :param id: The id of this Criterion.
        :param type: The type of this Criterion.
        :param description: The description of this Criterion.
        :param tools: The tools of this Criterion.
        """
        self.openapi_types = {
            "id": str,
            "type": str,
            "description": CriterionDescription,
            "tools": List[Tool],
        }

        self.attribute_map = {
            "id": "id",
            "type": "type",
            "description": "description",
            "tools": "tools",
        }

        self._id = id
        self._type = type
        self._description = description
        self._tools = tools

    @classmethod
    def from_dict(cls, dikt: dict) -> "Criterion":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Criterion of this Criterion.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this Criterion.

        ID of the criterion

        :return: The id of this Criterion.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this Criterion.

        ID of the criterion

        :param id: The id of this Criterion.
        :type id: str
        """

        self._id = id

    @property
    def type(self):
        """Gets the type of this Criterion.

        Type of criterion

        :return: The type of this Criterion.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this Criterion.

        Type of criterion

        :param type: The type of this Criterion.
        :type type: str
        """
        allowed_values = ["software", "service", "fair"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}".format(
                    type, allowed_values
                )
            )

        self._type = type

    @property
    def description(self):
        """Gets the description of this Criterion.


        :return: The description of this Criterion.
        :rtype: CriterionDescription
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this Criterion.


        :param description: The description of this Criterion.
        :type description: CriterionDescription
        """

        self._description = description

    @property
    def tools(self):
        """Gets the tools of this Criterion.

        Set of tools that are supported for the given criterion

        :return: The tools of this Criterion.
        :rtype: List[Tool]
        """
        return self._tools

    @tools.setter
    def tools(self, tools):
        """Sets the tools of this Criterion.

        Set of tools that are supported for the given criterion

        :param tools: The tools of this Criterion.
        :type tools: List[Tool]
        """

        self._tools = tools
