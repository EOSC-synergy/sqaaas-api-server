import copy
import functools
import itertools
import logging
import os
import re
import uuid
import yaml

from aiohttp import web
from urllib.parse import urlparse
from urllib.parse import ParseResult

from openapi_server import config
from openapi_server.controllers import db
from openapi_server.controllers.jepl import JePLUtils

from github.GithubException import GithubException
from github.GithubException import UnknownObjectException
from jenkins import JenkinsException


logger = logging.getLogger('sqaaas_api.controller')


def upstream_502_response(r):
    _reason = 'Unsuccessful request to upstream service API'
    logger.error(_reason)
    return web.json_response(
        r,
        status=502,
        reason=_reason,
        text=_reason
    )


def debug_request(f):
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        logger.debug('Received request (keyword args): %s' % kwargs)
        ret = await f(*args, **kwargs)
        return ret
    return decorated_function


def extended_data_validation(f):
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        body = kwargs['body']
        config_data_list = body['config_data']
        composer_data = body['composer_data']
        # Validate pipeline name
        if re.search(r'[^-.\w]', body['name']):
            _reason = 'Invalid pipeline name (allowed characters: [A-Za-z0-9_.-])'
            logger.warning(_reason)
            return web.Response(status=400, reason=_reason, text=_reason)
        # Docker push feature
        for srv_name, srv_data in composer_data['services'].items():
            try:
                registry_data = srv_data['image']['registry']
            except KeyError as e:
                logger.debug('No registry data found for service <%s>' % srv_name)
            else:
                if registry_data['push']:
                    try:
                        if not (registry_data['credential_id'] or
                                config.get_ci('docker_credential_id')):
                            raise KeyError
                    except KeyError:
                        _reason = ('Request to push Docker images, but no credentials '
                                   'provided and/or fallback credentials found in API '
                                   'configuration')
                        logger.warning(_reason)
                        return web.Response(status=400, reason=_reason, text=_reason)
                    try:
                        if not srv_data['image']['name']:
                            raise KeyError
                    except KeyError:
                        _reason = 'Request to push Docker images, but no image name provided!'
                        logger.warning(_reason)
                        return web.Response(status=400, reason=_reason, text=_reason)
                    try:
                        if not srv_data['build']:
                            raise KeyError
                        else:
                            has_context = 'context' in srv_data['build'].keys() and srv_data['build']['context']
                            has_dockerfile = 'dockerfile' in srv_data['build'].keys() and srv_data['build']['dockerfile']
                            if not (has_context or has_dockerfile):
                                raise KeyError
                    except KeyError:
                        _reason = 'Request to push Docker images, but no build data provided!'
                        logger.warning(_reason)
                        return web.Response(status=400, reason=_reason, text=_reason)
        ret = await f(*args, **kwargs)
        return ret
    return decorated_function


def validate_request(f):
    @functools.wraps(f)
    async def decorated_function(*args, **kwargs):
        _pipeline_id = kwargs['pipeline_id']
        try:
            uuid.UUID(_pipeline_id, version=4)
            _db = db.load_content()
            if _pipeline_id in list(_db):
                logger.debug('Pipeline <%s> found in DB' % _pipeline_id)
            else:
                _reason = 'Pipeline not found!: %s' % _pipeline_id
                logger.warning(_reason)
                return web.Response(status=404, reason=_reason, text=_reason)
        except ValueError:
            _reason = 'Invalid pipeline ID supplied!: %s' % _pipeline_id
            logger.warning(_reason)
            return web.Response(status=400, reason=_reason, text=_reason)

        try:
            logger.debug('Running decorated method <%s>' % f.__name__)
            ret = await f(*args, **kwargs)
        except UnknownObjectException as e:
            _status = e.status
            _reason = e.data['message']
            logger.error('(GitHub) %s (exit code: %s)' % (_reason, _status))
            r = {'upstream_status': _status, 'upstream_reason': _reason}
            return upstream_502_response(r)
        except GithubException as e:
            _status = e.status
            if 'errors' in list(e.data):
                _reason = e.data['errors'][0]['message']
            else:
                _reason = e.data['message']
            logger.error('(GitHub) %s (exit code: %s)' % (_reason, _status))
            r = {'upstream_status': _status, 'upstream_reason': _reason}
            return upstream_502_response(r)
        except JenkinsException as e:
            msg_first_line = str(e).splitlines()[0]
            logger.error('(Jenkins) %s' % msg_first_line)
            _reason = msg_first_line
            _status = 404
            _status_regexp = re.search('.+\[(40\d{1})\].+', _reason)
            if _status_regexp:
                _status = int(_status_regexp.groups()[0])
            r = {'upstream_status': _status, 'upstream_reason': _reason}
            return upstream_502_response(r)
        return ret
    return decorated_function


