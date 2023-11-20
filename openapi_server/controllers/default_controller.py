# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import asyncio
import base64
import calendar
from datetime import datetime
import copy
from importlib.metadata import version as impversion
from importlib.resources import files as impfiles
import io
import itertools
import logging
import json
import os
import pandas
import re
import urllib
import uuid
import yaml
from zipfile import ZipFile, ZipInfo

from aiohttp import web
from jinja2 import Environment, PackageLoader
from deepdiff import DeepDiff
import namegenerator

import openapi_server
from openapi_server import config
from openapi_server import controllers
from openapi_server.controllers import crypto as crypto_utils
from openapi_server.controllers import db
from openapi_server.controllers.badgr import BadgrUtils
from openapi_server.controllers.git import GitUtils
from openapi_server.controllers.github import GitHubUtils
from openapi_server.controllers.jenkins import JenkinsUtils
from openapi_server.controllers.jepl import JePLUtils
from openapi_server.controllers import utils as ctls_utils
from openapi_server.exception import SQAaaSAPIException
from openapi_server.models.inline_object import InlineObject

from report2sqaaas import utils as r2s_utils


SUPPORTED_PLATFORMS = {
    'github': 'https://github.com'
}
REPOSITORY_BACKEND = config.get(
    'repository_backend'
)
GITHUB_ORG = config.get_repo('organization')
JENKINS_GITHUB_ORG = config.get_ci('github_organization_name')
JENKINS_CREDENTIALS_FOLDER = config.get_ci('credentials_folder')
JENKINS_COMPLETED_STATUS = ['SUCCESS', 'FAILURE', 'UNSTABLE', 'ABORTED']
TOOLING_QAA_SPECIFIC_KEY = 'tools_qaa_specific'
ASSESSMENT_REPORT_LOCATION = config.get(
    'assessment_report_location',
    fallback='.report/assessment_output.json'
)
STATUS_BADGE_LOCATION = config.get(
    'status_badge_location',
    fallback='.badge/status_shields.svg'
)

SW_PREFIX = 'QC'
SRV_PREFIX = 'SvcQC'
FAIR_PREFIX = 'QC.FAIR'
FAIR_RDA_PREFIX = 'RDA'

BADGE_CATEGORIES = ['bronze', 'silver', 'gold']

logger = logging.getLogger('sqaaas.api.controller')


git_utils, gh_utils, jk_utils, badgr_utils = controllers.init_utils()


async def _add_pipeline_to_db(body, branch_upstream=None, report_to_stdout=False):
    """Stores the pipeline into the database.

    Returns an UUID that identifies the pipeline in the database.

    :param body: JSON request payload, as defined in the spec when 'POST /pipeline'
    :type body: dict | bytes
    :param branch_upstream: Name of the upstream branch
    :type branch_upstream: str
    :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tools (required by QAA module)
    :type report_to_stdout: bool
    """
    pipeline_id = str(uuid.uuid4())
    pipeline_name = body['name']
    pipeline_repo = '/'.join([GITHUB_ORG , pipeline_name + '.sqaaas'])
    pipeline_repo_url = '/'.join([SUPPORTED_PLATFORMS[REPOSITORY_BACKEND], pipeline_repo])
    logger.debug('Repository ID for pipeline name <%s>: %s' % (pipeline_name, pipeline_repo))
    logger.debug('Using GitHub repository name: %s' % pipeline_repo)

    db.add_entry(
        pipeline_id,
        pipeline_repo,
        pipeline_repo_url,
        body,
        pipeline_repo_branch=branch_upstream,
        report_to_stdout=report_to_stdout
    )

    return pipeline_id


@ctls_utils.debug_request
@ctls_utils.extended_data_validation
async def add_pipeline(request: web.Request, body, report_to_stdout=None) -> web.Response:
    """Creates a pipeline.

    Provides a ready-to-use Jenkins pipeline based on the v2 series of jenkins-pipeline-library.

    :param body: JSON request payload
    :type body: dict | bytes
    :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tools (required by QAA module)
    :type report_to_stdout: bool

    """
    pipeline_id = await _add_pipeline_to_db(body, report_to_stdout=report_to_stdout)

    r = {'id': pipeline_id}
    return web.json_response(r, status=201)


async def _get_tooling_for_assessment(
    repositories,
    user_requested_tools=[]
):
    """Returns per-criterion tooling metadata filtered for assessment.

    Two levels of filtering:
    - By <requirement_level>
    - By matching files in the repo content, either by <extensions> or
    <filenames>

    Whenever the criterion is filtered out, having REQUIRED or RECOMMENDED
    tools, a <filtered> property is added to the criterion dict that is
    returned by this method

    :param body: modified request body with the required data for assessment
    :type repo_code: dict
    :param user_requested_tools: Optional tools that shall be accounted
    :type user_requested_tools: list
    """
    @GitUtils.do_git_work
    def _filter_tools(repo, criteria_data_list, path='.', **kwargs):
        levels_for_assessment = ['REQUIRED', 'RECOMMENDED']
        criteria_data_list_filtered = []
        criteria_filtered = {}
        for criterion_data in criteria_data_list:
            criterion_data_copy = copy.deepcopy(criterion_data)
            criterion_id = criterion_data_copy['id']
            # Exception for 'SvcQC.Dep' & 'QC.FAIR': the tool to be used is
            # already provided through the <repo> object.
            if criterion_id in ['SvcQC.Dep']:
                _tool_to_be_used = repo['deploy_tool']
                criterion_data_copy['tools'] = [_tool_to_be_used]
            elif criterion_id in ['QC.FAIR']:
                _tool_to_be_used = repo['fair_tool']
                criterion_data_copy['tools'] = [_tool_to_be_used]
            criterion_has_required_level = False
            filter_tool_by_requirement_level = True
            toolset_for_reporting = []
            filtered_required_tools = []
            for tool in criterion_data_copy['tools']:
                # Tool filter #1: <reporting:requirement_level> property
                if filter_tool_by_requirement_level:
                    account_tool_by_requirement_level = False
                    try:
                        level = tool['reporting']['requirement_level']
                        if level in levels_for_assessment:
                            account_tool_by_requirement_level = True
                            logger.debug((
                                'Accounting for QAA the tool <%s> (reason: '
                                'REQUIRED/RECOMMENDED): %s' % (
                                    tool['name'], tool
                                )
                            ))
                            if level in ['REQUIRED']:
                                criterion_has_required_level = True
                        else:
                            if tool in user_requested_tools:
                                account_tool_by_requirement_level = True
                                logger.debug((
                                    'Accounting for QAA the tool <%s> (reason: '
                                    'tool requested by user): %s' % (
                                        tool['name'], tool
                                    )
                                ))
                    except KeyError:
                        logger.debug((
                            'Skipping tool <%s> as it does not have reporting data '
                            'defined: %s' % (tool['name'], tool)
                        ))
                else:
                    # NOTE: Setting this flag to true is a trick to make tools that
                    # have been requested not to be filtered-by-requirement-level
                    # can enter the next conditional block (lang files)
                    account_tool_by_requirement_level = True
                # Tool filter #2: presence of file extensions or filenames in the
                # repository based on the language
                if account_tool_by_requirement_level :
                    account_tool = False
                    lang = tool['lang']
                    lang_entry = ctls_utils.get_language_entry(lang)
                    if not lang_entry:
                        account_tool = True
                        logger.debug((
                            'Skipping file matching for tool <%s>: entry for '
                            'language <%s> has not been found in metadata file' % (
                                tool['name'], lang
                            )
                        ))
                    else:
                        files_found = []
                        field = None
                        value = None
                        for field_name in ['extensions', 'filenames']:
                            value = lang_entry.get(field_name, None)
                            if not value:
                                continue
                            logger.debug(
                                'Matching repo files by <%s> for language <%s>: '
                                '%s' % (
                                    field_name, lang, value
                                )
                            )
                            files_found = ctls_utils.find_files_by_language(
                                field_name, value, repo=repo, path=path
                            )
                            if files_found:
                                account_tool = True
                                logger.debug((
                                    'Found matching files in repository: '
                                    '%s' % files_found
                                ))
                                if tool['name'] in ['hadolint']:
                                    # Check if 'explicit_paths' property is enabled
                                    _relative_paths = [
                                        os.path.relpath(_file, path)
                                            for _file in files_found
                                    ]
                                    tool['args'] = ctls_utils.add_explicit_paths_for_tool(
                                        tool['args'], _relative_paths
                                    )
                                break
                        if not files_found:
                            _reason = (
                                'No matching files found for language <%s> in '
                                'repository searching by extensions or '
                                'filenames' % lang
                            )
                            if criterion_has_required_level:
                                filtered_required_tools.append(_reason)
                            logger.debug(_reason)
                    if account_tool:
                        logger.info(
                            'Tool <%s> accounted for assessment' % tool['name']
                        )
                        toolset_for_reporting.append(tool)
                    else:
                        logger.info((
                            'Not adding tool <%s> for the assessment. No matching '
                            'files (language: %s) found in the repository <%s>' % (
                                tool['name'], lang, repo['repo']
                            )
                        ))

            if not toolset_for_reporting:
                _reason = ((
                    'No tool defined for assessment (missing <reporting> '
                    'property) in <%s> criterion' % criterion_id
                ))
                if criterion_has_required_level:
                    filtered_out_data = ctls_utils.format_filtered_data(
                        False,
                        filtered_required_tools
                    )
                    criteria_filtered[criterion_id] = filtered_out_data
                    logger.warn(_reason)
                else:
                    logger.debug(_reason)
            else:
                logger.info((
                    'Found %s tool/s for assessment of criterion <%s>: %s' % (
                        len(toolset_for_reporting),
                        criterion_id,
                        [tool['name'] for tool in toolset_for_reporting])
                ))
                criterion_data_copy['tools'] = toolset_for_reporting
                criteria_data_list_filtered.append(criterion_data_copy)

        return criteria_data_list_filtered, criteria_filtered, kwargs


    # Get the relevant criteria for the type of assessment/digital object
    (
        relevant_criteria_data,
        digital_object_type
    ) = await _get_criteria_for_digital_object(repositories)

    # Get the tools that are relevant based on the repo content (add them to
    # <criteria_data_list_filtered>) and also the ones that are not (add them
    # in <criteria_filtered>)
    criteria_data_list_filtered = []
    criteria_filtered = {}
    for repo_criteria_mapping in relevant_criteria_data:
        try:
            (
                _criteria_data_list_filtered,
                _criteria_filtered,
                repo_settings
            ) = _filter_tools(**repo_criteria_mapping)
        except SQAaaSAPIException as e:
            raise e
        else:
            criteria_data_list_filtered.extend(_criteria_data_list_filtered)
            criteria_filtered.update(_criteria_filtered)

    if not criteria_data_list_filtered:
        _reason = 'Could not find any tool for criteria assessment'
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    return (
        criteria_data_list_filtered,
        criteria_filtered,
        repo_settings,
        digital_object_type
    )


