import json
import logging
import os
import uuid
import time

from typing import List, Dict
from aiohttp import web

from openapi_server.models.pipeline import Pipeline
from openapi_server import util
from openapi_server.controllers.github import GitHubUtils
from openapi_server.controllers.jepl import JePLUtils
from openapi_server.controllers.jenkins import JenkinsUtils


DB_FILE = 'sqaaas.json'
JENKINS_URL = 'https://jenkins.eosc-synergy.eu/'
JENKINS_USER = 'orviz'
JENKINS_GITHUB_ORG = 'eosc-synergy-org'

logger = logging.getLogger('sqaaas_api.controller')


with open('.gh_token','r') as f:
    token = f.read().strip()
logger.debug('Loading GitHub token from local filesystem')
gh_utils = GitHubUtils(token)

with open('.jk_token','r') as f:
    jk_token = f.read().strip()
logger.debug('Loading Jenkins token from local filesystem')
jk_utils = JenkinsUtils(JENKINS_URL, JENKINS_USER, jk_token)


def load_db_content():
    data = {}
    if os.path.exists(DB_FILE) and os.stat(DB_FILE).st_size > 0:
        with open(DB_FILE) as db:
            data = json.load(db)
    return data


def store_db_content(data):
    with open(DB_FILE, 'w') as db:
        json.dump(data, db)
    print_db_content()


def print_db_content():
    data = load_db_content()
    print('### Pipeline DB ##')
    for k in data.keys():
        print(k, data[k])
    print('##################')


async def add_pipeline(request: web.Request, body) -> web.Response:
    """Creates a pipeline.

    Provides a ready-to-use Jenkins pipeline based on the v2 series of jenkins-pipeline-library.

    :param body:
    :type body: dict | bytes

    """
    pipeline_id = str(uuid.uuid4())
    # body = Pipeline.from_dict(body)

    # FIXME For the time being, we just support one config.yml
    config_json = body['config_data'][0]
    composer_json = body['composer_data']
    jenkinsfile_data = body['jenkinsfile_data']

    # FIXME sqaaas_repo must be provided by the user
    sqaaas_repo = list(config_json['config']['project_repos'])[0] + '.sqaaas'
    logger.debug('Using GitHub repository name: %s' % sqaaas_repo)

    db = load_db_content()
    db[pipeline_id] = {
        'sqaaas_repo': sqaaas_repo,
        'data': {
            'config_data': config_json,
            'composer_data': composer_json,
            'jenkinsfile': jenkinsfile_data
        }
    }
    store_db_content(db)
    
    r = {'id': pipeline_id}
    return web.json_response(r, status=200)


async def delete_pipeline_by_id(request: web.Request, pipeline_id) -> web.Response:
    """Delete pipeline by ID

    

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_pipelines(request: web.Request) -> web.Response:
    """Gets pipeline IDs.

    Returns the list of IDs for the defined pipelines.

    """
    db = load_db_content()
    return web.json_response(db, status=200)


async def get_pipeline_by_id(request: web.Request, pipeline_id) -> web.Response:
    """Find pipeline by ID



    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_pipeline_composer(request: web.Request, pipeline_id) -> web.Response:
    """Gets composer configuration used by the pipeline.

    Returns the content of JePL&#39;s docker-compose.yml file. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_pipeline_config(request: web.Request, pipeline_id) -> web.Response:
    """Gets pipeline&#39;s main configuration.

    Returns the content of JePL&#39;s config.yml file. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_pipeline_jenkinsfile(request: web.Request, pipeline_id) -> web.Response:
    """Gets Jenkins pipeline definition used by the pipeline.

    Returns the content of JePL&#39;s Jenkinsfile file. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_pipeline_status(request: web.Request, pipeline_id) -> web.Response:
    """Get pipeline status.

    Obtains the build URL in Jenkins for the given pipeline. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def run_pipeline(request: web.Request, pipeline_id) -> web.Response:
    """Runs pipeline.

    Executes the given pipeline by means of the Jenkins API. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    db = load_db_content()
    pipeline_name = db[pipeline_id]['sqaaas_repo']
    pipeline_data = db[pipeline_id]['data']
    logger.debug('Loading pipeline <%s> from DB' % pipeline_id)

    sqaaas_repo = pipeline_name
    config_yml, composer_yml = JePLUtils.get_sqa_files(
        pipeline_data['config_data'],
        pipeline_data['composer_data'])
    jenkinsfile = JePLUtils.get_jenkinsfile(pipeline_data['jenkinsfile'])

    repo_data = gh_utils.get_org_repository(sqaaas_repo)
    if repo_data:
        logger.warning('Repository <%s> already exists!' % repo_data.raw_data['full_name'])
    else:
        gh_utils.create_org_repository(sqaaas_repo)
        gh_utils.push_file('.sqa/config.yml', config_yml, 'Update config.yml', sqaaas_repo)
        logger.debug('Pushing file to GitHub repository <%s>: .sqa/config.yml' % sqaaas_repo)
        gh_utils.push_file('.sqa/docker-compose.yml', composer_yml, 'Update docker-compose.yml', sqaaas_repo)
        logger.debug('Pushing file to GitHub repository <%s>: .sqa/docker-compose.yml' % sqaaas_repo)
        gh_utils.push_file('Jenkinsfile', jenkinsfile, 'Update Jenkinsfile', sqaaas_repo)
        logger.debug('Pushing file to GitHub repository <%s>: Jenkinsfile' % sqaaas_repo)
        logger.info('GitHub repository <%s> created with the JePL file structure' % sqaaas_repo)
        repo_data = gh_utils.get_org_repository(sqaaas_repo)

    full_job_name = '/'.join([
        JENKINS_GITHUB_ORG,
        sqaaas_repo,
        repo_data.raw_data['default_branch']
    ])
    db[pipeline_id]['job_name'] = full_job_name

    build_url = None
    if jk_utils.get_job_url(sqaaas_repo):
        logger.warning('Jenkins job <%s> already exists!' % full_job_name)
        build_url = jk_utils.build_job(full_job_name)
    else:
        jk_utils.scan_organization()
        while not build_url:
            build_url = jk_utils.get_job_url(sqaaas_repo)
            logger.debug('Waiting for scan organization process to finish..')
            time.sleep(30)
        logger.debug('Scan organization finished')
    build_no = build_url['number']
    build_url = build_url['url']
    logger.info('Jenkins job build URL obtained for repository <%s>: %s' % (sqaaas_repo, build_url))

    db[pipeline_id]['build'] = {
        'number': build_no,
        'url': build_url
    }
    store_db_content(db)

    r = {'build_url': build_url}
    return web.json_response(r, status=200)


async def create_pull_request(request: web.Request, pipeline_id) -> web.Response:
    """Creates pull request with JePL files.

    Create a pull request with the generated JePL files. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


async def get_compressed_files(request: web.Request, pipeline_id) -> web.Response:
    """Get JePL files in compressed format.

    Obtains the generated JePL files in compressed format. 

    :param pipeline_id: ID of the pipeline to get
    :type pipeline_id: str

    """
    return web.Response(status=200)


