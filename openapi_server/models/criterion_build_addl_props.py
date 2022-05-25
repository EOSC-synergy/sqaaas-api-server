# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_build_addl_props_repos_inner import CriterionBuildAddlPropsReposInner
from openapi_server.models.criterion_build_addl_props_when import CriterionBuildAddlPropsWhen
from openapi_server import util


class CriterionBuildAddlProps(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, repos: List[CriterionBuildAddlPropsReposInner]=None, when: CriterionBuildAddlPropsWhen=None):
        """CriterionBuildAddlProps - a model defined in OpenAPI

        :param repos: The repos of this CriterionBuildAddlProps.
        :param when: The when of this CriterionBuildAddlProps.
        """
        self.openapi_types = {
            'repos': List[CriterionBuildAddlPropsReposInner],
            'when': CriterionBuildAddlPropsWhen
        }

        self.attribute_map = {
            'repos': 'repos',
            'when': 'when'
        }

        self._repos = repos
        self._when = when

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionBuildAddlProps':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild_addl_props of this CriterionBuildAddlProps.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repos(self):
        """Gets the repos of this CriterionBuildAddlProps.

        List of repositories (from config:project_repos) for which the given criterion will be checked

        :return: The repos of this CriterionBuildAddlProps.
        :rtype: List[CriterionBuildAddlPropsReposInner]
        """
        return self._repos

    @repos.setter
    def repos(self, repos):
        """Sets the repos of this CriterionBuildAddlProps.

        List of repositories (from config:project_repos) for which the given criterion will be checked

        :param repos: The repos of this CriterionBuildAddlProps.
        :type repos: List[CriterionBuildAddlPropsReposInner]
        """
        if repos is None:
            raise ValueError("Invalid value for `repos`, must not be `None`")

        self._repos = repos

    @property
    def when(self):
        """Gets the when of this CriterionBuildAddlProps.


        :return: The when of this CriterionBuildAddlProps.
        :rtype: CriterionBuildAddlPropsWhen
        """
        return self._when

    @when.setter
    def when(self, when):
        """Sets the when of this CriterionBuildAddlProps.


        :param when: The when of this CriterionBuildAddlProps.
        :type when: CriterionBuildAddlPropsWhen
        """

        self._when = when