async def _get_criteria_for_digital_object(repositories):
    """Returns the criteria associated with the digital object to be assessed.

    The type of digital object is guessed from the repository key name, so
    - 'repo_code' is source code DO type
    - 'deployment' is service DO type
    - 'fair' is data DO type

    :param repositories: dict with the repositories (and associated data) to
                         validate
    :type repositories: dict
    """
    _repo_keys = list(repositories)
    _digital_object_type = None
    # source code
    if 'repo_code' in _repo_keys:
        _repo_key = 'repo_code'
        _digital_object_type = 'software'
    # service
    elif 'repo_deploy' in _repo_keys:
        _repo_key = 'repo_deploy'
        _digital_object_type = 'service'
    # fair
    elif 'fair' in _repo_keys:
        _repo_key = 'fair'
        _digital_object_type = 'fair'
    # not known/supported
    else:
        _reason = (
            'Neither source code/deployment repositories nor FAIR inputs have '
            'been provided for the assessment'
        )
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    # Get the criteria that corresponds to the DO type
    criteria_data_list = await _get_criteria(
        digital_object_type = _digital_object_type
    )

    relevant_criteria_data = []
    # Exception 'repo_docs': add a separate entry if docs are in
    # a different repo
    _has_individual_doc_repo = 'repo_docs' in _repo_keys
    if _has_individual_doc_repo:
        # Get only the 'QC.Doc' criterion & add the rest to new list
        criteria_data_list_new = []
        for criterion_data in criteria_data_list:
            if criterion_data['id'] not in ['QC.Doc']:
                criteria_data_list_new.append(criterion_data)
            else:
                relevant_criteria_data.append({
                    'repo': repositories['repo_docs'],
                    'criteria_data_list': [criterion_data]
                })
        criteria_data_list = criteria_data_list_new

    # Add criteria list for the digital object type
    relevant_criteria_data.append({
        'repo': repositories[_repo_key],
        'criteria_data_list': criteria_data_list
    })
    logger.debug(
        'Resultant repository and criteria mapping: '
        '%s' % relevant_criteria_data
    )

    return relevant_criteria_data, _digital_object_type


def _validate_assessment_input(body):
    """Validates input data from the assessment request.

    Current policy: only allow one type of DO assessment, either 'source code',
    'service' or 'fair. If multiple are provided, it will follow the priority:
    source code -> services -> data.

    :param body: JSON payload request.
    :type body: dict | bytes
    """
    repo_code = body.get('repo_code', {})
    repo_docs = body.get('repo_docs', {})
    deployment = body.get('deployment', {})
    fair = body.get('fair', {})

    repositories = {}
    main_repo_key = None

    # source code
    if repo_code:
        main_repo_key = 'repo_code'
        # healthy check
        if deployment:
            logger.warning((
                'Provided URLs both for the source code and deployment '
                'assessment. Ignoring service assessment and continuing with '
                'source code assessment.'
            ))
        # Add repo/s for source code assessment
        if repo_docs:
            # healthy check: are repo_code and repo_docs the same URL?
            _same_code_and_docs_repo = list(repo_code.values()) == list(repo_docs.values())
            if not _same_code_and_docs_repo:
                repositories['repo_docs'] = repo_docs
        repositories['repo_code'] = repo_code
    # deployment
    elif deployment:
        main_repo_key = 'repo_deploy'
        if fair:
            logger.warning((
                'Provided input both for deployment and FAIR assessment. '
                'Ignoring FAIR assessment and continuing with service '
                'assessment.'
            ))
        repositories['repo_deploy'] = deployment['repo_deploy']
        # Exception for 'repo_deploy': add 'deploy_tool' at the same level as
        # 'repo_deploy' so that we can pop it afterwards in _filter_tool
        repositories['repo_deploy']['deploy_tool'] = deployment['deploy_tool']
    # FAIR: set 'repo' property to None to avoid git clone in _filter_tools()
    elif fair:
        main_repo_key = 'fair'
        repositories['fair'] = {
            'repo': None,
            'fair_tool': fair['fair_tool']
        }
    else:
        # FIXME This will change when FAIR is integrated
        _reason = (
            'Neither source code, deployment repositories nor FAIR inputs have '
            'been provided for the assessment'
        )
        raise SQAaaSAPIException(422, _reason)

    return repositories, main_repo_key


@ctls_utils.debug_request
async def add_pipeline_for_assessment(request: web.Request, body, user_requested_tools=[]) -> web.Response:
    """Creates a pipeline for assessment (QAA module).

    Creates a pipeline for assessment (QAA module).

    :param body: JSON payload request.
    :type body: dict | bytes
    :param user_requested_tools: Optional tools that shall be accounted
    :type user_requested_tools: list

    """
    # FIXME If it is applicable to every HTTP request, it shall be added as
    # part of the validate_request() decorator
    body = ctls_utils.del_empty_keys(body)
    repositories, main_repo_key = _validate_assessment_input(body)
    ci_credential_id = None

    #0 Encrypt credentials before storing in DB
    for _repo_key, _repo_data in repositories.items():
        _repo_creds = _repo_data.get('credentials_id', None)
        # type(str) == CI credentials (only id required)
        if type(_repo_creds) in [str]:
            ci_credential_id = _repo_creds
        # type(dict) == Credentials directly provided (user_id, token needed)
        elif type(_repo_creds) in [dict]:
            # Generate a new 'credential_data' key
            _repo_data['credential_data'] = {}
            _repo_creds_data = _repo_data.pop('credentials_id', None)
            for prop in ['secret_id', 'token', 'user_id']:
                _prop_value = _repo_creds_data.get(prop, '')
                if _prop_value:
                    _prop_encrypted = crypto_utils.encrypt_str(_prop_value)
                    _repo_data['credential_data'][prop] = _prop_encrypted
            # Generate and add Jenkins credential ID
            ci_credential_id = '-'.join([
                'sqaaas_tmp_cred', namegenerator.gen()
            ])
            _repo_data['credentials_id'] = ci_credential_id
            _repo_data['credential_tmp'] = True
        else:
            logger.error((
                'Provided credentials are not valid: format <%s> is not '
                'recognized' % type(_repo_creds)
            ))
            # FIXME Exit here?

    #1 Filter per-criterion tools that will take part in the assessment
    repo_settings = {}
    try:
        (
            criteria_data_list,
            criteria_filtered,
            repo_settings,
            digital_object_type
        ) = await _get_tooling_for_assessment(
                repositories=repositories,
                user_requested_tools=user_requested_tools
            )
        logger.debug((
            'Gathered tooling data enabled for assessment'
            ': %s' % criteria_data_list
        ))
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    #2 Load request payload (same as passed to POST /pipeline) from templates
    env = Environment(
        loader=PackageLoader('openapi_server', 'templates')
    )
    template = env.get_template('pipeline_assessment.json')

    # FIXME This only considers one repo
    build_repo_name = repositories[main_repo_key].get('repo', None)
    build_repo_branch = repositories[main_repo_key].get('branch', None)
    if 'fair' in list(repositories):
        # FIXME Temporary hack until the web provides all required input fields
        _fair_tool = repositories['fair']['fair_tool']
        for arg in _fair_tool['args']:
            if arg.get('id', '') in ['persistent_identifier']:
                build_repo_name = arg['value']
                break
    build_repo_name = build_repo_name.strip('/')
    pipeline_name = '.'.join([
        os.path.basename(build_repo_name),
        'assess'
    ])
    logger.debug('Generated pipeline name for the assessment: %s' % pipeline_name)

    json_rendered = template.render(
        pipeline_name=pipeline_name,
        repositories=repositories,
        criteria_data_list=criteria_data_list,
        tooling_qaa_specific_key=TOOLING_QAA_SPECIFIC_KEY,
        ci_credential_id = ci_credential_id
    )
    json_data = json.loads(json_rendered)
    logger.debug('Generated JSON payload (from template) required to create the pipeline for the assessment: %s' % json_data)

    #3 Create pipeline
    try:
        pipeline_id = await _add_pipeline_to_db(
            json_data,
            branch_upstream=build_repo_branch,
            report_to_stdout=True
        )
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    #4 Store tool related data in the DB
    pipeline_data = db.get_entry(pipeline_id)
    criteria_tools = pipeline_data['tools']
    for criterion_data in criteria_data_list:
        _criterion_id = criterion_data['id']
        for _tool_data in criterion_data['tools']:
            _tool_name = _tool_data['name']
            criteria_tools[_criterion_id][_tool_name].update({
                'lang': _tool_data['lang'],
                'version': _tool_data['version'],
                'docker': _tool_data['docker']
            })
    db.add_tool_data(pipeline_id, criteria_tools)

    #5 Store repo settings
    ## FIXME For the time being, just consider the main repo code. Still an
    ## array object must be returned
    repo_settings.update({
        'name': ctls_utils.get_short_repo_name(build_repo_name),
        'url': build_repo_name
    })
    if 'repo_code' in list(repositories) or 'repo_deploy' in list(repositories):
        platform = ctls_utils.supported_git_platform(
            repositories[main_repo_key]['repo'], platforms=SUPPORTED_PLATFORMS
        )
        _main_repo_creds = repositories[main_repo_key].get(
            'credential_data', {}
        )
        if platform in ['github']:
            gh_repo_name = repo_settings['name']
            try:
                gh_repo = gh_utils.get_repository(
                    gh_repo_name, _main_repo_creds, raise_exception=True
                )
                repo_settings.update({
                    'avatar_url': gh_utils.get_avatar(
                        gh_repo_name, _main_repo_creds
                    ),
                    'description': gh_utils.get_description(repo=gh_repo),
                    'languages': gh_utils.get_languages(repo=gh_repo),
                    'topics': gh_utils.get_topics(repo=gh_repo),
                    'stargazers_count': gh_utils.get_stargazers(repo=gh_repo),
                    'watchers_count': gh_utils.get_watchers(repo=gh_repo),
                    'contributors_count': gh_utils.get_contributors(repo=gh_repo),
                    'forks_count': gh_utils.get_forks(repo=gh_repo),
                })
            except SQAaaSAPIException as e:
                _reason = e.message
                return web.Response(
                    status=e.http_code, reason=_reason, text=_reason
                )

    # Update 'repo_settings' on DB
    db.add_repo_settings(
        pipeline_id,
        repo_settings
    )

    #6 Store QAA data
    db.add_assessment_data(
        pipeline_id,
        {
            'digital_object_type': digital_object_type,
            'criteria_filtered': criteria_filtered
        }
    )

    logger.info(
        'Pipeline for the QA assessment successfully created: %s' % pipeline_id
    )

    r = {'id': pipeline_id}
    return web.json_response(r, status=201)


