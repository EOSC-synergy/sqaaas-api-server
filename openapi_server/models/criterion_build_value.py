# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_build_value_repos_inner import CriterionBuildValueReposInner
from openapi_server.models.criterion_build_value_when import CriterionBuildValueWhen
from openapi_server import util


class CriterionBuildValue(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, repos: List[CriterionBuildValueReposInner]=None, when: CriterionBuildValueWhen=None):
        """CriterionBuildValue - a model defined in OpenAPI

        :param repos: The repos of this CriterionBuildValue.
        :param when: The when of this CriterionBuildValue.
        """
        self.openapi_types = {
            'repos': List[CriterionBuildValueReposInner],
            'when': CriterionBuildValueWhen
        }

        self.attribute_map = {
            'repos': 'repos',
            'when': 'when'
        }

        self._repos = repos
        self._when = when

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionBuildValue':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild_value of this CriterionBuildValue.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repos(self):
        """Gets the repos of this CriterionBuildValue.

        List of repositories (from config:project_repos) for which the given criterion will be checked

        :return: The repos of this CriterionBuildValue.
        :rtype: List[CriterionBuildValueReposInner]
        """
        return self._repos

    @repos.setter
    def repos(self, repos):
        """Sets the repos of this CriterionBuildValue.

        List of repositories (from config:project_repos) for which the given criterion will be checked

        :param repos: The repos of this CriterionBuildValue.
        :type repos: List[CriterionBuildValueReposInner]
        """
        if repos is None:
            raise ValueError("Invalid value for `repos`, must not be `None`")

        self._repos = repos

    @property
    def when(self):
        """Gets the when of this CriterionBuildValue.


        :return: The when of this CriterionBuildValue.
        :rtype: CriterionBuildValueWhen
        """
        return self._when

    @when.setter
    def when(self, when):
        """Sets the when of this CriterionBuildValue.


        :param when: The when of this CriterionBuildValue.
        :type when: CriterionBuildValueWhen
        """

        self._when = when