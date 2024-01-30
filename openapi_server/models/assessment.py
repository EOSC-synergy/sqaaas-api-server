# coding: utf-8

from datetime import date, datetime
from typing import Dict, List, Type

from openapi_server import util
from openapi_server.models.assessment_deployment import AssessmentDeployment
from openapi_server.models.assessment_fair import AssessmentFAIR
from openapi_server.models.base_model_ import Model
from openapi_server.models.criterion_workflow import CriterionWorkflow
from openapi_server.models.repository import Repository


class Assessment(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(
        self,
        repo_code: Repository = None,
        repo_docs: Repository = None,
        deployment: AssessmentDeployment = None,
        fair: AssessmentFAIR = None,
        criteria_workflow: List[CriterionWorkflow] = None,
    ):
        """Assessment - a model defined in OpenAPI

        :param repo_code: The repo_code of this Assessment.
        :param repo_docs: The repo_docs of this Assessment.
        :param deployment: The deployment of this Assessment.
        :param fair: The fair of this Assessment.
        :param criteria_workflow: The criteria_workflow of this Assessment.
        """
        self.openapi_types = {
            "repo_code": Repository,
            "repo_docs": Repository,
            "deployment": AssessmentDeployment,
            "fair": AssessmentFAIR,
            "criteria_workflow": List[CriterionWorkflow],
        }

        self.attribute_map = {
            "repo_code": "repo_code",
            "repo_docs": "repo_docs",
            "deployment": "deployment",
            "fair": "fair",
            "criteria_workflow": "criteria_workflow",
        }

        self._repo_code = repo_code
        self._repo_docs = repo_docs
        self._deployment = deployment
        self._fair = fair
        self._criteria_workflow = criteria_workflow

    @classmethod
    def from_dict(cls, dikt: dict) -> "Assessment":
        """Returns the dict as a model

        :param dikt: A dict.
        :return: The Assessment of this Assessment.
        """
        return util.deserialize_model(dikt, cls)

    @property
    def repo_code(self):
        """Gets the repo_code of this Assessment.


        :return: The repo_code of this Assessment.
        :rtype: Repository
        """
        return self._repo_code

    @repo_code.setter
    def repo_code(self, repo_code):
        """Sets the repo_code of this Assessment.


        :param repo_code: The repo_code of this Assessment.
        :type repo_code: Repository
        """

        self._repo_code = repo_code

    @property
    def repo_docs(self):
        """Gets the repo_docs of this Assessment.


        :return: The repo_docs of this Assessment.
        :rtype: Repository
        """
        return self._repo_docs

    @repo_docs.setter
    def repo_docs(self, repo_docs):
        """Sets the repo_docs of this Assessment.


        :param repo_docs: The repo_docs of this Assessment.
        :type repo_docs: Repository
        """

        self._repo_docs = repo_docs

    @property
    def deployment(self):
        """Gets the deployment of this Assessment.


        :return: The deployment of this Assessment.
        :rtype: AssessmentDeployment
        """
        return self._deployment

    @deployment.setter
    def deployment(self, deployment):
        """Sets the deployment of this Assessment.


        :param deployment: The deployment of this Assessment.
        :type deployment: AssessmentDeployment
        """

        self._deployment = deployment

    @property
    def fair(self):
        """Gets the fair of this Assessment.


        :return: The fair of this Assessment.
        :rtype: AssessmentFAIR
        """
        return self._fair

    @fair.setter
    def fair(self, fair):
        """Sets the fair of this Assessment.


        :param fair: The fair of this Assessment.
        :type fair: AssessmentFAIR
        """

        self._fair = fair

    @property
    def criteria_workflow(self):
        """Gets the criteria_workflow of this Assessment.


        :return: The criteria_workflow of this Assessment.
        :rtype: List[CriterionWorkflow]
        """
        return self._criteria_workflow

    @criteria_workflow.setter
    def criteria_workflow(self, criteria_workflow):
        """Sets the criteria_workflow of this Assessment.


        :param criteria_workflow: The criteria_workflow of this Assessment.
        :type criteria_workflow: List[CriterionWorkflow]
        """

        self._criteria_workflow = criteria_workflow
