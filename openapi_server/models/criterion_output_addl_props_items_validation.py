# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class CriterionOutputAddlPropsItemsValidation(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, valid: bool=None, data_unstructured: object=None):
        """CriterionOutputAddlPropsItemsValidation - a model defined in OpenAPI

        :param valid: The valid of this CriterionOutputAddlPropsItemsValidation.
        :param data_unstructured: The data_unstructured of this CriterionOutputAddlPropsItemsValidation.
        """
        self.openapi_types = {
            'valid': bool,
            'data_unstructured': object
        }

        self.attribute_map = {
            'valid': 'valid',
            'data_unstructured': 'data_unstructured'
        }

        self._valid = valid
        self._data_unstructured = data_unstructured

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionOutputAddlPropsItemsValidation':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionOutput_addl_propsItems_validation of this CriterionOutputAddlPropsItemsValidation.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def valid(self):
        """Gets the valid of this CriterionOutputAddlPropsItemsValidation.


        :return: The valid of this CriterionOutputAddlPropsItemsValidation.
        :rtype: bool
        """
        return self._valid

    @valid.setter
    def valid(self, valid):
        """Sets the valid of this CriterionOutputAddlPropsItemsValidation.


        :param valid: The valid of this CriterionOutputAddlPropsItemsValidation.
        :type valid: bool
        """

        self._valid = valid

    @property
    def data_unstructured(self):
        """Gets the data_unstructured of this CriterionOutputAddlPropsItemsValidation.


        :return: The data_unstructured of this CriterionOutputAddlPropsItemsValidation.
        :rtype: object
        """
        return self._data_unstructured

    @data_unstructured.setter
    def data_unstructured(self, data_unstructured):
        """Sets the data_unstructured of this CriterionOutputAddlPropsItemsValidation.


        :param data_unstructured: The data_unstructured of this CriterionOutputAddlPropsItemsValidation.
        :type data_unstructured: object
        """

        self._data_unstructured = data_unstructured
