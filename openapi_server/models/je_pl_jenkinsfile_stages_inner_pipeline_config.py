# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class JePLJenkinsfileStagesInnerPipelineConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, config_file: str=None, base_repository: str=None, base_branch: str=None, credentials_id: str=None, jepl_validator_docker_image: str=None):
        """JePLJenkinsfileStagesInnerPipelineConfig - a model defined in OpenAPI

        :param config_file: The config_file of this JePLJenkinsfileStagesInnerPipelineConfig.
        :param base_repository: The base_repository of this JePLJenkinsfileStagesInnerPipelineConfig.
        :param base_branch: The base_branch of this JePLJenkinsfileStagesInnerPipelineConfig.
        :param credentials_id: The credentials_id of this JePLJenkinsfileStagesInnerPipelineConfig.
        :param jepl_validator_docker_image: The jepl_validator_docker_image of this JePLJenkinsfileStagesInnerPipelineConfig.
        """
        self.openapi_types = {
            'config_file': str,
            'base_repository': str,
            'base_branch': str,
            'credentials_id': str,
            'jepl_validator_docker_image': str
        }

        self.attribute_map = {
            'config_file': 'config_file',
            'base_repository': 'base_repository',
            'base_branch': 'base_branch',
            'credentials_id': 'credentials_id',
            'jepl_validator_docker_image': 'jepl_validator_docker_image'
        }

        self._config_file = config_file
        self._base_repository = base_repository
        self._base_branch = base_branch
        self._credentials_id = credentials_id
        self._jepl_validator_docker_image = jepl_validator_docker_image

    @classmethod
    def from_dict(cls, dikt: dict) -> 'JePLJenkinsfileStagesInnerPipelineConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The JePL_jenkinsfile_stages_inner_pipeline_config of this JePLJenkinsfileStagesInnerPipelineConfig.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def config_file(self):
        """Gets the config_file of this JePLJenkinsfileStagesInnerPipelineConfig.


        :return: The config_file of this JePLJenkinsfileStagesInnerPipelineConfig.
        :rtype: str
        """
        return self._config_file

    @config_file.setter
    def config_file(self, config_file):
        """Sets the config_file of this JePLJenkinsfileStagesInnerPipelineConfig.


        :param config_file: The config_file of this JePLJenkinsfileStagesInnerPipelineConfig.
        :type config_file: str
        """

        self._config_file = config_file

    @property
    def base_repository(self):
        """Gets the base_repository of this JePLJenkinsfileStagesInnerPipelineConfig.


        :return: The base_repository of this JePLJenkinsfileStagesInnerPipelineConfig.
        :rtype: str
        """
        return self._base_repository

    @base_repository.setter
    def base_repository(self, base_repository):
        """Sets the base_repository of this JePLJenkinsfileStagesInnerPipelineConfig.


        :param base_repository: The base_repository of this JePLJenkinsfileStagesInnerPipelineConfig.
        :type base_repository: str
        """

        self._base_repository = base_repository

    @property
    def base_branch(self):
        """Gets the base_branch of this JePLJenkinsfileStagesInnerPipelineConfig.


        :return: The base_branch of this JePLJenkinsfileStagesInnerPipelineConfig.
        :rtype: str
        """
        return self._base_branch

    @base_branch.setter
    def base_branch(self, base_branch):
        """Sets the base_branch of this JePLJenkinsfileStagesInnerPipelineConfig.


        :param base_branch: The base_branch of this JePLJenkinsfileStagesInnerPipelineConfig.
        :type base_branch: str
        """

        self._base_branch = base_branch

    @property
    def credentials_id(self):
        """Gets the credentials_id of this JePLJenkinsfileStagesInnerPipelineConfig.


        :return: The credentials_id of this JePLJenkinsfileStagesInnerPipelineConfig.
        :rtype: str
        """
        return self._credentials_id

    @credentials_id.setter
    def credentials_id(self, credentials_id):
        """Sets the credentials_id of this JePLJenkinsfileStagesInnerPipelineConfig.


        :param credentials_id: The credentials_id of this JePLJenkinsfileStagesInnerPipelineConfig.
        :type credentials_id: str
        """

        self._credentials_id = credentials_id

    @property
    def jepl_validator_docker_image(self):
        """Gets the jepl_validator_docker_image of this JePLJenkinsfileStagesInnerPipelineConfig.


        :return: The jepl_validator_docker_image of this JePLJenkinsfileStagesInnerPipelineConfig.
        :rtype: str
        """
        return self._jepl_validator_docker_image

    @jepl_validator_docker_image.setter
    def jepl_validator_docker_image(self, jepl_validator_docker_image):
        """Sets the jepl_validator_docker_image of this JePLJenkinsfileStagesInnerPipelineConfig.


        :param jepl_validator_docker_image: The jepl_validator_docker_image of this JePLJenkinsfileStagesInnerPipelineConfig.
        :type jepl_validator_docker_image: str
        """

        self._jepl_validator_docker_image = jepl_validator_docker_image