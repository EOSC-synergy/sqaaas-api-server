import asyncio
import base64
import calendar
from datetime import datetime
import copy
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
TOKEN_GH_FILE = config.get_repo(
    'token', fallback='/etc/sqaaas/.gh_token')
GITHUB_ORG = config.get_repo('organization')

TOKEN_JK_FILE = config.get_ci(
    'token', fallback='/etc/sqaaas/.jk_token')
JENKINS_URL = config.get_ci('url')
JENKINS_USER = config.get_ci('user')
JENKINS_GITHUB_ORG = config.get_ci('github_organization_name')

TOKEN_BADGR_FILE = config.get_badge(
    'token', fallback='/etc/sqaaas/.badgr_token')
BADGR_URL = config.get_badge('url')
BADGR_USER = config.get_badge('user')
BADGR_ISSUER = config.get_badge('issuer')

logger = logging.getLogger('sqaaas.api.controller')

# Instance of code repo backend object
with open(TOKEN_GH_FILE,'r') as f:
    token = f.read().strip()
logger.debug('Loading GitHub token from local filesystem')
gh_utils = GitHubUtils(token)
git_utils = GitUtils(token)

# Instance of CI system object
with open(TOKEN_JK_FILE,'r') as f:
    jk_token = f.read().strip()
logger.debug('Loading Jenkins token from local filesystem')
jk_utils = JenkinsUtils(JENKINS_URL, JENKINS_USER, jk_token)

# Instance of Badge issuing service object
with open(TOKEN_BADGR_FILE,'r') as f:
    badgr_token = f.read().strip()
logger.debug('Loading Badgr password from local filesystem')
badgr_utils = BadgrUtils(BADGR_URL, BADGR_USER, badgr_token, BADGR_ISSUER)


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


async def _get_tooling_for_assessment(optional_tools=[]):
    """Returns per-criterion tooling metadata filtered for assessment.

    :param optional_tools: Optional tools that shall be accounted
    :type optional_tools: list
    """
    levels_for_assessment = ['REQUIRED', 'RECOMMENDED']

    tooling_metadata_json = await _get_tooling_metadata()
    criteria_data_list = await _sort_tooling_by_criteria(tooling_metadata_json)
    criteria_data_list_filtered = []
    for criterion_data in criteria_data_list:
        criterion_data_copy = copy.deepcopy(criterion_data)
        toolset_for_reporting = []
        for tool in criterion_data['tools']:
            account_tool = False
            # NOTE!! Filtered based on the availability of the <reporting:requirement_level> property
            try:
                level = tool['reporting']['requirement_level']
                if level in levels_for_assessment:
                    account_tool = True
                    logger.debug('Accounting for assessment the REQUIRED/RECOMMENDED tool: %s' % tool)
                else:
                    if tool in optional_tools:
                        account_tool = True
                        logger.debug('Accounting the requested OPTIONAL tool <%s>' % tool)
            except KeyError:
                logger.debug('Could not get reporting data from tooling for tool <%s>' % tool)
            if account_tool:
                toolset_for_reporting.append(tool)
        criterion_id = criterion_data['id']
        if not toolset_for_reporting:
            logger.debug('No tool defined for assessment (missing <reporting> property) in <%s> criterion' % criterion_id)
        else:
            logger.debug('Found %s tool/s for assessment of criterion <%s>: %s' % (
                len(toolset_for_reporting), criterion_id, [tool['name'] for tool in toolset_for_reporting]))
            criterion_data_copy['tools'] = toolset_for_reporting
            criteria_data_list_filtered.append(criterion_data_copy)

    if not criteria_data_list_filtered:
        _reason = 'Could not find any tool for criteria assessment'
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    return criteria_data_list_filtered


async def add_pipeline_for_assessment(request: web.Request, body, optional_tools=[]) -> web.Response:
    """Creates a pipeline for assessment (QAA module).

    Creates a pipeline for assessment (QAA module).

    :param body: JSON payload request.
    :type body: dict | bytes
    :param optional_tools: Optional tools that shall be accounted
    :type optional_tools: list

    """
    repo_code = body['repo_code']
    repo_docs = body.get('repo_docs', {})

    #0 Filter per-criterion tools that will take part in the assessment
    try:
        criteria_data_list = await _get_tooling_for_assessment(optional_tools=optional_tools)
        logger.debug('Gathered tooling data enabled for assessment: %s' % criteria_data_list)
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    #1 Load request payload (same as passed to POST /pipeline) from templates
    env = Environment(
        loader=PackageLoader('openapi_server', 'templates')
    )
    template = env.get_template('pipeline_assessment.json')
    pipeline_name = '.'.join([
        os.path.basename(repo_code['repo']),
        'assess'
    ])
    logger.debug('Generated pipeline name for the assessment: %s' % pipeline_name)
    json_rendered = template.render(
        pipeline_name=pipeline_name,
        repo_code=repo_code,
        repo_docs=repo_docs,
        criteria_data_list=criteria_data_list
    )
    json_data = json.loads(json_rendered)
    logger.debug('Generated JSON payload (from template) required to create the pipeline for the assessment: %s' % json_data)

    #2 Create pipeline
    pipeline_id = await _add_pipeline_to_db(json_data, report_to_stdout=True)

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


