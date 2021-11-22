import base64
import calendar
from datetime import datetime
import io
import itertools
import logging
import json
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
BADGR_BADGECLASS = config.get_badge('badgeclass')

logger = logging.getLogger('sqaaas_api.controller')

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
badgr_utils = BadgrUtils(BADGR_URL, BADGR_USER, badgr_token, BADGR_ISSUER, BADGR_BADGECLASS)


@ctls_utils.debug_request
@ctls_utils.extended_data_validation
async def add_pipeline(request: web.Request, body, report_to_stdout=None) -> web.Response:
    """Creates a pipeline.

    Provides a ready-to-use Jenkins pipeline based on the v2 series of jenkins-pipeline-library.

    :param body:
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

    r = {'id': pipeline_id}
    return web.json_response(r, status=201)


@ctls_utils.debug_request
@ctls_utils.extended_data_validation
@ctls_utils.validate_request
async def update_pipeline_by_id(request: web.Request, pipeline_id, body) -> web.Response:
    """Update pipeline by ID

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param body:
    :type body: dict | bytes

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
            body
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
        build_item_no = jk_utils.build_job(jk_job_name)
        if build_item_no:
            build_status = 'QUEUED'
        logger.info('Build status for pipeline <%s>: %s' % (pipeline_repo, build_status))
        reason = 'Triggered the existing Jenkins job'
    else:
        jk_utils.scan_organization()
        scan_org_wait = True
        build_status = 'WAITING_SCAN_ORG'
        reason = 'Triggered scan organization for building the Jenkins job'

    if issue_badge:
        logger.debug('Badge issuing (<issue_badge> flag) is requested for the current build: %s' % commit_id)

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

    return web.Response(status=204, reason=reason, text=reason)


@ctls_utils.debug_request
@ctls_utils.validate_request
async def get_pipeline_status(request: web.Request, pipeline_id) -> web.Response:
    """Get pipeline status.

    Obtains the build URL in Jenkins for the given pipeline.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    pipeline_repo = pipeline_data['pipeline_repo']

    if 'jenkins' not in pipeline_data.keys():
        _reason = 'Could not retrieve Jenkins job information: Pipeline has not yet ran'
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)

    jenkins_info = pipeline_data['jenkins']
    build_info = jenkins_info['build_info']

    jk_job_name = jenkins_info['job_name']
    build_item_no = build_info['item_number']
    build_no = build_info['number']
    build_url = build_info['url']
    build_status = build_info.get('status', None)

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

    if not build_no:
        if build_item_no:
            build_data = jk_utils.get_queue_item(build_item_no)
            if build_data:
                build_no = build_data['number']
                build_url = build_data['url']
                build_status = 'EXECUTING'
                logger.info('Jenkins job build URL obtained for repository <%s>: %s' % (pipeline_repo, build_url))
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

    badge_data = jenkins_info['build_info']['badge']
    if jenkins_info['issue_badge']:
        logger.info('Issuing badge as requested when running the pipeline')
        try:
            badge_data = await _issue_badge(
                pipeline_id,
                pipeline_data['data']['config'],
                build_status,
                build_url,
                build_info['commit_id'],
                build_info['commit_url']
            )
            jenkins_info['issue_badge'] = False
        except SQAaaSAPIException as e:
            if e.http_code == 422:
                logger.warning(e.message)
            else:
                return web.Response(status=e.http_code, reason=e.message, text=e.message)

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
        issue_badge=jenkins_info['issue_badge'],
        badge_data=badge_data
    )

    r = {
        'build_url': build_url,
        'build_status': build_status,
        'openbadge_id': badge_data.get('openBadgeId', None)
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


async def _issue_badge(pipeline_id, config_data_list, build_status, build_url, commit_id, commit_url):
    """Issues a badge using BadgrUtils.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str
    :param config_data_list: List of config data Dicts
    :type config_data_list: list
    :param build_status:
    :type build_status: str
    :param build_url: Jenkins' job build URL.
    :type build_url: str
    :param commit_id: Commit ID assigned by git as a result of pushing the JePL files.
    :type commit_id: str
    :param commit_url: Commit URL of the git repository platform.
    :type commit_url: str

    """
    if not build_status in ['SUCCESS', 'UNSTABLE']:
        _reason = 'Cannot issue a badge for pipeline <%s>: build status is \'%s\'' % (pipeline_id, build_status)
        logger.error(_reason)
        raise SQAaaSAPIException(422, _reason)

    # Get 'sw_criteria' & 'srv_criteria'
    SW_CODE_PREFIX = 'QC.'
    SRV_CODE_PREFIX = 'SvcQC'
    logger.debug('Filtering Software criteria codes by <%s> prefix' % SW_CODE_PREFIX)
    logger.debug('Filtering Service criteria codes by <%s> prefix' % SRV_CODE_PREFIX)
    criteria = [
        config_data['data_json']['sqa_criteria'].keys()
            for config_data in config_data_list
    ]
    criteria = list(itertools.chain.from_iterable(criteria))
    sw_criteria = [
        criterion
            for criterion in criteria
                if criterion.startswith(SW_CODE_PREFIX)
    ]
    srv_criteria = [
        criterion
            for criterion in criteria
                if criterion.startswith(SRV_CODE_PREFIX)
    ]
    logger.debug('Obtained Software criteria: %s' % sw_criteria)
    logger.debug('Obtained Service criteria: %s' % srv_criteria)

    logger.info('Issuing badge for pipeline <%s>' % pipeline_id)
    try:
        badge_data = badgr_utils.issue_badge(
            commit_id=commit_id,
            commit_url=commit_url,
            ci_build_url=build_url,
            sw_criteria=sw_criteria,
            srv_criteria=srv_criteria
        )
    except Exception as e:
        _reason = 'Cannot issue a badge for pipeline <%s>: %s' % (pipeline_id, e)
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)
    else:
        logger.info('Badge successfully issued: %s' % badge_data['openBadgeId'])
        return badge_data


@ctls_utils.debug_request
@ctls_utils.validate_request
async def issue_badge(request: web.Request, pipeline_id) -> web.Response:
    """Issues a quality badge.

    Uses Badgr API to issue a badge after successful pipeline execution.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    pipeline_data = db.get_entry(pipeline_id)
    try:
        jenkins_info = pipeline_data['jenkins']
        build_info = jenkins_info['build_info']
    except KeyError:
        _reason = 'Could not retrieve Jenkins job information: Pipeline has not ran yet'
        logger.error(_reason)
        return web.Response(status=422, reason=_reason, text=_reason)
    try:
        badge_data = await _issue_badge(
            pipeline_id,
            pipeline_data['data']['config'],
            build_info['status'],
            build_info['url'],
            build_info['commit_id'],
            build_info['commit_url']
        )
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    # Add badge data to DB
    db.update_jenkins(
        pipeline_id,
        jenkins_info['job_name'],
        commit_id=jenkins_info['build_info']['commit_id'],
        commit_url=jenkins_info['build_info']['commit_url'],
        build_no=jenkins_info['build_info']['number'],
        build_url=jenkins_info['build_info']['url'],
        scan_org_wait=jenkins_info['scan_org_wait'],
        build_status=jenkins_info['build_info']['status'],
        issue_badge=False,
        badge_data=jenkins_info['build_info']['badge']
    )
    return web.json_response(badge_data, status=200)


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
            'badgr_badgeclass': BADGR_BADGECLASS,
            'award_month': calendar.month_name[dt.month],
            'award_day': dt.day,
            'award_year': dt.year,
        })

        return web.Response(
            text=html_rendered,
            content_type='text/html',
            status=200
        )

    return web.json_response(badge_data, status=200)


