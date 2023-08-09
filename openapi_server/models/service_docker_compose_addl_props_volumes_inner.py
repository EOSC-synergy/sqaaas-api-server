# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class ServiceDockerComposeAddlPropsVolumesInner(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, type: str=None, source: str=None, target: str=None):
        """ServiceDockerComposeAddlPropsVolumesInner - a model defined in OpenAPI

        :param type: The type of this ServiceDockerComposeAddlPropsVolumesInner.
        :param source: The source of this ServiceDockerComposeAddlPropsVolumesInner.
        :param target: The target of this ServiceDockerComposeAddlPropsVolumesInner.
        """
        self.openapi_types = {
            'type': str,
            'source': str,
            'target': str
        }

        self.attribute_map = {
            'type': 'type',
            'source': 'source',
            'target': 'target'
        }

        self._type = type
        self._source = source
        self._target = target

    @classmethod
    def from_dict(cls, dikt: dict) -> 'ServiceDockerComposeAddlPropsVolumesInner':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The ServiceDockerCompose_addl_props_volumes_inner of this ServiceDockerComposeAddlPropsVolumesInner.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        """Gets the type of this ServiceDockerComposeAddlPropsVolumesInner.


        :return: The type of this ServiceDockerComposeAddlPropsVolumesInner.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this ServiceDockerComposeAddlPropsVolumesInner.


        :param type: The type of this ServiceDockerComposeAddlPropsVolumesInner.
        :type type: str
        """
        allowed_values = ["bind"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}"
                .format(type, allowed_values)
            )

        self._type = type

    @property
    def source(self):
        """Gets the source of this ServiceDockerComposeAddlPropsVolumesInner.


        :return: The source of this ServiceDockerComposeAddlPropsVolumesInner.
        :rtype: str
        """
        return self._source

    @source.setter
    def source(self, source):
        """Sets the source of this ServiceDockerComposeAddlPropsVolumesInner.


        :param source: The source of this ServiceDockerComposeAddlPropsVolumesInner.
        :type source: str
        """

        self._source = source

    @property
    def target(self):
        """Gets the target of this ServiceDockerComposeAddlPropsVolumesInner.


        :return: The target of this ServiceDockerComposeAddlPropsVolumesInner.
        :rtype: str
        """
        return self._target

    @target.setter
    def target(self, target):
        """Sets the target of this ServiceDockerComposeAddlPropsVolumesInner.


        :param target: The target of this ServiceDockerComposeAddlPropsVolumesInner.
        :type target: str
        """

        self._target = target
