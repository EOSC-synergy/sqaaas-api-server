# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.je_pl_jenkinsfile_stages_inner import JePLJenkinsfileStagesInner
from openapi_server import util


class JePLJenkinsfile(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, stages: List[JePLJenkinsfileStagesInner]=None):
        """JePLJenkinsfile - a model defined in OpenAPI

        :param stages: The stages of this JePLJenkinsfile.
        """
        self.openapi_types = {
            'stages': List[JePLJenkinsfileStagesInner]
        }

        self.attribute_map = {
            'stages': 'stages'
        }

        self._stages = stages

    @classmethod
    def from_dict(cls, dikt: dict) -> 'JePLJenkinsfile':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The JePL_jenkinsfile of this JePLJenkinsfile.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def stages(self):
        """Gets the stages of this JePLJenkinsfile.


        :return: The stages of this JePLJenkinsfile.
        :rtype: List[JePLJenkinsfileStagesInner]
        """
        return self._stages

    @stages.setter
    def stages(self, stages):
        """Sets the stages of this JePLJenkinsfile.


        :param stages: The stages of this JePLJenkinsfile.
        :type stages: List[JePLJenkinsfileStagesInner]
        """

        self._stages = stages
