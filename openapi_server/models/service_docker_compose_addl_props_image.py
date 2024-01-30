# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model
from openapi_server.models.service_docker_compose_addl_props_image_registry import \
    ServiceDockerComposeAddlPropsImageRegistry


class ServiceDockerComposeAddlPropsImage(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        name: str = None,
        registry: ServiceDockerComposeAddlPropsImageRegistry = None,
    ):
        """ServiceDockerComposeAddlPropsImage - a model defined in OpenAPI

        :param name: The name of this ServiceDockerComposeAddlPropsImage.
        :param registry: The registry of this ServiceDockerComposeAddlPropsImage.
        """
        self.openapi_types = {
            "name": str,
            "registry": ServiceDockerComposeAddlPropsImageRegistry,
        }

        self.attribute_map = {"name": "name", "registry": "registry"}

        self._name = name
        self._registry = registry

    @classmethod
    def from_dict(cls, dikt: dict) -> "ServiceDockerComposeAddlPropsImage":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_addl_props_image of this ServiceDockerComposeAddlPropsImage.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this ServiceDockerComposeAddlPropsImage.


        :return: The name of this ServiceDockerComposeAddlPropsImage.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this ServiceDockerComposeAddlPropsImage.


        :param name: The name of this ServiceDockerComposeAddlPropsImage.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")

        self._name = name

    @property
    def registry(self):
        """Gets the registry of this ServiceDockerComposeAddlPropsImage.


        :return: The registry of this ServiceDockerComposeAddlPropsImage.
        :rtype: ServiceDockerComposeAddlPropsImageRegistry
        """
        return self._registry

    @registry.setter
    def registry(self, registry):
        """Sets the registry of this ServiceDockerComposeAddlPropsImage.


        :param registry: The registry of this ServiceDockerComposeAddlPropsImage.
        :type registry: ServiceDockerComposeAddlPropsImageRegistry
        """

        self._registry = registry