async def _get_criterion_tooling(criterion_id, metadata_json):
    """Sorts out the criterion information to be returned in the HTTP response.

    :param criterion_id: ID of the criterion
    :type criterion_id: str
    :param metadata_json: JSON with the metadata
    :type metadata_json: dict
    """
    try:
        criterion_data = metadata_json['criteria'][criterion_id]['tools']
    except Exception as e:
        _reason = 'Cannot find tooling information for criterion <%s> in metadata: %s' % (
            criterion_id, metadata_json)
        logger.error(_reason)
        raise SQAaaSAPIException(502, _reason)

    # Add default tools
    default_data = {"default": list(metadata_json["tools"]["default"])}
    criterion_data.update(default_data)

    criterion_data_list = []
    for lang, tools in criterion_data.items():
        for tool in tools:
            d = {}
            try:
                d['name'] = tool
                d['lang'] = lang
                d.update(metadata_json['tools'][lang][tool])
            except KeyError:
                logger.warn('Cannot find data for tool <%s> (lang: %s)' % (
                    tool, lang))
            if d:
                criterion_data_list.append(d)

    return criterion_data_list


async def get_criteria(request: web.Request, criterion_id=None) -> web.Response:
    """Returns data about criteria.

    :param criterion_id: Get data from a specific criterion
    :type criterion_id: str

    """
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

    r = []
    criteria_id_list = list(tooling_metadata_json['criteria'])
    if criterion_id:
        criteria_id_list = [criterion_id]
        logger.debug('Filtering by criterion <%s>' % criterion_id)
    try:
        for criterion in criteria_id_list:
            tooling_data = await _get_criterion_tooling(
                criterion, tooling_metadata_json)
            r.append({'id': criterion, 'tools': tooling_data})
    except SQAaaSAPIException as e:
        return web.Response(status=e.http_code, reason=e.message, text=e.message)

    return web.json_response(r, status=200)


async def get_pipeline_output(request: web.Request, pipeline_id) -> web.Response:
    """Get output from pipeline execution

    Returns the console output from the pipeline execution.

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)
