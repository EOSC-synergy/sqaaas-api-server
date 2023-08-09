# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AssessmentOutputValidatorPlugin(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name: str=None, version: str=None):
        """AssessmentOutputValidatorPlugin - a model defined in OpenAPI

        :param name: The name of this AssessmentOutputValidatorPlugin.
        :param version: The version of this AssessmentOutputValidatorPlugin.
        """
        self.openapi_types = {
            'name': str,
            'version': str
        }

        self.attribute_map = {
            'name': 'name',
            'version': 'version'
        }

        self._name = name
        self._version = version

    @classmethod
    def from_dict(cls, dikt: dict) -> 'AssessmentOutputValidatorPlugin':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutputValidator_plugin of this AssessmentOutputValidatorPlugin.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this AssessmentOutputValidatorPlugin.

        Name of the plugin

        :return: The name of this AssessmentOutputValidatorPlugin.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this AssessmentOutputValidatorPlugin.

        Name of the plugin

        :param name: The name of this AssessmentOutputValidatorPlugin.
        :type name: str
        """

        self._name = name

    @property
    def version(self):
        """Gets the version of this AssessmentOutputValidatorPlugin.

        Version of the plugin

        :return: The version of this AssessmentOutputValidatorPlugin.
        :rtype: str
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this AssessmentOutputValidatorPlugin.

        Version of the plugin

        :param version: The version of this AssessmentOutputValidatorPlugin.
        :type version: str
        """

        self._version = version
