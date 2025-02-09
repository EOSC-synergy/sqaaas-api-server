# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

# coding: utf-8

# import models into model package
from openapi_server.models.add_pipeline201_response import AddPipeline201Response
from openapi_server.models.assessment import Assessment
from openapi_server.models.assessment_deployment import AssessmentDeployment
from openapi_server.models.assessment_fair import AssessmentFAIR
from openapi_server.models.assessment_output import AssessmentOutput
from openapi_server.models.assessment_output_badge import AssessmentOutputBadge
from openapi_server.models.assessment_output_meta import AssessmentOutputMeta
from openapi_server.models.assessment_output_report_value import (
    AssessmentOutputReportValue,
)
from openapi_server.models.assessment_output_report_value_coverage import (
    AssessmentOutputReportValueCoverage,
)
from openapi_server.models.assessment_output_repository import (
    AssessmentOutputRepository,
)
from openapi_server.models.assessment_output_subcriteria import (
    AssessmentOutputSubcriteria,
)
from openapi_server.models.assessment_output_tool_ci import AssessmentOutputToolCI
from openapi_server.models.assessment_output_validator import AssessmentOutputValidator
from openapi_server.models.assessment_output_validator_plugin import (
    AssessmentOutputValidatorPlugin,
)
from openapi_server.models.assessment_output_validator_standard import (
    AssessmentOutputValidatorStandard,
)
from openapi_server.models.assessment_output_validator_tool import (
    AssessmentOutputValidatorTool,
)
from openapi_server.models.badge import Badge
from openapi_server.models.badge_assertion import BadgeAssertion
from openapi_server.models.badge_assertion_recipient import BadgeAssertionRecipient
from openapi_server.models.badge_criteria_stats import BadgeCriteriaStats
from openapi_server.models.create_pull_request200_response import (
    CreatePullRequest200Response,
)
from openapi_server.models.create_pull_request_request import CreatePullRequestRequest
from openapi_server.models.creds_input import CredsInput
from openapi_server.models.creds_user_pass import CredsUserPass
from openapi_server.models.criterion import Criterion
from openapi_server.models.criterion_build_value import CriterionBuildValue
from openapi_server.models.criterion_build_value_repos_inner import (
    CriterionBuildValueReposInner,
)
from openapi_server.models.criterion_build_value_when import CriterionBuildValueWhen
from openapi_server.models.criterion_description import CriterionDescription
from openapi_server.models.criterion_output_value_inner import CriterionOutputValueInner
from openapi_server.models.criterion_output_value_inner_validation import (
    CriterionOutputValueInnerValidation,
)
from openapi_server.models.criterion_workflow import CriterionWorkflow
from openapi_server.models.get_pipeline_commands_scripts200_response_inner import (
    GetPipelineCommandsScripts200ResponseInner,
)
from openapi_server.models.get_pipeline_composer_jepl200_response import (
    GetPipelineComposerJepl200Response,
)
from openapi_server.models.get_pipeline_config_jepl200_response_inner import (
    GetPipelineConfigJepl200ResponseInner,
)
from openapi_server.models.get_pipeline_jenkinsfile_jepl200_response import (
    GetPipelineJenkinsfileJepl200Response,
)
from openapi_server.models.get_pipeline_status200_response import (
    GetPipelineStatus200Response,
)
from openapi_server.models.je_pl_composer import JePLComposer
from openapi_server.models.je_pl_config import JePLConfig
from openapi_server.models.je_pl_config_config import JePLConfigConfig
from openapi_server.models.je_pl_jenkinsfile import JePLJenkinsfile
from openapi_server.models.je_pl_jenkinsfile_stages_inner import (
    JePLJenkinsfileStagesInner,
)
from openapi_server.models.je_pl_jenkinsfile_stages_inner_pipeline_config import (
    JePLJenkinsfileStagesInnerPipelineConfig,
)
from openapi_server.models.je_pl_jenkinsfile_stages_inner_when import (
    JePLJenkinsfileStagesInnerWhen,
)
from openapi_server.models.pipeline import Pipeline
from openapi_server.models.repository import Repository
from openapi_server.models.repository_credentials_id import RepositoryCredentialsId
from openapi_server.models.service_docker_compose_value import ServiceDockerComposeValue
from openapi_server.models.service_docker_compose_value_build import (
    ServiceDockerComposeValueBuild,
)
from openapi_server.models.service_docker_compose_value_image import (
    ServiceDockerComposeValueImage,
)
from openapi_server.models.service_docker_compose_value_image_registry import (
    ServiceDockerComposeValueImageRegistry,
)
from openapi_server.models.service_docker_compose_value_volumes_inner import (
    ServiceDockerComposeValueVolumesInner,
)
from openapi_server.models.tool import Tool
from openapi_server.models.tool_arg import ToolArg
from openapi_server.models.tool_docker import ToolDocker
from openapi_server.models.tox_simplified import ToxSimplified
from openapi_server.models.upstream_error import UpstreamError
from openapi_server.models.when_branch import WhenBranch
