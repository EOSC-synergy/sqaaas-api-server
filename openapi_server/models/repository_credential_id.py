# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.assessment_creds import AssessmentCreds
from openapi_server.models.creds_user_pass import CredsUserPass
from openapi_server import util


class RepositoryCredentialId(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        id: str = None,
        type: str = None,
        username_var: str = None,
        password_var: str = None,
        secret_id: str = None,
        user_id: str = None,
        token: str = None,
    ):
        """RepositoryCredentialId - a model defined in OpenAPI

        :param id: The id of this RepositoryCredentialId.
        :param type: The type of this RepositoryCredentialId.
        :param username_var: The username_var of this RepositoryCredentialId.
        :param password_var: The password_var of this RepositoryCredentialId.
        :param secret_id: The secret_id of this RepositoryCredentialId.
        :param user_id: The user_id of this RepositoryCredentialId.
        :param token: The token of this RepositoryCredentialId.
        """
        self.openapi_types = {
            "id": str,
            "type": str,
            "username_var": str,
            "password_var": str,
            "secret_id": str,
            "user_id": str,
            "token": str,
        }

        self.attribute_map = {
            "id": "id",
            "type": "type",
            "username_var": "username_var",
            "password_var": "password_var",
            "secret_id": "secret_id",
            "user_id": "user_id",
            "token": "token",
        }

        self._id = id
        self._type = type
        self._username_var = username_var
        self._password_var = password_var
        self._secret_id = secret_id
        self._user_id = user_id
        self._token = token

    @classmethod
    def from_dict(cls, dikt: dict) -> "RepositoryCredentialId":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Repository_credential_id of this RepositoryCredentialId.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this RepositoryCredentialId.

        Credential ID (as defined in Jenkins)

        :return: The id of this RepositoryCredentialId.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this RepositoryCredentialId.

        Credential ID (as defined in Jenkins)

        :param id: The id of this RepositoryCredentialId.
        :type id: str
        """
        if id is None:
            raise ValueError("Invalid value for `id`, must not be `None`")

        self._id = id

    @property
    def type(self):
        """Gets the type of this RepositoryCredentialId.

        Credential type

        :return: The type of this RepositoryCredentialId.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this RepositoryCredentialId.

        Credential type

        :param type: The type of this RepositoryCredentialId.
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
        """Gets the username_var of this RepositoryCredentialId.


        :return: The username_var of this RepositoryCredentialId.
        :rtype: str
        """
        return self._username_var

    @username_var.setter
    def username_var(self, username_var):
        """Sets the username_var of this RepositoryCredentialId.


        :param username_var: The username_var of this RepositoryCredentialId.
        :type username_var: str
        """
        if username_var is None:
            raise ValueError("Invalid value for `username_var`, must not be `None`")

        self._username_var = username_var

    @property
    def password_var(self):
        """Gets the password_var of this RepositoryCredentialId.


        :return: The password_var of this RepositoryCredentialId.
        :rtype: str
        """
        return self._password_var

    @password_var.setter
    def password_var(self, password_var):
        """Sets the password_var of this RepositoryCredentialId.


        :param password_var: The password_var of this RepositoryCredentialId.
        :type password_var: str
        """
        if password_var is None:
            raise ValueError("Invalid value for `password_var`, must not be `None`")

        self._password_var = password_var

    @property
    def secret_id(self):
        """Gets the secret_id of this RepositoryCredentialId.

        Secret ID (required by Vault)

        :return: The secret_id of this RepositoryCredentialId.
        :rtype: str
        """
        return self._secret_id

    @secret_id.setter
    def secret_id(self, secret_id):
        """Sets the secret_id of this RepositoryCredentialId.

        Secret ID (required by Vault)

        :param secret_id: The secret_id of this RepositoryCredentialId.
        :type secret_id: str
        """

        self._secret_id = secret_id

    @property
    def user_id(self):
        """Gets the user_id of this RepositoryCredentialId.

        Account name to be used for authentication (required by GitLab, GitHub)

        :return: The user_id of this RepositoryCredentialId.
        :rtype: str
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id):
        """Sets the user_id of this RepositoryCredentialId.

        Account name to be used for authentication (required by GitLab, GitHub)

        :param user_id: The user_id of this RepositoryCredentialId.
        :type user_id: str
        """

        self._user_id = user_id

    @property
    def token(self):
        """Gets the token of this RepositoryCredentialId.

        Temporary (short-lived) token for authentication (required by GitLab, GitHub)

        :return: The token of this RepositoryCredentialId.
        :rtype: str
        """
        return self._token

    @token.setter
    def token(self, token):
        """Sets the token of this RepositoryCredentialId.

        Temporary (short-lived) token for authentication (required by GitLab, GitHub)

        :param token: The token of this RepositoryCredentialId.
        :type token: str
        """

        self._token = token
