# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.assessment_output_report_addl_props_coverage import \
    AssessmentOutputReportAddlPropsCoverage
from openapi_server.models.assessment_output_subcriteria import \
    AssessmentOutputSubcriteria
from openapi_server.models.base_model_ import Model


class AssessmentOutputReportAddlProps(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        valid: bool = False,
        filtered_reason: List[str] = [],
        subcriteria: Dict[str, AssessmentOutputSubcriteria] = None,
        coverage: AssessmentOutputReportAddlPropsCoverage = None,
    ):
        """AssessmentOutputReportAddlProps - a model defined in OpenAPI

        :param valid: The valid of this AssessmentOutputReportAddlProps.
        :param filtered_reason: The filtered_reason of this AssessmentOutputReportAddlProps.
        :param subcriteria: The subcriteria of this AssessmentOutputReportAddlProps.
        :param coverage: The coverage of this AssessmentOutputReportAddlProps.
        """
        self.openapi_types = {
            "valid": bool,
            "filtered_reason": List[str],
            "subcriteria": Dict[str, AssessmentOutputSubcriteria],
            "coverage": AssessmentOutputReportAddlPropsCoverage,
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
    def from_dict(cls, dikt: dict) -> "AssessmentOutputReportAddlProps":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutput_report_addl_props of this AssessmentOutputReportAddlProps.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def valid(self):
        """Gets the valid of this AssessmentOutputReportAddlProps.

        Overall validity of the criterion

        :return: The valid of this AssessmentOutputReportAddlProps.
        :rtype: bool
        """
        return self._valid

    @valid.setter
    def valid(self, valid):
        """Sets the valid of this AssessmentOutputReportAddlProps.

        Overall validity of the criterion

        :param valid: The valid of this AssessmentOutputReportAddlProps.
        :type valid: bool
        """

        self._valid = valid

    @property
    def filtered_reason(self):
        """Gets the filtered_reason of this AssessmentOutputReportAddlProps.

        Contains the reason why the criterion was filtered out (if applicable)

        :return: The filtered_reason of this AssessmentOutputReportAddlProps.
        :rtype: List[str]
        """
        return self._filtered_reason

    @filtered_reason.setter
    def filtered_reason(self, filtered_reason):
        """Sets the filtered_reason of this AssessmentOutputReportAddlProps.

        Contains the reason why the criterion was filtered out (if applicable)

        :param filtered_reason: The filtered_reason of this AssessmentOutputReportAddlProps.
        :type filtered_reason: List[str]
        """

        self._filtered_reason = filtered_reason

    @property
    def subcriteria(self):
        """Gets the subcriteria of this AssessmentOutputReportAddlProps.


        :return: The subcriteria of this AssessmentOutputReportAddlProps.
        :rtype: Dict[str, AssessmentOutputSubcriteria]
        """
        return self._subcriteria

    @subcriteria.setter
    def subcriteria(self, subcriteria):
        """Sets the subcriteria of this AssessmentOutputReportAddlProps.


        :param subcriteria: The subcriteria of this AssessmentOutputReportAddlProps.
        :type subcriteria: Dict[str, AssessmentOutputSubcriteria]
        """

        self._subcriteria = subcriteria

    @property
    def coverage(self):
        """Gets the coverage of this AssessmentOutputReportAddlProps.


        :return: The coverage of this AssessmentOutputReportAddlProps.
        :rtype: AssessmentOutputReportAddlPropsCoverage
        """
        return self._coverage

    @coverage.setter
    def coverage(self, coverage):
        """Sets the coverage of this AssessmentOutputReportAddlProps.


        :param coverage: The coverage of this AssessmentOutputReportAddlProps.
        :type coverage: AssessmentOutputReportAddlPropsCoverage
        """

        self._coverage = coverage
