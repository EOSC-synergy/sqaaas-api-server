# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AssessmentCreds(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, secret_id: str = None, user_id: str = None, token: str = None):
        """AssessmentCreds - a model defined in OpenAPI

        :param secret_id: The secret_id of this AssessmentCreds.
        :param user_id: The user_id of this AssessmentCreds.
        :param token: The token of this AssessmentCreds.
        """
        self.openapi_types = {"secret_id": str, "user_id": str, "token": str}

        self.attribute_map = {
            "secret_id": "secret_id",
            "user_id": "user_id",
            "token": "token",
        }

        self._secret_id = secret_id
        self._user_id = user_id
        self._token = token

    @classmethod
    def from_dict(cls, dikt: dict) -> "AssessmentCreds":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentCreds of this AssessmentCreds.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def secret_id(self):
        """Gets the secret_id of this AssessmentCreds.

        Secret ID (required by Vault)

        :return: The secret_id of this AssessmentCreds.
        :rtype: str
        """
        return self._secret_id

    @secret_id.setter
    def secret_id(self, secret_id):
        """Sets the secret_id of this AssessmentCreds.

        Secret ID (required by Vault)

        :param secret_id: The secret_id of this AssessmentCreds.
        :type secret_id: str
        """

        self._secret_id = secret_id

    @property
    def user_id(self):
        """Gets the user_id of this AssessmentCreds.

        Account name to be used for authentication (required by GitLab, GitHub)

        :return: The user_id of this AssessmentCreds.
        :rtype: str
        """
        return self._user_id

    @user_id.setter
    def user_id(self, user_id):
        """Sets the user_id of this AssessmentCreds.

        Account name to be used for authentication (required by GitLab, GitHub)

        :param user_id: The user_id of this AssessmentCreds.
        :type user_id: str
        """

        self._user_id = user_id

    @property
    def token(self):
        """Gets the token of this AssessmentCreds.

        Temporary (short-lived) token for authentication (required by GitLab, GitHub)

        :return: The token of this AssessmentCreds.
        :rtype: str
        """
        return self._token

    @token.setter
    def token(self, token):
        """Sets the token of this AssessmentCreds.

        Temporary (short-lived) token for authentication (required by GitLab, GitHub)

        :param token: The token of this AssessmentCreds.
        :type token: str
        """

        self._token = token
