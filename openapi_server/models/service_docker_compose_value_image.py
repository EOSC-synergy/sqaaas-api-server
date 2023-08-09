# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.service_docker_compose_value_image_registry import ServiceDockerComposeValueImageRegistry
from openapi_server import util


class ServiceDockerComposeValueImage(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name: str=None, registry: ServiceDockerComposeValueImageRegistry=None):
        """ServiceDockerComposeValueImage - a model defined in OpenAPI

        :param name: The name of this ServiceDockerComposeValueImage.
        :param registry: The registry of this ServiceDockerComposeValueImage.
        """
        self.openapi_types = {
            'name': str,
            'registry': ServiceDockerComposeValueImageRegistry
        }

        self.attribute_map = {
            'name': 'name',
            'registry': 'registry'
        }

        self._name = name
        self._registry = registry

    @classmethod
    def from_dict(cls, dikt: dict) -> 'ServiceDockerComposeValueImage':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_value_image of this ServiceDockerComposeValueImage.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this ServiceDockerComposeValueImage.


        :return: The name of this ServiceDockerComposeValueImage.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this ServiceDockerComposeValueImage.


        :param name: The name of this ServiceDockerComposeValueImage.
        :type name: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")

        self._name = name

    @property
    def registry(self):
        """Gets the registry of this ServiceDockerComposeValueImage.


        :return: The registry of this ServiceDockerComposeValueImage.
        :rtype: ServiceDockerComposeValueImageRegistry
        """
        return self._registry

    @registry.setter
    def registry(self, registry):
        """Sets the registry of this ServiceDockerComposeValueImage.


        :param registry: The registry of this ServiceDockerComposeValueImage.
        :type registry: ServiceDockerComposeValueImageRegistry
        """

        self._registry = registry
