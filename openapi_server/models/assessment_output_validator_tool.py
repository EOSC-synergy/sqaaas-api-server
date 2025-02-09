# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.assessment_output_tool_ci import AssessmentOutputToolCI
from openapi_server.models.base_model_ import Model
from openapi_server.models.tool_docker import ToolDocker


class AssessmentOutputValidatorTool(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        name: str = None,
        lang: str = None,
        version: str = None,
        docker: ToolDocker = None,
        ci: AssessmentOutputToolCI = None,
        level: str = None,
    ):
        """AssessmentOutputValidatorTool - a model defined in OpenAPI

        :param name: The name of this AssessmentOutputValidatorTool.
        :param lang: The lang of this AssessmentOutputValidatorTool.
        :param version: The version of this AssessmentOutputValidatorTool.
        :param docker: The docker of this AssessmentOutputValidatorTool.
        :param ci: The ci of this AssessmentOutputValidatorTool.
        :param level: The level of this AssessmentOutputValidatorTool.
        """
        self.openapi_types = {
            "name": str,
            "lang": str,
            "version": str,
            "docker": ToolDocker,
            "ci": AssessmentOutputToolCI,
            "level": str,
        }

        self.attribute_map = {
            "name": "name",
            "lang": "lang",
            "version": "version",
            "docker": "docker",
            "ci": "ci",
            "level": "level",
        }

        self._name = name
        self._lang = lang
        self._version = version
        self._docker = docker
        self._ci = ci
        self._level = level

    @classmethod
    def from_dict(cls, dikt: dict) -> "AssessmentOutputValidatorTool":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutputValidatorTool of this AssessmentOutputValidatorTool.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this AssessmentOutputValidatorTool.

        Name of the tool

        :return: The name of this AssessmentOutputValidatorTool.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this AssessmentOutputValidatorTool.

        Name of the tool

        :param name: The name of this AssessmentOutputValidatorTool.
        :type name: str
        """

        self._name = name

    @property
    def lang(self):
        """Gets the lang of this AssessmentOutputValidatorTool.

        Language that the tool is aligned with

        :return: The lang of this AssessmentOutputValidatorTool.
        :rtype: str
        """
        return self._lang

    @lang.setter
    def lang(self, lang):
        """Sets the lang of this AssessmentOutputValidatorTool.

        Language that the tool is aligned with

        :param lang: The lang of this AssessmentOutputValidatorTool.
        :type lang: str
        """

        self._lang = lang

    @property
    def version(self):
        """Gets the version of this AssessmentOutputValidatorTool.

        Version of the tool

        :return: The version of this AssessmentOutputValidatorTool.
        :rtype: str
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this AssessmentOutputValidatorTool.

        Version of the tool

        :param version: The version of this AssessmentOutputValidatorTool.
        :type version: str
        """

        self._version = version

    @property
    def docker(self):
        """Gets the docker of this AssessmentOutputValidatorTool.


        :return: The docker of this AssessmentOutputValidatorTool.
        :rtype: ToolDocker
        """
        return self._docker

    @docker.setter
    def docker(self, docker):
        """Sets the docker of this AssessmentOutputValidatorTool.


        :param docker: The docker of this AssessmentOutputValidatorTool.
        :type docker: ToolDocker
        """

        self._docker = docker

    @property
    def ci(self):
        """Gets the ci of this AssessmentOutputValidatorTool.


        :return: The ci of this AssessmentOutputValidatorTool.
        :rtype: AssessmentOutputToolCI
        """
        return self._ci

    @ci.setter
    def ci(self, ci):
        """Sets the ci of this AssessmentOutputValidatorTool.


        :param ci: The ci of this AssessmentOutputValidatorTool.
        :type ci: AssessmentOutputToolCI
        """

        self._ci = ci

    @property
    def level(self):
        """Gets the level of this AssessmentOutputValidatorTool.

        Level of criticality of the tool

        :return: The level of this AssessmentOutputValidatorTool.
        :rtype: str
        """
        return self._level

    @level.setter
    def level(self, level):
        """Sets the level of this AssessmentOutputValidatorTool.

        Level of criticality of the tool

        :param level: The level of this AssessmentOutputValidatorTool.
        :type level: str
        """
        allowed_values = ["REQUIRED", "RECOMMENDED", "OPTIONAL"]  # noqa: E501
        if level not in allowed_values:
            raise ValueError(
                "Invalid value for `level` ({0}), must be one of {1}".format(
                    level, allowed_values
                )
            )

        self._level = level
