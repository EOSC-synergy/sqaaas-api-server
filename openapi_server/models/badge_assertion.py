# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.badge_assertion_recipient import BadgeAssertionRecipient
from openapi_server.models.base_model_ import Model


class BadgeAssertion(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        open_badge_id: str = None,
        created_at: datetime = None,
        created_by: str = None,
        badge_class: str = None,
        issuer: str = None,
        image: str = None,
        recipient: BadgeAssertionRecipient = None,
        issued_on: datetime = None,
    ):
        """BadgeAssertion - a model defined in OpenAPI

        :param open_badge_id: The open_badge_id of this BadgeAssertion.
        :param created_at: The created_at of this BadgeAssertion.
        :param created_by: The created_by of this BadgeAssertion.
        :param badge_class: The badge_class of this BadgeAssertion.
        :param issuer: The issuer of this BadgeAssertion.
        :param image: The image of this BadgeAssertion.
        :param recipient: The recipient of this BadgeAssertion.
        :param issued_on: The issued_on of this BadgeAssertion.
        """
        self.openapi_types = {
            "open_badge_id": str,
            "created_at": datetime,
            "created_by": str,
            "badge_class": str,
            "issuer": str,
            "image": str,
            "recipient": BadgeAssertionRecipient,
            "issued_on": datetime,
        }

        self.attribute_map = {
            "open_badge_id": "openBadgeID",
            "created_at": "createdAt",
            "created_by": "createdBy",
            "badge_class": "badgeClass",
            "issuer": "issuer",
            "image": "image",
            "recipient": "recipient",
            "issued_on": "issuedOn",
        }

        self._open_badge_id = open_badge_id
        self._created_at = created_at
        self._created_by = created_by
        self._badge_class = badge_class
        self._issuer = issuer
        self._image = image
        self._recipient = recipient
        self._issued_on = issued_on

    @classmethod
    def from_dict(cls, dikt: dict) -> "BadgeAssertion":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The BadgeAssertion of this BadgeAssertion.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def open_badge_id(self):
        """Gets the open_badge_id of this BadgeAssertion.


        :return: The open_badge_id of this BadgeAssertion.
        :rtype: str
        """
        return self._open_badge_id

    @open_badge_id.setter
    def open_badge_id(self, open_badge_id):
        """Sets the open_badge_id of this BadgeAssertion.


        :param open_badge_id: The open_badge_id of this BadgeAssertion.
        :type open_badge_id: str
        """

        self._open_badge_id = open_badge_id

    @property
    def created_at(self):
        """Gets the created_at of this BadgeAssertion.


        :return: The created_at of this BadgeAssertion.
        :rtype: datetime
        """
        return self._created_at

    @created_at.setter
    def created_at(self, created_at):
        """Sets the created_at of this BadgeAssertion.


        :param created_at: The created_at of this BadgeAssertion.
        :type created_at: datetime
        """

        self._created_at = created_at

    @property
    def created_by(self):
        """Gets the created_by of this BadgeAssertion.


        :return: The created_by of this BadgeAssertion.
        :rtype: str
        """
        return self._created_by

    @created_by.setter
    def created_by(self, created_by):
        """Sets the created_by of this BadgeAssertion.


        :param created_by: The created_by of this BadgeAssertion.
        :type created_by: str
        """

        self._created_by = created_by

    @property
    def badge_class(self):
        """Gets the badge_class of this BadgeAssertion.


        :return: The badge_class of this BadgeAssertion.
        :rtype: str
        """
        return self._badge_class

    @badge_class.setter
    def badge_class(self, badge_class):
        """Sets the badge_class of this BadgeAssertion.


        :param badge_class: The badge_class of this BadgeAssertion.
        :type badge_class: str
        """

        self._badge_class = badge_class

    @property
    def issuer(self):
        """Gets the issuer of this BadgeAssertion.


        :return: The issuer of this BadgeAssertion.
        :rtype: str
        """
        return self._issuer

    @issuer.setter
    def issuer(self, issuer):
        """Sets the issuer of this BadgeAssertion.


        :param issuer: The issuer of this BadgeAssertion.
        :type issuer: str
        """

        self._issuer = issuer

    @property
    def image(self):
        """Gets the image of this BadgeAssertion.


        :return: The image of this BadgeAssertion.
        :rtype: str
        """
        return self._image

    @image.setter
    def image(self, image):
        """Sets the image of this BadgeAssertion.


        :param image: The image of this BadgeAssertion.
        :type image: str
        """

        self._image = image

    @property
    def recipient(self):
        """Gets the recipient of this BadgeAssertion.


        :return: The recipient of this BadgeAssertion.
        :rtype: BadgeAssertionRecipient
        """
        return self._recipient

    @recipient.setter
    def recipient(self, recipient):
        """Sets the recipient of this BadgeAssertion.


        :param recipient: The recipient of this BadgeAssertion.
        :type recipient: BadgeAssertionRecipient
        """

        self._recipient = recipient

    @property
    def issued_on(self):
        """Gets the issued_on of this BadgeAssertion.


        :return: The issued_on of this BadgeAssertion.
        :rtype: datetime
        """
        return self._issued_on

    @issued_on.setter
    def issued_on(self, issued_on):
        """Sets the issued_on of this BadgeAssertion.


        :param issued_on: The issued_on of this BadgeAssertion.
        :type issued_on: datetime
        """

        self._issued_on = issued_on
