# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class CredsSshUserPrivateKey(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id: str=None, type: str=None, keyfile_var: str=None, passphrase_var: str=None, username_var: str=None):
        """CredsSshUserPrivateKey - a model defined in OpenAPI

        :param id: The id of this CredsSshUserPrivateKey.
        :param type: The type of this CredsSshUserPrivateKey.
        :param keyfile_var: The keyfile_var of this CredsSshUserPrivateKey.
        :param passphrase_var: The passphrase_var of this CredsSshUserPrivateKey.
        :param username_var: The username_var of this CredsSshUserPrivateKey.
        """
        self.openapi_types = {
            'id': str,
            'type': str,
            'keyfile_var': str,
            'passphrase_var': str,
            'username_var': str
        }

        self.attribute_map = {
            'id': 'id',
            'type': 'type',
            'keyfile_var': 'keyfile_var',
            'passphrase_var': 'passphrase_var',
            'username_var': 'username_var'
        }

        self._id = id
        self._type = type
        self._keyfile_var = keyfile_var
        self._passphrase_var = passphrase_var
        self._username_var = username_var

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CredsSshUserPrivateKey':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Creds_ssh_user_private_key of this CredsSshUserPrivateKey.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this CredsSshUserPrivateKey.


        :return: The id of this CredsSshUserPrivateKey.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CredsSshUserPrivateKey.


        :param id: The id of this CredsSshUserPrivateKey.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")

        self._id = id

    @property
    def type(self):
        """Gets the type of this CredsSshUserPrivateKey.


        :return: The type of this CredsSshUserPrivateKey.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this CredsSshUserPrivateKey.


        :param type: The type of this CredsSshUserPrivateKey.
        :type type: str
        """
        allowed_values = ["ssh_user_private_key"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}"
                .format(type, allowed_values)
            )

        self._type = type

    @property
    def keyfile_var(self):
        """Gets the keyfile_var of this CredsSshUserPrivateKey.


        :return: The keyfile_var of this CredsSshUserPrivateKey.
        :rtype: str
        """
        return self._keyfile_var

    @keyfile_var.setter
    def keyfile_var(self, keyfile_var):
        """Sets the keyfile_var of this CredsSshUserPrivateKey.


        :param keyfile_var: The keyfile_var of this CredsSshUserPrivateKey.
        :type keyfile_var: str
        """
        if keyfile_var is None:
            raise ValueError("Invalid value for `keyfile_var`, must not be `None`")

        self._keyfile_var = keyfile_var

    @property
    def passphrase_var(self):
        """Gets the passphrase_var of this CredsSshUserPrivateKey.


        :return: The passphrase_var of this CredsSshUserPrivateKey.
        :rtype: str
        """
        return self._passphrase_var

    @passphrase_var.setter
    def passphrase_var(self, passphrase_var):
        """Sets the passphrase_var of this CredsSshUserPrivateKey.


        :param passphrase_var: The passphrase_var of this CredsSshUserPrivateKey.
        :type passphrase_var: str
        """

        self._passphrase_var = passphrase_var

    @property
    def username_var(self):
        """Gets the username_var of this CredsSshUserPrivateKey.


        :return: The username_var of this CredsSshUserPrivateKey.
        :rtype: str
        """
        return self._username_var

    @username_var.setter
    def username_var(self, username_var):
        """Sets the username_var of this CredsSshUserPrivateKey.


        :param username_var: The username_var of this CredsSshUserPrivateKey.
        :type username_var: str
        """

        self._username_var = username_var
