import asyncio
import base64
import calendar
from datetime import datetime
import copy
from importlib.metadata import version
import io
import itertools
import logging
import json
import os
import re
import urllib
import uuid
from zipfile import ZipFile, ZipInfo

from aiohttp import web
from jinja2 import Environment, PackageLoader
from deepdiff import DeepDiff
import namegenerator

from openapi_server import config
from openapi_server import controllers
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
TOOLING_QAA_SPECIFIC_KEY = 'tools_qaa_specific'

SW_PREFIX = 'QC'
SRV_PREFIX = 'SvcQC'
FAIR_PREFIX = 'QC.Fair'

BADGE_CATEGORIES = ['bronze', 'silver', 'gold']

logger = logging.getLogger('sqaaas.api.controller')


git_utils, gh_utils, jk_utils, badgr_utils = controllers.init_utils()


async def _add_pipeline_to_db(body, report_to_stdout=False):
    """Stores the pipeline into the database.

    Returns an UUID that identifies the pipeline in the database.

    :param body: JSON request payload, as defined in the spec when 'POST /pipeline'
    :type body: dict | bytes
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
    body,
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
    def _filter_tools(repo, criteria_data_list, path='.'):
        criteria_data_list_filtered = []
        criteria_filtered_out = {}
        for criterion_data in criteria_data_list:
            criterion_data_copy = copy.deepcopy(criterion_data)
            criterion_has_required_level = False
            criterion_id = criterion_data_copy['id']
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
                    criteria_filtered_out[criterion_id] = filtered_out_data
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
        
        return criteria_data_list_filtered, criteria_filtered_out

    repo_code = body.get('repo_code', {})
    repo_docs = body.get('repo_docs', {})
    deployment = body.get('deployment', {})
    fair = body.get('fair', {})
    
    levels_for_assessment = ['REQUIRED', 'RECOMMENDED']
    tooling_metadata_json = await _get_tooling_metadata()
    criteria_data_list = await _sort_tooling_by_criteria(tooling_metadata_json)

    # NOTE Not allowing multiple assessments for the moment
    relevant_criteria_data = [] 
    if repo_code:
        # healthy check
        if deployment:
            logger.warning((
                'Provided URLs both for the source code and deployment '
                'assessment. Ignoring service assessment and continuing with '
                'source code assessment.'
            ))
        # are repo_code and repo_docs different?
        _same_repo = True
        if repo_docs:
            _same_repo = list(repo_code.values()) == list(repo_docs.values())

        _code_criteria = []
        for _data in criteria_data_list:
            _criterion_id = _data['id']
            if (
                _criterion_id.startswith('QC') and
                not _criterion_id in ['QC.FAIR']
            ):
                if _criterion_id in ['QC.Doc'] and not _same_repo:
                    relevant_criteria_data.append({
                        'repo': repo_docs,
                        'criteria_data_list': [_data]
                    })
                else:
                    _code_criteria.append(_data)
        relevant_criteria_data.append({
            'repo': repo_code,
            'criteria_data_list': _code_criteria
        })
    elif deployment:
        _code_criteria = []
        # deployment tool
        _deploy_tool = deployment['deploy_tool']
        for _data in criteria_data_list:
            if _data['id'].startswith('SvcQC'):
                if _data['id'] in ['SvcQC.Dep']:
                    _data['tools'] = [_deploy_tool]
                    user_requested_tools.append(_deploy_tool)
                _code_criteria.append(_data)

        # relevant_criteria_data
        relevant_criteria_data.append({
            'repo': deployment['repo_deploy'],
            'criteria_data_list': _code_criteria
        })
    elif fair:
        relevant_criteria_data.append({
            'repo': None,
            'criteria_data_list': []
        })
    else:
        # FIXME This will change when FAIR is integrated
        _reason = (
            'Neither source code/deployment repositories nor FAIR inputs have '
            'been provided for the assessment'
        )
        raise SQAaaSAPIException(422, _reason)
    logger.debug(
        'Resultant repository and criteria mapping: '
        '%s' % relevant_criteria_data
    )

    criteria_data_list_filtered = []
    criteria_filtered_out = {}
    for repo_criteria_mapping in relevant_criteria_data:
        (
            _criteria_data_list_filtered,
            _criteria_filtered_out
        ) = _filter_tools(**repo_criteria_mapping)
        criteria_data_list_filtered.extend(_criteria_data_list_filtered)
        criteria_filtered_out.update(_criteria_filtered_out)

    if not criteria_data_list_filtered:
        _reason = 'Could not find any tool for criteria assessment'
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)
    
    # print('*'*20)
    # import json
    # print(json.dumps(_criteria_data_list_filtered, indent=4))
    # print('*'*20)
    # import sys
    # sys.exit(0)

    return criteria_data_list_filtered, criteria_filtered_out


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

    #0 Validate request
    repo_code = body.get('repo_code', {})
    deployment = body.get('deployment', {})
    fair = body.get('fair', {})
    repo_data = {}
    
    repo_url = repo_code.get('repo', None) # is there data actually?
    if repo_url:
        repo_data = repo_code
        # Purge 
        body.pop('deployment', {})
    elif deployment:
        repo_deploy = deployment.get('repo_deploy', {})
        repo_deploy_url = repo_deploy.get('repo', None)
        if repo_deploy_url:
            repo_data = repo_deploy
            # Purge
            body.pop('repo_code', {})
            body.pop('repo_docs', {})
    
    if not repo_data and not fair:
        _reason = (
            'Invalid request: not valid data found for a '
            'software/service/FAIRness assessment'
        )
        return web.Response(status=422, reason=_reason, text=_reason)

    #1 Filter per-criterion tools that will take part in the assessment
    try:
        (
            criteria_data_list,
            criteria_filtered_out
        ) = await _get_tooling_for_assessment(
                body=body,
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
    pipeline_name = '.'.join([
        os.path.basename(repo_data['repo']),
        'assess'
    ])
    logger.debug('Generated pipeline name for the assessment: %s' % pipeline_name)
    json_rendered = template.render(
        pipeline_name=pipeline_name,
        repo_code=repo_code,
        repo_docs=body.get('repo_docs', {}),
        repo_deploy=deployment.get('repo_deploy', {}),
        criteria_data_list=criteria_data_list,
        tooling_qaa_specific_key=TOOLING_QAA_SPECIFIC_KEY
    )
    json_data = json.loads(json_rendered)
    logger.debug('Generated JSON payload (from template) required to create the pipeline for the assessment: %s' % json_data)

    #3 Create pipeline
    pipeline_id = await _add_pipeline_to_db(
        json_data,
        report_to_stdout=True
    )

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
    ## For the time being, just consider the main repo code. Still an array
    ## object must be returned
    active_branch = repo_data.get('branch', None)
    if not active_branch:
        active_branch = GitUtils.get_remote_active_branch(
            repo_data['repo']
        )
    repo_settings = {
        'name': ctls_utils.get_short_repo_name(repo_data['repo']),
        'url': repo_data['repo'],
        'tag': active_branch
    }
    platform = ctls_utils.supported_git_platform(
        repo_data['repo'], platforms=SUPPORTED_PLATFORMS
    )
    if platform in ['github']:
        gh_repo_name = repo_settings['name']
        repo_settings.update({
            'avatar_url': gh_utils.get_avatar(gh_repo_name),
            'description': gh_utils.get_description(gh_repo_name),
            'languages': gh_utils.get_languages(gh_repo_name),
            'topics': gh_utils.get_topics(gh_repo_name),
            'stargazers_count': gh_utils.get_stargazers(gh_repo_name),
            'watchers_count': gh_utils.get_watchers(gh_repo_name),
            'contributors_count': gh_utils.get_contributors(gh_repo_name),
            'forks_count': gh_utils.get_forks(gh_repo_name)
        })
    db.add_repo_settings(
        pipeline_id,
        repo_settings
    )

    #6 Store QAA data
    db.add_assessment_data(
        pipeline_id,
        criteria_filtered_out
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
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_repo = pipeline_data['pipeline_repo']

    if gh_utils.get_repository(pipeline_repo):
        gh_utils.delete_repo(pipeline_repo)
    if 'jenkins' in pipeline_data.keys():
        jk_job_name = pipeline_data['jenkins']['job_name']
        if jk_utils.exist_job(jk_job_name):
            jk_utils.scan_organization()
    else:
        logger.debug('Jenkins job not found. Pipeline might not have been yet executed')

    db.del_entry(pipeline_id)

    return web.Response(status=204)


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
    pipeline_repo = pipeline_data['pipeline_repo']
    pipeline_repo_url = pipeline_data['pipeline_repo_url']
    pipeline_repo_branch = repo_branch

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
        repo_data = gh_utils.get_repository(pipeline_repo)
        if not repo_data:
            repo_data = gh_utils.create_org_repository(pipeline_repo)
        pipeline_repo_branch = repo_data.default_branch

    logger.debug('Using pipeline repository <%s> (branch: %s)' % (
        pipeline_repo, pipeline_repo_branch))

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
    commit_url = gh_utils.get_commit_url(pipeline_repo, commit_id)

    logger.info('Pipeline repository set up at <%s> (branch: %s)' % (
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
    if jk_utils.exist_job(jk_job_name):
        logger.warning('Jenkins job <%s> already exists!' % jk_job_name)
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
        issue_badge=issue_badge
    )

    # Fire & forget _update_status()
    asyncio.create_task(_update_status(pipeline_id, triggered_by_run=True))

    return web.Response(status=204, reason=reason, text=reason)


async def _update_status(pipeline_id, triggered_by_run=False):
    """Updates the build status of a pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    """
    pipeline_data = db.get_entry(pipeline_id)

    if 'jenkins' not in pipeline_data.keys():
        _reason = 'Could not retrieve Jenkins job information: Pipeline <%s> has not yet ran' % pipeline_id
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    jenkins_info = pipeline_data['jenkins']
    build_info = jenkins_info['build_info']

    build_url = build_info['url']
    build_status = build_info.get('status', None)
    jk_job_name = jenkins_info['job_name']
    build_item_no = build_info['item_number']
    build_no = build_info['number']

    if jenkins_info['scan_org_wait']:
        logger.debug('scan_org_wait still enabled for pipeline job: %s' % jk_job_name)
        build_data = jk_utils.get_job_info(jk_job_name)
        if build_data.get('lastBuild', None):
            try:
                build_url = build_data['lastBuild']['url']
                build_no = build_data['lastBuild']['number']
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
        while not build_data and triggered_by_run:
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
    else:
        _status = jk_utils.get_build_info(
            jk_job_name,
            build_no
        )
        if _status['result']:
            build_status = _status['result']
            logger.debug('Job result returned from Jenkins: %s' % _status['result'])
        else:
            if _status.get('queueId', None):
                build_status = 'EXECUTING'
                logger.debug('Jenkins job queueId found: setting job status to <EXECUTING>')
    logger.info('Build status <%s> for job: %s (build_no: %s)' % (build_status, jk_job_name, build_no))

    # Add build status to DB
    db.update_jenkins(
        pipeline_id,
        jk_job_name,
        commit_id=jenkins_info['build_info']['commit_id'],
        commit_url=jenkins_info['build_info']['commit_url'],
        build_item_no=build_item_no,
        build_no=build_no,
        build_url=build_url,
        scan_org_wait=jenkins_info['scan_org_wait'],
        build_status=build_status,
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

    r = {
        'build_url': build_url,
        'build_status': build_status
    }
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
                'package_version': version(validator_package_name)
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
            if criterion_name in list(pipeline_data['qaa']):
                logger.error((
                    'Broken criterion <%s> is already present in the list '
                    'of filtered criteria. Overriding content..'
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
            pipeline_data['qaa'].update(broken_validation_data)
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
        criteria_filtered_out = pipeline_data['qaa']
        criteria_tools = pipeline_data['tools']

        for criterion_name, criterion_output_data_list in output_data.items():
            # Health check: a given criterion MUST NOT be present both in the
            # filtered list and as part of the pipeline execution stages
            # if criterion_name in list(criteria_filtered_out):
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
        # report_data.update(criteria_filtered_out)
        #
        # Subcriterion data shall be in the form:
        # {
        #   'description': 'str',
        #   'valid': true/false
        #   'evidence': [ .. ]
        #   'required_for_next_level_badge': true/false
        # }
        filtered_criteria = {}
        for _criterion, _data in criteria_filtered_out.items():
            filtered_criteria[_criterion] = {
                'valid': False,
                'subcriteria': {}
            }
            _metadata = r2s_utils.load_criterion_from_standard(_criterion)
            for _subcriterion, _subcriterion_metadata in _metadata.items():
                filtered_criteria[_criterion]['subcriteria'][_subcriterion] = {
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
            ) = _get_coverage(filtered_criteria[_criterion]['subcriteria'])
            
            filtered_criteria[_criterion]['coverage'] = {
                'percentage': percentage_criterion,
                'total_subcriteria': total_subcriteria,
                'success_subcriteria': success_subcriteria
            }
            # Add filtered criterion to reporting data
            report_data.update(filtered_criteria)

        return report_data

    def _get_criteria_per_badge_type(report_data):
        criteria_fulfilled_list = [
            criterion
            for criterion, criterion_data in report_data.items()
            if criterion_data['valid']
        ]

        if not criteria_fulfilled_list:
            logger.warn('No criteria was fulfilled!')
            criteria_fulfilled_map = {}
        else:
            # NOTE Keys aligned with subsection name in sqaaas.ini
            criteria_fulfilled_map = {
                'software': [],
                'services': [],
                'fair': [],
            }
            for criterion in criteria_fulfilled_list:
                if criterion.startswith(FAIR_PREFIX):
                    badge_type = 'fair'
                elif criterion.startswith(SW_PREFIX):
                    badge_type = 'software'
                elif criterion.startswith(SRV_PREFIX):
                    badge_type = 'services'
                criteria_fulfilled_map[badge_type].append(criterion)
        return criteria_fulfilled_map

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
        for badge_type, criteria_fulfilled_list in criteria_fulfilled_map.items():
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
            if badgeclass_name:
                try:
                    badge_obj = await _issue_badge(
                        pipeline_id,
                        badgeclass_name,
                    )
                    badge_data[badge_type]['data'] = badge_obj
                except SQAaaSAPIException as e:
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
                                rf"(^({SW_PREFIX}|{SRV_PREFIX})\.[A-Za-z]+)",
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
                                _required_for_next_level = True

                            (report_data_copy[criterion]
                                             ['subcriteria']
                                             [subcriterion]
                                             ['required_for_next_level_badge']
                            ) = _required_for_next_level

    r = {
        'repository': [pipeline_data.get('repo_settings', {})],
        'report': report_data_copy,
        'badge': badge_data
    }
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


async def _issue_badge(pipeline_id, badgeclass_name):
    """Issues a badge using BadgrUtils.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
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

    try:
        badge_data = badgr_utils.issue_badge(
            badgeclass_name=badgeclass_name,
            commit_id=build_info['commit_id'],
            commit_url=build_info['commit_url'],
            ci_build_url=build_info['url']
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

    dt = datetime.strptime(
        badge_data['createdAt'],
        '%Y-%m-%dT%H:%M:%S.%fZ'
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


async def get_criteria(request: web.Request, criterion_id=None) -> web.Response:
    """Returns data about criteria.

    :param criterion_id: Get data from a specific criterion
    :type criterion_id: str

    """
    try:
        tooling_metadata_json = await _get_tooling_metadata()
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    criteria_id_list = []
    if criterion_id:
        criteria_id_list = [criterion_id]
    criteria_data_list = await _sort_tooling_by_criteria(
        tooling_metadata_json, criteria_id_list=criteria_id_list)

    return web.json_response(criteria_data_list, status=200)
