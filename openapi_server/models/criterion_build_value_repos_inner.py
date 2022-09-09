# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.tool import Tool
from openapi_server.models.tox_simplified import ToxSimplified
from openapi_server import util


class CriterionBuildValueReposInner(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, repo_url: str=None, container: str=None, commands: List[str]=None, tox: ToxSimplified=None, tool: Tool=None):
        """CriterionBuildValueReposInner - a model defined in OpenAPI

        :param repo_url: The repo_url of this CriterionBuildValueReposInner.
        :param container: The container of this CriterionBuildValueReposInner.
        :param commands: The commands of this CriterionBuildValueReposInner.
        :param tox: The tox of this CriterionBuildValueReposInner.
        :param tool: The tool of this CriterionBuildValueReposInner.
        """
        self.openapi_types = {
            'repo_url': str,
            'container': str,
            'commands': List[str],
            'tox': ToxSimplified,
            'tool': Tool
        }

        self.attribute_map = {
            'repo_url': 'repo_url',
            'container': 'container',
            'commands': 'commands',
            'tox': 'tox',
            'tool': 'tool'
        }

        self._repo_url = repo_url
        self._container = container
        self._commands = commands
        self._tox = tox
        self._tool = tool

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionBuildValueReposInner':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionBuild_value_repos_inner of this CriterionBuildValueReposInner.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repo_url(self):
        """Gets the repo_url of this CriterionBuildValueReposInner.

        URL of the repository

        :return: The repo_url of this CriterionBuildValueReposInner.
        :rtype: str
        """
        return self._repo_url

    @repo_url.setter
    def repo_url(self, repo_url):
        """Sets the repo_url of this CriterionBuildValueReposInner.

        URL of the repository

        :param repo_url: The repo_url of this CriterionBuildValueReposInner.
        :type repo_url: str
        """

        self._repo_url = repo_url

    @property
    def container(self):
        """Gets the container of this CriterionBuildValueReposInner.

        Container name as defined in the JePL composer's file (i.e. docker-compose.yml)

        :return: The container of this CriterionBuildValueReposInner.
        :rtype: str
        """
        return self._container

    @container.setter
    def container(self, container):
        """Sets the container of this CriterionBuildValueReposInner.

        Container name as defined in the JePL composer's file (i.e. docker-compose.yml)

        :param container: The container of this CriterionBuildValueReposInner.
        :type container: str
        """

        self._container = container

    @property
    def commands(self):
        """Gets the commands of this CriterionBuildValueReposInner.

        List of commands to execute

        :return: The commands of this CriterionBuildValueReposInner.
        :rtype: List[str]
        """
        return self._commands

    @commands.setter
    def commands(self, commands):
        """Sets the commands of this CriterionBuildValueReposInner.

        List of commands to execute

        :param commands: The commands of this CriterionBuildValueReposInner.
        :type commands: List[str]
        """

        self._commands = commands

    @property
    def tox(self):
        """Gets the tox of this CriterionBuildValueReposInner.


        :return: The tox of this CriterionBuildValueReposInner.
        :rtype: ToxSimplified
        """
        return self._tox

    @tox.setter
    def tox(self, tox):
        """Sets the tox of this CriterionBuildValueReposInner.


        :param tox: The tox of this CriterionBuildValueReposInner.
        :type tox: ToxSimplified
        """

        self._tox = tox

    @property
    def tool(self):
        """Gets the tool of this CriterionBuildValueReposInner.


        :return: The tool of this CriterionBuildValueReposInner.
        :rtype: Tool
        """
        return self._tool

    @tool.setter
    def tool(self, tool):
        """Sets the tool of this CriterionBuildValueReposInner.


        :param tool: The tool of this CriterionBuildValueReposInner.
        :type tool: Tool
        """

        self._tool = tool
