# coding: utf-8

from datetime import date, datetime

from typing import List, Dict, Type

from openapi_server.models.base_model_ import Model
from openapi_server.models.agent import Agent
from openapi_server.models.step import Step
from openapi_server import util


class CriterionWorkflow(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, id: str=None, agent: Agent=None, steps: List[Step]=None):
        """CriterionWorkflow - a model defined in OpenAPI

        :param id: The id of this CriterionWorkflow.
        :param agent: The agent of this CriterionWorkflow.
        :param steps: The steps of this CriterionWorkflow.
        """
        self.openapi_types = {
            'id': str,
            'agent': Agent,
            'steps': List[Step]
        }

        self.attribute_map = {
            'id': 'id',
            'agent': 'agent',
            'steps': 'steps'
        }

        self._id = id
        self._agent = agent
        self._steps = steps

    @classmethod
    def from_dict(cls, dikt: dict) -> 'CriterionWorkflow':
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The CriterionWorkflow of this CriterionWorkflow.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def id(self):
        """Gets the id of this CriterionWorkflow.

        ID of the criterion

        :return: The id of this CriterionWorkflow.
        :rtype: str
        """
        return self._id

    @id.setter
    def id(self, id):
        """Sets the id of this CriterionWorkflow.

        ID of the criterion

        :param id: The id of this CriterionWorkflow.
        :type id: str
        """

        self._id = id

    @property
    def agent(self):
        """Gets the agent of this CriterionWorkflow.


        :return: The agent of this CriterionWorkflow.
        :rtype: Agent
        """
        return self._agent

    @agent.setter
    def agent(self, agent):
        """Sets the agent of this CriterionWorkflow.


        :param agent: The agent of this CriterionWorkflow.
        :type agent: Agent
        """

        self._agent = agent

    @property
    def steps(self):
        """Gets the steps of this CriterionWorkflow.

        steps containing the workflow to validate a given criterion

        :return: The steps of this CriterionWorkflow.
        :rtype: List[Step]
        """
        return self._steps

    @steps.setter
    def steps(self, steps):
        """Sets the steps of this CriterionWorkflow.

        steps containing the workflow to validate a given criterion

        :param steps: The steps of this CriterionWorkflow.
        :type steps: List[Step]
        """

        self._steps = steps