@ctls_utils.debug_request
@ctls_utils.extended_data_validation
@ctls_utils.validate_request
async def update_pipeline_by_id(request: web.Request, pipeline_id, body, report_to_stdout=None) -> web.Response:
    """Update pipeline by ID

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param body:
    :type body: dict | bytes
    :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tools (required by QAA module)
    :type report_to_stdout: bool

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']
    pipeline_repo = pipeline_data['pipeline_repo']
    pipeline_repo_url = pipeline_data['pipeline_repo_url']

    config_json, composer_json, jenkinsfile_data = ctls_utils.get_pipeline_data(body)
    config_json_last, composer_json_last, jenkinsfile_data_last = ctls_utils.get_pipeline_data(pipeline_data_raw)

    diff_exists = False
    for elem in [
        (config_json_last, config_json),
        (composer_json_last, composer_json),
        (jenkinsfile_data_last, jenkinsfile_data),
    ]:
        ddiff = DeepDiff(*elem)
        if ddiff:
            diff_exists = True
            logging.debug(ddiff)

    if diff_exists:
        logger.debug('DB-updating modified pipeline on user request: %s' % pipeline_id)
        db.add_entry(
            pipeline_id,
            pipeline_repo,
            pipeline_repo_url,
            body,
            report_to_stdout=report_to_stdout
        )
    else:
        logger.debug('Not updating the pipeline: no difference found')

    return web.Response(status=204)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def delete_pipeline_by_id(request: web.Request, pipeline_id) -> web.Response:
    """Delete pipeline by ID

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    try:
        build_url, build_status = await _update_status(pipeline_id)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    _message = None
    if not build_url:
        _message = (
            'Cannot stop pipeline <%s>: build not already started (current '
            'status: %s)' % (pipeline_id, build_status)
        )
        logger.info(_message)
    else:
        pipeline_data = db.get_entry(pipeline_id)
        pipeline_repo = pipeline_data['pipeline_repo']
        jenkins_info = pipeline_data['jenkins']
        build_info = jenkins_info['build_info']

        jk_job_name = jenkins_info['job_name']
        build_no = build_info['number']
        if build_status in JENKINS_COMPLETED_STATUS:
            _message = (
                'Cannot stop pipeline <%s>: pipeline has finalized (status: '
                '%s)' % (pipeline_id, build_status)
            )
        else:
            jk_utils.stop_build(jk_job_name, build_no)
            logger.info('Stopping current build of pipeline <%s>' % pipeline_id)
            logger.debug('Stopping build: %s' % build_info['url'])
            # Set build status to ABORTED
            db.update_jenkins(
                pipeline_id,
                jk_job_name=jenkins_info['job_name'],
                commit_id=build_info['commit_id'],
                commit_url=build_info['commit_url'],
                build_item_no=build_info['item_number'],
                build_no=build_info['number'],
                build_url=build_info['url'],
                build_status='ABORTED',
                scan_org_wait=jenkins_info['scan_org_wait'],
                creds_tmp=jenkins_info['creds_tmp'],
                creds_folder=jenkins_info['creds_folder'],
                issue_badge=jenkins_info['issue_badge']
            )
            logger.info('Set ABORTED status to pipeline <%s>' % pipeline_id)

    return web.Response(status=204, reason=_message, text=_message)


