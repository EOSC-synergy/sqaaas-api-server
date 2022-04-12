# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.badge_assertion import BadgeAssertion
from openapi_server import util


class Badge(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, data: BadgeAssertion=None, share: str=None, verification_url: str=None):
        """Badge - a model defined in OpenAPI

        :param data: The data of this Badge.
        :param share: The share of this Badge.
        :param verification_url: The verification_url of this Badge.
        """
        self.openapi_types = {
            'data': BadgeAssertion,
            'share': str,
            'verification_url': str
        }

        self.attribute_map = {
            'data': 'data',
            'share': 'share',
            'verification_url': 'verification_url'
        }

        self._data = data
        self._share = share
        self._verification_url = verification_url

    @classmethod
    def from_dict(cls, dikt: dict) -> 'Badge':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Badge of this Badge.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def data(self):
        """Gets the data of this Badge.


        :return: The data of this Badge.
        :rtype: BadgeAssertion
        """
        return self._data

    @data.setter
    def data(self, data):
        """Sets the data of this Badge.


        :param data: The data of this Badge.
        :type data: BadgeAssertion
        """

        self._data = data

    @property
    def share(self):
        """Gets the share of this Badge.


        :return: The share of this Badge.
        :rtype: str
        """
        return self._share

    @share.setter
    def share(self, share):
        """Sets the share of this Badge.


        :param share: The share of this Badge.
        :type share: str
        """

        self._share = share

    @property
    def verification_url(self):
        """Gets the verification_url of this Badge.


        :return: The verification_url of this Badge.
        :rtype: str
        """
        return self._verification_url

    @verification_url.setter
    def verification_url(self, verification_url):
        """Sets the verification_url of this Badge.


        :param verification_url: The verification_url of this Badge.
        :type verification_url: str
        """

        self._verification_url = verification_url
