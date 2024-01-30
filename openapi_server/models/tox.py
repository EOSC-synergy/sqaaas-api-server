# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.tox_tox import ToxTox
from openapi_server import util


class Tox(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, tox: ToxTox = None):
        """Tox - a model defined in OpenAPI

        :param tox: The tox of this Tox.
        """
        self.openapi_types = {"tox": ToxTox}

        self.attribute_map = {"tox": "tox"}

        self._tox = tox

    @classmethod
    def from_dict(cls, dikt: dict) -> "Tox":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Tox of this Tox.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def tox(self):
        """Gets the tox of this Tox.


        :return: The tox of this Tox.
        :rtype: ToxTox
        """
        return self._tox

    @tox.setter
    def tox(self, tox):
        """Sets the tox of this Tox.


        :param tox: The tox of this Tox.
        :type tox: ToxTox
        """

        self._tox = tox