@ctls_utils.debug_request
async def get_pipelines(request: web.Request) -> web.Response:
    """Gets pipeline IDs.

    Returns the list of IDs for the defined pipelines.

    """
    pipeline_list = []
    for pipeline_id, pipeline_data in db.get_entry().items():
        d = {'id': pipeline_id}
        d.update(pipeline_data['raw_request'])
        pipeline_list.append(d)

    return web.json_response(pipeline_list, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_by_id(request: web.Request, pipeline_id) -> web.Response:
    """Find pipeline by ID

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']

    r = {'id': pipeline_id}
    r.update(pipeline_data_raw)
    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_composer(request: web.Request, pipeline_id) -> web.Response:
    """Gets composer configuration used by the pipeline.

    Returns the content of JePL&#39;s docker-compose.yml file.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']

    r = pipeline_data_raw['composer_data']
    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_composer_jepl(request: web.Request, pipeline_id) -> web.Response:
    """Gets JePL composer configuration for the given pipeline.

    Returns the content of JePL&#39;s composer file.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)

    composer_data = pipeline_data['data']['composer']
    r = {
        'file_name': composer_data['file_name'],
        'content': composer_data['data_json']
    }

    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_config(request: web.Request, pipeline_id) -> web.Response:
    """Gets pipeline&#39;s main configuration.

    Returns the content of JePL&#39;s config.yml file.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']

    r = pipeline_data_raw['config_data']
    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_config_jepl(request: web.Request, pipeline_id) -> web.Response:
    """Gets JePL config configuration for the given pipeline.

    Returns the content of JePL&#39;s config file.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)

    config_data_list = pipeline_data['data']['config']
    r = [{
            'file_name': config_data['file_name'],
            'content': config_data['data_json']
        }
            for config_data in config_data_list
    ]

    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_commands_scripts(request: web.Request, pipeline_id) -> web.Response:
    """Gets the commands builder scripts

    Returns the content of the list of scripts generated for the commands builder.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    commands_scripts = pipeline_data['data']['commands_scripts']

    logger.info(
        'Successfully returned the list of scripts\'s content '
        'for pipeline <%s>' % pipeline_id
    )
    logger.debug(commands_scripts)

    return web.json_response(commands_scripts, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_jenkinsfile(request: web.Request, pipeline_id) -> web.Response:
    """Gets Jenkins pipeline definition used by the pipeline.

    Returns the content of JePL&#39;s Jenkinsfile file.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']

    r = pipeline_data_raw['jenkinsfile_data']
    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_jenkinsfile_jepl(request: web.Request, pipeline_id) -> web.Response:
    """Gets Jenkins configuration for the given pipeline.

    Returns the content of Jenkinsfile file for the given pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    jenkinsfile = pipeline_data['data']['jenkinsfile']

    r = {
        'file_name': 'Jenkinsfile',
        'content': jenkinsfile
    }

    return web.json_response(r, status=200)


def _set_im_config_files_content(
        additional_files_to_commit, repo_url, repo_branch
    ):
    """Iterates over the the list of additional files to commit (IM config
    files) present in the DB and calls add_im_image_id() to fetch and modify
    each one.

    This method shall only be required when the content of the IM config files
    is not available at pipeline-creation time, e.g. when the deployment files
    are not present in the defined external repositories. Thus, the URL of the
    repo is ONLY known when calling /run?repo_url, /pull_request or
    /compressed_files paths.

    :param additional_files_to_commit: List of
        {'file_name': <file_name>, 'file_data': <file_data>} objects
    :type additional_files_to_commit: list
    :param repo_url: URL of the remote repository
    :type repo_url: str
    :param repo_branch: Branch name of the remote repository
    :type repo_branch: str
    """
    # Additional files to commit, i.e. IM config files: when repo_url is
    # defined, data of the additional files is not defined because the repo
    # URL is not known at pipeline creation time
    additional_files_list = []
    for additional_file in additional_files_to_commit:
        if additional_file['file_data']:
            additional_files_list.append(additional_file)
        else:
            im_config_file = additional_file['file_name']
            im_image_id = additional_file['deployment']['im_image_id']
            openstack_url = additional_file['deployment']['openstack_url']
            _repo = {
                'repo': repo_url,
                'branch': repo_branch
            }
            _tech = ('ec3_client'
                if 'ec3_templates' in list(additional_file['deployment'])
                else 'im_client'
            )
            additional_files_list.append(
                ctls_utils.add_image_to_im(
                    im_config_file,
                    im_image_id,
                    openstack_url,
                    tech=_tech,
                    repo=_repo
                )
            )

    return additional_files_list


@ctls_utils.debug_request
@ctls_utils.validate_request
async def run_pipeline(
        request: web.Request,
        pipeline_id,
        issue_badge=False,
        repo_url=None,
        repo_branch=None,
        keepgoing=False
    ) -> web.Response:
    """Runs pipeline.

    Executes the given pipeline by means of the Jenkins API.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param issue_badge: Flag to indicate whether a badge shall be issued if the pipeline succeeds
    :type issue_badge: bool
    :param repo_url: URL of the upstream repository to fetch the code from
    :type repo_url: str
    :param repo_branch: Branch name of the upstream repository to fetch the code from
    :type repo_branch: str
    :param keepgoing: Flag to indicate that the pipeline will run until the end
    :type keepgoing: bool

    """
    if keepgoing:
        db.update_environment(pipeline_id, {'JPL_KEEPGOING': 'enabled'})

    pipeline_data = db.get_entry(pipeline_id)
    pipeline_data_raw = pipeline_data['raw_request']
    pipeline_repo = pipeline_data['pipeline_repo']
    pipeline_repo_url = pipeline_data['pipeline_repo_url']
    pipeline_repo_branch = pipeline_data['pipeline_repo_branch']
    if repo_branch:
        pipeline_repo_branch = repo_branch
        logger.info('Repository branch provided: %s' % repo_branch)

    config_data_list = pipeline_data['data']['config']
    composer_data = pipeline_data['data']['composer']
    jenkinsfile = pipeline_data['data']['jenkinsfile']

    additional_files_list = pipeline_data['data'].get(
        'additional_files_to_commit', []
    )
    if repo_url:
        if not ctls_utils.has_this_repo(config_data_list):
            _reason = ((
                'No criteria has been associated with the provided '
                'repository: %s' % repo_url
            ))
            logger.error(_reason)
            return web.Response(status=422, reason=_reason, text=_reason)
        logger.info((
            'Remote repository <%s> provided, will fetch & push content into '
            '<%s> organization: <%s> repository' % (
                repo_url, GITHUB_ORG, pipeline_repo_url
            )
        ))
        logger.debug('Create target repository: %s' % pipeline_repo_url)
        gh_utils.create_org_repository(pipeline_repo)
        logger.debug(
            'Clone & Push source repository <%s> to target repository <%s>' % (
                repo_url, pipeline_repo_url)
        )
        try:
            pipeline_repo_branch = git_utils.clone_and_push(
                repo_url, pipeline_repo_url, source_repo_branch=repo_branch)
        except SQAaaSAPIException as e:
            logger.error(e.message)
            _reason = (
                'Could not access to repository: %s (branch: %s)' % (
                    repo_url, repo_branch
                )
            )
            return web.Response(
                status=e.http_code, reason=_reason, text=_reason
            )
        else:
            logger.debug((
                'Pipeline repository updated with the content from source: '
                '%s (branch: %s)' % (pipeline_repo, pipeline_repo_branch)
            ))
        # Set IM config file content now that we know the remote repo URL
        additional_files_list = _set_im_config_files_content(
            pipeline_data['data']['additional_files_to_commit'],
            repo_url,
            repo_branch
        )
    else:
        _create_repo = False
        _repo = gh_utils.get_repository(pipeline_repo)
        if not _repo:
            _create_repo = True
        else:
            # Remove repo if empty
            if not gh_utils.get_repo_content(pipeline_repo):
                _repo.delete()
                _create_repo = True
                self.logger.debug(
                    'Removing repository as part of re-creation:'
                    '%s' % pipeline_repo
                )
            # Uses a specific branch, not the default one
            if pipeline_repo_branch:
                if not gh_utils.get_branch(pipeline_repo, pipeline_repo_branch):
                    _create_repo = True
            else:
                pipeline_repo_branch = _repo.default_branch

        if _create_repo:
            # Create repo from template (incl. README): use the same branch
            # name as upstream
            _repo = gh_utils.create_org_repository(
                pipeline_repo,
                branch=pipeline_repo_branch,
                include_readme=True
            )
            pipeline_repo_branch = _repo.default_branch

    logger.debug('Using pipeline repository <%s> (branch: %s)' % (
        pipeline_repo, pipeline_repo_branch))

    _pipeline_repo_name = pipeline_repo.split('/')[-1]
    jk_job_name = '/'.join([
        JENKINS_GITHUB_ORG,
        _pipeline_repo_name,
        jk_utils.format_job_name(pipeline_repo_branch)
    ])

    logger.info('Triggering pipeline in Jenkins CI: %s' % jk_job_name)

    build_item_no = None
    build_no = None
    build_url = None
    build_status = 'NOT_EXECUTED'
    scan_org_wait = False
    reason = ''

    # 0) Create CI temporary credentials ('credential_tmp') if needed
    creds_tmp = []
    creds_folder = JENKINS_CREDENTIALS_FOLDER
    ci_credentials = config_data_list[0]['data_json']['config']['credentials']
    for ci_credential in ci_credentials:
        _id = ci_credential['id']
        credential_data, credential_tmp = ctls_utils.get_credential_data(
            _id, pipeline_data_raw
        )
        if credential_tmp:
            logger.info(
                'Credential <%s> will be added temporarily to the CI '
                'server' % _id
            )
            _user_id = crypto_utils.decrypt_str(credential_data['user_id'])
            _token = crypto_utils.decrypt_str(credential_data['token'])

            if not creds_folder:
                logger.info(
                    'Jenkins credential folder (<credentials_folder> '
                    'property) not defined in config. Using project\'s '
                    'organisation folder name: %s' % JENKINS_GITHUB_ORG
                )
                creds_folder = JENKINS_GITHUB_ORG

            jk_utils.create_credential(
                _id,
                _user_id,
                _token,
                folder_name=creds_folder
            )
            creds_tmp.append(_id)

    # 1) Check if job already exists on Jenkins
    job_exists = False
    last_build_no = None
    if jk_utils.exist_job(jk_job_name):
        job_exists = True
        logger.warning('Jenkins job <%s> already exists!' % jk_job_name)
        _job_info = jk_utils.get_job_info(jk_job_name)
        jk_job_name = _job_info['fullName']
        last_build_no = _job_info['lastBuild']['number']

    # 2) Do the commit
    try:
        commit_id = JePLUtils.push_files(
            gh_utils,
            pipeline_repo,
            config_data_list,
            composer_data,
            jenkinsfile,
            pipeline_data['data']['commands_scripts'],
            additional_files_list,
            branch=pipeline_repo_branch
        )
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)
    else:
        commit_url = gh_utils.get_commit_url(pipeline_repo, commit_id)

    # 3) Automated-run check: previous commit should trigger the build
    build_job_task = None
    if job_exists:
        _build_to_check = last_build_no+1
        # Fire & forget _handle_job_building()
        build_job_task = asyncio.create_task(_handle_job_building(jk_job_name, _build_to_check))
        if build_job_task.done():
            build_no, build_status, build_url, build_item_no = build_job_task.result()
    else:
        jk_utils.scan_organization()
        scan_org_wait = True
        build_status = 'WAITING_SCAN_ORG'
        reason = 'Triggered scan organization for building the Jenkins job'

    if issue_badge:
        logger.debug((
            'Badge issuing (<issue_badge> flag) is requested for the current '
            'build: %s' % commit_id
        ))

    # Update pipeline in DB
    db.update_entry(
        pipeline_id,
        pipeline_repo_branch=pipeline_repo_branch
    )

    # FIXME Just need to update build data:
    #   <build_status>, <build_item_no>, <scan_org_wait>, <issue_badge>?
    db.update_jenkins(
        pipeline_id,
        jk_job_name,
        commit_id,
        commit_url,
        build_item_no=build_item_no,
        build_no=build_no,
        build_url=build_url,
        build_status=build_status,
        scan_org_wait=scan_org_wait,
        creds_tmp=creds_tmp,
        creds_folder=creds_folder,
        issue_badge=issue_badge
    )

    # Fire & forget _update_status()
    asyncio.create_task(_update_status(pipeline_id, triggered_by_run=True, build_task=build_job_task))
    logger.info(
        'Creating a parallel task to watch for the start of the '
        'pipeline <%s>' % pipeline_id
    )

    return web.Response(status=204, reason=reason, text=reason)


async def _handle_job_building(jk_job_name, build_to_check):
    # wait for automated triggering
    _build_triggered = False
    _max_tries = 8
    _count_tries = 0
    build_no = None
    build_status = None
    build_item_no = None
    while not _build_triggered:
        if _count_tries >= _max_tries:
            break
        _job_info = jk_utils.get_job_info(jk_job_name)
        # NOTE (Jenkins API specific) First element of _builds
        # should match 'build_to_check'
        _builds = _job_info['builds']
        _builds_last = _builds[0]['number']
        if _builds_last == build_to_check:
            _build_triggered = True
            build_no = build_to_check
            build_status = 'EXECUTING'
            build_url = _job_info['lastBuild']['url']
        else:
            logger.debug((
                'Last build number in Jenkins (%s) does not match with the '
                'required build number to check (%s) for job: %s' % (
                    _builds_last, build_to_check, jk_job_name
                )
            ))
        _count_tries += 1
        await asyncio.sleep(5)
    # Build manually if not triggered automatically
    if not _build_triggered:
        # <build_item_no> is only valid for about 5 min after job completion
        build_item_no = jk_utils.build_job(jk_job_name)
        if build_item_no:
            build_status = 'QUEUED'
            logger.info('Build status for pipeline <%s>: %s' % (
                pipeline_repo, build_status
            ))
            reason = 'Triggered the existing Jenkins job'
        else:
            _reason = 'Could not trigger build job'
            logger.error(_reason)
            raise SQAaaSAPIException(422, _reason)

    return (build_no, build_status, build_url, build_item_no)


async def _update_status(pipeline_id, triggered_by_run=False, build_task=None):
    """Updates the build status of a pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    """
    pipeline_data = db.get_entry(pipeline_id)
    build_no = None
    build_status = None
    build_url = None
    build_item_no = None

    _pipeline_executed = False

    if build_task:
        if build_task.done():
            build_no, build_status, build_item_no = build_job_task.result()
        else:
            _pipeline_executed = False

    jenkins_info = pipeline_data.get('jenkins', {})
    if jenkins_info:
        _pipeline_executed = True
        build_info = jenkins_info['build_info']
        jk_job_name = jenkins_info['job_name']
        build_no = build_info['number']
        build_status = build_info.get('status', None)
        build_url = build_info['url']
        build_item_no = build_info['item_number']

    if not _pipeline_executed:
        _reason = 'Could not retrieve Jenkins job information: Pipeline <%s> has not yet ran' % pipeline_id
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    if jenkins_info['scan_org_wait']:
        logger.debug('scan_org_wait still enabled for pipeline job: %s' % jk_job_name)
        _job_info = jk_utils.get_job_info(jk_job_name)
        if _job_info.get('lastBuild', None):
            try:
                build_url = _job_info['lastBuild']['url']
                build_no = _job_info['lastBuild']['number']
            except KeyError as e:
                logger.warning(e)
            else:
                logger.info('Jenkins job build URL (after Scan Organization finished) obtained: %s' % build_url)
                jenkins_info['build_info'].update({
                    'url': build_url,
                    'number': build_no,
                    'status': 'EXECUTING'
                })
                jenkins_info['scan_org_wait'] = False
        else:
            logger.debug('Job still waiting for scan organization to end')
            build_status = 'WAITING_SCAN_ORG'
    elif not build_no:
        build_data = {}
        # Keep looping if triggered by /run, but do not if triggered
        # by /status or /output
        if triggered_by_run:
            while not build_data:
                if not build_task.done():
                    await build_task
                build_no, build_status, build_url, build_item_no = build_task.result()
                if build_item_no:
                    build_data = await jk_utils.get_queue_item(build_item_no)
                    if build_data:
                        build_no = build_data['number']
                        build_url = build_data['url']
                        build_status = 'EXECUTING'
                        logger.info('Jenkins job build URL obtained for repository <%s>: %s' % (
                            pipeline_data['pipeline_repo'],
                            build_url
                        ))
                    else:
                        logger.debug('Could not get build data from Jenkins queue item: %s' % build_item_no)
                        await asyncio.sleep(3)
                # End 'while' if build_no & build_status
                elif (build_no and build_status):
                    build_data = True
    else:
        _status = jk_utils.get_build_info(
            jk_job_name,
            build_no
        )
        if _status['result']:
            build_status = _status['result']
            logger.debug('Job result returned from Jenkins: %s' % _status['result'])
            # Set as UNSTABLE when cleanup stage fails
            if jk_utils.cleanup_stage_failed(jk_job_name, build_no):
                build_status = 'UNSTABLE'
                logger.info(
                    'Cleanup stage failed: setting pipeline status to UNSTABLE'
                )
        else:
            if _status.get('queueId', None):
                build_status = 'EXECUTING'
                logger.debug('Jenkins job queueId found: setting job status to <EXECUTING>')
    logger.info('Build status <%s> for job: %s (build_no: %s)' % (build_status, jk_job_name, build_no))

    # Update assessment status on DB (and push payload)
    badge_status = None
    if build_status in ['SUCCESS', 'UNSTABLE']: # done, success
        pass # keep previous status
    elif build_status in ['ABORTED', 'FAILURE']: # done, failure
        badge_status = 'nullified'
    else:
        badge_status = 'building'
    logger.debug('Got current badge status for assessment (build: %s): %s' % (
        build_status, badge_status
    ))
    await _handle_badge_status(pipeline_id, pipeline_data, badge_status)

    # Add build status to DB
    db.update_jenkins(
        pipeline_id,
        jk_job_name,
        commit_id=jenkins_info['build_info']['commit_id'],
        commit_url=jenkins_info['build_info']['commit_url'],
        build_item_no=build_item_no,
        build_no=build_no,
        build_url=build_url,
        build_status=build_status,
        scan_org_wait=jenkins_info['scan_org_wait'],
        creds_tmp=jenkins_info.get('creds_tmp', []),
        creds_folder=jenkins_info.get('creds_folder', None),
        issue_badge=jenkins_info['issue_badge']
    )

    return (build_url, build_status)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_status(request: web.Request, pipeline_id) -> web.Response:
    """Get pipeline status.

    Obtains the build URL in Jenkins for the given pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    try:
        build_url, build_status = await _update_status(pipeline_id)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    # Remove any temporary credential
    pipeline_data = db.get_entry(pipeline_id)
    jenkins_info = pipeline_data['jenkins']
    creds_tmp = jenkins_info.get('creds_tmp', [])
    creds_folder = jenkins_info.get('creds_folder', None)
    build_status = jenkins_info['build_info'].get('status', '')

    creds_tmp_copy = copy.deepcopy(creds_tmp)
    if build_status in JENKINS_COMPLETED_STATUS:
        for _id in creds_tmp:
            jk_utils.remove_credential(_id, folder_name=creds_folder)
            creds_tmp_copy.remove(_id)

    # Return values
    r = {
        'build_url': build_url,
        'build_status': build_status
    }

    logger.info(
        'Successfully obtained the current status of the '
        'pipeline <%s>' % pipeline_id
    )
    logger.debug(r)

    return web.json_response(r, status=200)


async def _run_validation(criterion_name, **kwargs):
    """Validates the stdout using the sqaaas-reporting tool.

    Returns a (<tooling data>, <validation data>) tuple.

    :param criterion_name: ID of the criterion
    :type criterion_name: str
    :param kwargs: Additional data to provide to the validator
    :type kwargs: dict

    """
    tool = kwargs.get('tool', None)
    tooling_metadata_json = await _get_tooling_metadata()

    def _get_tool_reporting_data(tool):
        data = {}
        for tool_type, tools in tooling_metadata_json['tools'].items():
            if tool in list(tools):
                data = tools[tool]['reporting']
                logger.debug('Found reporting data in tooling for tool <%s>' % tool)
                return data
        return data

    try:
        # Obtain the report2sqaaas input args (aka <opts>) from tooling
        reporting_data = _get_tool_reporting_data(tool)
    except KeyError as e:
        _reason = 'Cannot get reporting data for tool <%s>: %s' % (tool, e)
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    # Add additional data for the validator plugin
    validator_opts = copy.deepcopy(reporting_data)
    validator_opts['stdout'] = kwargs.get('stdout_text', None)
    validator_opts['status'] = kwargs.get('status', None)
    validator_opts['criterion'] = criterion_name

    allowed_validators = r2s_utils.get_validators()
    validator_name = reporting_data['validator']
    out = None
    broken_validation_data = None
    if validator_name not in allowed_validators:
        _reason = 'Could not find report2sqaaas validator plugin <%s> (found: %s)' % (validator_name, allowed_validators)
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)
    else:
        validator = r2s_utils.get_validator(validator_opts)
        try:
            out = validator.driver.validate()
        except Exception as e:
            _reason = ((
                'Error raised when validating tool <%s> with validator '
                'plugin <%s>: %s' % (tool, validator_name, str(e))
            ))
            logger.error(_reason)

            interrupt = config.get_boolean(
                'interrupt_on_validation_error',
                fallback=False
            )
            if interrupt:
                logger.debug((
                    'End execution since <interrupt_on_validation_error> flag '
                    'is enabled'
                ))
                raise SQAaaSAPIException(422, _reason)
            else:
                broken_validation_data = ctls_utils.format_filtered_data(
                    False,
                    [_reason]
                )
        else:
            validator_package_name = '-'.join([
                'report2sqaaas-plugin', validator_name
            ])
            out.update({
                'package_name': validator_package_name,
                'package_version': impversion(validator_package_name)
            })

    return (reporting_data, out, broken_validation_data)


async def _get_commands_from_script(stdout_command, commands_script_list):
    """Returns the commands hosted in the bash commands script

    :param stdout_command: Tool command run by the pipeline.
    :type stdout_command: str
    :param commands_script_list: List of command scripts used in the pipeline.
    :type commands_script_list: list
    """
    bash_script_pattern = ".+(script\..+\.sh).*"
    try:
        script_name = re.search(bash_script_pattern, stdout_command).group(1)
    except AttributeError:
        return False
    for commands_script in commands_script_list:
        if script_name in commands_script['file_name']:
            return commands_script['content']


async def _get_tool_from_command(tool_criterion_map, stdout_command):
    """Returns the matching tool according to the given command.

    :param tool_criterion_map: Dict indexed by tool that contains the commands executed
    :type tool_criterion_map: dict
    :param stdout_command: Tool command run by the pipeline.
    :type stdout_command: str

    """
    matched_tool = None
    for tool_name, tool_data in tool_criterion_map.items():
        tool_cmd_list = tool_data['commands']
        # For the matching tool process, let's consider all cmds as a whole
        tool_cmd = ';'.join(tool_cmd_list)
        if stdout_command.find(tool_cmd) != -1:
            matched_tool = tool_name
            logger.debug('Matching tool <%s> found for stdout command <%s>' % (matched_tool, tool_cmd))
            break
    if not matched_tool:
        _reason = 'No matching tool found in command: %s' % stdout_command.replace('\n','')
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)

    return matched_tool


async def _validate_output(stage_data_list, pipeline_data):
    """Validates the output obtained from the pipeline execution.

    Returns the data following according to GET /pipeline/<id>/output path specification.

    :param stage_data_list: Per-stage data gathered from Jenkins pipeline execution.
    :type stage_data_list: list
    :param pipeline_data: Pipeline's data from DB
    :type pipeline_data: dict
    """
    logger.debug('Output validation has been requested')
    output_data = {}
    broken_validation_data = {}
    for stage_data in stage_data_list:
        criterion_stage_data = copy.deepcopy(stage_data)
        criterion_name = criterion_stage_data['criterion']

        logger.debug('Successful stage exit status for criterion <%s>' % criterion_name)
        # Check if the command lies within a bash script
        stdout_command = criterion_stage_data['stdout_command']
        commands_from_script = await _get_commands_from_script(
                stdout_command,
                pipeline_data['data']['commands_scripts']
        )
        if commands_from_script:
            logger.debug(
                'Detected a bash script in the criterion <%s> '
                'command. The real commands are: %s' % (
                    criterion_name, commands_from_script))
            stdout_command = commands_from_script
        tool_criterion_map = pipeline_data['tools'][criterion_name]
        matched_tool = await _get_tool_from_command(
            tool_criterion_map,
            stdout_command
        )
        criterion_stage_data['tool'] = matched_tool

        logger.debug('Validating output from criterion <%s>' % criterion_name)
        reporting_data, out, broken_data = await _run_validation(
            criterion_name, **criterion_stage_data
        )

        # If broken criterion, add to filtered criteria list
        if broken_data:
            # Health check: broken criteria should not be already in
            # the list of filtered criteria
            if criterion_name in list(pipeline_data['qaa']['criteria_filtered']):
                logger.error((
                    'Broken criterion <%s> is already present in the list '
                    'of filtered criteria. Overriding '
                    'content..' % criterion_name
                ))
            broken_validation_data[criterion_name] = broken_data
            logger.info(
                'Add broken criterion <%s> to filtered criteria list' % (
                    criterion_name
                )
            )
            continue

        logger.debug('Output returned by <%s> tool validator: %s' % (matched_tool, out))
        criterion_stage_data.update(reporting_data)
        criterion_stage_data['validation'] = out

        # Append if criterion is already there
        if criterion_name in list(output_data):
            output_data[criterion_name].append(criterion_stage_data)
        else:
            output_data[criterion_name] = [criterion_stage_data]

    return (output_data, broken_validation_data)


async def _get_output(pipeline_id, validate=False):
    """Handles the output gathering from pipeline execution

    Returns the output data.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param validate: Flag to indicate whether the returned output shall be validate using sqaaas-reporting tool
    :type validate: bool
    """
    build_url, build_status = await _update_status(pipeline_id)

    pipeline_data = db.get_entry(pipeline_id)
    jenkins_info = pipeline_data['jenkins']
    build_info = jenkins_info['build_info']

    stage_data_list = jk_utils.get_stage_data(
        jenkins_info['job_name'],
        build_info['number']
    )

    output_data = stage_data_list
    if validate:
        output_data, broken_validation_data = await _validate_output(
            stage_data_list, pipeline_data
        )
        if broken_validation_data:
            pipeline_data['qaa']['criteria_filtered'].update(broken_validation_data)
            db.add_assessment_data(pipeline_id, pipeline_data['qaa'])
            logger.info((
                'Updated broken criteria in DB\'s QAA assessment: '
                '%s' % pipeline_data['qaa']
            ))

    return output_data


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_output(request: web.Request, pipeline_id, validate=False) -> web.Response:
    """Get output from pipeline execution

    Returns the console output from the pipeline execution.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param validate: Flag to indicate whether the returned output shall be validate using sqaaas-reporting tool
    :type validate: bool

    """
    try:
        output_data = await _get_output(pipeline_id, validate=validate)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    return web.json_response(output_data, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_output_for_assessment(request: web.Request, pipeline_id) -> web.Response:
    """Get the assessment output

    Returns the reporting and badging data from the execution of the assessment pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    try:
        output_data = await _get_output(pipeline_id, validate=True)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    def _get_coverage(subcriteria):
        total_subcriteria = len(list(subcriteria))
        success_subcriteria = 0
        for subcriterion_id, subcriterion_data in subcriteria.items():
            if subcriteria[subcriterion_id]['valid']:
                success_subcriteria += 1
        percentage_criterion = 0
        if total_subcriteria > 0:
            percentage_criterion = int(
                success_subcriteria * 100 / total_subcriteria
            )

        return (
            total_subcriteria,
            success_subcriteria,
            percentage_criterion
        )

    def _format_report():
        report_data = {}
        pipeline_data = db.get_entry(pipeline_id)
        criteria_filtered = pipeline_data['qaa']
        criteria_tools = pipeline_data['tools']

        for criterion_name, criterion_output_data_list in output_data.items():
            # Health check: a given criterion MUST NOT be present both in the
            # filtered list and as part of the pipeline execution stages
            # if criterion_name in list(criteria_filtered):
            #     _reason = ((
            #         'Criterion <%s> has been both filtered out and executed '
            #         'in the pipeline' % criterion_name
            #     ))
            #     logger.error(_reason)
            #     raise SQAaaSAPIException(422, _reason)

            criterion_valid_list = []
            subcriteria = {}
            for criterion_output_data in criterion_output_data_list:
                validator_data = criterion_output_data['validation']
                criterion_valid_list.append(validator_data['valid'])
                # Plugin data
                package_name = validator_data.pop('package_name')
                package_version = validator_data.pop('package_version')
                plugin_data = {
                    'name': package_name,
                    'version': package_version
                }
                validator_data['plugin'] = plugin_data
                # Tool data
                tool = criterion_output_data['tool']
                ci_data = {
                    'name': criterion_output_data['name'],
                    'status': criterion_output_data['status'],
                    'stdout_command': criteria_tools[criterion_name][tool]['commands'],
                    'stdout_text': criterion_output_data['stdout_text'],
                    'url': criterion_output_data['url']
                }
                tool_data = {
                    'name': tool,
                    'lang': criteria_tools[criterion_name][tool].get('lang', None),
                    'version': criteria_tools[criterion_name][tool].get('version', None),
                    'docker': criteria_tools[criterion_name][tool].get('docker', None),
                    'ci': ci_data,
                    'level': criterion_output_data['requirement_level'],
                    'build_repo': pipeline_data.get('pipeline_repo_url', None)
                }

                # Compose subcriteria record
                for subcriterion_data in validator_data['subcriteria']:
                    subcriterion_id = subcriterion_data['id']
                    if subcriterion_id not in list(subcriteria):
                        subcriteria[subcriterion_id] = {
                            'description': subcriterion_data['description'],
                            'requirement_level': subcriterion_data.get(
                                'requirement_level', 'MAY'
                            ),
                            'hint': subcriterion_data['hint'],
                            'evidence': []
                        }
                    evidence_data = {
                        'valid': subcriterion_data['valid'],
                        'message': subcriterion_data['evidence'],
                        'plugin': plugin_data,
                        'tool': tool_data,
                        'standard': validator_data['standard'],
                        'data_unstructured': validator_data.get(
                            'data_unstructured', {}
                        )
                    }
                    subcriteria[subcriterion_id]['evidence'].append(
                        evidence_data
                    )
                # Subcriterion validity
                for subcriterion_id, subcriterion_data in subcriteria.items():
                    valid = all(evidence['valid']
                        for evidence in subcriterion_data['evidence'])
                    subcriteria[subcriterion_id]['valid'] = valid
                # Coverage
                (
                    total_subcriteria,
                    success_subcriteria,
                    percentage_criterion
                ) = _get_coverage(subcriteria)

            report_data[criterion_name] = {
                'valid': all(criterion_valid_list),
                'subcriteria': subcriteria,
                'coverage': {
                    'percentage': percentage_criterion,
                    'total_subcriteria': total_subcriteria,
                    'success_subcriteria': success_subcriteria
                }
            }

        # Report filtered-out criteria
        # report_data.update(criteria_filtered)
        #
        # Subcriterion data shall be in the form:
        # {
        #   'description': 'str',
        #   'valid': true/false
        #   'evidence': [ .. ]
        #   'required_for_next_level_badge': true/false
        # }
        _criteria_filtered = {}
        for _criterion, _data in criteria_filtered.items():
            _criteria_filtered[_criterion] = {
                'valid': False,
                'subcriteria': {}
            }
            _metadata = r2s_utils.load_criterion_from_standard(_criterion)
            for _subcriterion, _subcriterion_metadata in _metadata.items():
                _criteria_filtered[_criterion]['subcriteria'][_subcriterion] = {
                    'description': _subcriterion_metadata['description'],
                    'valid': _data.get('valid', False),
                    'hint': _subcriterion_metadata['hint'],
                    'evidence': [{
                        'valid': False,
                        'message': '\n'.join(_data.get(
                            'filtered_reason',
                            _subcriterion_metadata['evidence']['failure']
                        ))
                    }]
                }
            # Coverage
            (
                total_subcriteria,
                success_subcriteria,
                percentage_criterion
            ) = _get_coverage(_criteria_filtered[_criterion]['subcriteria'])

            _criteria_filtered[_criterion]['coverage'] = {
                'percentage': percentage_criterion,
                'total_subcriteria': total_subcriteria,
                'success_subcriteria': success_subcriteria
            }
            # Add filtered criterion to reporting data
            report_data.update(_criteria_filtered)

        return report_data

    def _get_criteria_per_badge_type(report_data):
        _criteria_data = report_data
        _criteria_list = list(report_data)
        if FAIR_PREFIX in _criteria_list:
            logger.info((
                'QC.FAIR criterion detected: considering only '
                'QC.FAIR subcriteria'
            ))
            _criteria_data = report_data['QC.FAIR']['subcriteria']
            badge_type = 'fair'
        elif _criteria_list[0].startswith(SW_PREFIX):
            badge_type = 'software'
        elif _criteria_list[0].startswith(SRV_PREFIX):
            badge_type = 'services'

        criteria_fulfilled_list = [criterion
            for criterion, criterion_data in _criteria_data.items()
                if criterion_data['valid']
        ]

        criteria_fulfilled_map = {}
        if not criteria_fulfilled_list:
            logger.warn('No criteria was fulfilled!')
        criteria_fulfilled_map[badge_type] = criteria_fulfilled_list
            # # NOTE Keys aligned with subsection name in sqaaas.ini
            # criteria_fulfilled_map = {
            #     'software': [],
            #     'services': [],
            #     'fair': [],
            # }
            # for criterion in criteria_fulfilled_list:
            #     if criterion.startswith(FAIR_PREFIX):
            #         badge_type = 'fair'
            #     elif criterion.startswith(SW_PREFIX):
            #         badge_type = 'software'
            #     elif criterion.startswith(SRV_PREFIX):
            #         badge_type = 'services'
            #     criteria_fulfilled_map[badge_type].append(criterion)
        return criteria_fulfilled_map

    def _get_spec_version():
        """Returns the version of the SQAaaS API specification.

        This method reads the specification version from the file stored
        locally at 'openapi_server/openapi/openapi.yaml'.
        """
        input_file = (impfiles(openapi_server) / 'openapi/openapi.yaml')
        with open(input_file, 'r') as fspec:
            spec_data = yaml.safe_load(fspec)

        return spec_data['info']['version']

    def _get_report_url_raw(pipeline_repo, pipeline_repo_branch):
        """Returns the raw URL of the SQAaaS assessment report.

        :param pipeline_repo: the assessment repo (*.assess.sqaaas)
        :param pipeline_repo: the assessment repo branch
        """
        _raw_url = None
        if REPOSITORY_BACKEND in ['github']:
            _raw_url = os.path.join(
                'https://raw.githubusercontent.com/',
                pipeline_repo,
                pipeline_repo_branch,
                ASSESSMENT_REPORT_LOCATION
            )

        return _raw_url

    # ----------------------------------------------
    # -- Main body of get_output_for_assessment() --
    # ----------------------------------------------
    #
    # Iterate over the criteria and associated tool results to compose the payload of the HTTP response:
    #    - <report> property
    #       + If any(valid is False and requirement_level in REQUIRED), then <QC.xxx>:valid=False
    #       + Compose <QC.xxx>:data:[REQUIRED|RECOMMENDED|OPTIONAL]:tool_name:data
    #    - <badge> property
    #       + Get SET of badge:[bronze|silver|gold] from sqaaas.ini
    #       + Compose SET of criteria fulfilled checking <QC.xxx>:valid is True
    #         + SET INTERSECTION to get the badge type
    #       + __FAIR special use case__:
    #         + Additional property provided by the validator plugin ---> <subcriteria>
    #         + If <subcriteria> is defined, then use these for the badge matchmaking (and not the criterion_name)
    # Format <report> key
    try:
        report_data = _format_report()
        if not report_data:
            _reason = 'Could not gather reporting data. Exiting..'
            logger.error(_reason)
            raise SQAaaSAPIException(422, _reason)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    # Gather & format <badge> key
    badge_data = {}
    share_data = None
    pipeline_data = {}
    report_data_copy = {}
    badge_status = 'no_badge'
    _repo_settings = {}
    # List of fullfilled criteria per badge type (i.e. [software, services, fair])
    criteria_fulfilled_map = _get_criteria_per_badge_type(report_data)
    if criteria_fulfilled_map:
        # Get pipeline data for the badge
        pipeline_data = db.get_entry(pipeline_id)
        try:
            jenkins_info = pipeline_data['jenkins']
            build_info = jenkins_info['build_info']
            commit_url = build_info['commit_url']
        except KeyError:
            _reason = 'Could not retrieve Jenkins job information: Pipeline has not ran yet'
            logger.error(_reason)
            return web.Response(status=422, reason=_reason, text=_reason)
        # Get Badgr's badgeclass and proceed with badge issuance
        missing_criteria_all = [] # required_for_next_level flag
        # NOTE: 1-to-1 relationship between badge_type and assessment
        badge_type, criteria_fulfilled_list = list(criteria_fulfilled_map.items())[0]
        (
            badgeclass_name,
            badge_category,
            criteria_summary
        ) = await _badgeclass_matchmaking(
            pipeline_id, badge_type, criteria_fulfilled_list
        )
        # Generate criteria summary
        criteria_summary_copy = copy.deepcopy(criteria_summary)
        for _badge_category, _badge_category_data in criteria_summary_copy.items():
            to_fulfill_set = set(_badge_category_data['to_fulfill'])
            missing_set = set(_badge_category_data['missing'])
            fulfilled_list = list(to_fulfill_set.difference(missing_set))
            criteria_summary[_badge_category]['fulfilled'] = fulfilled_list
        badge_data[badge_type] = {
            'criteria': criteria_summary
        }

        badge_data[badge_type]['data'] = {}
        if badgeclass_name:
            badge_status = badge_category
            try:
                badge_obj = await _issue_badge(
                    pipeline_id,
                    badge_type,
                    badgeclass_name,
                )
                badge_data[badge_type]['data'] = badge_obj
            except SQAaaSAPIException as e:
                badge_status = 'nullified'
                return web.Response(status=e.http_code, reason=e.message, text=e.message)
            else:
                # Generate & store share
                share_data = await _get_badge_share(badge_obj, commit_url)
                badge_data[badge_type]['share'] = share_data
                # Generate verification URL
                openbadgeid = badge_obj['openBadgeId']
                openbadgeid_urlencode = urllib.parse.quote_plus(openbadgeid)
                commit_urlencode = urllib.parse.quote_plus(commit_url)
                embed_url = (
                    f'{openbadgeid_urlencode}?identity__url='
                    f'{commit_urlencode}&amp;identity__url='
                    f'{commit_urlencode}'
                )
                badge_data[badge_type]['verification_url'] = (
                    'https://badgecheck.io/?url=%s' % embed_url
                )
            finally:
                # Manage repo_settings
                _repo_settings = await _handle_badge_status(
                    pipeline_id, pipeline_data, badge_status
                )

        # Next level badge
        next_level_badge = await _get_next_level_badge(badge_category)
        if next_level_badge:
            missing_criteria_all.extend(
                criteria_summary[next_level_badge]['missing']
            )

        # Store badge data in DB
        db.add_badge_data(pipeline_id, badge_data)

        # Subcriterion required_for_next_level
        report_data_copy = copy.deepcopy(report_data)
        for criterion, criterion_data in report_data.items():
            _subcriteria = criterion_data['subcriteria']
            if _subcriteria:
                for subcriterion, subcriterion_data in _subcriteria.items():
                    _valid = subcriterion_data['valid']
                    if not _valid:
                        try:
                            _criterion = re.search(
                                rf"(^({SW_PREFIX}|{SRV_PREFIX})\.[A-Za-z]+)|(^({FAIR_RDA_PREFIX})_[A-Z][0-9]+)",
                                subcriterion
                            ).group(0)
                        except AttributeError:
                            logger.error((
                                'Could not extract criterion string from '
                                'subcriterion string: %s. Could not check '
                                'whether the subcriterion is required for '
                                'the next-level badge' % subcriterion
                            ))
                        else:
                            _required_for_next_level = False
                            if _criterion in missing_criteria_all:
                                # get() method used in case the criterion
                                # validation returned a failure
                                _requirement_level = subcriterion_data.get(
                                    'requirement_level', 'MUST'
                                )
                                if _requirement_level in ['MUST']:
                                    _required_for_next_level = True

                            (report_data_copy[criterion]
                                             ['subcriteria']
                                             [subcriterion]
                                             ['required_for_next_level_badge']
                            ) = _required_for_next_level


    # Manage repo_settings
    _repo_settings = await _handle_badge_status(
        pipeline_id, pipeline_data, badge_status
    )

    # Compose the final payload
    pipeline_repo = pipeline_data['pipeline_repo']
    pipeline_repo_branch = pipeline_data['pipeline_repo_branch']
    r = {
        'meta': {
            'version': _get_spec_version(),
            'report_json_url': _get_report_url_raw(
                pipeline_repo, pipeline_repo_branch
            )
        },
        'repository': _repo_settings,
        'report': report_data_copy,
        'badge': badge_data
    }

    # Store JSON report in the assessment repository
    logger.debug(
        'Store resultant JSON report in the assessment '
        'repository: %s' % pipeline_repo
    )
    commit = gh_utils.push_file(
        file_name=ASSESSMENT_REPORT_LOCATION,
        file_data=json.dumps(r, indent=4),
        commit_msg='Add assessment report',
        repo_name=pipeline_repo,
    )
    if commit:
        logger.info(
            'Assessment report stored in repository <%s> under <%s> '
            'location' % (pipeline_repo, ASSESSMENT_REPORT_LOCATION)
        )
    else:
        logger.warning(
            'Could not store assessment report in repository '
            '<%s>' % pipeline_repo
        )

    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def create_pull_request(request: web.Request, pipeline_id, body) -> web.Response:
    """Creates pull request with JePL files.

    Create a pull request with the generated JePL files.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param body:
    :type body: dict | bytes

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_repo = pipeline_data['pipeline_repo']
    config_data_list = pipeline_data['data']['config']
    composer_data = pipeline_data['data']['composer']
    jenkinsfile = pipeline_data['data']['jenkinsfile']

    body = InlineObject.from_dict(body)
    supported_platform = ctls_utils.supported_git_platform(body.repo, platforms=SUPPORTED_PLATFORMS)
    if not supported_platform:
        _reason = ('Git platform <%s> is currently not supported for creating pull '
                   'requests (choose between: %s)' % (
                       supported_platform,
                       SUPPORTED_PLATFORMS.keys()))
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)
    target_repo_name = ctls_utils.get_short_repo_name(body.repo)
    logger.debug('Target repository (base) formatted. Resultant name: %s' % target_repo_name)
    target_repo = gh_utils.get_repository(
        target_repo_name, raise_exception=True)

    target_branch_name = target_repo.default_branch
    if body.branch:
        target_branch_name = body.branch
    logger.debug('Target repository (base) path: %s (branch: %s)' % (
        target_repo_name, target_branch_name))

    # step 1: create the source repo (either fork or target repo itself)
    fork_created = gh_utils.create_fork(target_repo_name)
    if fork_created:
        source_repo = fork_created
        source_branch_name = fork_created.parent.default_branch
    else:
        logger.debug('Source (head) and target (base) are the same repository')
        source_branch_name = '_'.join(['sqaaas', namegenerator.gen()])
        logger.debug('Source (head) random branch name generated: %s' % source_branch_name)
        source_repo = gh_utils.create_branch(
            target_repo_name, source_branch_name, target_branch_name)
        logger.debug('Branch <%s> created from head branch <%s>' % (
            source_branch_name, target_branch_name))
    logger.debug('Source repository (head) path: %s (branch: %s)' % (
       source_repo.full_name, source_branch_name))
    # step 2: push JePL files
    #   Set IM config file content now that we know the remote repo URL
    additional_files_list = _set_im_config_files_content(
        pipeline_data['data']['additional_files_to_commit'],
        body.repo,
        body.branch
    ) or []
    JePLUtils.push_files(
        gh_utils,
        source_repo.full_name,
        config_data_list,
        composer_data,
        jenkinsfile,
        pipeline_data['data']['commands_scripts'],
        additional_files_list,
        branch=source_branch_name
    )
    # step 3: create PR if it does not exist
    target_pr_data = [
        dict([['html_url', pr.html_url], ['data', (pr.head.repo.name, pr.head.ref)]])
            for pr in target_repo.get_pulls() if pr.state in ['open']]
    source_repo_data = (source_repo.name, source_branch_name)
    pr_exists = [
        pr_data
            for pr_data in target_pr_data if pr_data['data'] == source_repo_data
    ]
    if pr_exists:
        pr_url = pr_exists[0]['html_url']
        logger.info('Pull request <%s> updated (already existed)' % pr_url)
    else:
        pr = gh_utils.create_pull_request(
            source_repo.full_name,
            source_branch_name,
            target_repo_name,
            target_branch_name
        )
        pr_url = pr['html_url']

    r = {'pull_request_url': pr_url}
    return web.json_response(r, status=200)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_compressed_files(request: web.Request, pipeline_id) -> web.Response:
    """Get JePL files in compressed format.

    Obtains the generated JePL files in compressed format.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)

    config_data_list = pipeline_data['data']['config']
    composer_data = pipeline_data['data']['composer']
    jenkinsfile = pipeline_data['data']['jenkinsfile']
    commands_scripts = pipeline_data['data']['commands_scripts']

    config_yml_list = [
        (data['file_name'], data['data_yml'])
            for data in config_data_list
    ]
    composer_yml = [(
        composer_data['file_name'],
        composer_data['data_yml']
    )]
    jenkinsfile = [(
        'Jenkinsfile', jenkinsfile
    )]
    if commands_scripts:
        commands_scripts = [
            (data['file_name'], data['content'])
                for data in commands_scripts
        ]

    binary_stream = io.BytesIO()
    with ZipFile(binary_stream, 'w') as zfile:
        for t in (
                config_yml_list +
                composer_yml +
                jenkinsfile +
                commands_scripts
            ):
            zinfo = ZipInfo(t[0])
            zfile.writestr(zinfo, t[1].encode('UTF-8'))

    zip_data = binary_stream.getbuffer()
    response = web.StreamResponse()
    response.content_type = 'application/zip'
    response.content_length = len(zip_data)
    response.headers.add(
        'Content-Disposition', 'attachment; filename="sqaaas.zip"')
    await response.prepare(request)
    await response.write(zip_data)

    return response


