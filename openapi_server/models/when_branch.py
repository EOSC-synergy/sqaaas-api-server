# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class WhenBranch(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, pattern: str = None, comparator: str = "GLOB"):
        """WhenBranch - a model defined in OpenAPI

        :param pattern: The pattern of this WhenBranch.
        :param comparator: The comparator of this WhenBranch.
        """
        self.openapi_types = {"pattern": str, "comparator": str}

        self.attribute_map = {"pattern": "pattern", "comparator": "comparator"}

        self._pattern = pattern
        self._comparator = comparator

    @classmethod
    def from_dict(cls, dikt: dict) -> "WhenBranch":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The When_branch of this WhenBranch.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def pattern(self):
        """Gets the pattern of this WhenBranch.


        :return: The pattern of this WhenBranch.
        :rtype: str
        """
        return self._pattern

    @pattern.setter
    def pattern(self, pattern):
        """Sets the pattern of this WhenBranch.


        :param pattern: The pattern of this WhenBranch.
        :type pattern: str
        """
        if pattern is None:
            raise ValueError("Invalid value for `pattern`, must not be `None`")
        if pattern is not None and len(pattern) < 1:
            raise ValueError(
                "Invalid value for `pattern`, length must be greater than or equal to `1`"
            )

        self._pattern = pattern

    @property
    def comparator(self):
        """Gets the comparator of this WhenBranch.


        :return: The comparator of this WhenBranch.
        :rtype: str
        """
        return self._comparator

    @comparator.setter
    def comparator(self, comparator):
        """Sets the comparator of this WhenBranch.


        :param comparator: The comparator of this WhenBranch.
        :type comparator: str
        """
        allowed_values = ["EQUALS", "GLOB", "REGEXP"]  # noqa: E501
        if comparator not in allowed_values:
            raise ValueError(
                "Invalid value for `comparator` ({0}), must be one of {1}".format(
                    comparator, allowed_values
                )
            )

        self._comparator = comparator