@ctls_utils.debug_request
@ctls_utils.validate_request
async def run_pipeline(request: web.Request, pipeline_id, issue_badge=False, repo_url=None, repo_branch=None) -> web.Response:
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

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_repo = pipeline_data['pipeline_repo']
    pipeline_repo_url = pipeline_data['pipeline_repo_url']
    pipeline_repo_branch = 'sqaaas'

    config_data_list = pipeline_data['data']['config']
    composer_data = pipeline_data['data']['composer']
    jenkinsfile = pipeline_data['data']['jenkinsfile']

    if repo_url:
        if not ctls_utils.has_this_repo(config_data_list):
            _reason = 'No criteria has been associated with the repository where the pipeline is meant to be added (aka \'this_repo\')'
            logger.error(_reason)
            return web.Response(status=422, reason=_reason, text=_reason)
        _branch_msg = '(default branch)'
        if repo_branch:
            pipeline_repo_branch = repo_branch
            _branch_msg = '(branch: %s)' % repo_branch
        logger.info('Remote repository URL provided, cloning repository in %s organization: <%s> %s' % (GITHUB_ORG, repo_url, _branch_msg))
        logger.debug('Creating pipeline repository in %s organization: %s' % (GITHUB_ORG, pipeline_repo_url))
        gh_utils.create_org_repository(pipeline_repo)
        logger.debug('Cloning locally the source repository <%s> & Pushing to target repository: %s' % (repo_url, pipeline_repo_url))
        _repo_url = ctls_utils.format_git_url(repo_url)
        logger.debug('Formatting source repository URL to avoid git askpass when repo does not exist: %s' % _repo_url)
        try:
            pipeline_repo_branch = git_utils.clone_and_push(
                _repo_url, pipeline_repo_url, source_repo_branch=repo_branch)[-1]
        except SQAaaSAPIException as e:
            logger.error(e.message)
            _reason = 'Could not access to repository: %s (branch: %s)' % (_repo_url, repo_branch)
            return web.Response(status=e.http_code, reason=_reason, text=_reason)
        else:
            logger.info(('Pipeline repository updated with the content from source: %s (branch: %s)' % (pipeline_repo, pipeline_repo_branch)))
    else:
        repo_data = gh_utils.get_repository(pipeline_repo)
        if not repo_data:
            repo_data = gh_utils.create_org_repository(pipeline_repo)
        pipeline_repo_branch = repo_data.default_branch
    logger.info('Using pipeline repository: %s (branch: %s)' % (
        pipeline_repo, pipeline_repo_branch))

    commit_id = JePLUtils.push_files(
        gh_utils,
        pipeline_repo,
        config_data_list,
        composer_data,
        jenkinsfile,
        pipeline_data['data']['commands_scripts'],
        branch=pipeline_repo_branch
    )
    commit_url = gh_utils.get_commit_url(pipeline_repo, commit_id)

    _pipeline_repo_name = pipeline_repo.split('/')[-1]
    jk_job_name = '/'.join([
        JENKINS_GITHUB_ORG,
        _pipeline_repo_name,
        jk_utils.format_job_name(pipeline_repo_branch)
    ])

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
            logger.info('Build status for pipeline <%s>: %s' % (pipeline_repo, build_status))
            reason = 'Triggered the existing Jenkins job'
        else:
            _reason = 'Could not trigger build job'
            logger.error(_reason)
            raise SQAaaSAPIException(_reason)
    else:
        jk_utils.scan_organization()
        scan_org_wait = True
        build_status = 'WAITING_SCAN_ORG'
        reason = 'Triggered scan organization for building the Jenkins job'

    if issue_badge:
        logger.debug('Badge issuing (<issue_badge> flag) is requested for the current build: %s' % commit_id)

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


