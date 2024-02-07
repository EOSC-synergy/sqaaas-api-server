# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_output_value_inner_validation import (
    CriterionOutputValueInnerValidation,
)


class CriterionOutputValueInner(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        status: str = None,
        stdout_command: str = None,
        stdout_text: str = None,
        tool: str = None,
        validator: str = None,
        validation: CriterionOutputValueInnerValidation = None,
    ):
        """CriterionOutputValueInner - a model defined in OpenAPI

        :param status: The status of this CriterionOutputValueInner.
        :param stdout_command: The stdout_command of this CriterionOutputValueInner.
        :param stdout_text: The stdout_text of this CriterionOutputValueInner.
        :param tool: The tool of this CriterionOutputValueInner.
        :param validator: The validator of this CriterionOutputValueInner.
        :param validation: The validation of this CriterionOutputValueInner.
        """
        self.openapi_types = {
            "status": str,
            "stdout_command": str,
            "stdout_text": str,
            "tool": str,
            "validator": str,
            "validation": CriterionOutputValueInnerValidation,
        }

        self.attribute_map = {
            "status": "status",
            "stdout_command": "stdout_command",
            "stdout_text": "stdout_text",
            "tool": "tool",
            "validator": "validator",
            "validation": "validation",
        }

        self._status = status
        self._stdout_command = stdout_command
        self._stdout_text = stdout_text
        self._tool = tool
        self._validator = validator
        self._validation = validation

    @classmethod
    def from_dict(cls, dikt: dict) -> "CriterionOutputValueInner":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionOutput_value_inner of this CriterionOutputValueInner.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def status(self):
        """Gets the status of this CriterionOutputValueInner.


        :return: The status of this CriterionOutputValueInner.
        :rtype: str
        """
        return self._status

    @status.setter
    def status(self, status):
        """Sets the status of this CriterionOutputValueInner.


        :param status: The status of this CriterionOutputValueInner.
        :type status: str
        """
        allowed_values = ["SUCCESS", "FAILED"]  # noqa: E501
        if status not in allowed_values:
            raise ValueError(
                "Invalid value for `status` ({0}), must be one of {1}".format(
                    status, allowed_values
                )
            )

        self._status = status

    @property
    def stdout_command(self):
        """Gets the stdout_command of this CriterionOutputValueInner.


        :return: The stdout_command of this CriterionOutputValueInner.
        :rtype: str
        """
        return self._stdout_command

    @stdout_command.setter
    def stdout_command(self, stdout_command):
        """Sets the stdout_command of this CriterionOutputValueInner.


        :param stdout_command: The stdout_command of this CriterionOutputValueInner.
        :type stdout_command: str
        """

        self._stdout_command = stdout_command

    @property
    def stdout_text(self):
        """Gets the stdout_text of this CriterionOutputValueInner.


        :return: The stdout_text of this CriterionOutputValueInner.
        :rtype: str
        """
        return self._stdout_text

    @stdout_text.setter
    def stdout_text(self, stdout_text):
        """Sets the stdout_text of this CriterionOutputValueInner.


        :param stdout_text: The stdout_text of this CriterionOutputValueInner.
        :type stdout_text: str
        """

        self._stdout_text = stdout_text

    @property
    def tool(self):
        """Gets the tool of this CriterionOutputValueInner.


        :return: The tool of this CriterionOutputValueInner.
        :rtype: str
        """
        return self._tool

    @tool.setter
    def tool(self, tool):
        """Sets the tool of this CriterionOutputValueInner.


        :param tool: The tool of this CriterionOutputValueInner.
        :type tool: str
        """

        self._tool = tool

    @property
    def validator(self):
        """Gets the validator of this CriterionOutputValueInner.


        :return: The validator of this CriterionOutputValueInner.
        :rtype: str
        """
        return self._validator

    @validator.setter
    def validator(self, validator):
        """Sets the validator of this CriterionOutputValueInner.


        :param validator: The validator of this CriterionOutputValueInner.
        :type validator: str
        """

        self._validator = validator

    @property
    def validation(self):
        """Gets the validation of this CriterionOutputValueInner.


        :return: The validation of this CriterionOutputValueInner.
        :rtype: CriterionOutputValueInnerValidation
        """
        return self._validation

    @validation.setter
    def validation(self, validation):
        """Sets the validation of this CriterionOutputValueInner.


        :param validation: The validation of this CriterionOutputValueInner.
        :type validation: CriterionOutputValueInnerValidation
        """

        self._validation = validation
