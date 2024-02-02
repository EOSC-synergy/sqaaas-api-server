# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class ToxSimplified(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, testenv: List[str] = ["ALL"], tox_file: str = "tox.ini"):
        """ToxSimplified - a model defined in OpenAPI

        :param testenv: The testenv of this ToxSimplified.
        :param tox_file: The tox_file of this ToxSimplified.
        """
        self.openapi_types = {"testenv": List[str], "tox_file": str}

        self.attribute_map = {"testenv": "testenv", "tox_file": "tox_file"}

        self._testenv = testenv
        self._tox_file = tox_file

    @classmethod
    def from_dict(cls, dikt: dict) -> "ToxSimplified":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Tox_simplified of this ToxSimplified.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def testenv(self):
        """Gets the testenv of this ToxSimplified.


        :return: The testenv of this ToxSimplified.
        :rtype: List[str]
        """
        return self._testenv

    @testenv.setter
    def testenv(self, testenv):
        """Sets the testenv of this ToxSimplified.


        :param testenv: The testenv of this ToxSimplified.
        :type testenv: List[str]
        """

        self._testenv = testenv

    @property
    def tox_file(self):
        """Gets the tox_file of this ToxSimplified.


        :return: The tox_file of this ToxSimplified.
        :rtype: str
        """
        return self._tox_file

    @tox_file.setter
    def tox_file(self, tox_file):
        """Sets the tox_file of this ToxSimplified.


        :param tox_file: The tox_file of this ToxSimplified.
        :type tox_file: str
        """

        self._tox_file = tox_file
