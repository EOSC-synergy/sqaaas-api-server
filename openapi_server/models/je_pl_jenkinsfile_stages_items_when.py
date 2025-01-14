# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class JePLJenkinsfileStagesItemsWhen(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, branches: List[str] = None):
        """JePLJenkinsfileStagesItemsWhen - a model defined in OpenAPI

        :param branches: The branches of this JePLJenkinsfileStagesItemsWhen.
        """
        self.openapi_types = {"branches": List[str]}

        self.attribute_map = {"branches": "branches"}

        self._branches = branches

    @classmethod
    def from_dict(cls, dikt: dict) -> "JePLJenkinsfileStagesItemsWhen":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The JePL_jenkinsfile_stagesItems_when of this JePLJenkinsfileStagesItemsWhen.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def branches(self):
        """Gets the branches of this JePLJenkinsfileStagesItemsWhen.


        :return: The branches of this JePLJenkinsfileStagesItemsWhen.
        :rtype: List[str]
        """
        return self._branches

    @branches.setter
    def branches(self, branches):
        """Sets the branches of this JePLJenkinsfileStagesItemsWhen.


        :param branches: The branches of this JePLJenkinsfileStagesItemsWhen.
        :type branches: List[str]
        """

        self._branches = branches
