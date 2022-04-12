# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class CredsCert(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id: str=None, type: str=None, keystore_var: str=None, alias_var: str=None, password_var: str=None):
        """CredsCert - a model defined in OpenAPI

        :param id: The id of this CredsCert.
        :param type: The type of this CredsCert.
        :param keystore_var: The keystore_var of this CredsCert.
        :param alias_var: The alias_var of this CredsCert.
        :param password_var: The password_var of this CredsCert.
        """
        self.openapi_types = {
            'id': str,
            'type': str,
            'keystore_var': str,
            'alias_var': str,
            'password_var': str
        }

        self.attribute_map = {
            'id': 'id',
            'type': 'type',
            'keystore_var': 'keystore_var',
            'alias_var': 'alias_var',
            'password_var': 'password_var'
        }

        self._id = id
        self._type = type
        self._keystore_var = keystore_var
        self._alias_var = alias_var
        self._password_var = password_var

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CredsCert':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Creds_cert of this CredsCert.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this CredsCert.


        :return: The id of this CredsCert.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CredsCert.


        :param id: The id of this CredsCert.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")

        self._id = id

    @property
    def type(self):
        """Gets the type of this CredsCert.


        :return: The type of this CredsCert.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this CredsCert.


        :param type: The type of this CredsCert.
        :type type: str
        """
        allowed_values = ["file", "zip"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}"
                .format(type, allowed_values)
            )

        self._type = type

    @property
    def keystore_var(self):
        """Gets the keystore_var of this CredsCert.


        :return: The keystore_var of this CredsCert.
        :rtype: str
        """
        return self._keystore_var

    @keystore_var.setter
    def keystore_var(self, keystore_var):
        """Sets the keystore_var of this CredsCert.


        :param keystore_var: The keystore_var of this CredsCert.
        :type keystore_var: str
        """
        if keystore_var is None:
            raise ValueError("Invalid value for `keystore_var`, must not be `None`")

        self._keystore_var = keystore_var

    @property
    def alias_var(self):
        """Gets the alias_var of this CredsCert.


        :return: The alias_var of this CredsCert.
        :rtype: str
        """
        return self._alias_var

    @alias_var.setter
    def alias_var(self, alias_var):
        """Sets the alias_var of this CredsCert.


        :param alias_var: The alias_var of this CredsCert.
        :type alias_var: str
        """

        self._alias_var = alias_var

    @property
    def password_var(self):
        """Gets the password_var of this CredsCert.


        :return: The password_var of this CredsCert.
        :rtype: str
        """
        return self._password_var

    @password_var.setter
    def password_var(self, password_var):
        """Sets the password_var of this CredsCert.


        :param password_var: The password_var of this CredsCert.
        :type password_var: str
        """

        self._password_var = password_var
