# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class BadgeCriteriaStats(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        to_fulfill: List[str] = [],
        missing: List[str] = [],
        fulfilled: List[str] = [],
    ):
        """BadgeCriteriaStats - a model defined in OpenAPI

        :param to_fulfill: The to_fulfill of this BadgeCriteriaStats.
        :param missing: The missing of this BadgeCriteriaStats.
        :param fulfilled: The fulfilled of this BadgeCriteriaStats.
        """
        self.openapi_types = {
            "to_fulfill": List[str],
            "missing": List[str],
            "fulfilled": List[str],
        }

        self.attribute_map = {
            "to_fulfill": "to_fulfill",
            "missing": "missing",
            "fulfilled": "fulfilled",
        }

        self._to_fulfill = to_fulfill
        self._missing = missing
        self._fulfilled = fulfilled

    @classmethod
    def from_dict(cls, dikt: dict) -> "BadgeCriteriaStats":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The BadgeCriteriaStats of this BadgeCriteriaStats.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def to_fulfill(self):
        """Gets the to_fulfill of this BadgeCriteriaStats.

        List of criteria codes to be fulfilled for the given badge class

        :return: The to_fulfill of this BadgeCriteriaStats.
        :rtype: List[str]
        """
        return self._to_fulfill

    @to_fulfill.setter
    def to_fulfill(self, to_fulfill):
        """Sets the to_fulfill of this BadgeCriteriaStats.

        List of criteria codes to be fulfilled for the given badge class

        :param to_fulfill: The to_fulfill of this BadgeCriteriaStats.
        :type to_fulfill: List[str]
        """

        self._to_fulfill = to_fulfill

    @property
    def missing(self):
        """Gets the missing of this BadgeCriteriaStats.

        List of missing criteria codes for the badge class to be granted

        :return: The missing of this BadgeCriteriaStats.
        :rtype: List[str]
        """
        return self._missing

    @missing.setter
    def missing(self, missing):
        """Sets the missing of this BadgeCriteriaStats.

        List of missing criteria codes for the badge class to be granted

        :param missing: The missing of this BadgeCriteriaStats.
        :type missing: List[str]
        """

        self._missing = missing

    @property
    def fulfilled(self):
        """Gets the fulfilled of this BadgeCriteriaStats.

        List of fulfilled criteria codes for the given badge class

        :return: The fulfilled of this BadgeCriteriaStats.
        :rtype: List[str]
        """
        return self._fulfilled

    @fulfilled.setter
    def fulfilled(self, fulfilled):
        """Sets the fulfilled of this BadgeCriteriaStats.

        List of fulfilled criteria codes for the given badge class

        :param fulfilled: The fulfilled of this BadgeCriteriaStats.
        :type fulfilled: List[str]
        """

        self._fulfilled = fulfilled
