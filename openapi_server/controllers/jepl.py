import copy
import logging
import namegenerator

from jinja2 import Environment, PackageLoader, select_autoescape

from openapi_server.controllers import utils as ctls_utils


logger = logging.getLogger('sqaaas_api.jepl')


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
    def get_commands_script(checkout_dir, cmd_list):
        """Returns a String with the 'commands' builder script.

        :param checkout_dir: Directory to chdir to run the script
        :param cmd_list: List of commands from the builder
        """
        env = Environment(
            loader=PackageLoader('openapi_server', 'templates')
        )
        template = env.get_template('commands_script.sh')
        return template.render({
            'checkout_dir': checkout_dir,
            'commands': ' && '.join(cmd_list)
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
    def compose_files(cls, config_json, composer_json):
        """Composes the JePL file structure from the raw JSONs obtained
        through the HTTP request.

        :param cls: Current class (from classmethod)
        :param config_json: JePL's config as received through the API request (JSON payload)
        :param composer_json: Composer content as received throught the API request (JSON payload).
        """
        # Extract & process those data that are not directly translated into
        # the composer and JePL config
        config_data_list, composer_data, commands_script_list = ctls_utils.process_extra_data(
            config_json,
            composer_json)

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

        return (config_data_list, composer_data, jenkinsfile, commands_script_list)

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
            branch):
        """Push the given JePL file structure to the given repo.

        :param cls: Current class (from classmethod)
        :param gh_utils: GitHubUtils object.
        :param repo: Name of the git repository.
        :param config_data_list: List of pipeline's JePL config data.
        :param composer_data: Dict containing pipeline's JePL composer data.
        :param jenkinsfile: String containing the Jenkins configuration.
        :param commands_script_list: List of generated scripts for the commands builder.
        :param branch: Name of the branch in the remote repository.
        """
        # config
        config_files_pushed = []
        for config_data in config_data_list:
            _file_name = config_data['file_name']
            logger.debug('Pushing JePL config file to GitHub repository <%s>: %s' % (
                repo, _file_name))
            gh_utils.push_file(
                _file_name,
                config_data['data_yml'],
                'Update %s' % _file_name,
                repo,
                branch
            )
            config_files_pushed.append(_file_name)
        config_files_from_repo = [
            file_content.path
                for file_content in cls.get_files('config', gh_utils, repo, branch)
        ]
        config_files_to_remove = set(config_files_from_repo).difference(set(config_files_pushed))
        for config_file in config_files_to_remove:
            logger.debug('Deleting no longer needed config.yml file: %s' % config_file)
            gh_utils.delete_file(config_file, repo, branch)
        # composer
        logger.debug('Pushing composer file to GitHub repository <%s>: %s' % (
            repo, composer_data['file_name']))
        gh_utils.push_file(
            composer_data['file_name'],
            composer_data['data_yml'],
            'Update %s' % composer_data['file_name'],
            repo,
            branch
        )
        # jenkinsfile
        logger.debug('Pushing Jenkinsfile to GitHub repository <%s>' % repo)
        # FIXME Getting only the last commit as the representation for the whole
        # set of JePL files. This HAS to be changed so that a unique commit is done
        last_commit = gh_utils.push_file(
            'Jenkinsfile',
            jenkinsfile,
            'Update Jenkinsfile',
            repo,
            branch
        )
        # commands' builder scripts
        commands_scripts_pushed = []
        for commands_script in commands_script_list:
            logger.debug('Pushing script for commands builder to GitHub repository <%s>: %s' % (
                repo, commands_script['file_name']))
            gh_utils.push_file(
                commands_script['file_name'],
                commands_script['content'],
                'Update %s' % commands_script['file_name'],
                repo,
                branch
            )
            commands_scripts_pushed.append(commands_script['file_name'])
        commands_scripts_from_repo = [
            file_content.path
                for file_content in cls.get_files('commands_script', gh_utils, repo, branch)
        ]
        commands_scripts_to_remove = set(commands_scripts_from_repo).difference(set(commands_scripts_pushed))
        for script in commands_scripts_to_remove:
            logger.debug('Deleting no longer needed commands\' builder script file: %s' % script)
            gh_utils.delete_file(script, repo, branch)

        logger.info('GitHub repository <%s> created with the JePL file structure' % repo)

        return last_commit

    def get_composer_service(name, image=None, dockerfile=None, oneshot=True):
        """Get service definition compliant with the composer file.

        :param name: Name of the service.
        :param image: Image name/location in the Docker registry (default: Docker Hub).
        :param dockerfile: Path to the Dockerfile, when building is required.
        :param oneshot: Whether the Docker image is oneshot.
        """
        srv_data = {}
        if image:
            srv_data['image'] = {'name': image}
        if dockerfile:
            srv_data['build'] = {
                'dockerfile': dockerfile
            }
        if not oneshot:
            srv_data['oneshot'] = oneshot
        return {name: srv_data}
