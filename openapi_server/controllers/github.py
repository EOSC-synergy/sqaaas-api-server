import logging

from github import Github
from github import InputGitTreeElement
from github.GithubException import GithubException
from github.GithubException import UnknownObjectException
from jinja2 import Environment, PackageLoader

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
        self.logger = logging.getLogger('sqaaas.api.github')

    def get_repo_content(self, repo_name, branch, path='.'):
        """Gets the repository content from the given branch.

        Returns a List of ContentFile objects.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param branch: Name of the branch
        """
        repo = self.get_org_repository(repo_name)
        return repo.get_dir_contents(path, ref=branch)

    def get_file(self, file_name, repo_name, branch, fail_if_not_exists=False):
        """Gets the file's content from a GitHub repository.

        Returns a ContentFile object.

        :param file_name: Name of the file
        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param branch: Name of the branch
        :param fail_if_not_exists: Flag to indicate whether to fail if file is
            not found
        """
        repo = self.get_org_repository(repo_name)
        try:
            return repo.get_contents(file_name, ref=branch)
        except (UnknownObjectException, GithubException) as e:
            _reason = ((
                'Could not get file <%s> from GitHub repo <%s> (branch <%s>): '
                '%s' % (
                    file_name, repo_name, branch, str(e)
                )
            ))
            if fail_if_not_exists:
                self.logger.error(_reason)
                raise SQAaaSAPIException(422, _reason)
            else:
                self.logger.debug(_reason)
                return False

    def push_file(self, file_name, file_data, commit_msg, repo_name, branch):
        """Pushes a file into GitHub repository.

        Returns the commit ID (SHA format).

        :param file_name: Name of the affected file
        :param file_data: Contents of the file
        :param commit_msg: Message to use in the commit
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        repo = self.get_org_repository(repo_name)
        contents = self.get_file(file_name, repo_name, branch)
        r = {}
        if contents:
            self.logger.debug('File <%s> already exists in the repository, updating..' % file_name)
            r = repo.update_file(contents.path, commit_msg, file_data, contents.sha, branch)
        else:
            self.logger.debug('File <%s> does not currently exist in the repository, creating..' % file_name)
            r = repo.create_file(file_name, commit_msg, file_data, branch)
        return r['commit'].sha

    def push_files(self, file_list, commit_msg, repo_name, branch):
        """Pushes multiple files into a GitHub repository.

        Returns the commit ID (SHA format).

        :param file_list: List of dicts with the file name (<file_name>) and
            data (<file_data>)
        :param commit_msg: Message to use in the commit
        :param repo_name: Name of the repo to push (format:
            <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        repo = self.get_org_repository(repo_name)
        element_list = []
        for file_dict in file_list:
            file_name = file_dict['file_name']
            file_data = file_dict.get('file_data', None)
            to_delete = file_dict['delete']
            if to_delete:
                blob_sha = None
                self.logger.debug((
                    'File <%s> marked for deletion in the next '
                    'commit' % file_name
                ))
            else:
                blob_sha = repo.create_git_blob(file_data, "utf-8").sha
                self.logger.debug((
                    'File <%s> added for the next commit' % file_name
                ))
            element_list.append(InputGitTreeElement(
                path=file_name, mode='100644', type='blob', sha=blob_sha
            ))
        branch_sha = repo.get_branch(branch).commit.sha
        base_tree = repo.get_git_tree(sha=branch_sha)
        tree = repo.create_git_tree(element_list, base_tree)
        parent = repo.get_git_commit(sha=branch_sha)
        commit = repo.create_git_commit(commit_msg, tree, [parent])
        branch_refs = repo.get_git_ref("heads/%s" % branch)
        branch_refs.edit(sha=commit.sha)
        self.logger.debug((
            'Files pushed to remote repository <%s> (branch: %s) with commit '
            'SHA <%s>: %s' % (repo_name, branch, commit.sha, file_list)
        ))

        return commit.sha


    def delete_file(self, file_name, repo_name, branch):
        """Pushes a file into GitHub repository.

        Returns the commit ID (SHA format).

        :param file_name: Name of the affected file
        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch: Branch to push
        """
        commit_msg = 'Delete %s file' % file_name
        repo = self.get_org_repository(repo_name)
        contents = self.get_file(file_name, repo_name, branch)
        if contents:
            repo.delete_file(contents.path, commit_msg, contents.sha, branch)
            self.logger.debug('File %s deleted from repository <%s>' % (file_name, repo_name))

    def create_branch(self, repo_name, branch_name, head_branch_name):
        """Creates a branch in the given Github repository.

        Returns a Repository object.

        :param repo_name: Name of the repo to push (format: <user|org>/<repo_name>)
        :param branch_name: Name of the branch to create
        :param head_branch_name: Name of the branch to do the checkout from
        """
        repo = self.get_repository(repo_name)
        head_branch = repo.get_branch(head_branch_name)
        repo.create_git_ref(
            ref='refs/heads/' + branch_name,
            sha=head_branch.commit.sha)
        return repo

    def create_fork(self, upstream_repo_name, upstream_branch_name=None, org_name='eosc-synergy'):
        """Creates a fork in the given Github organization.

        Returns a Repository object.

        :param upstream_repo_name: Name of the remote repo to fork (format: <user|org>/<repo_name>)
        :param upstream_branch_name: Name of the remote branch to fork
        :param org_name: Name of the Github organization to where the repo will be forked
        """
        upstream_repo = self.get_repository(upstream_repo_name)
        fork = None
        upstream_org_name = upstream_repo_name.split('/')[0]

        if upstream_org_name.lower() in [org_name]:
            self.logger.debug('Upstream organization matches the target organization <%s>' % org_name)
        else:
            org = self.client.get_organization(org_name)
            fork = org.create_fork(upstream_repo)

        return fork

    def create_pull_request(self,
                            repo_name, branch_name,
                            upstream_repo_name, upstream_branch_name=None):
        """Creates a pull request in the given upstream repository.

        Returns a Repository object.

        :param repo_name: Name of the source repository (format: <user|org>/<repo_name>)
        :param branch_name: Name of the source branch
        :param upstream_repo_name: Name of the remote repo to fork (format: <user|org>/<repo_name>)
        :param upstream_branch_name: Name of the remote branch to fork
        """
        upstream_repo = self.get_repository(upstream_repo_name)
        if not upstream_branch_name:
            upstream_branch_name = upstream_repo.default_branch
            self.logger.debug(('Branch not defined for the upstream repository. '
                               'Using default: %s' % upstream_branch_name))
        body = '''
        Add JePL folder structure via SQAaaS.

        FILES
          - [x] .sqa/config.yml
          - [x] .sqa/docker-compose.yml
          - [x] Jenkinsfile
        '''
        _repo_org = repo_name.split('/')[0]
        head = ':'.join([_repo_org, branch_name])

        self.logger.debug('Creating pull request: %s (head) -> %s (base)' % (
            head, upstream_branch_name))
        pr = upstream_repo.create_pull(
            title='Add CI/CD pipeline (JePL) in project <%s>' % upstream_repo_name,
            body=body,
            head=head,
            base=upstream_branch_name)
        self.logger.debug(('Pull request successfully created: %s (head) -> %s '
                           '(base)' % (head, upstream_branch_name)))
        return pr.raw_data

    def get_repository(self, repo_name, raise_exception=False):
        """Return a Repository from a GitHub repo if it exists, False otherwise.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param raise_exception: Boolean to mark whether the UnknownObjectException shall be raised
        """
        repo = False
        try:
            repo = self.client.get_repo(repo_name)
        except UnknownObjectException as e:
            self.logger.debug('Unknown Github exception: %s' % e)
            if raise_exception:
                raise e
        finally:
            if repo:
                self.logger.debug('Repository <%s> found' % repo_name)
            else:
                self.logger.debug('Repository <%s> not found!' % repo_name)
        return repo

    def get_org_repository(self, repo_name, org_name='eosc-synergy'):
        """Gets a repository from the given Github organization.

        If found, it returns the repo object, otherwise False

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        """
        _org_name, _repo_name = repo_name.split('/')
        org = self.client.get_organization(_org_name)
        try:
            return org.get_repo(_repo_name)
        except UnknownObjectException:
            return False

    def create_org_repository(self, repo_name, include_readme=True):
        """Creates a GitHub repository for the current organization.

        Returns the Repository object.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        """
        _org_name, _repo_name = repo_name.split('/')
        repo = self.get_org_repository(repo_name)
        if not repo:
            org = self.client.get_organization(_org_name)
            repo = org.create_repo(_repo_name)
            self.logger.debug('GitHub repository <%s> does not exist, creating..' % repo_name)
            if include_readme:
                # Get README
                env = Environment(
                    loader=PackageLoader('openapi_server', 'templates')
                )
                template = env.get_template('README')
                file_data = template.render({
                    'repo_name': repo_name
                })
                branch = repo.default_branch
                self.push_file(
                    'README.md', file_data, 'Add README', repo_name, branch
                )
        else:
            self.logger.debug('GitHub repository <%s> already exists' % repo_name)
        return repo

    def delete_repo(self, repo_name):
        """Delete a GitHub repository.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        """
        repo = self.get_org_repository(repo_name)
        self.logger.debug('Deleting repository: %s' % repo_name)
        repo.delete()
        self.logger.debug('Repository <%s> successfully deleted' % repo_name)

    def get_commit_url(self, repo_name, commit_id):
        """Returns the commit URL (HTML format) that corresponds to the given commit ID.

        :param repo_name: Name of the repo (format: <user|org>/<repo_name>)
        :param commit_id: SHA-based ID for the commit
        """
        repo = self.get_org_repository(repo_name)
        self.logger.debug('Getting commit data for SHA <%s>' % commit_id)
        return repo.get_commit(commit_id).html_url
