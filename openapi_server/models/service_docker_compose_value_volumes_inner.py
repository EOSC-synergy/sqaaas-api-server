# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class ServiceDockerComposeValueVolumesInner(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, type: str = None, source: str = None, target: str = None):
        """ServiceDockerComposeValueVolumesInner - a model defined in OpenAPI

        :param type: The type of this ServiceDockerComposeValueVolumesInner.
        :param source: The source of this ServiceDockerComposeValueVolumesInner.
        :param target: The target of this ServiceDockerComposeValueVolumesInner.
        """
        self.openapi_types = {"type": str, "source": str, "target": str}

        self.attribute_map = {"type": "type", "source": "source", "target": "target"}

        self._type = type
        self._source = source
        self._target = target

    @classmethod
    def from_dict(cls, dikt: dict) -> "ServiceDockerComposeValueVolumesInner":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_value_volumes_inner of this ServiceDockerComposeValueVolumesInner.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        """Gets the type of this ServiceDockerComposeValueVolumesInner.


        :return: The type of this ServiceDockerComposeValueVolumesInner.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this ServiceDockerComposeValueVolumesInner.


        :param type: The type of this ServiceDockerComposeValueVolumesInner.
        :type type: str
        """
        allowed_values = ["bind"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}".format(
                    type, allowed_values
                )
            )

        self._type = type

    @property
    def source(self):
        """Gets the source of this ServiceDockerComposeValueVolumesInner.


        :return: The source of this ServiceDockerComposeValueVolumesInner.
        :rtype: str
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this ServiceDockerComposeValueVolumesInner.


        :param source: The source of this ServiceDockerComposeValueVolumesInner.
        :type source: str
        """

        self._source = source

    @property
    def target(self):
        """Gets the target of this ServiceDockerComposeValueVolumesInner.


        :return: The target of this ServiceDockerComposeValueVolumesInner.
        :rtype: str
        """
        return self._target

    @target.setter
    def target(self, target):
        """Sets the target of this ServiceDockerComposeValueVolumesInner.


        :param target: The target of this ServiceDockerComposeValueVolumesInner.
        :type target: str
        """

        self._target = target
