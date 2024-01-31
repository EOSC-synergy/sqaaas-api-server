# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import functools
import logging
import os
import re
import stat
import tempfile

from git import Repo, cmd
from git.exc import GitCommandError
from urllib3.util import Url, parse_url

from openapi_server import config
from openapi_server.controllers import crypto as crypto_utils
from openapi_server.exception import SQAaaSAPIException

logger = logging.getLogger("sqaaas.api.git")

REMOTE_NAME = "sqaaas"

CLONE_FOLDER = config.get_vcs("clone_folder", fallback="/tmp")


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
        if message.find("remote: Repository not found") != -1:
            message = "Repository not found or not accessible: %s" % kwargs["repo"]
        elif re.search("fatal: repository '(.+)' not found", message):
            message = "Repository not found or not accessible: %s" % kwargs["repo"]
        elif re.search("fatal: Remote branch (.+) not found", message):
            message = (
                "Repository branch '%s'not found or not accessible for "
                "repository: %s" % (kwargs["branch"], kwargs["repo"])
            )
        elif re.search("fatal: Authentication failed", message):
            message = (
                "Authentication failed when cloning repository: " "%s" % kwargs["repo"]
            )
        elif re.search("fatal: unable to access", message):
            message = (
                "Insufficient privileges to access repository: " "%s" % kwargs["repo"]
            )

        return message

    @staticmethod
    def _format_git_creds(repo_creds):
        """Formats git URL to avoid asking for password when repos do not
        exist.

        :param repo_creds: dict with credential definition (Vault secret, Git
        user/token)
        """
        _creds_prefix_template = "%s:%s@"
        _user_id = ""
        _token = ""
        if "user_id" and "token" in list(repo_creds):  # Git user/token
            _user_id = repo_creds.get("user_id", "")
            _user_id = crypto_utils.decrypt_str(_user_id)
            _token = repo_creds.get("token", "")
            _token = crypto_utils.decrypt_str(_token)
        _creds_prefix_url = _creds_prefix_template % (_user_id, _token)

        return _creds_prefix_url

    @staticmethod
    def _format_git_url(repo_url, repo_creds={}):
        """Formats git URL to avoid asking for password when repos do not exist.

        :param repo_url: URL of the git repository
        :param repo_creds: dict with credential definition (Vault secret, Git
        user/token)
        """
        logger.debug(
            (
                "Format source repository URL to avoid git askpass when repo "
                "does not exist: %s" % repo_url
            )
        )
        repo_url_prefix_creds = GitUtils._format_git_creds(repo_creds)
        repo_url_parsed = parse_url(repo_url)
        repo_url_final = Url(
            scheme=repo_url_parsed.scheme,
            auth=repo_url_parsed.auth,
            host=repo_url_prefix_creds + repo_url_parsed.host,
            path=repo_url_parsed.path,
            query=repo_url_parsed.query,
            fragment=repo_url_parsed.fragment,
        )

        return repo_url_final.url

    @staticmethod
    def get_default_branch_from_remote(repo_url, repo_creds={}):
        """Gets default branch name from a remote repository. It is useful when
        the branch name is not provided by the user.

        :param repo_url: URL of the remote git repository
        :param repo_creds: dict with credential definition (Vault secret, Git
        user/token)
        """
        repo_url_no_creds = repo_url  # for logging purposes
        if repo_creds:
            repo_url = GitUtils._format_git_url(repo_url, repo_creds=repo_creds)

        logger.debug(("Inspecting content of repo <%s>" % (repo_url_no_creds)))
        g = cmd.Git()
        try:
            blob = g.ls_remote(repo_url, "HEAD", symref=True)
            branch = blob.split("\n")[0].split("/")[-1].split("\t")[0]
        except GitCommandError as e:
            _msg = GitUtils._custom_exception_messages(e, repo=repo_url, branch=branch)
            logger.error(_msg)
            raise SQAaaSAPIException(422, _msg)
        else:
            logger.debug(
                "Obtained default branch name from remote repository <%s>: %s"
                % (repo_url_no_creds, branch)
            )
            return branch

    def setup_env(self, dirpath):
        """Setups the environment for handling remote repositories.

        :param dirpath: Directory to add the helper to
        """
        helper_path = os.path.join(dirpath, "git-askpass-helper.sh")
        with open(helper_path, "w") as f:
            f.writelines(
                "%s\n" % line for line in ["#!/bin/sh", 'exec echo "$GIT_PASSWORD"']
            )
        os.chmod(helper_path, stat.S_IEXEC)
        os.environ["GIT_ASKPASS"] = helper_path
        os.environ["GIT_PASSWORD"] = self.access_token
        logger.debug("Git environment set: askpass helper & env vars")

    def clone_and_push(self, source_repo, target_repo, source_repo_branch=None):
        """Copies the source Git repository into the target one.

        Returns the target's branch name.

        :param source_repo: Absolute URL of the source repository (e.g. https://example.org)
        :param target_repo: Absolute URL of the target repository (e.g. https://github.com/org/example)
        :param source_repo_branch: Specific branch name to use from the source repository
        """
        if not source_repo_branch:
            source_repo_branch = GitUtils.get_default_branch_from_remote(source_repo)
        source_repo = GitUtils._format_git_url(source_repo)
        with tempfile.TemporaryDirectory(dir=CLONE_FOLDER) as dirpath:
            repo = None
            try:
                repo = Repo.clone_from(
                    source_repo, dirpath, single_branch=True, b=source_repo_branch
                )
            except GitCommandError as e:
                _msg = GitUtils._custom_exception_messages(
                    e, repo=source_repo, branch=source_repo_branch
                )
                logger.error(_msg)
                raise SQAaaSAPIException(422, _msg)
            else:
                self.setup_env(dirpath)

            sqaaas = repo.create_remote(REMOTE_NAME, url=target_repo)
            sqaaas.push(force=True)
            logger.debug("Repository pushed to remote: %s" % repo.remotes.sqaaas.url)
            default_branch = repo.active_branch.name

        return default_branch

    @staticmethod
    def do_git_work(f):
        """Decorator to perform some git work inside a cloned repository.

        The decorated method MUST have a kwarg 'repo' of type dict with
        2 keys: {'repo': 'https://example.org/foo', 'branch': None}. For
        private repos the additional 'credential_data' key is present.
        """

        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            repo = kwargs.get("repo", None)
            repo_url = repo.get("repo", None)
            if not repo_url:
                _msg = "Repository URL not provided: will not trigger git repository action"
                logger.warning(_msg)
            else:
                repo_creds = repo.get("credential_data", {})
                source_repo = GitUtils._format_git_url(repo_url, repo_creds=repo_creds)
                source_repo_no_creds = repo_url  # for logging purposes
                source_repo_branch = repo.get("branch", None)
                if not source_repo_branch:
                    source_repo_branch = GitUtils.get_default_branch_from_remote(
                        repo_url, repo_creds
                    )
                with tempfile.TemporaryDirectory(dir=CLONE_FOLDER) as dirpath:
                    try:
                        repo = Repo.clone_from(
                            source_repo,
                            dirpath,
                            single_branch=True,
                            b=source_repo_branch,
                        )
                        msg = "Repository <%s> was cloned (branch: %s)" % (
                            source_repo_no_creds,
                            source_repo_branch,
                        )
                        logger.debug(msg)
                    except GitCommandError as e:
                        _msg = GitUtils._custom_exception_messages(
                            e, repo=repo_url, branch=source_repo_branch
                        )
                        logger.error(_msg)
                        raise SQAaaSAPIException(422, _msg)
                    else:
                        # Set path to the temporary directory
                        kwargs["path"] = dirpath
                        # repo settings
                        kwargs["tag"] = source_repo_branch
                        kwargs["commit_id"] = repo.commit(source_repo_branch).hexsha
            ret = f(*args, **kwargs)
            return ret

        return decorated_function