# FIXME Badge categories must not be hardcoded here
async def _get_next_level_badge(badge_category):
    next_level_badge = None
    if badge_category:
        list_item_no = BADGE_CATEGORIES.index(badge_category)
        try:
            next_level_badge = BADGE_CATEGORIES[list_item_no + 1]
        except IndexError:
            logger.debug('Already achieved highest badge class level')
    else:
        next_level_badge = BADGE_CATEGORIES[0]

    return next_level_badge


async def _badgeclass_matchmaking(pipeline_id, badge_type, criteria_fulfilled_list):
    """Does the matchmaking to obtain the badgeclass to be awarded (if any).

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param badge_type: The type of badge from [software, services, fair].
    :type badge_type: str
    :param criteria_fulfilled_list: List of criteria codes fulfilled by the pipeline.
    :type criteria_fulfilled_list: list
    """
    badge_awarded_badgeclass_name = None
    badge_awarded_category = None
    criteria_summary = {}
    for badge_category in BADGE_CATEGORIES:
        logger.debug('Matching given criteria against defined %s criteria for %s' % (
            badge_category.upper(), badge_type.upper())
        )

        criteria_summary[badge_category] = {
            'to_fulfill': [],
            'missing': []
        }

        # Get badge type's config values
        badgeclass_name = config.get_badge(
            'badgeclass', subsection_list=[badge_type, badge_category]
        )
        criteria_to_fulfill_list = config.get_badge(
            'criteria', subsection_list=[badge_type, badge_category]
        ).split()
        # Remove any repeated criterion
        criteria_to_fulfill_list = list(set(criteria_to_fulfill_list))
        criteria_summary[badge_category]['to_fulfill'] = criteria_to_fulfill_list
        # Matchmaking
        missing_criteria_list = list(set(criteria_to_fulfill_list).difference(criteria_fulfilled_list))
        criteria_summary[badge_category]['missing'] = missing_criteria_list
        if missing_criteria_list:
            logger.warn('Pipeline <%s> not fulfilling %s criteria. Missing criteria: %s' % (
                pipeline_id, badge_category.upper(), missing_criteria_list)
            )
        else:
            logger.info('Pipeline <%s> fulfills %s badge criteria!' % (
                pipeline_id, badge_category.upper())
            )
            badge_awarded_badgeclass_name = badgeclass_name
            badge_awarded_category = badge_category

    if badge_awarded_badgeclass_name:
        logger.debug('Badgeclass to use for badge issuance: %s' % badge_awarded_badgeclass_name)

    return (
        badge_awarded_badgeclass_name,
        badge_awarded_category,
        criteria_summary
    )


