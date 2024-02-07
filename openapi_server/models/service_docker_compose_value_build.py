# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class ServiceDockerComposeValueBuild(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self, context: str = None, dockerfile: str = None, args: Dict[str, str] = None
    ):
        """ServiceDockerComposeValueBuild - a model defined in OpenAPI

        :param context: The context of this ServiceDockerComposeValueBuild.
        :param dockerfile: The dockerfile of this ServiceDockerComposeValueBuild.
        :param args: The args of this ServiceDockerComposeValueBuild.
        """
        self.openapi_types = {"context": str, "dockerfile": str, "args": Dict[str, str]}

        self.attribute_map = {
            "context": "context",
            "dockerfile": "dockerfile",
            "args": "args",
        }

        self._context = context
        self._dockerfile = dockerfile
        self._args = args

    @classmethod
    def from_dict(cls, dikt: dict) -> "ServiceDockerComposeValueBuild":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_value_build of this ServiceDockerComposeValueBuild.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def context(self):
        """Gets the context of this ServiceDockerComposeValueBuild.


        :return: The context of this ServiceDockerComposeValueBuild.
        :rtype: str
        """
        return self._context

    @context.setter
    def context(self, context):
        """Sets the context of this ServiceDockerComposeValueBuild.


        :param context: The context of this ServiceDockerComposeValueBuild.
        :type context: str
        """

        self._context = context

    @property
    def dockerfile(self):
        """Gets the dockerfile of this ServiceDockerComposeValueBuild.


        :return: The dockerfile of this ServiceDockerComposeValueBuild.
        :rtype: str
        """
        return self._dockerfile

    @dockerfile.setter
    def dockerfile(self, dockerfile):
        """Sets the dockerfile of this ServiceDockerComposeValueBuild.


        :param dockerfile: The dockerfile of this ServiceDockerComposeValueBuild.
        :type dockerfile: str
        """

        self._dockerfile = dockerfile

    @property
    def args(self):
        """Gets the args of this ServiceDockerComposeValueBuild.


        :return: The args of this ServiceDockerComposeValueBuild.
        :rtype: Dict[str, str]
        """
        return self._args

    @args.setter
    def args(self, args):
        """Sets the args of this ServiceDockerComposeValueBuild.


        :param args: The args of this ServiceDockerComposeValueBuild.
        :type args: Dict[str, str]
        """

        self._args = args
