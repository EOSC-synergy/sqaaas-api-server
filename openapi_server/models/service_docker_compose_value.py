# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.service_docker_compose_value_build import (
    ServiceDockerComposeValueBuild,
)
from openapi_server.models.service_docker_compose_value_image import (
    ServiceDockerComposeValueImage,
)
from openapi_server.models.service_docker_compose_value_volumes_inner import (
    ServiceDockerComposeValueVolumesInner,
)
from openapi_server import util


class ServiceDockerComposeValue(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        build: ServiceDockerComposeValueBuild = None,
        image: ServiceDockerComposeValueImage = None,
        hostname: str = None,
        volumes: List[ServiceDockerComposeValueVolumesInner] = None,
        command: str = None,
        environment: Dict[str, str] = None,
        oneshot: bool = True,
    ):
        """ServiceDockerComposeValue - a model defined in OpenAPI

        :param build: The build of this ServiceDockerComposeValue.
        :param image: The image of this ServiceDockerComposeValue.
        :param hostname: The hostname of this ServiceDockerComposeValue.
        :param volumes: The volumes of this ServiceDockerComposeValue.
        :param command: The command of this ServiceDockerComposeValue.
        :param environment: The environment of this ServiceDockerComposeValue.
        :param oneshot: The oneshot of this ServiceDockerComposeValue.
        """
        self.openapi_types = {
            "build": ServiceDockerComposeValueBuild,
            "image": ServiceDockerComposeValueImage,
            "hostname": str,
            "volumes": List[ServiceDockerComposeValueVolumesInner],
            "command": str,
            "environment": Dict[str, str],
            "oneshot": bool,
        }

        self.attribute_map = {
            "build": "build",
            "image": "image",
            "hostname": "hostname",
            "volumes": "volumes",
            "command": "command",
            "environment": "environment",
            "oneshot": "oneshot",
        }

        self._build = build
        self._image = image
        self._hostname = hostname
        self._volumes = volumes
        self._command = command
        self._environment = environment
        self._oneshot = oneshot

    @classmethod
    def from_dict(cls, dikt: dict) -> "ServiceDockerComposeValue":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_value of this ServiceDockerComposeValue.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def build(self):
        """Gets the build of this ServiceDockerComposeValue.


        :return: The build of this ServiceDockerComposeValue.
        :rtype: ServiceDockerComposeValueBuild
        """
        return self._build

    @build.setter
    def build(self, build):
        """Sets the build of this ServiceDockerComposeValue.


        :param build: The build of this ServiceDockerComposeValue.
        :type build: ServiceDockerComposeValueBuild
        """

        self._build = build

    @property
    def image(self):
        """Gets the image of this ServiceDockerComposeValue.


        :return: The image of this ServiceDockerComposeValue.
        :rtype: ServiceDockerComposeValueImage
        """
        return self._image

    @image.setter
    def image(self, image):
        """Sets the image of this ServiceDockerComposeValue.


        :param image: The image of this ServiceDockerComposeValue.
        :type image: ServiceDockerComposeValueImage
        """

        self._image = image

    @property
    def hostname(self):
        """Gets the hostname of this ServiceDockerComposeValue.


        :return: The hostname of this ServiceDockerComposeValue.
        :rtype: str
        """
        return self._hostname

    @hostname.setter
    def hostname(self, hostname):
        """Sets the hostname of this ServiceDockerComposeValue.


        :param hostname: The hostname of this ServiceDockerComposeValue.
        :type hostname: str
        """

        self._hostname = hostname

    @property
    def volumes(self):
        """Gets the volumes of this ServiceDockerComposeValue.


        :return: The volumes of this ServiceDockerComposeValue.
        :rtype: List[ServiceDockerComposeValueVolumesInner]
        """
        return self._volumes

    @volumes.setter
    def volumes(self, volumes):
        """Sets the volumes of this ServiceDockerComposeValue.


        :param volumes: The volumes of this ServiceDockerComposeValue.
        :type volumes: List[ServiceDockerComposeValueVolumesInner]
        """

        self._volumes = volumes

    @property
    def command(self):
        """Gets the command of this ServiceDockerComposeValue.


        :return: The command of this ServiceDockerComposeValue.
        :rtype: str
        """
        return self._command

    @command.setter
    def command(self, command):
        """Sets the command of this ServiceDockerComposeValue.


        :param command: The command of this ServiceDockerComposeValue.
        :type command: str
        """

        self._command = command

    @property
    def environment(self):
        """Gets the environment of this ServiceDockerComposeValue.

        Environment variables to be used at pipeline runtime

        :return: The environment of this ServiceDockerComposeValue.
        :rtype: Dict[str, str]
        """
        return self._environment

    @environment.setter
    def environment(self, environment):
        """Sets the environment of this ServiceDockerComposeValue.

        Environment variables to be used at pipeline runtime

        :param environment: The environment of this ServiceDockerComposeValue.
        :type environment: Dict[str, str]
        """

        self._environment = environment

    @property
    def oneshot(self):
        """Gets the oneshot of this ServiceDockerComposeValue.


        :return: The oneshot of this ServiceDockerComposeValue.
        :rtype: bool
        """
        return self._oneshot

    @oneshot.setter
    def oneshot(self, oneshot):
        """Sets the oneshot of this ServiceDockerComposeValue.


        :param oneshot: The oneshot of this ServiceDockerComposeValue.
        :type oneshot: bool
        """

        self._oneshot = oneshot
