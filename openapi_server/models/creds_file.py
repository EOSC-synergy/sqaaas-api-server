# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class CredsFile(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id: str = None, type: str = None, variable: str = None):
        """CredsFile - a model defined in OpenAPI

        :param id: The id of this CredsFile.
        :param type: The type of this CredsFile.
        :param variable: The variable of this CredsFile.
        """
        self.openapi_types = {"id": str, "type": str, "variable": str}

        self.attribute_map = {"id": "id", "type": "type", "variable": "variable"}

        self._id = id
        self._type = type
        self._variable = variable

    @classmethod
    def from_dict(cls, dikt: dict) -> "CredsFile":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Creds_file of this CredsFile.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this CredsFile.


        :return: The id of this CredsFile.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CredsFile.


        :param id: The id of this CredsFile.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")

        self._id = id

    @property
    def type(self):
        """Gets the type of this CredsFile.


        :return: The type of this CredsFile.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this CredsFile.


        :param type: The type of this CredsFile.
        :type type: str
        """
        allowed_values = ["file", "zip"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}".format(
                    type, allowed_values
                )
            )

        self._type = type

    @property
    def variable(self):
        """Gets the variable of this CredsFile.


        :return: The variable of this CredsFile.
        :rtype: str
        """
        return self._variable

    @variable.setter
    def variable(self, variable):
        """Sets the variable of this CredsFile.


        :param variable: The variable of this CredsFile.
        :type variable: str
        """

        self._variable = variable
