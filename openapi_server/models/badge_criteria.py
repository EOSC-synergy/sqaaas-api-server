# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class BadgeCriteria(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        to_fulfill: List[str] = None,
        fulfilled: List[str] = None,
        missing: List[str] = None,
    ):
        """BadgeCriteria - a model defined in OpenAPI

        :param to_fulfill: The to_fulfill of this BadgeCriteria.
        :param fulfilled: The fulfilled of this BadgeCriteria.
        :param missing: The missing of this BadgeCriteria.
        """
        self.openapi_types = {
            "to_fulfill": List[str],
            "fulfilled": List[str],
            "missing": List[str],
        }

        self.attribute_map = {
            "to_fulfill": "to_fulfill",
            "fulfilled": "fulfilled",
            "missing": "missing",
        }

        self._to_fulfill = to_fulfill
        self._fulfilled = fulfilled
        self._missing = missing

    @classmethod
    def from_dict(cls, dikt: dict) -> "BadgeCriteria":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Badge_criteria of this BadgeCriteria.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def to_fulfill(self):
        """Gets the to_fulfill of this BadgeCriteria.


        :return: The to_fulfill of this BadgeCriteria.
        :rtype: List[str]
        """
        return self._to_fulfill

    @to_fulfill.setter
    def to_fulfill(self, to_fulfill):
        """Sets the to_fulfill of this BadgeCriteria.


        :param to_fulfill: The to_fulfill of this BadgeCriteria.
        :type to_fulfill: List[str]
        """

        self._to_fulfill = to_fulfill

    @property
    def fulfilled(self):
        """Gets the fulfilled of this BadgeCriteria.


        :return: The fulfilled of this BadgeCriteria.
        :rtype: List[str]
        """
        return self._fulfilled

    @fulfilled.setter
    def fulfilled(self, fulfilled):
        """Sets the fulfilled of this BadgeCriteria.


        :param fulfilled: The fulfilled of this BadgeCriteria.
        :type fulfilled: List[str]
        """

        self._fulfilled = fulfilled

    @property
    def missing(self):
        """Gets the missing of this BadgeCriteria.


        :return: The missing of this BadgeCriteria.
        :rtype: List[str]
        """
        return self._missing

    @missing.setter
    def missing(self, missing):
        """Sets the missing of this BadgeCriteria.


        :param missing: The missing of this BadgeCriteria.
        :type missing: List[str]
        """

        self._missing = missing
