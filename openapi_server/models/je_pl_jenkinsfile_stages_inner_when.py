# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class JePLJenkinsfileStagesInnerWhen(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, branches: List[str]=None):
        """JePLJenkinsfileStagesInnerWhen - a model defined in OpenAPI

        :param branches: The branches of this JePLJenkinsfileStagesInnerWhen.
        """
        self.openapi_types = {
            'branches': List[str]
        }

        self.attribute_map = {
            'branches': 'branches'
        }

        self._branches = branches

    @classmethod
    def from_dict(cls, dikt: dict) -> 'JePLJenkinsfileStagesInnerWhen':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The JePL_jenkinsfile_stages_inner_when of this JePLJenkinsfileStagesInnerWhen.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def branches(self):
        """Gets the branches of this JePLJenkinsfileStagesInnerWhen.


        :return: The branches of this JePLJenkinsfileStagesInnerWhen.
        :rtype: List[str]
        """
        return self._branches

    @branches.setter
    def branches(self, branches):
        """Sets the branches of this JePLJenkinsfileStagesInnerWhen.


        :param branches: The branches of this JePLJenkinsfileStagesInnerWhen.
        :type branches: List[str]
        """

        self._branches = branches
