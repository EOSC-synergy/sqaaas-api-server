# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class CreatePullRequestRequest(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, repo: str=None, branch: str=None):
        """CreatePullRequestRequest - a model defined in OpenAPI

        :param repo: The repo of this CreatePullRequestRequest.
        :param branch: The branch of this CreatePullRequestRequest.
        """
        self.openapi_types = {
            'repo': str,
            'branch': str
        }

        self.attribute_map = {
            'repo': 'repo',
            'branch': 'branch'
        }

        self._repo = repo
        self._branch = branch

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CreatePullRequestRequest':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The create_pull_request_request of this CreatePullRequestRequest.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repo(self):
        """Gets the repo of this CreatePullRequestRequest.

        URL of the upstream repo

        :return: The repo of this CreatePullRequestRequest.
        :rtype: str
        """
        return self._repo

    @repo.setter
    def repo(self, repo):
        """Sets the repo of this CreatePullRequestRequest.

        URL of the upstream repo

        :param repo: The repo of this CreatePullRequestRequest.
        :type repo: str
        """
        if repo is None:
            raise ValueError("Invalid value for `repo`, must not be `None`")

        self._repo = repo

    @property
    def branch(self):
        """Gets the branch of this CreatePullRequestRequest.

        Brach from the upstream repo used as the base for the pull request

        :return: The branch of this CreatePullRequestRequest.
        :rtype: str
        """
        return self._branch

    @branch.setter
    def branch(self, branch):
        """Sets the branch of this CreatePullRequestRequest.

        Brach from the upstream repo used as the base for the pull request

        :param branch: The branch of this CreatePullRequestRequest.
        :type branch: str
        """

        self._branch = branch