# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.repository import Repository
from openapi_server.models.tool import Tool
from openapi_server import util


class AssessmentDeployment(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, repo_deploy: Repository = None, deploy_tool: Tool = None):
        """AssessmentDeployment - a model defined in OpenAPI

        :param repo_deploy: The repo_deploy of this AssessmentDeployment.
        :param deploy_tool: The deploy_tool of this AssessmentDeployment.
        """
        self.openapi_types = {"repo_deploy": Repository, "deploy_tool": Tool}

        self.attribute_map = {
            "repo_deploy": "repo_deploy",
            "deploy_tool": "deploy_tool",
        }

        self._repo_deploy = repo_deploy
        self._deploy_tool = deploy_tool

    @classmethod
    def from_dict(cls, dikt: dict) -> "AssessmentDeployment":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentDeployment of this AssessmentDeployment.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repo_deploy(self):
        """Gets the repo_deploy of this AssessmentDeployment.


        :return: The repo_deploy of this AssessmentDeployment.
        :rtype: Repository
        """
        return self._repo_deploy

    @repo_deploy.setter
    def repo_deploy(self, repo_deploy):
        """Sets the repo_deploy of this AssessmentDeployment.


        :param repo_deploy: The repo_deploy of this AssessmentDeployment.
        :type repo_deploy: Repository
        """

        self._repo_deploy = repo_deploy

    @property
    def deploy_tool(self):
        """Gets the deploy_tool of this AssessmentDeployment.


        :return: The deploy_tool of this AssessmentDeployment.
        :rtype: Tool
        """
        return self._deploy_tool

    @deploy_tool.setter
    def deploy_tool(self, deploy_tool):
        """Sets the deploy_tool of this AssessmentDeployment.


        :param deploy_tool: The deploy_tool of this AssessmentDeployment.
        :type deploy_tool: Tool
        """

        self._deploy_tool = deploy_tool
