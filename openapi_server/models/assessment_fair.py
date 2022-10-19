# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server import util


class AssessmentFAIR(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, persistent_identifier: str=None, metadata_protocol: str=None, metadata_endpoint: str=None, evaluator_tool: str=None, evaluator_endpoint: str=None, badge_policy_url: str=None):
        """AssessmentFAIR - a model defined in OpenAPI

        :param persistent_identifier: The persistent_identifier of this AssessmentFAIR.
        :param metadata_protocol: The metadata_protocol of this AssessmentFAIR.
        :param metadata_endpoint: The metadata_endpoint of this AssessmentFAIR.
        :param evaluator_tool: The evaluator_tool of this AssessmentFAIR.
        :param evaluator_endpoint: The evaluator_endpoint of this AssessmentFAIR.
        :param badge_policy_url: The badge_policy_url of this AssessmentFAIR.
        """
        self.openapi_types = {
            'persistent_identifier': str,
            'metadata_protocol': str,
            'metadata_endpoint': str,
            'evaluator_tool': str,
            'evaluator_endpoint': str,
            'badge_policy_url': str
        }

        self.attribute_map = {
            'persistent_identifier': 'persistent_identifier',
            'metadata_protocol': 'metadata_protocol',
            'metadata_endpoint': 'metadata_endpoint',
            'evaluator_tool': 'evaluator_tool',
            'evaluator_endpoint': 'evaluator_endpoint',
            'badge_policy_url': 'badge_policy_url'
        }

        self._persistent_identifier = persistent_identifier
        self._metadata_protocol = metadata_protocol
        self._metadata_endpoint = metadata_endpoint
        self._evaluator_tool = evaluator_tool
        self._evaluator_endpoint = evaluator_endpoint
        self._badge_policy_url = badge_policy_url

    @classmethod
    def from_dict(cls, dikt: dict) -> 'AssessmentFAIR':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The AssessmentFAIR of this AssessmentFAIR.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def persistent_identifier(self):
        """Gets the persistent_identifier of this AssessmentFAIR.

        Persistent identifier for the dataset

        :return: The persistent_identifier of this AssessmentFAIR.
        :rtype: str
        """
        return self._persistent_identifier

    @persistent_identifier.setter
    def persistent_identifier(self, persistent_identifier):
        """Sets the persistent_identifier of this AssessmentFAIR.

        Persistent identifier for the dataset

        :param persistent_identifier: The persistent_identifier of this AssessmentFAIR.
        :type persistent_identifier: str
        """

        self._persistent_identifier = persistent_identifier

    @property
    def metadata_protocol(self):
        """Gets the metadata_protocol of this AssessmentFAIR.

        Protocol for metadata harvesting

        :return: The metadata_protocol of this AssessmentFAIR.
        :rtype: str
        """
        return self._metadata_protocol

    @metadata_protocol.setter
    def metadata_protocol(self, metadata_protocol):
        """Sets the metadata_protocol of this AssessmentFAIR.

        Protocol for metadata harvesting

        :param metadata_protocol: The metadata_protocol of this AssessmentFAIR.
        :type metadata_protocol: str
        """

        self._metadata_protocol = metadata_protocol

    @property
    def metadata_endpoint(self):
        """Gets the metadata_endpoint of this AssessmentFAIR.

        URL of the metadata protocol interface

        :return: The metadata_endpoint of this AssessmentFAIR.
        :rtype: str
        """
        return self._metadata_endpoint

    @metadata_endpoint.setter
    def metadata_endpoint(self, metadata_endpoint):
        """Sets the metadata_endpoint of this AssessmentFAIR.

        URL of the metadata protocol interface

        :param metadata_endpoint: The metadata_endpoint of this AssessmentFAIR.
        :type metadata_endpoint: str
        """

        self._metadata_endpoint = metadata_endpoint

    @property
    def evaluator_tool(self):
        """Gets the evaluator_tool of this AssessmentFAIR.

        Name of the evaluator tool

        :return: The evaluator_tool of this AssessmentFAIR.
        :rtype: str
        """
        return self._evaluator_tool

    @evaluator_tool.setter
    def evaluator_tool(self, evaluator_tool):
        """Sets the evaluator_tool of this AssessmentFAIR.

        Name of the evaluator tool

        :param evaluator_tool: The evaluator_tool of this AssessmentFAIR.
        :type evaluator_tool: str
        """

        self._evaluator_tool = evaluator_tool

    @property
    def evaluator_endpoint(self):
        """Gets the evaluator_endpoint of this AssessmentFAIR.

        URL of the endpoint where the evaluator is accessible

        :return: The evaluator_endpoint of this AssessmentFAIR.
        :rtype: str
        """
        return self._evaluator_endpoint

    @evaluator_endpoint.setter
    def evaluator_endpoint(self, evaluator_endpoint):
        """Sets the evaluator_endpoint of this AssessmentFAIR.

        URL of the endpoint where the evaluator is accessible

        :param evaluator_endpoint: The evaluator_endpoint of this AssessmentFAIR.
        :type evaluator_endpoint: str
        """

        self._evaluator_endpoint = evaluator_endpoint

    @property
    def badge_policy_url(self):
        """Gets the badge_policy_url of this AssessmentFAIR.

        URL where the badge policies are defined

        :return: The badge_policy_url of this AssessmentFAIR.
        :rtype: str
        """
        return self._badge_policy_url

    @badge_policy_url.setter
    def badge_policy_url(self, badge_policy_url):
        """Sets the badge_policy_url of this AssessmentFAIR.

        URL where the badge policies are defined

        :param badge_policy_url: The badge_policy_url of this AssessmentFAIR.
        :type badge_policy_url: str
        """

        self._badge_policy_url = badge_policy_url
