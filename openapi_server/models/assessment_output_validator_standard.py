# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AssessmentOutputValidatorStandard(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, title: str = None, version: str = None, url: str = None):
        """AssessmentOutputValidatorStandard - a model defined in OpenAPI

        :param title: The title of this AssessmentOutputValidatorStandard.
        :param version: The version of this AssessmentOutputValidatorStandard.
        :param url: The url of this AssessmentOutputValidatorStandard.
        """
        self.openapi_types = {"title": str, "version": str, "url": str}

        self.attribute_map = {"title": "title", "version": "version", "url": "url"}

        self._title = title
        self._version = version
        self._url = url

    @classmethod
    def from_dict(cls, dikt: dict) -> "AssessmentOutputValidatorStandard":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutputValidatorStandard of this AssessmentOutputValidatorStandard.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def title(self):
        """Gets the title of this AssessmentOutputValidatorStandard.

        Standard title

        :return: The title of this AssessmentOutputValidatorStandard.
        :rtype: str
        """
        return self._title

    @title.setter
    def title(self, title):
        """Sets the title of this AssessmentOutputValidatorStandard.

        Standard title

        :param title: The title of this AssessmentOutputValidatorStandard.
        :type title: str
        """

        self._title = title

    @property
    def version(self):
        """Gets the version of this AssessmentOutputValidatorStandard.

        Standard version

        :return: The version of this AssessmentOutputValidatorStandard.
        :rtype: str
        """
        return self._version

    @version.setter
    def version(self, version):
        """Sets the version of this AssessmentOutputValidatorStandard.

        Standard version

        :param version: The version of this AssessmentOutputValidatorStandard.
        :type version: str
        """

        self._version = version

    @property
    def url(self):
        """Gets the url of this AssessmentOutputValidatorStandard.

        URL containing the standard's specification

        :return: The url of this AssessmentOutputValidatorStandard.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this AssessmentOutputValidatorStandard.

        URL containing the standard's specification

        :param url: The url of this AssessmentOutputValidatorStandard.
        :type url: str
        """

        self._url = url
