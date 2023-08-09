# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.je_pl_composer import JePLComposer
from openapi_server import util


class InlineResponse2002(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, file_name: str=None, content: JePLComposer=None):
        """InlineResponse2002 - a model defined in OpenAPI

        :param file_name: The file_name of this InlineResponse2002.
        :param content: The content of this InlineResponse2002.
        """
        self.openapi_types = {
            'file_name': str,
            'content': JePLComposer
        }

        self.attribute_map = {
            'file_name': 'file_name',
            'content': 'content'
        }

        self._file_name = file_name
        self._content = content

    @classmethod
    def from_dict(cls, dikt: dict) -> 'InlineResponse2002':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The inline_response_200_2 of this InlineResponse2002.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def file_name(self):
        """Gets the file_name of this InlineResponse2002.


        :return: The file_name of this InlineResponse2002.
        :rtype: str
        """
        return self._file_name

    @file_name.setter
    def file_name(self, file_name):
        """Sets the file_name of this InlineResponse2002.


        :param file_name: The file_name of this InlineResponse2002.
        :type file_name: str
        """

        self._file_name = file_name

    @property
    def content(self):
        """Gets the content of this InlineResponse2002.


        :return: The content of this InlineResponse2002.
        :rtype: JePLComposer
        """
        return self._content

    @content.setter
    def content(self, content):
        """Sets the content of this InlineResponse2002.


        :param content: The content of this InlineResponse2002.
        :type content: JePLComposer
        """

        self._content = content
