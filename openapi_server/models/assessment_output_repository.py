# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AssessmentOutputRepository(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, name: str=None, url: str=None, avatar_url: str=None, description: str=None, languages: List[str]=None, tag: str=None, topics: List[str]=None, stargazers_count: float=None, watchers_count: float=None, contributors_count: float=None, forks_count: float=None):
        """AssessmentOutputRepository - a model defined in OpenAPI

        :param name: The name of this AssessmentOutputRepository.
        :param url: The url of this AssessmentOutputRepository.
        :param avatar_url: The avatar_url of this AssessmentOutputRepository.
        :param description: The description of this AssessmentOutputRepository.
        :param languages: The languages of this AssessmentOutputRepository.
        :param tag: The tag of this AssessmentOutputRepository.
        :param topics: The topics of this AssessmentOutputRepository.
        :param stargazers_count: The stargazers_count of this AssessmentOutputRepository.
        :param watchers_count: The watchers_count of this AssessmentOutputRepository.
        :param contributors_count: The contributors_count of this AssessmentOutputRepository.
        :param forks_count: The forks_count of this AssessmentOutputRepository.
        """
        self.openapi_types = {
            'name': str,
            'url': str,
            'avatar_url': str,
            'description': str,
            'languages': List[str],
            'tag': str,
            'topics': List[str],
            'stargazers_count': float,
            'watchers_count': float,
            'contributors_count': float,
            'forks_count': float
        }

        self.attribute_map = {
            'name': 'name',
            'url': 'url',
            'avatar_url': 'avatar_url',
            'description': 'description',
            'languages': 'languages',
            'tag': 'tag',
            'topics': 'topics',
            'stargazers_count': 'stargazers_count',
            'watchers_count': 'watchers_count',
            'contributors_count': 'contributors_count',
            'forks_count': 'forks_count'
        }

        self._name = name
        self._url = url
        self._avatar_url = avatar_url
        self._description = description
        self._languages = languages
        self._tag = tag
        self._topics = topics
        self._stargazers_count = stargazers_count
        self._watchers_count = watchers_count
        self._contributors_count = contributors_count
        self._forks_count = forks_count

    @classmethod
    def from_dict(cls, dikt: dict) -> 'AssessmentOutputRepository':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentOutputRepository of this AssessmentOutputRepository.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def name(self):
        """Gets the name of this AssessmentOutputRepository.

        (nick) Name of the repository

        :return: The name of this AssessmentOutputRepository.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this AssessmentOutputRepository.

        (nick) Name of the repository

        :param name: The name of this AssessmentOutputRepository.
        :type name: str
        """

        self._name = name

    @property
    def url(self):
        """Gets the url of this AssessmentOutputRepository.

        URL of the repository

        :return: The url of this AssessmentOutputRepository.
        :rtype: str
        """
        return self._url

    @url.setter
    def url(self, url):
        """Sets the url of this AssessmentOutputRepository.

        URL of the repository

        :param url: The url of this AssessmentOutputRepository.
        :type url: str
        """

        self._url = url

    @property
    def avatar_url(self):
        """Gets the avatar_url of this AssessmentOutputRepository.

        Avatar URL for the repository

        :return: The avatar_url of this AssessmentOutputRepository.
        :rtype: str
        """
        return self._avatar_url

    @avatar_url.setter
    def avatar_url(self, avatar_url):
        """Sets the avatar_url of this AssessmentOutputRepository.

        Avatar URL for the repository

        :param avatar_url: The avatar_url of this AssessmentOutputRepository.
        :type avatar_url: str
        """

        self._avatar_url = avatar_url

    @property
    def description(self):
        """Gets the description of this AssessmentOutputRepository.

        One-liner containing the repository's purpose

        :return: The description of this AssessmentOutputRepository.
        :rtype: str
        """
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of this AssessmentOutputRepository.

        One-liner containing the repository's purpose

        :param description: The description of this AssessmentOutputRepository.
        :type description: str
        """

        self._description = description

    @property
    def languages(self):
        """Gets the languages of this AssessmentOutputRepository.

        Programming language used

        :return: The languages of this AssessmentOutputRepository.
        :rtype: List[str]
        """
        return self._languages

    @languages.setter
    def languages(self, languages):
        """Sets the languages of this AssessmentOutputRepository.

        Programming language used

        :param languages: The languages of this AssessmentOutputRepository.
        :type languages: List[str]
        """

        self._languages = languages

    @property
    def tag(self):
        """Gets the tag of this AssessmentOutputRepository.

        Git tag that corresponds to the current version

        :return: The tag of this AssessmentOutputRepository.
        :rtype: str
        """
        return self._tag

    @tag.setter
    def tag(self, tag):
        """Sets the tag of this AssessmentOutputRepository.

        Git tag that corresponds to the current version

        :param tag: The tag of this AssessmentOutputRepository.
        :type tag: str
        """

        self._tag = tag

    @property
    def topics(self):
        """Gets the topics of this AssessmentOutputRepository.

        Labels that characterize the repository

        :return: The topics of this AssessmentOutputRepository.
        :rtype: List[str]
        """
        return self._topics

    @topics.setter
    def topics(self, topics):
        """Sets the topics of this AssessmentOutputRepository.

        Labels that characterize the repository

        :param topics: The topics of this AssessmentOutputRepository.
        :type topics: List[str]
        """

        self._topics = topics

    @property
    def stargazers_count(self):
        """Gets the stargazers_count of this AssessmentOutputRepository.

        (GitHub only) Number of stars

        :return: The stargazers_count of this AssessmentOutputRepository.
        :rtype: float
        """
        return self._stargazers_count

    @stargazers_count.setter
    def stargazers_count(self, stargazers_count):
        """Sets the stargazers_count of this AssessmentOutputRepository.

        (GitHub only) Number of stars

        :param stargazers_count: The stargazers_count of this AssessmentOutputRepository.
        :type stargazers_count: float
        """

        self._stargazers_count = stargazers_count

    @property
    def watchers_count(self):
        """Gets the watchers_count of this AssessmentOutputRepository.

        (GitHub only) Number of watchers

        :return: The watchers_count of this AssessmentOutputRepository.
        :rtype: float
        """
        return self._watchers_count

    @watchers_count.setter
    def watchers_count(self, watchers_count):
        """Sets the watchers_count of this AssessmentOutputRepository.

        (GitHub only) Number of watchers

        :param watchers_count: The watchers_count of this AssessmentOutputRepository.
        :type watchers_count: float
        """

        self._watchers_count = watchers_count

    @property
    def contributors_count(self):
        """Gets the contributors_count of this AssessmentOutputRepository.

        (GitHub only) Number of contributors

        :return: The contributors_count of this AssessmentOutputRepository.
        :rtype: float
        """
        return self._contributors_count

    @contributors_count.setter
    def contributors_count(self, contributors_count):
        """Sets the contributors_count of this AssessmentOutputRepository.

        (GitHub only) Number of contributors

        :param contributors_count: The contributors_count of this AssessmentOutputRepository.
        :type contributors_count: float
        """

        self._contributors_count = contributors_count

    @property
    def forks_count(self):
        """Gets the forks_count of this AssessmentOutputRepository.

        (GitHub only) Number of forks

        :return: The forks_count of this AssessmentOutputRepository.
        :rtype: float
        """
        return self._forks_count

    @forks_count.setter
    def forks_count(self, forks_count):
        """Sets the forks_count of this AssessmentOutputRepository.

        (GitHub only) Number of forks

        :param forks_count: The forks_count of this AssessmentOutputRepository.
        :type forks_count: float
        """

        self._forks_count = forks_count