async def _run_validation(tool, stdout):
    """Validates the stdout using the sqaaas-reporting tool.

    Returns a (<tooling data>, <validation data>) tuple.

    :param tool: Tool name
    :type tool: str
    :param stdout: Tool output
    :type stdout: str

    """
    tooling_metadata_json = await _get_tooling_metadata()

    def _get_tool_reporting_data(tool):
        for tool_type, tools in tooling_metadata_json['tools'].items():
            if tool in tools.keys():
                data = tools[tool]['reporting']
                logger.debug('Found reporting data in tooling for tool <%s>' % tool)
                return data

    try:
        # Obtain the report2sqaas input args (aka <opts>) from tooling
        reporting_data = _get_tool_reporting_data(tool)
    except KeyError as e:
        _reason = 'Cannot get reporting data for tool <%s>: %s' % (tool, e)
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    # Add output text as the report2sqaaas <stdout> input arg
    validator_opts = copy.deepcopy(reporting_data)
    validator_opts['stdout'] = stdout

    allowed_validators = r2s_utils.get_validators()
    validator_name = reporting_data['validator']
    if validator_name not in allowed_validators:
        _reason = 'Could not find report2sqaaas validator plugin <%s> (found: %s)' % (validator_name, allowed_validators)
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)
    validator = r2s_utils.get_validator(validator_opts)
    return (reporting_data, validator.driver.validate())


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
    for tool_name, tool_cmd_list in tool_criterion_map.items():
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
        reporting_data, out = await _run_validation(matched_tool, criterion_stage_data['stdout_text'])
        logger.debug('Output returned by <%s> tool validator: %s' % (matched_tool, out))
        criterion_stage_data.update(reporting_data)
        criterion_stage_data['validation'] = out

        # Append if criterion is already there
        if criterion_name in list(output_data):
            output_data[criterion_name].append(criterion_stage_data)
        else:
            output_data[criterion_name] = [criterion_stage_data]

    return output_data


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
        output_data = await _validate_output(stage_data_list, pipeline_data)

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

    def _format_report():
        report_data = {}
        for criterion_name, criterion_output_data_list in output_data.items():
            criterion_valid = True
            report_data[criterion_name] = {}
            level_data = {}
            for criterion_output_data in criterion_output_data_list:
                level = criterion_output_data['requirement_level']
                tool = criterion_output_data['tool']
                validation_data = criterion_output_data['validation']
                valid = validation_data.pop('valid')
                # Check validity of the criterion output
                if level in ['REQUIRED'] and valid == False:
                    criterion_valid = False
                # Compose criterion stage data
                tool_data = {'name': tool}
                tool_data.update(validation_data)
                if level in list(level_data):
                    level_data[level].append(tool_data)
                else:
                    level_data[level] = [tool_data]
            report_data[criterion_name]['valid'] = criterion_valid
            report_data[criterion_name]['data'] = level_data
        return report_data

    def _get_criteria_per_badge_type(report_data):
        # Criteria prefixes
        SW_PREFIX = 'QC.'
        SRV_PREFIX = 'SvcQC'
        FAIR_PREFIX = 'QC.Fair'

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
    report_data = _format_report()
    if not report_data:
        _reason = 'Could not gather reporting data. Exiting..'
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)

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
        except KeyError:
            _reason = 'Could not retrieve Jenkins job information: Pipeline has not ran yet'
            logger.error(_reason)
            return web.Response(status=422, reason=_reason, text=_reason)
        # Get Badgr's badgeclass and proceed with badge issuance
        for badge_type, criteria_fulfilled_list in criteria_fulfilled_map.items():
            badgeclass_name = await _badgeclass_matchmaking(
                pipeline_id, badge_type, criteria_fulfilled_list
            )
            if badgeclass_name:
                try:
                    if not badge_type in list(badge_data):
                        badge_data[badge_type] = {}
                    badge_data[badge_type] = await _issue_badge(
                        pipeline_id,
                        badgeclass_name,
                    )
                except SQAaaSAPIException as e:
                    return web.Response(status=e.http_code, reason=e.message, text=e.message)
        # Store badge data in DB
        db.add_badge_data(pipeline_id, badge_data)
        # Generate share
        share_data = _get_badge_share(badge_data, build_info['commit_url'])

    r = {
        'report': report_data,
        'badge': {
            'data': badge_data,
            'share': share_data
        }
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
    JePLUtils.push_files(
        gh_utils,
        source_repo.full_name,
        config_data_list,
        composer_data,
        jenkinsfile,
        pipeline_data['data']['commands_scripts'],
        branch=source_branch_name)
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
        commands_scripts = [(
            (data['file_name'], data['content'])
                for data in commands_scripts
        )]

    binary_stream = io.BytesIO()
    with ZipFile(binary_stream, 'w') as zfile:
        for t in config_yml_list + composer_yml + jenkinsfile + commands_scripts:
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
    for badge_category in ['bronze', 'silver', 'gold']:
        logger.debug('Matching given criteria against defined %s criteria for %s' % (
            badge_category.upper(), badge_type.upper())
        )

        # Get badge type's config values
        badge_section = ':'.join([badge_type, badge_category])
        badgeclass_name = config.get_badge_sub(
            badge_section, 'badgeclass'
        )
        criteria_to_fulfill_list = config.get_badge_sub(
            ':'.join([badge_type, badge_category]), 'criteria'
        ).split()
        # Matchmaking
        missing_criteria = set(criteria_to_fulfill_list).difference(criteria_fulfilled_list)
        if missing_criteria:
            logger.warn('Pipeline <%s> not fulfilling %s criteria. Missing criteria: %s' % (
                pipeline_id, badge_category.upper(), missing_criteria)
            )
            break
        else:
            logger.info('Pipeline <%s> fulfills %s badge criteria!' % (
                pipeline_id, badge_category.upper())
            )
            badge_awarded_badgeclass_name = badgeclass_name

    if badge_awarded_badgeclass_name:
        logger.debug('Badgeclass to use for badge issuance: %s' % badge_awarded_badgeclass_name)

    return badge_awarded_badgeclass_name


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
        'badgr_badgeclass': badge_data['badgeClass'],
        'award_month': calendar.month_name[dt.month],
        'award_day': dt.day,
        'award_year': dt.year,
    })


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_badge(request: web.Request, pipeline_id, share=None) -> web.Response:
    """Gets badge data associated with the given pipeline

    Returns the badge data associated with the pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param share: Returns the badge in the specific format
    :type share: str

    """
    pipeline_data = db.get_entry(pipeline_id)

    try:
        build_info = pipeline_data['jenkins']['build_info']
        commit_url = build_info['commit_url']
        badge_data = build_info['badge']
        if not badge_data:
            raise KeyError
    except KeyError:
        _reason = 'Badge not issued for pipeline <%s>' % pipeline_id
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)

    logger.info('Badge <%s> found' % badge_data['openBadgeId'])

    if share == 'html':
        html_rendered = _get_badge_html(badge_data, commit_url)

        return web.Response(
            text=html_rendered,
            content_type='text/html',
            status=200
        )

    return web.json_response(badge_data, status=200)


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

    logger.debug('Getting supported tools from <%s> repo (metadata file: %s)' % (
        tooling_repo_url, tooling_metadata_file))
    platform = ctls_utils.supported_git_platform(
        tooling_repo_url, platforms=SUPPORTED_PLATFORMS)
    tooling_metadata_json = {}
    if platform in ['github']:
        short_repo_name = ctls_utils.get_short_repo_name(tooling_repo_url)
        tooling_metadata_content = gh_utils.get_file(
            tooling_metadata_file, short_repo_name, branch=tooling_repo_branch)
        tooling_metadata_encoded = tooling_metadata_content.content
        tooling_metadata_decoded = base64.b64decode(tooling_metadata_encoded).decode('UTF-8')
        tooling_metadata_json = json.loads(tooling_metadata_decoded)
    else:
        raise NotImplementedError(('Getting tooling metadata from a non-Github '
                                   'repo is not currently supported'))

    return tooling_metadata_json


