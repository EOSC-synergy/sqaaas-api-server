# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.assessment_output_report_value_coverage import (
    AssessmentOutputReportValueCoverage,
)
from openapi_server.models.assessment_output_subcriteria import (
    AssessmentOutputSubcriteria,
)
from openapi_server import util


class AssessmentOutputReportValue(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        valid: bool = False,
        filtered_reason: List[str] = [],
        subcriteria: Dict[str, AssessmentOutputSubcriteria] = None,
        coverage: AssessmentOutputReportValueCoverage = None,
    ):
        """AssessmentOutputReportValue - a model defined in OpenAPI

        :param valid: The valid of this AssessmentOutputReportValue.
        :param filtered_reason: The filtered_reason of this AssessmentOutputReportValue.
        :param subcriteria: The subcriteria of this AssessmentOutputReportValue.
        :param coverage: The coverage of this AssessmentOutputReportValue.
        """
        self.openapi_types = {
            "valid": bool,
            "filtered_reason": List[str],
            "subcriteria": Dict[str, AssessmentOutputSubcriteria],
            "coverage": AssessmentOutputReportValueCoverage,
        }

        self.attribute_map = {
            "valid": "valid",
            "filtered_reason": "filtered_reason",
            "subcriteria": "subcriteria",
            "coverage": "coverage",
        }

        self._valid = valid
        self._filtered_reason = filtered_reason
        self._subcriteria = subcriteria
        self._coverage = coverage

    @classmethod
    def from_dict(cls, dikt: dict) -> "AssessmentOutputReportValue":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutput_report_value of this AssessmentOutputReportValue.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def valid(self):
        """Gets the valid of this AssessmentOutputReportValue.

        Overall validity of the criterion

        :return: The valid of this AssessmentOutputReportValue.
        :rtype: bool
        """
        return self._valid

    @valid.setter
    def valid(self, valid):
        """Sets the valid of this AssessmentOutputReportValue.

        Overall validity of the criterion

        :param valid: The valid of this AssessmentOutputReportValue.
        :type valid: bool
        """

        self._valid = valid

    @property
    def filtered_reason(self):
        """Gets the filtered_reason of this AssessmentOutputReportValue.

        Contains the reason why the criterion was filtered out (if applicable)

        :return: The filtered_reason of this AssessmentOutputReportValue.
        :rtype: List[str]
        """
        return self._filtered_reason

    @filtered_reason.setter
    def filtered_reason(self, filtered_reason):
        """Sets the filtered_reason of this AssessmentOutputReportValue.

        Contains the reason why the criterion was filtered out (if applicable)

        :param filtered_reason: The filtered_reason of this AssessmentOutputReportValue.
        :type filtered_reason: List[str]
        """

        self._filtered_reason = filtered_reason

    @property
    def subcriteria(self):
        """Gets the subcriteria of this AssessmentOutputReportValue.


        :return: The subcriteria of this AssessmentOutputReportValue.
        :rtype: Dict[str, AssessmentOutputSubcriteria]
        """
        return self._subcriteria

    @subcriteria.setter
    def subcriteria(self, subcriteria):
        """Sets the subcriteria of this AssessmentOutputReportValue.


        :param subcriteria: The subcriteria of this AssessmentOutputReportValue.
        :type subcriteria: Dict[str, AssessmentOutputSubcriteria]
        """

        self._subcriteria = subcriteria

    @property
    def coverage(self):
        """Gets the coverage of this AssessmentOutputReportValue.


        :return: The coverage of this AssessmentOutputReportValue.
        :rtype: AssessmentOutputReportValueCoverage
        """
        return self._coverage

    @coverage.setter
    def coverage(self, coverage):
        """Sets the coverage of this AssessmentOutputReportValue.


        :param coverage: The coverage of this AssessmentOutputReportValue.
        :type coverage: AssessmentOutputReportValueCoverage
        """

        self._coverage = coverage
