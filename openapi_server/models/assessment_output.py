# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.assessment_output_badge import AssessmentOutputBadge
from openapi_server.models.assessment_output_meta import AssessmentOutputMeta
from openapi_server.models.assessment_output_report_value import AssessmentOutputReportValue
from openapi_server.models.assessment_output_repository import AssessmentOutputRepository
from openapi_server import util


class AssessmentOutput(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, meta: AssessmentOutputMeta=None, repository: List[AssessmentOutputRepository]=None, report: Dict[str, AssessmentOutputReportValue]=None, badge: AssessmentOutputBadge=None):
        """AssessmentOutput - a model defined in OpenAPI

        :param meta: The meta of this AssessmentOutput.
        :param repository: The repository of this AssessmentOutput.
        :param report: The report of this AssessmentOutput.
        :param badge: The badge of this AssessmentOutput.
        """
        self.openapi_types = {
            'meta': AssessmentOutputMeta,
            'repository': List[AssessmentOutputRepository],
            'report': Dict[str, AssessmentOutputReportValue],
            'badge': AssessmentOutputBadge
        }

        self.attribute_map = {
            'meta': 'meta',
            'repository': 'repository',
            'report': 'report',
            'badge': 'badge'
        }

        self._meta = meta
        self._repository = repository
        self._report = report
        self._badge = badge

    @classmethod
    def from_dict(cls, dikt: dict) -> 'AssessmentOutput':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutput of this AssessmentOutput.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def meta(self):
        """Gets the meta of this AssessmentOutput.


        :return: The meta of this AssessmentOutput.
        :rtype: AssessmentOutputMeta
        """
        return self._meta

    @meta.setter
    def meta(self, meta):
        """Sets the meta of this AssessmentOutput.


        :param meta: The meta of this AssessmentOutput.
        :type meta: AssessmentOutputMeta
        """

        self._meta = meta

    @property
    def repository(self):
        """Gets the repository of this AssessmentOutput.

        Details about the (code, data) repository

        :return: The repository of this AssessmentOutput.
        :rtype: List[AssessmentOutputRepository]
        """
        return self._repository

    @repository.setter
    def repository(self, repository):
        """Sets the repository of this AssessmentOutput.

        Details about the (code, data) repository

        :param repository: The repository of this AssessmentOutput.
        :type repository: List[AssessmentOutputRepository]
        """

        self._repository = repository

    @property
    def report(self):
        """Gets the report of this AssessmentOutput.


        :return: The report of this AssessmentOutput.
        :rtype: Dict[str, AssessmentOutputReportValue]
        """
        return self._report

    @report.setter
    def report(self, report):
        """Sets the report of this AssessmentOutput.


        :param report: The report of this AssessmentOutput.
        :type report: Dict[str, AssessmentOutputReportValue]
        """

        self._report = report

    @property
    def badge(self):
        """Gets the badge of this AssessmentOutput.


        :return: The badge of this AssessmentOutput.
        :rtype: AssessmentOutputBadge
        """
        return self._badge

    @badge.setter
    def badge(self, badge):
        """Sets the badge of this AssessmentOutput.


        :param badge: The badge of this AssessmentOutput.
        :type badge: AssessmentOutputBadge
        """

        self._badge = badge