async def _issue_badge(pipeline_id, badge_type, badgeclass_name):
    """Issues a badge using BadgrUtils.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param badge_type: String that identifies the type of badge
    :type badge_type: str
    :param badgeclass_name: String that corresponds to the BadgeClass name (as it appears in Badgr web)
    :type badgeclass_name: str
    """
    logger.info('Issuing badge for pipeline <%s>' % pipeline_id)

    # Get pipeline data
    pipeline_data = db.get_entry(pipeline_id)
    try:
        jenkins_info = pipeline_data['jenkins']
        build_info = jenkins_info['build_info']
    except KeyError:
        _reason = 'Could not retrieve Jenkins job information: Pipeline has not ran yet'
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)

    badge_args = {}
    if badge_type not in ['fair']:
        badge_args = {
            'tag': pipeline_data['repo_settings']['tag'],
            'commit_id': pipeline_data['repo_settings']['commit_id'],
        }

    try:
        badge_data = badgr_utils.issue_badge(
            badge_type=badge_type,
            badgeclass_name=badgeclass_name,
            url=pipeline_data['repo_settings']['url'],
            build_commit_id=build_info['commit_id'],
            build_commit_url=build_info['commit_url'],
            ci_build_url=build_info['url'],
            **badge_args
        )
    except Exception as e:
        _reason = 'Cannot issue a badge for pipeline <%s>: %s' % (pipeline_id, e)
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)
    else:
        logger.info('Badge successfully issued: %s' % badge_data['openBadgeId'])
        return badge_data


