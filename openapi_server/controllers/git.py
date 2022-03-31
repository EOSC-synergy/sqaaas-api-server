import functools
import logging
import os
import stat
import tempfile

from git import Repo
from git.exc import GitCommandError

from openapi_server.exception import SQAaaSAPIException


logger = logging.getLogger('sqaaas.api.git')

REMOTE_NAME = 'sqaaas'

class GitUtils(object):
    """Class for handling Git commands.

    Authentication done via askpass helper.
    """
    def __init__(self, access_token):
        """GitUtils object definition.

        :param access_token: Access token to access the remote Git repository
        """
        self.access_token = access_token

    def setup_env(self, dirpath):
        """Setups the environment for handling remote repositories.

        :param dirpath: Directory to add the helper to
        """
        helper_path = os.path.join(dirpath, 'git-askpass-helper.sh')
        with open(helper_path, 'w') as f:
            f.writelines('%s\n' % l for l in ['#!/bin/sh', 'exec echo "$GIT_PASSWORD"'])
        os.chmod(helper_path, stat.S_IEXEC)
        os.environ['GIT_ASKPASS'] = helper_path
        os.environ['GIT_PASSWORD'] = self.access_token
        logger.debug('Git environment set: askpass helper & env vars')

    def clone_and_push(self, source_repo, target_repo, source_repo_branch=None):
        """Copies the source Git repository into the target one.

        Returns a tuple with the repository URL and default branch name.

        :param source_repo: Absolute URL of the source repository (e.g. https://example.org)
        :param target_repo: Absolute URL of the target repository (e.g. https://github.com/org/example)
        :param source_repo_branch: Specific branch name to use from the source repository
        """
        with tempfile.TemporaryDirectory() as dirpath:
            repo = None
            try:
                if source_repo_branch:
                    repo = Repo.clone_from(source_repo, dirpath, single_branch=True, b=source_repo_branch)
                else:
                    repo = Repo.clone_from(source_repo, dirpath)
            except GitCommandError as e:
                raise SQAaaSAPIException(422, e)
            else:
                self.setup_env(dirpath)

            sqaaas = repo.create_remote(REMOTE_NAME, url=target_repo)
            try:
                sqaaas.fetch()
                sqaaas.pull()
                logger.debug('Repository updated: %s' % repo.remotes.sqaaas.url)
            except GitCommandError as e:
                logger.warning('Could not fetch&pull from target repository: %s (git msg: %s)' % (target_repo, e))
            finally:
                sqaaas.push(force=True)
                logger.debug('Repository pushed to remote: %s' % repo.remotes.sqaaas.url)
            default_branch = repo.active_branch
        return sqaaas.url, default_branch.name

    @staticmethod
    def get_remote_active_branch(remote_repo, remote_branch=None):
        """Gets active branch from remote repository.

        :param remote_repo: Absolute URL of the source repository (e.g. https://example.org)
        :param remote_branch: Specific branch name to use from the source repository
        """
        branch = None
        with tempfile.TemporaryDirectory() as dirpath:
            try:
                logger.debug((
                    'Inspecting content of repo <%s> (branch %s)' % (
                        remote_repo, remote_branch
                    )
                ))
                if branch:
                    repo = Repo.clone_from(
                        remote_repo, dirpath,
                        single_branch=True, b=remote_branch
                    )
                else:
                    repo = Repo.clone_from(
                        remote_repo, dirpath
                    )
                branch = repo.active_branch
                branch = branch.name
            except GitCommandError as e:
                raise SQAaaSAPIException(422, e)
            else:
                return branch

    @staticmethod
    def do_git_work(f):
        """Decorator to perform some git work inside a cloned repository.

        The decorated method MUST have a kwarg 'repo' of type dict with
        2 keys: {'repo': 'https://example.org/foo', 'branch': None}
        """
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            repo = kwargs['repo']
            source_repo = repo['repo']
            source_repo_branch = repo.get('branch', None)
            with tempfile.TemporaryDirectory() as dirpath:
                # Get active branch from remote repository
                branch = GitUtils.get_remote_active_branch(
                    source_repo, source_repo_branch
                )
                # Set path to the temporary directory
                kwargs['path'] = dirpath
                # Perform the actual work
                ret = f(*args, **kwargs)
                return ret
        return decorated_function
