# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.when_branch import WhenBranch
from openapi_server import util


class CriterionBuildAddlPropsWhen(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, branch: WhenBranch=None, building_tag: bool=None):
        """CriterionBuildAddlPropsWhen - a model defined in OpenAPI

        :param branch: The branch of this CriterionBuildAddlPropsWhen.
        :param building_tag: The building_tag of this CriterionBuildAddlPropsWhen.
        """
        self.openapi_types = {
            'branch': WhenBranch,
            'building_tag': bool
        }

        self.attribute_map = {
            'branch': 'branch',
            'building_tag': 'building_tag'
        }

        self._branch = branch
        self._building_tag = building_tag

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionBuildAddlPropsWhen':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild_addl_props_when of this CriterionBuildAddlPropsWhen.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def branch(self):
        """Gets the branch of this CriterionBuildAddlPropsWhen.


        :return: The branch of this CriterionBuildAddlPropsWhen.
        :rtype: WhenBranch
        """
        return self._branch

    @branch.setter
    def branch(self, branch):
        """Sets the branch of this CriterionBuildAddlPropsWhen.


        :param branch: The branch of this CriterionBuildAddlPropsWhen.
        :type branch: WhenBranch
        """

        self._branch = branch

    @property
    def building_tag(self):
        """Gets the building_tag of this CriterionBuildAddlPropsWhen.


        :return: The building_tag of this CriterionBuildAddlPropsWhen.
        :rtype: bool
        """
        return self._building_tag

    @building_tag.setter
    def building_tag(self, building_tag):
        """Sets the building_tag of this CriterionBuildAddlPropsWhen.


        :param building_tag: The building_tag of this CriterionBuildAddlPropsWhen.
        :type building_tag: bool
        """

        self._building_tag = building_tag
