import copy
import logging
import namegenerator

from jinja2 import Environment, PackageLoader, select_autoescape

from openapi_server import config
from openapi_server.controllers import utils as ctls_utils
from openapi_server.exception import SQAaaSAPIException


logger = logging.getLogger('sqaaas.api.jepl')


class JePLUtils(object):
    """Class that generates JePL configuration files."""
    def generate_file_name(file_type, random=False):
        """Generates a file name for any of the JePL-related types of file

        :param file_type: Type of JePL file, one of [config, composer, jenkinsfile].
        :param random: Boolean that marks whether a random string should be inserted in the file name.
        """
        file_type_chunks = {
            'config': ['.sqa/config', 'yml'],
            'composer': ['.sqa/docker-compose', 'yml'],
            'jenkinsfile': ['Jenkinsfile'],
            'commands_script': ['.sqa/script', 'sh']
        }
        chunk_list = copy.deepcopy(file_type_chunks[file_type])
        if random:
            random_str = namegenerator.gen()
            chunk_list.insert(1, random_str)

        return '.'.join(chunk_list)

    @classmethod
    def append_file_name(cls, file_type, file_data_list, force_random_name=False):
        """Appends a 'file_name' property, according to its type (file_type),
        to each Dict element of the given List (file_data_list)

        :param cls: Current class (from classmethod)
        :param file_type: Type of JePL file, one of [config, composer, jenkinsfile].
        :param file_data_list: List of JSON payload data to be associated with the generated file name.
        :param force_random_name: If set the method will always return a random name for the file.
        """
        new_file_data_list = []
        count = 0
        for data in file_data_list:
            if count > 0 or force_random_name:
                file_name = cls.generate_file_name(file_type, random=True)
            else:
                file_name = cls.generate_file_name(file_type)
            new_data = copy.deepcopy(data)
            new_data.update({'file_name': file_name})
            new_file_data_list.append(new_data)
            count += 1

        return new_file_data_list

    @staticmethod
    def get_commands_script(
            checkout_dir, cmd_list, template_name='', template_kwargs={}):
        """Returns a String with the 'commands' builder script.

        :param checkout_dir: Directory to chdir to run the script
        :param cmd_list: List of commands from the builder
        :param template: Native template for specific tool customizations
        :param template_kwargs: Object required for template rendering
        """
        env = Environment(
            loader=PackageLoader('openapi_server', 'templates'),
        )
        if template_name in ['im_client', 'ec3_client']:
            template = env.get_template('commands_script_im.sh')
            # RADL or TOSCA image id
            im_config_file = template_kwargs.get('im_config_file', '')
            _reason = None
            if not im_config_file:
                _reason = ((
                    'No RADL or TOSCA config file provided for im_client: '
                    '%s' % template_kwargs
                ))
            else:
                if im_config_file.endswith('radl'):
                    template_kwargs['im_config_file_type'] = 'radl'
                elif im_config_file.endswith(('yaml', 'yml')):
                    template_kwargs['im_config_file_type'] = 'yaml'
                else:
                    _reason = (
                        'File <%s> not recognized as either TOSCA or RADL'
                    )
            if _reason:
                logger.debug(_reason)
                raise SQAaaSAPIException(422, _reason)
            # IaaS site selection
            iaas = template_kwargs.get('openstack_site_id', '')
            if not iaas:
                _reason = ((
                    'Cannot find <openstack_site_id> for im_client in the '
                    'configuration: %s' % template_kwargs
                ))
                logger.debug(_reason)
                raise SQAaaSAPIException(422, _reason)
            template_kwargs.update(
                config.get_service_deployment(iaas)
            )
        else:
            template = env.get_template('commands_script.sh')
        return template.render({
            'checkout_dir': checkout_dir,
            'commands': cmd_list,
            'template': template_name,
            'template_kwargs': template_kwargs
        })

    def get_jenkinsfile(config_data_list):
        """Returns a String with the Jenkinsfile rendered from the given
        JSON payload.

        :param config_data_list: List of config data Dicts
        """
        env = Environment(
            loader=PackageLoader('openapi_server', 'templates')
        )
        template = env.get_template('Jenkinsfile')

        return template.render(config_data_list=config_data_list)

    @classmethod
    def compose_files(cls, config_json, composer_json, report_to_stdout=False):
        """Composes the JePL file structure from the raw JSONs obtained
        through the HTTP request.

        :param cls: Current class (from classmethod)
        :param config_json: JePL's config as received through the API request (JSON payload)
        :param composer_json: Composer content as received throught the API request (JSON payload).
        :param report_to_stdout: Flag to indicate whether the pipeline shall print via via stdout the reports produced by the tools (required by QAA module)
        """
        # Extract & process those data that are not directly translated into
        # the composer and JePL config
        (
            config_data_list,
            composer_data,
            commands_script_list,
            additional_files_to_commit,
            tool_criteria_map
        ) = ctls_utils.process_extra_data(
            config_json,
            composer_json,
            report_to_stdout=report_to_stdout
        )

        # Convert JSON to YAML
        for elem in config_data_list:
            elem['data_yml'] = ctls_utils.json_to_yaml(elem['data_json'])
        composer_data['data_yml'] = ctls_utils.json_to_yaml(composer_data['data_json'])

        # Set file names to JePL data
        # Note the composer data is forced to be a list since the API spec
        # currently defines it as an object, not as a list
        config_data_list = cls.append_file_name(
            'config', config_data_list)
        composer_data = cls.append_file_name(
            'composer', [composer_data])[0]
        jenkinsfile = cls.get_jenkinsfile(config_data_list)

        return (
            config_data_list,
            composer_data,
            jenkinsfile,
            commands_script_list,
            additional_files_to_commit,
            tool_criteria_map
        )

    def get_files(
        file_type,
        gh_utils,
        repo,
        branch):
        """Get JePL files of the given type from the remote repository.

        :param file_type: Type of JePL file, one of [config, composer, jenkinsfile].
        :param gh_utils: GithubUtils object.
        :param repo: Name of the git repository.
        :param branch: Name of the repository branch.
        """
        prefix_names = {
            'config': 'config',
            'composer': 'docker-compose',
            'commands_script': 'script'
        }
        path = '.'
        if file_type in ['config', 'composer', 'commands_script']:
            path = '.sqa'
        file_list = gh_utils.get_repo_content(repo, branch, path)
        prefix = prefix_names[file_type]
        return [
            file_content
                for file_content in file_list
                    if file_content.name.startswith(prefix)
        ]

    @classmethod
    def push_files(
            cls,
            gh_utils,
            repo,
            config_data_list,
            composer_data,
            jenkinsfile,
            commands_script_list,
            additional_files_to_commit,
            branch):
        """Push the given JePL file structure to the given repo.

        :param cls: Current class (from classmethod)
        :param gh_utils: GitHubUtils object.
        :param repo: Name of the git repository.
        :param config_data_list: List of pipeline's JePL config data.
        :param composer_data: Dict containing pipeline's JePL composer data.
        :param jenkinsfile: String containing the Jenkins configuration.
        :param commands_script_list: List of generated scripts for the commands
               builder.
        :param additional_files_to_commit: List of additional files that are needed.
        :param branch: Name of the branch in the remote repository.
        """
        ## config
        config_files_to_push = [
            {
                'file_name': config_data['file_name'],
                'file_data': config_data['data_yml'],
                'delete': False
            }
            for config_data in config_data_list
        ]
        config_files_from_repo = [
            file_content.path
                for file_content in cls.get_files(
                    'config', gh_utils, repo, branch
                )
        ]
        config_files_to_push_names = [
            file_dict['file_name']
            for file_dict in config_files_to_push
        ]
        config_files_to_remove_set = set(config_files_from_repo).difference(
            set(config_files_to_push_names)
        )
        config_files_to_remove = [
            {
                'file_name': config_file,
                'delete': True
            }
            for config_file in config_files_to_remove_set
        ]
        ## composer
        composer_files_to_push = [{
            'file_name': composer_data['file_name'],
            'file_data': composer_data['data_yml'],
            'delete': False
        }]
        ## jenkinsfile
        jenkinsfile_to_push = [{
            'file_name': 'Jenkinsfile',
            'file_data': jenkinsfile,
            'delete': False
        }]
        ## commands' builder scripts
        commands_scripts_to_push = [
            {
                'file_name': commands_script['file_name'],
                'file_data': commands_script['content'],
                'delete': False
            }
            for commands_script in commands_script_list
        ]
        commands_scripts_from_repo = [
            file_content.path
                for file_content in cls.get_files(
                    'commands_script', gh_utils, repo, branch
                )
        ]
        commands_scripts_to_push_names = [
            file_dict['file_name']
            for file_dict in commands_scripts_to_push
        ]
        commands_scripts_to_remove_set = set(
            commands_scripts_from_repo
        ).difference(set(commands_scripts_to_push_names))
        commands_scripts_to_remove = [
            {
                'file_name': script,
                'delete': True
            }
            for script in commands_scripts_to_remove_set
        ]
        ## Additional files to commit
        additional_files_to_push = [
            {
                'file_name': additional_file['file_name'],
                'file_data': additional_file['file_data'],
                'delete': False
            }
            for additional_file in additional_files_to_commit
        ]
        ## Merge & Push the definitive list of files
        files_to_push = (
            config_files_to_push + config_files_to_remove +
            composer_files_to_push +
            jenkinsfile_to_push +
            commands_scripts_to_push + commands_scripts_to_remove + 
            additional_files_to_push
        )
        commit = gh_utils.push_files(
            files_to_push,
            commit_msg='Add JePL file structure',
            repo_name=repo,
            branch=branch
        )
        logger.debug((
            'GitHub repository <%s> created with the JePL file '
            'structure' % repo
        ))

        return commit

    def get_composer_service(
            name,
            image=None,
            context=None,
            dockerfile=None,
            build_args=None,
            oneshot=True,
            entrypoint=None,
            environment=[]
    ):
        """Get service definition compliant with the composer file.

        :param name: Name of the service.
        :param image: Image name/location in the Docker registry (default: Docker Hub).
        :param context: Context path when building is required.
        :param dockerfile: Path to the Dockerfile, when building is required.
        :param oneshot: Whether the Docker image is oneshot.
        :param entrypoint: Entrypoint for the service.
        :param environment: Environment for the service.
        """
        srv_data = {}
        if image:
            logger.info('No build context is needed for service <%s>' % name)
            srv_data['image'] = {'name': image}
            logger.debug('Image name set for service <%s>: %s' % (name, image))
        if dockerfile:
            # Add './' when relative path. If not, Docker may confuse it with a remote URL
            context = './' + context
            srv_data['build'] = {
                'context': context,
                'dockerfile': dockerfile
            }
            if build_args:
                srv_data['build']['args'] = build_args
            logger.debug('Dockerfile build context set for service <%s>: %s' % (
                name, srv_data['build']))
        if not oneshot:
            srv_data['oneshot'] = oneshot
            logger.debug('Setting oneshot for service <%s>: %s' % (name, oneshot))
        if entrypoint:
            srv_data['entrypoint'] = entrypoint
            logger.debug('Setting entrypoint for service <%s>: %s' % (name, entrypoint))
        if environment:
            srv_data['environment'] = environment
            logger.debug('Setting environment for service <%s>: %s' % (name, environment))

        return srv_data


    def generate_stage_name(repo_name):
        """Generate the stage name in the event where the same repo will be
        used within the same criterion. It uses a counter-based suffix.

        Generated stage name will be in the form of <repo_name>(__[1-9][0-9]{0,})

        :param repo_name: Previous name of the repository.
        """
        # Only interested in the 1st chunk
        name_parts = repo_name.split('__', 1)
        if len(name_parts) == 1:
            counter = 1
        elif len(name_parts) == 2:
            counter = int(name_parts[1])
        else:
            logger.error((
                'Something nasty happened when parsing the repository name: '
                '<%s>' % repo_name
            ))
        counter += 1
        stage_name = '__'.join([name_parts[0], str(counter)])
        logger.debug('New counter-based repository name generated: '
                     '<%s>' % stage_name)
        return stage_name
