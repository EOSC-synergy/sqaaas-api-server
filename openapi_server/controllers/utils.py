import copy
import functools
import itertools
import logging
import namegenerator
from pathlib import Path
from pathlib import PurePath
import os
import re
import uuid
import yaml

from aiohttp import web
from urllib.parse import urlparse
from urllib.parse import ParseResult

from openapi_server import config
from openapi_server.controllers import db
from openapi_server.controllers.git import GitUtils
from openapi_server.controllers.jepl import JePLUtils

from github.GithubException import GithubException
from github.GithubException import UnknownObjectException
from jenkins import JenkinsException


logger = logging.getLogger('sqaaas.api.controller')

tooling_repo_url = config.get(
    'tooling_repo_url',
    fallback='https://github.com/EOSC-synergy/sqaaas-tooling'
)
tooling_repo_branch = config.get(
    'tooling_repo_branch',
    fallback='main'
)
docker_credential_id = config.get_ci(
    'docker_credential_id',
    fallback=None
)
docker_credential_org = config.get_ci(
    'docker_credential_org',
    fallback=None
)

tooling_repo_url = config.get(
    'tooling_repo_url',
    fallback='https://github.com/EOSC-synergy/sqaaas-tooling'
)
tooling_repo_branch = config.get(
    'tooling_repo_branch',
    fallback='main'
)
docker_credential_id = config.get_ci(
    'docker_credential_id',
    fallback=None
)
docker_credential_org = config.get_ci(
    'docker_credential_org',
    fallback=None
)


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
                                docker_credential_id):
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
        # Tooling
        for config_json in config_data_list:
            for criterion_name, criterion_data in config_json['sqa_criteria'].items():
                for repo in criterion_data['repos']:
                    try:
                        commands = repo.get('commands', [])
                        tool = repo.get('tool', {})
                        if not commands and not tool:
                            raise KeyError
                    except KeyError:
                        _reason = 'Builder <commands> might be empty only when <tool> has been provided'
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
    # NOTE!! For the time being, we just support one config.yml
    config_json = request_body['config_data'][0]
    composer_json = request_body['composer_data']
    jenkinsfile_data = request_body['jenkinsfile_data']

    return (config_json, composer_json, jenkinsfile_data)