def json_to_yaml(json_data):
    """Returns the YAML translation of the incoming JSON payload.

    :param json_data: JSON payload.
    """
    return yaml.dump(json_data)


def get_pipeline_data(request_body):
    """Get pipeline data.

    Obtains the pipeline data from the API request.
    """
    # NOTE For the time being, we just support one config.yml
    config_json = request_body['config_data'][0]
    composer_json = request_body['composer_data']
    jenkinsfile_data = request_body['jenkinsfile_data']

    return (config_json, composer_json, jenkinsfile_data)


class ProcessExtraData(object):
    """Utils class for the extra data processing."""
    @staticmethod
    def set_build_context(service_name, repo_name, composer_json):
        """Set the context within the docker-compose.yml's build property.

        :param service_name: Name of the DC service
        :param repo_name: Relative repo checkout path
        :param composer_json: Composer data (JSON)
        """
        logger.debug('Call to ProcessExtraData.set_build_context() method')
        if service_name:
            try:
                dockerfile_path = composer_json['services'][service_name]['build']['dockerfile']
                dockerfile_filename = os.path.basename(dockerfile_path)
                composer_json['services'][service_name]['build']['dockerfile'] = dockerfile_filename
                dockerfile_dirname = os.path.dirname(dockerfile_path)
                context_dir = dockerfile_dirname
                composer_json['services'][service_name]['build']['context'] = context_dir
                logger.debug('Build context set <%s> for service <%s>' % (
                    repo_name, service_name))
            except KeyError:
                logger.debug(('No build definition found for service <%s>. Not setting '
                              'build context' % service_name))

    @staticmethod
    def set_tox_env(repo_checkout_dir, repos_data):
        """Prepare the Tox environment for the given repo.

        Includes:
        - chdir to the checkout dir when not 'this_repo'
        - set defaults (tox.ini, run only envs from envlist)

        :param repo_checkout_dir: Relative repo checkout path
        :param repos_data: The individual repository data
        """
        logger.debug('Call to ProcessExtraData.set_tox_env() method')
        repo_key = repo_checkout_dir
        if repo_checkout_dir in ['.']:
            repo_key = 'this_repo'
        if not 'tox' in repos_data[repo_key].keys():
            logger.debug('Tox enviroment not found. Skipping environment setup.')
        else:
            # tox_file
            tox_file = repos_data[repo_key]['tox'].get('tox_file', None)
            if not tox_file:
                tox_file = 'tox.ini'
            repos_data[repo_key]['tox']['tox_file'] = os.path.join(
                repo_checkout_dir, tox_file)
            # testenv
            testenv = repos_data[repo_key]['tox'].get('testenv', [])
            if not testenv:
                testenv = ['ALL']
            logger.debug('Tox environment set (tox_file: %s, testenv: %s)' % (
                tox_file, testenv))
            repos_data[repo_key]['tox']['testenv'] = testenv


