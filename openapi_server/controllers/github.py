# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging

from github import Github, GithubObject, InputGitTreeElement
from github.GithubException import GithubException, UnknownObjectException
from jinja2 import Environment, PackageLoader
from openapi_server.controllers import crypto as crypto_utils
from openapi_server.exception import SQAaaSAPIException


class GitHubUtils(object):
    """Class for handling requests to GitHub API.

    Support only for token-based access.
    """

    def __init__(self, access_token):
        """GitHubUtils object definition.

        :param access_token: GitHub's access token
        """
        self.client = Github(access_token)
        self.logger = logging.getLogger("sqaaas.api.github")

    def _check_repo_args(f):
        def decorated_function(self, *args, **kwargs):
            repo = kwargs.get("repo", None)
            repo_name = kwargs.get("repo_name", None)
            repo_creds = kwargs.get("repo_creds", None)
            if not repo:
                if not repo_name:
                    _reason = (
                        "Bad arguments: either the name of the repo or a repo "
                        "object must be provided"
                    )
                    raise SQAaaSAPIException(422, _reason)
                repo = self.get_repository(
                    repo_name, repo_creds=repo_creds, raise_exception=True
                )
            f(self, repo)

        return decorated_function

    def get_repo_content(self, repo_name, branch=None, path="."):
        """Gets the repository content from the given branch.

        Returns a List of ContentFile objects.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param branch: Name of the branch
        """
        repo = self.get_org_repository(repo_name)
        if not repo:
            return False
        if not branch:
            branch = repo.default_branch
        try:
            contents = repo.get_dir_contents(path, ref=branch)
        except (UnknownObjectException, GithubException):
            contents = []

        return contents

    def get_file(
        self, file_name, repo_name, branch=GithubObject.NotSet, fail_if_not_exists=False
    ):
        """Gets the file's content from a GitHub repository.

        Returns a ContentFile object.

        :param file_name: Name of the file
        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param branch: Name of the branch
        :param fail_if_not_exists: Flag to indicate whether to fail if file is not found
        """
        repo = self.get_org_repository(repo_name)
        try:
            return repo.get_contents(file_name, ref=branch)
        except (UnknownObjectException, GithubException) as e:
            _reason = (
                "Could not get file <%s> from GitHub repo <%s> (branch <%s>): "
                "%s" % (file_name, repo_name, branch, str(e))
            )
            if fail_if_not_exists:
                self.logger.error(_reason)
                raise SQAaaSAPIException(422, _reason)
            else:
                self.logger.debug(_reason)
                return False

    def push_file(
        self, file_name, file_data, commit_msg, repo_name, branch=GithubObject.NotSet
    ):
        """Pushes a file into GitHub repository.

        Returns the commit ID (SHA format).

        :param file_name: Name of the affected file
        :param file_data: Contents of the file
        :param commit_msg: Message to use in the commit
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        repo = self.get_org_repository(repo_name)
        if not branch:
            branch = repo.default_branch
        contents = self.get_file(file_name, repo_name, branch)
        r = {}
        if contents:
            self.logger.debug(
                "File <%s> already exists in the repository (branch %s), updating.."
                % (file_name, branch)
            )
            r = repo.update_file(
                contents.path, commit_msg, file_data, contents.sha, branch
            )
        else:
            self.logger.debug(
                "File <%s> does not currently exist in the repository (branch %s), creating.."
                % (file_name, branch)
            )
            r = repo.create_file(file_name, commit_msg, file_data, branch)
        return r["commit"].sha

    def push_files(self, file_list, commit_msg, repo_name, branch=GithubObject.NotSet):
        """Pushes multiple files into a GitHub repository.

        Returns the commit ID (SHA format).

        :param file_list: List of dicts with the file name (<file_name>) and data
            (<file_data>)
        :param commit_msg: Message to use in the commit
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        repo = self.get_org_repository(repo_name)
        element_list = []
        for file_dict in file_list:
            file_name = file_dict["file_name"]
            file_data = file_dict.get("file_data", None)
            to_delete = file_dict["delete"]
            if to_delete:
                blob_sha = None
                self.logger.debug(
                    ("File <%s> marked for deletion in the next " "commit" % file_name)
                )
            else:
                blob_sha = repo.create_git_blob(file_data, "utf-8").sha
                self.logger.debug(("File <%s> added for the next commit" % file_name))
            element_list.append(
                InputGitTreeElement(
                    path=file_name, mode="100644", type="blob", sha=blob_sha
                )
            )
        try:
            # Avoid GH redirections (such as master to main)
            branch_data = repo.get_branch(branch)
            if branch_data.name not in [branch]:
                raise GithubException("Auto-raised exception")
            branch_sha = repo.get_branch(branch).commit.sha
            self.logger.debug(
                "Branch already exists in repo <%s>: %s" % (repo_name, branch)
            )
        except GithubException as e:
            self.logger.error(e)
            self.logger.debug(
                "Branch does not exist in repo <%s>: %s" % (repo_name, branch)
            )
            branch_sha = repo.get_branch(repo.default_branch).commit.sha
            repo.create_git_ref(ref="refs/heads/%s" % branch, sha=branch_sha)
            self.logger.info("Branch created for repo <%s>: %s" % (repo_name, branch))
        base_tree = repo.get_git_tree(sha=branch_sha)
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(sha=branch_sha)
        commit = repo.create_git_commit(commit_msg, tree, [parent])
        branch_refs = repo.get_git_ref("heads/%s" % branch)
        branch_refs.edit(sha=commit.sha)
        self.logger.debug(
            (
                "Files pushed to remote repository <%s> (branch: %s) with commit "
                "SHA <%s>: %s" % (repo_name, branch, commit.sha, file_list)
            )
        )

        return commit.sha

    def delete_file(self, file_name, repo_name, branch):
        """Pushes a file into GitHub repository.

        Returns the commit ID (SHA format).

        :param file_name: Name of the affected file
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        commit_msg = "Delete %s file" % file_name
        repo = self.get_org_repository(repo_name)
        contents = self.get_file(file_name, repo_name, branch)
        if contents:
            repo.delete_file(contents.path, commit_msg, contents.sha, branch)
            self.logger.debug(
                "File %s deleted from repository <%s>" % (file_name, repo_name)
            )

    def create_branch(self, repo_name, branch_name, head_branch_name):
        """Creates a branch in the given Github repository.

        Returns a Repository object.

        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch_name: Name of the branch to create
        :param head_branch_name: Name of the branch to do the checkout from
        """
        repo = self.get_repository(repo_name)
        head_branch = repo.get_branch(head_branch_name)
        repo.create_git_ref(ref="refs/heads/" + branch_name, sha=head_branch.commit.sha)
        return repo

    def create_fork(
        self, upstream_repo_name, upstream_branch_name=None, org_name="eosc-synergy"
    ):
        """Creates a fork in the given Github organization.

        Returns a Repository object.

        :param upstream_repo_name: Name of the remote repo to fork (format:
            <user|org>/<repo_name>)
        :param upstream_branch_name: Name of the remote branch to fork
        :param org_name: Name of the Github organization to where the repo will be
            forked
        """
        upstream_repo = self.get_repository(upstream_repo_name)
        fork = None
        upstream_org_name = upstream_repo_name.split("/")[0]

        if upstream_org_name.lower() in [org_name]:
            self.logger.debug(
                "Upstream organization matches the target organization <%s>" % org_name
            )
        else:
            org = self.client.get_organization(org_name)
            fork = org.create_fork(upstream_repo)

        return fork

    def create_pull_request(
        self, repo_name, branch_name, upstream_repo_name, upstream_branch_name=None
    ):
        """Creates a pull request in the given upstream repository.

        Returns a Repository object.

        :param repo_name: Name of the source repository (format: <user|org>/<repo_name>)
        :param branch_name: Name of the source branch
        :param upstream_repo_name: Name of the remote repo to fork (format:
            <user|org>/<repo_name>)
        :param upstream_branch_name: Name of the remote branch to fork
        """
        upstream_repo = self.get_repository(upstream_repo_name)
        if not upstream_branch_name:
            upstream_branch_name = upstream_repo.default_branch
            self.logger.debug(
                (
                    "Branch not defined for the upstream repository. "
                    "Using default: %s" % upstream_branch_name
                )
            )
        body = """
        Add JePL folder structure via SQAaaS.

        FILES
          - [x] .sqa/config.yml
          - [x] .sqa/docker-compose.yml
          - [x] Jenkinsfile
        """
        _repo_org = repo_name.split("/")[0]
        head = ":".join([_repo_org, branch_name])

        self.logger.debug(
            "Creating pull request: %s (head) -> %s (base)"
            % (head, upstream_branch_name)
        )
        pr = upstream_repo.create_pull(
            title="Add CI/CD pipeline (JePL) in project <%s>" % upstream_repo_name,
            body=body,
            head=head,
            base=upstream_branch_name,
        )
        self.logger.debug(
            (
                "Pull request successfully created: %s (head) -> %s "
                "(base)" % (head, upstream_branch_name)
            )
        )
        return pr.raw_data

    def get_branch(self, repo_name, branch_name):
        """Look for a a branch in the given Github repository.

        Returns a Branch object.

        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch_name: Name of the branch to look for
        """
        repo = self.get_repository(repo_name)
        branch = None
        try:
            branch = repo.get_branch(branch_name)
        except GithubException as e:
            self.logger.error(e)
            self.logger.debug(
                "Branch not found in repository <%s>: %s" % (repo_name, branch_name)
            )
        return branch

    def get_repository(self, repo_name, repo_creds={}, raise_exception=False):
        """Return a Repository from a GitHub repo if it exists, False otherwise.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param repo_creds: Credentials needed for successful authentication
        :param raise_exception: Boolean to mark whether the UnknownObjectException shall
            be raised
        """
        _client = None
        if repo_creds:
            _user_id = repo_creds.get("user_id", "")
            _user_id_decrypted = crypto_utils.decrypt_str(_user_id)
            _token = repo_creds.get("token", "")
            _token_decrypted = crypto_utils.decrypt_str(_token)
            _client = Github(_user_id_decrypted, _token_decrypted)
        else:
            _client = self.client

        repo = False
        try:
            repo = _client.get_repo(repo_name)
        except UnknownObjectException as e:
            _reason = "Github exception: %s" % e
            self.logger.error(_reason)
            if raise_exception:
                raise SQAaaSAPIException(422, _reason)
        finally:
            if repo:
                self.logger.debug("Repository <%s> found" % repo_name)
            else:
                self.logger.warning("Repository <%s> not found!" % repo_name)
        return repo

    def get_owner(self, repo_name, repo_creds={}):
        """Gets the user that owns the repo.

        If found, it returns a NamedUser object.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param repo_creds: Credentials needed for successful authentication
        """
        if repo_creds:
            _user_id = repo_creds.get("user_id", "")
            _token = repo_creds.get("token", "")
            _client = Github(_user_id, _token)
        else:
            _client = self.client

        _owner_name, _repo_name = repo_name.split("/", 1)
        return _client.get_user(_owner_name)

    def get_org_repository(self, repo_name, org_name="eosc-synergy"):
        """Gets a repository from the given Github organization.

        If found, it returns the repo object, otherwise False

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        """
        _org_name, _repo_name = repo_name.split("/", 1)
        _repo_name = _repo_name.rsplit("/", 1)[0]  # remove any trailing slash
        org = self.client.get_organization(_org_name)
        try:
            return org.get_repo(_repo_name)
        except UnknownObjectException:
            return False

    def create_org_repository(
        self, repo_name, branch=GithubObject.NotSet, include_readme=True
    ):
        """Creates a GitHub repository for the current organization.

        Returns the Repository object.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param branch: Name of the branch
        :param include_readme: Whether to include README from template
        """
        _org_name, _repo_name = repo_name.split("/", 1)
        _repo_name = _repo_name.rsplit("/", 1)[0]  # remove any trailing slash
        repo = self.get_org_repository(repo_name)
        # Create repo
        if not repo:
            self.logger.debug("GitHub repository does not exist: %s" % repo_name)
            org = self.client.get_organization(_org_name)
            repo = org.create_repo(_repo_name)
            self.logger.debug("Created new GitHub repository: %s" % repo_name)
        else:
            self.logger.debug("GitHub repository already exists: %s" % repo_name)
        # Push README
        if include_readme:
            env = Environment(loader=PackageLoader("openapi_server", "templates"))
            template = env.get_template("README")
            file_data = template.render({"repo_name": repo_name})
            self.push_file(
                "README.md", file_data, "Add README", repo_name, branch=branch
            )

        return repo

    def delete_repo(self, repo_name):
        """Delete a GitHub repository.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        """
        repo = self.get_org_repository(repo_name)
        self.logger.debug("Deleting repository: %s" % repo_name)
        repo.delete()
        self.logger.debug("Repository <%s> successfully deleted" % repo_name)

    def get_commit_url(self, repo_name, commit_id):
        """Returns the commit URL (HTML format) that corresponds to the given
        commit ID.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param commit_id: SHA-based ID for the commit
        """
        repo = self.get_org_repository(repo_name)
        self.logger.debug("Getting commit data for SHA <%s>" % commit_id)
        return repo.get_commit(commit_id).html_url

    @_check_repo_args
    def get_description(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the description from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.description

    @_check_repo_args
    def get_languages(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the languages used in a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        languages = repo.get_languages()
        return sorted(languages, key=languages.get, reverse=True)

    @_check_repo_args
    def get_topics(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the topic list from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.get_topics()

    @_check_repo_args
    def get_stargazers(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the star count from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.get_stargazers().totalCount

    @_check_repo_args
    def get_watchers(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the watcher count from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.get_watchers().totalCount

    @_check_repo_args
    def get_contributors(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the contributor count from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.get_contributors().totalCount

    @_check_repo_args
    def get_forks(self, repo=None, repo_name=None, repo_creds={}):
        """Gets the fork count from a Github repository.

        :param repo: Repository object
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        return repo.get_forks().totalCount

    def get_avatar(self, repo_name, repo_creds={}):
        """Gets the avatar URL from a Github repository.

        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        """
        owner = self.get_owner(repo_name, repo_creds=repo_creds)
        return owner.avatar_url