class ProcessExtraData(object):
    """Utils class for the extra data processing."""
    @staticmethod
    def set_service_volume(service_data):
        """Set the default volume data.

        :param service_data: Data of the DC service
        """
        logger.debug('Call to ProcessExtraData.set_service_volume() method')
        try:
            service_data['volumes']
        except KeyError:
            service_data['volumes'] = [{
                'type': 'bind',
                'source': './',
                'target': '/sqaaas-build'
            }]
            logger.debug('Setting volume data to default values: %s' % service_data['volumes'])
        ## Set 'working_dir' property (for simple use cases)
        ### NOTE!! Setting working_dir only makes sense when only one volume is expected!
        service_data['working_dir'] = service_data['volumes'][0]['target']
        logger.debug('Setting <working_dir> property to <%s>' % service_data['working_dir'])
    @staticmethod
    def set_service_oneshot(service_data):
        """Set the default volume data.

        :param service_data: Data of the DC service
        """
        logger.debug('Call to ProcessExtraData.set_service_oneshot() method')
        oneshot = True
        if 'oneshot' in service_data.keys():
            oneshot = service_data.pop('oneshot')
        if oneshot:
            logger.debug('Oneshot image, setting <sleep> command')
            service_data['command'] = 'sleep 6000000'

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

    @staticmethod
    def load_tooling_repo(project_repos_mapping, config_json):
        """Add tooling repository to <project_repos> property.

        :param project_repos_mapping: Dict containing the defined project_repos
        :param config_json: Config data (JSON)
        """
        logger.debug('Call to ProcessExtraData.load_tooling_repo() method')

        if tooling_repo_url in list(project_repos_mapping):
            logger.debug('Tool template repository <%s> already defined' % tooling_repo_url)
        else:
            repo_data = {}
            repo_data['name'] = get_short_repo_name(
                tooling_repo_url, include_netloc=True
            )
            repo_data['branch'] = tooling_repo_branch
            project_repos_mapping[tooling_repo_url] = repo_data

            config_json['config']['project_repos'][repo_data['name']] = {
                'repo': tooling_repo_url,
                'branch': tooling_repo_branch
            }

    def curate_service_image_properties(composer_json, service_name=None, tool={}, criterion_name=None, project_repos_mapping={}):
        """Curate the composer parameters of the given config.yml repo entry.

        Returns the service name.

        :param composer_json: Composer data (JSON)
        :param service_name: name of the service (if known)
        :param tool: Tool object
        :param criterion_name: Name of the criterion
        :param project_repos_mapping: Dict containing the defined project_repos
        """
        if not composer_json:
            logger.debug('No service was defined by the user')
            composer_json['version'] = '3.7'

        image = None
        context = None
        dockerfile = None
        build_args = None
        oneshot = True
        service_data = {} # existing service data

        if service_name:
            service_data = composer_json['services'][service_name]
            image = service_data.get('image', {}).get('name', '')
            dockerfile_path = service_data.get('build', {}).get('dockerfile', '')
            context = os.path.dirname(dockerfile_path)
            # For now <build_args> are only present in user-defined services
            build_args = service_data.get('build', {}).get('args', None)
        else:
            service_name = '_'.join([
                criterion_name.lower(), namegenerator.gen()
            ])
            logger.debug('Service name set: %s' % service_name)
            dockerfile_path = tool['docker'].get('dockerfile', '')
            context = os.path.join(
                project_repos_mapping[tooling_repo_url]['name'],
                os.path.dirname(dockerfile_path)
            )
            image = tool['docker'].get('image', '')
            oneshot = tool['docker'].get('oneshot', True)

        dockerfile = os.path.basename(dockerfile_path)
        service_image_properties = JePLUtils.get_composer_service(
            service_name,
            image=image,
            context=context,
            dockerfile=dockerfile,
            build_args=build_args,
            oneshot=oneshot
        )

        if service_data:
            service_data.update(service_image_properties)
        else:
            service_data = service_image_properties

        # Update service image definition
        if service_name in list(composer_json['services']):
            composer_json['services'][service_name].update(service_image_properties)
        else:
            composer_json['services'][service_name] = service_image_properties
        logger.info('Service <%s> image properties updated: %s' % (service_name, service_image_properties))

        return service_name

    @staticmethod
    def set_tool_execution_command(
            tool,
            criterion_name,
            criterion_repo,
            config_json,
            report_to_stdout=False):
        """Compose the command/s for the given tool according to its args in the tooling metadata.

        Returns a mapping of the tool and associated command for the given criterion, such as:
            {
                "licensee": [
                    "licensee detect . --json"
                ]
            }

        :param tool: Tool object
        :param criterion_name: Name of the criterion
        :param criterion_repo: Repo data for the criterion
        :param config_json: Config data (JSON)
        :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tool (required by QAA module)
        """
        def process_value(arg, commands_builder=False, option_no_flag=False):
            value = arg['value']
            if type(value) in [str]:
                value_list = list(filter(None, value.split(',')))
                value_list = list(map(str.strip, value_list))
                if arg.get('repeatable', False):
                    if len(value_list) == 1:
                        if option_no_flag:
                            value_list = value_list[0]
                            return list(map(lambda value: ' '.join([option_no_flag, value]), value_list.split()))
                    elif len(value_list) > 1:
                        if commands_builder:
                            return value_list
                return list([' '.join(value_list)])
            return value

        def process_args(args, cmd_list=[]):
            cmd_list = []
            for arg in args:
                flag = False
                if arg['type'] in ['optional']:
                    if not 'value' in list(arg):
                        flag = True
                    else:
                        if arg.get('selectable', False) and not arg['value']:
                            continue
                        if arg.get('repeatable', False):
                            cmd_list.extend(process_value(arg, commands_builder=commands_builder, option_no_flag=arg['option']))
                            continue
                    cmd_list.append(arg['option'])
                if not flag:
                    cmd_list.extend(process_value(arg, commands_builder=commands_builder))
                if arg.get('args', []):
                    cmd_list.extend(process_args(arg['args'], cmd_list=cmd_list))
            return cmd_list

        criterion_repo['commands'] = []
        tool_map = {} # tool DB data
        tool_name = tool['name']
        # special treatment for 'commands' builder
        commands_builder = False
        if tool_name in ['commands']:
            commands_builder = True
        # when existing, use executable instead of name
        # if executable exists but empty, then no name & no executable (commands)
        cmd_list = [tool_name]
        if 'executable' in list(tool):
            if not tool['executable']:
                cmd_list = []
            else:
                cmd_list = [tool['executable']]
        args = tool.get('args', [])
        cmd_list.extend(process_args(args))
        if commands_builder:
            cmd = cmd_list
        else:
            cmd = [' '.join(cmd_list)]
        criterion_repo['commands'].extend(cmd)
        if tool in list(tool_map):
            tool_map[tool_name].extend(cmd)
        else:
            tool_map[tool_name] = cmd
        # If applicable, print the generated report to stdout
        if report_to_stdout:
            report_file = tool.get('includes_report', None)
            if report_file:
                logger.debug('Adding `cat` command (last step) to print generated report to stdout')
                cat_cmd = 'cat %s' % report_file
                criterion_repo['commands'].append(cat_cmd)

        config_json['sqa_criteria'][criterion_name]['repos'] = criterion_repo

        return tool_map

    @staticmethod
    def set_config_when_clause(config_json):
        """Split out in different config.yml files according to 'when' clause.

        :param config_json: Config data (JSON)
        """
        logger.debug('Call to ProcessExtraData.set_config_when_clause() method')
        config_data_list = []
        config_json_no_when = copy.deepcopy(config_json)
        for criterion_name, criterion_data in config_json['sqa_criteria'].items():
            criterion_data_copy = copy.deepcopy(criterion_data)
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

        return config_data_list

    @staticmethod
    def generate_script_for_commands(stage_name, checkout_dir, commands_list, repos_data, commands_script_list):
        """Generate the bash script including the received commands.

        :param stage_name: The stage name
        :param checkout_dir: The local path where the repo has been cloned
        :param commands_list: The list of shell commands
        :param repos_data: The individual repository data
        :param commands_script_list: Current list of strings that generate the command builder scripts
        """
        logger.debug('Call to ProcessExtraData.generate_script_for_commands() method')
        commands_script_data = JePLUtils.get_commands_script(
            checkout_dir,
            commands_list
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
        repos_data[stage_name]['commands'] = [script_call]


def process_extra_data(config_json, composer_json, report_to_stdout=False):
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
    :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tool (required by QAA module)
    """
    # CONFIG:CONFIG (Generate short url-based repo name & mapping)
    project_repos_mapping = {}
    if 'project_repos' in config_json['config'].keys():
        project_repos_final = {}
        for project_repo in config_json['config']['project_repos']:
            repo_url = project_repo.pop('repo')
            # Get default branch if None is defined
            if not project_repo.get('branch', None):
                project_repo['branch'] = GitUtils.get_remote_active_branch(
                    repo_url
                )
            # Check for empty values
            project_repo = del_empty_keys(project_repo)
            # Set repo name
            repo_name_generated = get_short_repo_name(
                repo_url, include_netloc=True)
            # Compose final <project_repos>
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
    # - Array-to-Object conversion for repos
    # - Set 'context' to the appropriate checkout path for building the Dockerfile
    stage_name_mapping = {} # mapping with the last increment of a given <stage_name>
    commands_script_list = []
    tool_criteria_map = {}
    service_images_curated_list = [] # services processed by curate_service_image_properties()
    for criterion_name, criterion_data in config_json['sqa_criteria'].items():
        logger.debug('Processing config data for criterion <%s>' % criterion_name)
        criterion_data_copy = copy.deepcopy(criterion_data)
        if 'repos' in criterion_data.keys():
            repos_old = criterion_data_copy.pop('repos')
            repos_new = {}
            tooling_repo_is_loaded = False
            for repo in repos_old:
                logger.debug('Processing repository entry: %s' % repo)
                service_name = repo.get('container', None)
                try:
                    tool = repo.pop('tool')
                except KeyError:
                    logger.warn('Tool not provided on request!')
                    tool = {}
                if not service_name:
                    if not tooling_repo_is_loaded:
                        logger.debug('Service name is not defined: adding tooling repository to config.yml')
                        ProcessExtraData.load_tooling_repo(project_repos_mapping, config_json)
                        tooling_repo_is_loaded = True
                    else:
                        logger.debug('Service name is not defined: tooling repository already loaded in config.yml')

                # Processing image details for current repo
                service_name = ProcessExtraData.curate_service_image_properties(
                    composer_json,
                    service_name=service_name,
                    tool=tool,
                    criterion_name=criterion_name,
                    project_repos_mapping=project_repos_mapping
                )
                service_images_curated_list.append(service_name)
                # Set service_name in repo's <container> property
                repo['container'] = service_name

                # Compose command/s according to tooling metadata
                tool_criterion_map = ProcessExtraData.set_tool_execution_command(
                    tool, criterion_name, repo, config_json)
                if criterion_name in list(tool_criteria_map):
                    tool_criteria_map[criterion_name].update(tool_criterion_map)
                else:
                    tool_criteria_map[criterion_name] = tool_criterion_map

                tox_checkout_dir = '.'
                try:
                    repo_url = repo.pop('repo_url')
                    if not repo_url:
                        raise KeyError
                except KeyError:
                    # Use 'this_repo' as the placeholder for current repo & version
                    stage_name = 'this_repo'
                else:
                    stage_name = ' '.join([
                        project_repos_mapping[repo_url]['name'],
                        tool['name']
                    ])

                if stage_name in list(repos_new):
                    stage_name_last = stage_name_mapping.get(
                        stage_name, stage_name
                    )
                    stage_name_new = JePLUtils.generate_stage_name(
                        stage_name_last
                    )
                    stage_name_mapping[stage_name] = stage_name_new
                    stage_name = stage_name_new
                repos_new[stage_name] = repo

                if repo_url:
                    # Create script for 'commands' builder
                    # NOTE: This is a workaround -> a specific builder to tackle this will be implemented in JePL
                    if 'commands' in repo.keys():
                        ProcessExtraData.generate_script_for_commands(
                            stage_name=stage_name,
                            checkout_dir=project_repos_mapping[repo_url]['name'],
                            commands_list=repo['commands'],
                            repos_data=repos_new,
                            commands_script_list=commands_script_list
                        )
                    tox_checkout_dir = stage_name
                # FIXME Commented out until issue #154 gets resolved
                # Modify Tox properties (chdir, defaults)
                # ProcessExtraData.set_tox_env(tox_checkout_dir, repos_new)
            criterion_data_copy['repos'] = repos_new
        config_json['sqa_criteria'][criterion_name] = criterion_data_copy

    # Default CONFIG:ENVIRONMENT
    for jpl_envvar in ['JPL_DOCKERFORCEBUILD', 'JPL_KEEPGOING']:
        logger.debug('Enabling <%s> flag (default behaviour)' % jpl_envvar)
        if not 'environment' in config_json.keys():
            config_json['environment'] = {}
        config_json['environment'][jpl_envvar] = 'enabled'

    # COMPOSER (Docker Compose specific)
    for srv_name, srv_data in composer_json['services'].items():
        if srv_name not in service_images_curated_list:
            logger.debug('Service <%s> image properties not curated' % srv_name)
            service_name = ProcessExtraData.curate_service_image_properties(
                composer_json, service_name=srv_name
            )
            service_images_curated_list.append(service_name)

        logger.debug('Processing composer data for service <%s>' % srv_name)
        if 'image' in list(srv_data):
            use_default_dockerhub_org = False
            ## Set JPL_DOCKER* envvars
            if 'registry' in srv_data['image'].keys():
                logger.debug('Registry data found for image <%s>' % srv_data['image'])
                registry_data = srv_data['image'].pop('registry')
                # JPL_DOCKERPUSH
                if registry_data['push']:
                    srv_push = config_json['environment'].get('JPL_DOCKERPUSH', '')
                    srv_push += ' %s' % srv_name
                    srv_push = srv_push.strip()
                    config_json['environment']['JPL_DOCKERPUSH'] = srv_push
                    logger.debug('Setting JPL_DOCKERPUSH environment value to <%s>' % srv_push)
                    credential_id = None
                    if registry_data.get('credential_id', None):
                        credential_id = registry_data['credential_id']
                        logger.debug('Using custom Jenkins credentials: %s' % credential_id)
                    else:
                        credential_id = docker_credential_id
                        use_default_dockerhub_org = True
                        logger.debug('Using catch-all Jenkins credentials: %s' % credential_id)
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
                    logger.debug('Setting JPL_DOCKERSERVER environment value to <%s>' % registry_data['url'])
            ## Set 'image' property as string (required by Docker Compose)
            srv_data['image'] = srv_data['image']['name']
            if use_default_dockerhub_org:
                org = docker_credential_org
                logger.debug('Using default Docker Hub <%s> organization' % org)
                img_name = srv_data['image'].split('/')[-1]
                srv_data['image'] = '/'.join([org, img_name])
                logger.debug('Resultant Docker image name: %s' % srv_data['image'])
        ## Check for empty values
        srv_data = del_empty_keys(srv_data)
        ## Set 'volumes' property (incl. default values)
        ProcessExtraData.set_service_volume(srv_data)
        ## Handle 'oneshot' services
        ProcessExtraData.set_service_oneshot(srv_data)

    composer_data = {'data_json': composer_json}

    # CONFIG:SQA_CRITERIA
    # - Multiple stages/Jenkins when clause
    config_data_list = ProcessExtraData.set_config_when_clause(config_json)

    return (config_data_list, composer_data, commands_script_list, tool_criteria_map)


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


def supported_git_platform(repo_url, platforms):
    """Checks if the given repo_url belongs to any of the supported platforms.

    Returns the key of the git platform in case it matches with any of the supported
    platforms. Otherwise, returns None.

    :param repo_url: URL of the git repository
    :param platforms: Dict with the git supported platforms (e.g {'github': 'https://github.com'})
    """
    url_parsed = urlparse(repo_url)
    netloc_without_extension = url_parsed.netloc.split('.')[0]
    if not netloc_without_extension in list(platforms):
        netloc_without_extension = None
    return netloc_without_extension


def get_short_repo_name(repo_url, include_netloc=False):
    """Returns the short name of the git repo, i.e. <user/org>/<repo_name>.

    :param repo_url: URL of the git repository
    """
    url_parsed = urlparse(repo_url)
    short_repo_name = url_parsed.path
    if include_netloc:
        short_repo_name = ''.join([
            url_parsed.netloc,
            url_parsed.path,
        ])
    # cleanup
    short_repo_name = short_repo_name.lstrip('/')
    short_repo_name = short_repo_name.rsplit('.git')[0]
    logger.debug('Short repository name for <%s>: %s' % (repo_url, short_repo_name))
    return short_repo_name


def del_empty_keys(data):
    """Deletes the empty keys from a dict or json.

    :param data: dict or json data
    """
    props_to_remove = []
    for prop, prop_value in data.items():
        pop_prop = False
        if isinstance(prop_value, dict):
            if not any(prop_value.values()):
                pop_prop = True
        elif isinstance(prop_value, (list, str)):
            if not prop_value:
                pop_prop = True
        if pop_prop:
            props_to_remove.append(prop)
    [data.pop(prop) for prop in props_to_remove]
    return data


def get_language_entry(lang):
    """Get the entry for the given language in the language's metadata file.

    :param lang: name of the language (compliant with <linguist> tool language
                 definition)
    """
    language_metadata_file = config.get(
        'language_metadata_file',
        fallback='etc/languages.yml'
    )
    lang_entry = None
    with open(language_metadata_file) as yaml_file:
        try:
            data = yaml.safe_load(yaml_file)
        except yaml.YAMLError as e:
            _reason = 'Could not load <%s> file: %s' % (
                language_metadata_file, str(e)
            )
            logger.error(_reason)
        else:
            if lang not in list(data):
                logger.warn((
                    'Language <%s> not found in language metadata file '
                    '(%s)' % (lang, language_metadata_file)
                ))
            else:
                lang_entry = data[lang]

    return lang_entry


@GitUtils.do_git_work
def find_files_by_language(field, value, repo, path='.'):
    """Finds files in the current path that match the given list of
    extensions.

    :param field: field name (compliant with <linguist> tool).
                  Choices are ('extensions', 'filenames')
    :param value: field value (compliant with <linguist> tool)
    :param repo: repository object (URL & branch)
    :param path: look for file extensions in the given repo path
    """
    files_found = []
    if field in ['extensions']:
        for extension in value:
            file_list = sorted(Path(path).rglob('*'+extension))
            files_found.extend([str(file_name) for file_name in file_list])
    elif field in ['filenames']:
        for filename in value:
            if Path(PurePath(path, filename)).exists():
                files_found.append(filename)
    else:
        logger.warn((
            'Language field <%s> (from languages.yml) not supported!' % field
        ))
    if files_found:
        logger.debug('Files found in path matching required %s: %s' % (
            field, files_found)
        )

    return files_found
