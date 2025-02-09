# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.base_model_ import Model


class CredsUserPass(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        id: str = None,
        type: str = None,
        username_var: str = None,
        password_var: str = None,
    ):
        """CredsUserPass - a model defined in OpenAPI

        :param id: The id of this CredsUserPass.
        :param type: The type of this CredsUserPass.
        :param username_var: The username_var of this CredsUserPass.
        :param password_var: The password_var of this CredsUserPass.
        """
        self.openapi_types = {
            "id": str,
            "type": str,
            "username_var": str,
            "password_var": str,
        }

        self.attribute_map = {
            "id": "id",
            "type": "type",
            "username_var": "username_var",
            "password_var": "password_var",
        }

        self._id = id
        self._type = type
        self._username_var = username_var
        self._password_var = password_var

    @classmethod
    def from_dict(cls, dikt: dict) -> "CredsUserPass":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Creds_user_pass of this CredsUserPass.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this CredsUserPass.

        Credential ID (as defined in Jenkins)

        :return: The id of this CredsUserPass.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CredsUserPass.

        Credential ID (as defined in Jenkins)

        :param id: The id of this CredsUserPass.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")

        self._id = id

    @property
    def type(self):
        """Gets the type of this CredsUserPass.

        Credential type

        :return: The type of this CredsUserPass.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this CredsUserPass.

        Credential type

        :param type: The type of this CredsUserPass.
        :type type: str
        """
        allowed_values = ["username_password"]  # noqa: E501
        if type not in allowed_values:
            raise ValueError(
                "Invalid value for `type` ({0}), must be one of {1}".format(
                    type, allowed_values
                )
            )

        self._type = type

    @property
    def username_var(self):
        """Gets the username_var of this CredsUserPass.


        :return: The username_var of this CredsUserPass.
        :rtype: str
        """
        return self._username_var

    @username_var.setter
    def username_var(self, username_var):
        """Sets the username_var of this CredsUserPass.


        :param username_var: The username_var of this CredsUserPass.
        :type username_var: str
        """
        if username_var is None:
            raise ValueError("Invalid value for `username_var`, must not be `None`")

        self._username_var = username_var

    @property
    def password_var(self):
        """Gets the password_var of this CredsUserPass.


        :return: The password_var of this CredsUserPass.
        :rtype: str
        """
        return self._password_var

    @password_var.setter
    def password_var(self, password_var):
        """Sets the password_var of this CredsUserPass.


        :param password_var: The password_var of this CredsUserPass.
        :type password_var: str
        """
        if password_var is None:
            raise ValueError("Invalid value for `password_var`, must not be `None`")

        self._password_var = password_var
