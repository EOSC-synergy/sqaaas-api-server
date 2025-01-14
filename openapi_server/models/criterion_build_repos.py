# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model
from openapi_server.models.commands import Commands


class CriterionBuildRepos(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self, repo_id: str = None, container: str = None, build_tool: Commands = None
    ):
        """CriterionBuildRepos - a model defined in OpenAPI

        :param repo_id: The repo_id of this CriterionBuildRepos.
        :param container: The container of this CriterionBuildRepos.
        :param build_tool: The build_tool of this CriterionBuildRepos.
        """
        self.openapi_types = {"repo_id": str, "container": str, "build_tool": Commands}

        self.attribute_map = {
            "repo_id": "repo_id",
            "container": "container",
            "build_tool": "build_tool",
        }

        self._repo_id = repo_id
        self._container = container
        self._build_tool = build_tool

    @classmethod
    def from_dict(cls, dikt: dict) -> "CriterionBuildRepos":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild_repos of this CriterionBuildRepos.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repo_id(self):
        """Gets the repo_id of this CriterionBuildRepos.


        :return: The repo_id of this CriterionBuildRepos.
        :rtype: str
        """
        return self._repo_id

    @repo_id.setter
    def repo_id(self, repo_id):
        """Sets the repo_id of this CriterionBuildRepos.


        :param repo_id: The repo_id of this CriterionBuildRepos.
        :type repo_id: str
        """
        if repo_id is None:
            raise ValueError("Invalid value for `repo_id`, must not be `None`")

        self._repo_id = repo_id

    @property
    def container(self):
        """Gets the container of this CriterionBuildRepos.


        :return: The container of this CriterionBuildRepos.
        :rtype: str
        """
        return self._container

    @container.setter
    def container(self, container):
        """Sets the container of this CriterionBuildRepos.


        :param container: The container of this CriterionBuildRepos.
        :type container: str
        """
        if container is None:
            raise ValueError("Invalid value for `container`, must not be `None`")

        self._container = container

    @property
    def build_tool(self):
        """Gets the build_tool of this CriterionBuildRepos.


        :return: The build_tool of this CriterionBuildRepos.
        :rtype: Commands
        """
        return self._build_tool

    @build_tool.setter
    def build_tool(self, build_tool):
        """Sets the build_tool of this CriterionBuildRepos.


        :param build_tool: The build_tool of this CriterionBuildRepos.
        :type build_tool: Commands
        """
        if build_tool is None:
            raise ValueError("Invalid value for `build_tool`, must not be `None`")

        self._build_tool = build_tool