async def _get_badge_share(badge_data, commit_url):
    """Gets badge data for sharing.

    :param badge_data: Object with data obtained from Badgr
    :type badge_data: dict
    :param commit_url: Code repository commit URL
    :type commit_url: str
    """
    env = Environment(
        loader=PackageLoader('openapi_server', 'templates')
    )
    template = env.get_template('embed_badge.html')

    dt = pandas.to_datetime(
        badge_data['createdAt'],
        format='%Y-%m-%dT%H:%M:%S.%fZ'
    )
    html_rendered = template.render({
        'openBadgeId': badge_data['openBadgeId'],
        'commit_url': commit_url,
        'image': badge_data['image'],
        'badgr_badgeclass': badge_data['badgeclass'],
        'award_month': calendar.month_name[dt.month],
        'award_day': dt.day,
        'award_year': dt.year,
    })

    return html_rendered


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_badge(request: web.Request, pipeline_id) -> web.Response:
    """Gets badge data associated with the given pipeline

    Returns the badge data associated with the pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    """
    pipeline_data = db.get_entry(pipeline_id)

    try:
        badge_obj = pipeline_data['badge']
        if not badge_obj:
            raise KeyError
    except KeyError:
        _reason = 'Badge not issued for pipeline <%s>' % pipeline_id
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)

    logger.debug('Badge data found for pipeline <%s>: %s' % (
        pipeline_id, badge_obj)
    )

    return web.json_response(badge_obj, status=200)