def process_extra_data(config_json, composer_json):
    """Manage those properties, present in the API spec, that cannot
    be directly translated into a workable 'config.yml' or composer
    (i.e. 'docker-compose.yml).

    This method returns:
    - 'config_json_list' is a JSON List of Dicts {'data_json': <data>,
                                                    'data_when': <data>}
    - 'composer_json' is a JSON Dict
    - 'commands_script_list' is a list of strings to generate the command builder scripts

    :param config_json: JePL's config as received through the API request (JSON payload)
    :param composer_json: Composer content as received throught the API request (JSON payload).
    """
    # COMPOSER (Docker Compose specific)
    for srv_name, srv_data in composer_json['services'].items():
        use_default_dockerhub_org = False
        ## Set JPL_DOCKER* envvars
        if 'registry' in srv_data['image'].keys():
            registry_data = srv_data['image'].pop('registry')
            if not 'environment' in config_json.keys():
                config_json['environment'] = {}
            # JPL_DOCKERPUSH
            if registry_data['push']:
                srv_push = config_json['environment'].get('JPL_DOCKERPUSH', '')
                srv_push += ' %s' % srv_name
                srv_push = srv_push.strip()
                config_json['environment']['JPL_DOCKERPUSH'] = srv_push
                credential_id = None
                if registry_data.get('credential_id', None):
                    credential_id = registry_data['credential_id']
                else:
                    credential_id = config.get_ci(
                        'docker_credential_id', fallback=None)
                    use_default_dockerhub_org = True
                try:
                    config_json['config']['credentials']
                except KeyError:
                    config_json['config']['credentials'] = []
                finally:
                    config_json['config']['credentials'].append({
                        'id': credential_id,
                        'username_var': 'JPL_DOCKERUSER',
                        'password_var': 'JPL_DOCKERPASS'
                    })
            # JPL_DOCKERSERVER: current JePL 2.1.0 does not support 1-to-1 in image-to-registry
            # so defaulting to the last match
            if registry_data['url']:
                config_json['environment']['JPL_DOCKERSERVER'] = registry_data['url']
        ## Set 'image' property as string (required by Docker Compose)
        srv_data['image'] = srv_data['image']['name']
        if use_default_dockerhub_org:
            org = config.get_ci(
                'docker_credential_org', fallback=None)
            img_name = srv_data['image'].split('/')[-1]
            srv_data['image'] = '/'.join([org, img_name])
        ## Set 'volumes' property (incl. default values)
        try:
            srv_data['volumes']
        except KeyError:
            pass
        else:
            srv_data['volumes'] = [{
                'type': 'bind',
                'source': './',
                'target': '/sqaaas-build'
            }]
        ## Set 'working_dir' property (for simple use cases)
        ## NOTE Setting working_dir only makes sense when only one volume is expected!
        srv_data['working_dir'] = srv_data['volumes'][0]['target']
        ## Check for empty values
        props_to_remove = []
        for prop, prop_value in srv_data.items():
            pop_prop = False
            if isinstance(prop_value, dict):
                if not any(prop_value.values()):
                    pop_prop = True
            elif isinstance(prop_value, (list, str)):
                if not prop_value:
                    pop_prop = True
            if pop_prop:
                props_to_remove.append(prop)
        [srv_data.pop(prop) for prop in props_to_remove]
        ## Handle 'oneshot' services
        oneshot = True
        if 'oneshot' in srv_data.keys():
            oneshot = srv_data.pop('oneshot')
        if oneshot:
            srv_data['command'] = 'sleep 6000000'
        ## Set default build:context to '.'
        if 'build' in list(srv_data):
            ProcessExtraData.set_build_context(srv_name, '.', composer_json)

    composer_data = {'data_json': composer_json}

    # CONFIG:CONFIG (Set repo name)
    project_repos_final = {}
    project_repos_mapping = {}
    if 'project_repos' in config_json['config'].keys():
        for project_repo in config_json['config']['project_repos']:
            repo_url = project_repo.pop('repo')
            repo_url_parsed = urlparse(repo_url)
            repo_name_generated = ''.join([
                repo_url_parsed.netloc,
                repo_url_parsed.path,
            ])
            project_repos_final[repo_name_generated] = {
                'repo': repo_url,
                **project_repo
            }
            project_repos_mapping[repo_url] = {
                'name': repo_name_generated,
                **project_repo
            }
        config_json['config']['project_repos'] = project_repos_final

    # CONFIG:SQA_CRITERIA
    # - Multiple stages/Jenkins when clause
    # - Array-to-Object conversion for repos
    # - Set 'context' to the appropriate checkout path for building the Dockerfile
    config_data_list = []
    commands_script_list = []
    config_json_no_when = copy.deepcopy(config_json)
    for criterion_name, criterion_data in config_json['sqa_criteria'].items():
        criterion_data_copy = copy.deepcopy(criterion_data)
        if 'repos' in criterion_data.keys():
            repos_old = criterion_data_copy.pop('repos')
            repos_new = {}
            for repo in repos_old:
                service_name = repo.get('container', None)
                try:
                    repo_url = repo.pop('repo_url')
                    if not repo_url:
                        raise KeyError
                except KeyError:
                    # Use 'this_repo' as the placeholder for current repo & version
                    repos_new['this_repo'] = repo
                    # Modify Tox properties (chdir, defaults)
                    ProcessExtraData.set_tox_env('.', repos_new)
                    # Set Dockerfile's 'context' in the composer
                    ProcessExtraData.set_build_context(service_name, '.', composer_json)
                else:
                    repo_name = project_repos_mapping[repo_url]['name']
                    repos_new[repo_name] = repo
                    # Create script for 'commands' builder
                    # NOTE: This is a workaround -> a specific builder to tackle this will be implemented in JePL
                    if 'commands' in repo.keys():
                        commands_script_data = JePLUtils.get_commands_script(
                            repo_name,
                            repo['commands']
                        )
                        commands_script_data = JePLUtils.append_file_name(
                            'commands_script',
                            [{
                                'content': commands_script_data
                            }],
                            force_random_name=True
                        )
                        commands_script_list.extend(commands_script_data)
                        script_call = '/usr/bin/env sh %s' % commands_script_data[0]['file_name']
                        repos_new[repo_name]['commands'] = [script_call]
                    # Modify Tox properties (chdir, defaults)
                    ProcessExtraData.set_tox_env(repo_name, repos_new)
                    # Set Dockerfile's 'context' in the composer
                    ProcessExtraData.set_build_context(service_name, repo_name, composer_json)
            criterion_data_copy['repos'] = repos_new
        if 'when' in criterion_data.keys():
            config_json_when = copy.deepcopy(config_json)
            config_json_when['sqa_criteria'] = {
                criterion_name: criterion_data_copy
            }
            when_data = criterion_data_copy.pop('when')
            config_data_list.append({
		'data_json': config_json_when,
                'data_when': when_data
	    })
            config_json_no_when['sqa_criteria'].pop(criterion_name)
        else:
            config_json_no_when['sqa_criteria'][criterion_name] = criterion_data_copy

    if config_json_no_when['sqa_criteria']:
        config_data_list.append({
            'data_json': config_json_no_when,
            'data_when': None
        })

    return (config_data_list, composer_data, commands_script_list)


