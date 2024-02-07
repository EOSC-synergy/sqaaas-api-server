# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class CriterionDescription(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, msg: str = None, improves: str = None, docs: str = None):
        """CriterionDescription - a model defined in OpenAPI

        :param msg: The msg of this CriterionDescription.
        :param improves: The improves of this CriterionDescription.
        :param docs: The docs of this CriterionDescription.
        """
        self.openapi_types = {"msg": str, "improves": str, "docs": str}

        self.attribute_map = {"msg": "msg", "improves": "improves", "docs": "docs"}

        self._msg = msg
        self._improves = improves
        self._docs = docs

    @classmethod
    def from_dict(cls, dikt: dict) -> "CriterionDescription":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Criterion_description of this CriterionDescription.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def msg(self):
        """Gets the msg of this CriterionDescription.

        Short statemente about the criterion's goal

        :return: The msg of this CriterionDescription.
        :rtype: str
        """
        return self._msg

    @msg.setter
    def msg(self, msg):
        """Sets the msg of this CriterionDescription.

        Short statemente about the criterion's goal

        :param msg: The msg of this CriterionDescription.
        :type msg: str
        """

        self._msg = msg

    @property
    def improves(self):
        """Gets the improves of this CriterionDescription.

        Comma-separated list of software/service characteristics addressed by the given criterion

        :return: The improves of this CriterionDescription.
        :rtype: str
        """
        return self._improves

    @improves.setter
    def improves(self, improves):
        """Sets the improves of this CriterionDescription.

        Comma-separated list of software/service characteristics addressed by the given criterion

        :param improves: The improves of this CriterionDescription.
        :type improves: str
        """

        self._improves = improves

    @property
    def docs(self):
        """Gets the docs of this CriterionDescription.

        URL with additional information about the criterion

        :return: The docs of this CriterionDescription.
        :rtype: str
        """
        return self._docs

    @docs.setter
    def docs(self, docs):
        """Sets the docs of this CriterionDescription.

        URL with additional information about the criterion

        :param docs: The docs of this CriterionDescription.
        :type docs: str
        """

        self._docs = docs
