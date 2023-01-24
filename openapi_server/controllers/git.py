import functools
import logging
import os
import re
import stat
import tempfile

from git import Repo
from git.exc import GitCommandError
from urllib3.util import parse_url
from urllib3.util import Url

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

    @staticmethod
    def _custom_exception_messages(exc, **kwargs):
        """Returns more concised error messages from the ones returned by
        GitPython.

        :param exc: GitCommandError exception
        """
        message = str(exc)
        if message.find('remote: Repository not found') != -1:
            message = 'Repository not found: %s' % kwargs['repo']
        elif re.search("fatal: repository '(.+)' not found", message):
            message = 'Repository not found: %s' % kwargs['repo']

        return message

    @staticmethod
    def _format_git_url(repo_url):
        """Formats git URL to avoid asking for password when repos do not exist.

        :param repo_url: URL of the git repository
        """
        logger.debug((
            'Format source repository URL to avoid git askpass when repo '
            'does not exist: %s' % repo_url
        ))
        repo_url_parsed = parse_url(repo_url)
        repo_url_final = Url(
            scheme=repo_url_parsed.scheme,
            auth=repo_url_parsed.auth,
            host=':@'+repo_url_parsed.host,
            path=repo_url_parsed.path,
            query=repo_url_parsed.query,
            fragment=repo_url_parsed.fragment
        )
        return repo_url_final.url

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

        Returns the target's branch name.

        :param source_repo: Absolute URL of the source repository (e.g. https://example.org)
        :param target_repo: Absolute URL of the target repository (e.g. https://github.com/org/example)
        :param source_repo_branch: Specific branch name to use from the source repository
        """
        source_repo = GitUtils._format_git_url(source_repo)
        with tempfile.TemporaryDirectory() as dirpath:
            repo = None
            try:
                if source_repo_branch:
                    repo = Repo.clone_from(source_repo, dirpath, single_branch=True, b=source_repo_branch)
                else:
                    repo = Repo.clone_from(source_repo, dirpath)
            except GitCommandError as e:
                raise SQAaaSAPIException(
                    422, GitUtils._custom_exception_messages(
                        e, repo=source_repo
                    )
                )
            else:
                self.setup_env(dirpath)

            sqaaas = repo.create_remote(REMOTE_NAME, url=target_repo)
            sqaaas.push(force=True)
            logger.debug('Repository pushed to remote: %s' % repo.remotes.sqaaas.url)
            default_branch = repo.active_branch.name
        return default_branch

    @staticmethod
    def get_remote_active_branch(remote_repo):
        """Gets active branch from remote repository.

        :param remote_repo: Absolute URL of the source repository (e.g. https://example.org)
        """
        branch = None
        with tempfile.TemporaryDirectory() as dirpath:
            try:
                logger.debug((
                    'Inspecting content of repo <%s>' % (
                        remote_repo
                    )
                ))
                repo = Repo.clone_from(
                    remote_repo, dirpath
                )
                branch = repo.active_branch
                branch = branch.name
                logger.debug(
                    'Active branch name from remote repository <%s>: %s' % (
                        remote_repo, branch
                ))
            except GitCommandError as e:
                raise SQAaaSAPIException(
                    422, GitUtils._custom_exception_messages(
                        e, repo=remote_repo
                    )
                )
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
            repo = kwargs.get('repo', None)
            if repo:
                source_repo = GitUtils._format_git_url(repo['repo'])
                source_repo_branch = repo.get('branch', None)
                with tempfile.TemporaryDirectory() as dirpath:
                    try:
                        if source_repo_branch:
                            repo = Repo.clone_from(
                                source_repo, dirpath,
                                single_branch=True, b=source_repo_branch
                            )
                        else:
                            repo = Repo.clone_from(
                                source_repo, dirpath
                            )
                        branch = repo.active_branch
                        branch = branch.name
                        msg = 'Repository <%s> was cloned (branch: %s)' % (
                            source_repo, branch)
                        logger.debug(msg)
                    except GitCommandError as e:
                        raise SQAaaSAPIException(
                            422, GitUtils._custom_exception_messages(
                                e, repo=repo['repo']
                            )
                        )
                    else:
                        # Set path to the temporary directory
                        kwargs['path'] = dirpath
                        # repo settings
                        kwargs['tag'] = branch
                        kwargs['commit_id'] = repo.commit(branch).hexsha
                    ret = f(*args, **kwargs)
            else:
                ret = f(*args, **kwargs)
            return ret
        return decorated_function
