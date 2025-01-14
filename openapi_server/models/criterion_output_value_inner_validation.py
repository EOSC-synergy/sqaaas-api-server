# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class CriterionOutputValueInnerValidation(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, valid: bool = None, data_unstructured: object = None):
        """CriterionOutputValueInnerValidation - a model defined in OpenAPI

        :param valid: The valid of this CriterionOutputValueInnerValidation.
        :param data_unstructured: The data_unstructured of this CriterionOutputValueInnerValidation.
        """
        self.openapi_types = {"valid": bool, "data_unstructured": object}

        self.attribute_map = {
            "valid": "valid",
            "data_unstructured": "data_unstructured",
        }

        self._valid = valid
        self._data_unstructured = data_unstructured

    @classmethod
    def from_dict(cls, dikt: dict) -> "CriterionOutputValueInnerValidation":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionOutput_value_inner_validation of this CriterionOutputValueInnerValidation.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def valid(self):
        """Gets the valid of this CriterionOutputValueInnerValidation.


        :return: The valid of this CriterionOutputValueInnerValidation.
        :rtype: bool
        """
        return self._valid

    @valid.setter
    def valid(self, valid):
        """Sets the valid of this CriterionOutputValueInnerValidation.


        :param valid: The valid of this CriterionOutputValueInnerValidation.
        :type valid: bool
        """

        self._valid = valid

    @property
    def data_unstructured(self):
        """Gets the data_unstructured of this CriterionOutputValueInnerValidation.


        :return: The data_unstructured of this CriterionOutputValueInnerValidation.
        :rtype: object
        """
        return self._data_unstructured

    @data_unstructured.setter
    def data_unstructured(self, data_unstructured):
        """Sets the data_unstructured of this CriterionOutputValueInnerValidation.


        :param data_unstructured: The data_unstructured of this CriterionOutputValueInnerValidation.
        :type data_unstructured: object
        """

        self._data_unstructured = data_unstructured
