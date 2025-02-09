# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_build_repos import CriterionBuildRepos


class CriterionBuild(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, criterion: str = None, repos: List[CriterionBuildRepos] = None):
        """CriterionBuild - a model defined in OpenAPI

        :param criterion: The criterion of this CriterionBuild.
        :param repos: The repos of this CriterionBuild.
        """
        self.openapi_types = {"criterion": str, "repos": List[CriterionBuildRepos]}

        self.attribute_map = {"criterion": "criterion", "repos": "repos"}

        self._criterion = criterion
        self._repos = repos

    @classmethod
    def from_dict(cls, dikt: dict) -> "CriterionBuild":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild of this CriterionBuild.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def criterion(self):
        """Gets the criterion of this CriterionBuild.


        :return: The criterion of this CriterionBuild.
        :rtype: str
        """
        return self._criterion

    @criterion.setter
    def criterion(self, criterion):
        """Sets the criterion of this CriterionBuild.


        :param criterion: The criterion of this CriterionBuild.
        :type criterion: str
        """
        allowed_values = [
            "qc_style",
            "qc_unit",
            "qc_functional",
            "qc_security",
            "qc_doc",
        ]  # noqa: E501
        if criterion not in allowed_values:
            raise ValueError(
                "Invalid value for `criterion` ({0}), must be one of {1}".format(
                    criterion, allowed_values
                )
            )

        self._criterion = criterion

    @property
    def repos(self):
        """Gets the repos of this CriterionBuild.


        :return: The repos of this CriterionBuild.
        :rtype: List[CriterionBuildRepos]
        """
        return self._repos

    @repos.setter
    def repos(self, repos):
        """Sets the repos of this CriterionBuild.


        :param repos: The repos of this CriterionBuild.
        :type repos: List[CriterionBuildRepos]
        """
        if repos is None:
            raise ValueError("Invalid value for `repos`, must not be `None`")

        self._repos = repos