async def _get_tooling_metadata():
    """Returns the tooling metadata available in the given remote code repository."""
    tooling_repo_url = config.get(
        'tooling_repo_url',
        fallback='https://github.com/EOSC-synergy/sqaaas-tooling'
    )
    tooling_repo_branch = config.get(
        'tooling_repo_branch',
        fallback='main'
    )
    tooling_metadata_file = config.get(
        'tooling_metadata_file',
        fallback='tooling.json'
    )

    logger.debug((
        'Getting supported tools from <%s> repo (branch: %s, metadata file: '
        '%s)' % (
            tooling_repo_url, tooling_repo_branch, tooling_metadata_file
        )
    ))
    platform = ctls_utils.supported_git_platform(
        tooling_repo_url, platforms=SUPPORTED_PLATFORMS)
    tooling_metadata_json = {}
    if platform in ['github']:
        short_repo_name = ctls_utils.get_short_repo_name(tooling_repo_url)
        tooling_metadata_content = gh_utils.get_file(
            tooling_metadata_file,
            short_repo_name,
            branch=tooling_repo_branch,
            fail_if_not_exists=True
        )
        tooling_metadata_encoded = tooling_metadata_content.content
        tooling_metadata_decoded = base64.b64decode(tooling_metadata_encoded).decode('UTF-8')
        tooling_metadata_json = json.loads(tooling_metadata_decoded)
    else:
        raise NotImplementedError(('Getting tooling metadata from a non-Github '
                                   'repo is not currently supported'))

    return tooling_metadata_json


async def _get_criterion_tooling(
        criterion_id,
        tooling_metadata_json,
        tools_qaa_specific=False
    ):
    """Gets the criterion information as it is returned within the
    /criteria response.

    :param criterion_id: ID of the criterion
    :type criterion_id: str
    :param tooling_metadata_json: JSON with the metadata
    :type tooling_metadata_json: dict
    :param tools_qaa_specific: Flag to enable qaa-specific tools lookup
    :type tools_qaa_specific: boolean
    """
    tool_key = 'tools'
    add_default_tools = True
    if tools_qaa_specific:
        tool_key = TOOLING_QAA_SPECIFIC_KEY
        add_default_tools = False

    try:
        criterion_data = tooling_metadata_json['criteria'][criterion_id][tool_key]
    except Exception as e:
        _reason = 'Cannot find tooling information for criterion <%s> in metadata: %s' % (
            criterion_id, tooling_metadata_json)
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)

    # Add default tools
    if add_default_tools:
        default_data = {"default": list(tooling_metadata_json["tools"]["default"])}
        criterion_data.update(default_data)

    criterion_data_list = []
    for lang, tools in criterion_data.items():
        for tool in tools:
            d = {}
            try:
                d['name'] = tool
                d['lang'] = lang
                d.update(tooling_metadata_json['tools'][lang][tool])
            except KeyError:
                logger.warn('Cannot find data for tool <%s> (lang: %s)' % (
                    tool, lang))
            if d:
                criterion_data_list.append(d)

    return criterion_data_list


async def _sort_tooling_by_criteria(tooling_metadata_json, criteria_id_list=[]):
    """Sorts out the tooling data by each supported criterion.

    Returns a list of tooling data per supported criterion.

    :param tooling_metadata_json: JSON with the metadata
    :type tooling_metadata_json: dict
    :param criteria_id_list: custom set of criteria
    :type criteria_id_list: list
    """
    if criteria_id_list:
        logger.debug('Filtering criteria to <%s>' % criteria_id_list)
    else:
        criteria_id_list = list(tooling_metadata_json['criteria'])
        logger.debug('Considering all the supported criteria from tooling <%s>' % criteria_id_list)

    criteria_data_list = []
    try:
        for criterion in criteria_id_list:
            criterion_data = tooling_metadata_json['criteria'][criterion]
            tooling_data = await _get_criterion_tooling(
                criterion, tooling_metadata_json)
            criterion_data.update({
                'id': criterion,
                'tools': tooling_data
            })
            # Get tooling data for qaa-specific tools property
            if TOOLING_QAA_SPECIFIC_KEY in list(criterion_data):
                tooling_data_qaa = await _get_criterion_tooling(
                    criterion, tooling_metadata_json, tools_qaa_specific=True)
                criterion_data[TOOLING_QAA_SPECIFIC_KEY] = tooling_data_qaa

            criteria_data_list.append(criterion_data)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    return criteria_data_list


async def _get_criteria(
        criteria_id_list=[], assessment=False, digital_object_type=None
    ):
    """Gets and filters criteria from tooling.

    :param criterion_id_list: Specific list of criteria to check
    :type criterion_id_list: list
    :param assessment: Flag to indicate whether the criteria shall consider only assessment-related tools
    :type assessment: bool
    :param digital_object_type: one of ['software', 'service', 'fair']. This matches "type" in tooling
    :type digital_object_type: str

    """
    try:
        tooling_metadata_json = await _get_tooling_metadata()
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    criteria_data_list = await _sort_tooling_by_criteria(
        tooling_metadata_json, criteria_id_list=criteria_id_list)

    if assessment: # exclude 'commands' tool
        for criterion_data in criteria_data_list:
            _tool_list = []
            for tool_data in criterion_data['tools']:
                if tool_data['name'] not in ['commands']:
                    _tool_list.append(tool_data)
            criterion_data['tools'] = _tool_list

    _criteria_data_list_new = []
    if digital_object_type: # include only the criteria matching 'type'
        _criteria_data_list_new = [
            criterion_data
                for criterion_data in criteria_data_list
                    if digital_object_type in [criterion_data['type']]
        ]
        criteria_data_list = _criteria_data_list_new

    return criteria_data_list


async def get_criteria(request: web.Request, criterion_id=None, assessment=None) -> web.Response:
    """Returns data about criteria.

    :param criterion_id: Get data from a specific criterion
    :type criterion_id: str
    :param assessment: Flag to indicate whether the criteria shall consider only assessment-related tools
    :type assessment: bool

    """
    criteria_id_list = []
    if criterion_id:
        criteria_id_list = [criterion_id]
    criteria_data_list = await _get_criteria(
        criteria_id_list, assessment=assessment
    )

    return web.json_response(criteria_data_list, status=200)


async def _handle_badge_status(pipeline_id, pipeline_data, badge_status=None):
    """Returns data about criteria.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param pipeline_data: Pipeline's data from DB
    :type pipeline_data: dict
    :param badge_status: status string to be displayed on the badge.
    :type badge_status: str
    """
    repo_settings = pipeline_data.get('repo_settings', {})
    badge_status_previous = repo_settings.get('badge_status', None)
    if not badge_status:
        badge_status = badge_status_previous
    if badge_status != badge_status_previous:
        logger.debug('Status badge changed from <%s> to <%s>' % (
            badge_status_previous, badge_status
        ))
        repo_settings['badge_status'] = badge_status
        db.add_repo_settings(pipeline_id, repo_settings)
        logger.info('New status badge updated in DB for pipeline <%s>: status <%s>' % (
            pipeline_id, badge_status)
        )
        # Push badge
        pipeline_repo = pipeline_data['pipeline_repo']
        pipeline_repo_branch = pipeline_data['pipeline_repo_branch']
        gh_utils.push_file(
            file_name=STATUS_BADGE_LOCATION,
            file_data=ctls_utils.get_status_badge(badge_status),
            commit_msg='Update status badge',
            repo_name=pipeline_repo,
            branch=pipeline_repo_branch
        )
        logger.info('New status badge pushed to repository <%s>: status <%s>' % (
            pipeline_repo, badge_status)
        )
    else:
        logger.debug('No change in status badge: %s' % badge_status)

    return repo_settings