def has_this_repo(config_data_list):
    """Checks if a 'this_repo' has been defined in the existing criteria.

    :param config_data_list: List of config.yml data files
    """
    this_repo = False
    for config_data in config_data_list:
        sqa_criteria_data = config_data['data_json']['sqa_criteria']
        for criterion_name, criterion_data in sqa_criteria_data.items():
            if 'this_repo' in criterion_data['repos']:
                this_repo = True
    return this_repo


def format_git_url(repo_url):
    """Formats git URL to avoid asking for password when repos do not exist.

    :param repo_url: URL of the git repository
    """
    repo_url_parsed = urlparse(repo_url)
    repo_url_final = ParseResult(
        scheme=repo_url_parsed.scheme,
        netloc=':@'+repo_url_parsed.netloc,
        path=repo_url_parsed.path,
        params=repo_url_parsed.params,
        query=repo_url_parsed.query,
        fragment=repo_url_parsed.fragment
    )
    return repo_url_final.geturl()


# NOTE (workaround) Back to the old criteria codes from JePL 2.1.0
# FIXME by removing when using JePL > 2.1.0
def rekey_criteria_codes(record):
    criteria_map = {
        'QC.Sty': 'qc_style',
        'QC.Uni': 'qc_coverage',
        'QC.Fun': 'qc_functional',
        'QC.Sec': 'qc_security',
        'QC.Doc': 'qc_doc',
    }
    if isinstance(record, str):
        for new, old in criteria_map.items():
            record = record.replace(new, old)
        return record
    elif isinstance(record, dict):
        return {
            criteria_map.get(new, new): old for new, old in record.items()
        }