async def _get_criterion_tooling(criterion_id, tooling_metadata_json):
    """Gets the criterion information as it is returned within the /criteria response.

    :param criterion_id: ID of the criterion
    :type criterion_id: str
    :param tooling_metadata_json: JSON with the metadata
    :type tooling_metadata_json: dict
    """
    try:
        criterion_data = tooling_metadata_json['criteria'][criterion_id]['tools']
    except Exception as e:
        _reason = 'Cannot find tooling information for criterion <%s> in metadata: %s' % (
            criterion_id, tooling_metadata_json)
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)

    # Add default tools
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
            tooling_data = await _get_criterion_tooling(
                criterion, tooling_metadata_json)
            criteria_data_list.append({
                'id': criterion,
                'description': tooling_metadata_json['criteria'][criterion]['description'],
                'tools': tooling_data
            })
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    return criteria_data_list


async def get_criteria(request: web.Request, criterion_id=None) -> web.Response:
    """Returns data about criteria.

    :param criterion_id: Get data from a specific criterion
    :type criterion_id: str

    """
    tooling_metadata_json = await _get_tooling_metadata()

    criteria_id_list = []
    if criterion_id:
        criteria_id_list = [criterion_id]
    criteria_data_list = await _sort_tooling_by_criteria(
        tooling_metadata_json, criteria_id_list=criteria_id_list)

    return web.json_response(criteria_data_list, status=200)
