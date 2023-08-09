# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging

from openapi_server import config
from openapi_server.controllers.badgr import BadgrUtils
from openapi_server.controllers.git import GitUtils
from openapi_server.controllers.github import GitHubUtils
from openapi_server.controllers.jenkins import JenkinsUtils


SUPPORTED_PLATFORMS = {
    'github': 'https://github.com'
}
REPOSITORY_BACKEND = config.get(
    'repository_backend'
)
TOKEN_GH_FILE = config.get_repo(
    'token', fallback='/etc/sqaaas/.gh_token')
GITHUB_ORG = config.get_repo('organization')

TOKEN_JK_FILE = config.get_ci(
    'token', fallback='/etc/sqaaas/.jk_token')
JENKINS_URL = config.get_ci('url')
JENKINS_USER = config.get_ci('user')
JENKINS_GITHUB_ORG = config.get_ci('github_organization_name')

TOKEN_BADGR_FILE = config.get_badge(
    'token', fallback='/etc/sqaaas/.badgr_token')
BADGR_URL = config.get_badge('url')
BADGR_USER = config.get_badge('user')
BADGR_ISSUER = config.get_badge('issuer')

logger = logging.getLogger('sqaaas.api.controller')


def init_utils():
    # Instance of code repo backend object
    with open(TOKEN_GH_FILE,'r') as f:
        token = f.read().strip()
    logger.debug('Loading GitHub token from local filesystem')
    gh_utils = GitHubUtils(token)
    git_utils = GitUtils(token)

    # Instance of CI system object
    with open(TOKEN_JK_FILE,'r') as f:
        jk_token = f.read().strip()
    logger.debug('Loading Jenkins token from local filesystem')
    jk_utils = JenkinsUtils(JENKINS_URL, JENKINS_USER, jk_token)

    # Instance of Badge issuing service object
    with open(TOKEN_BADGR_FILE,'r') as f:
        badgr_token = f.read().strip()
    logger.debug('Loading Badgr password from local filesystem')
    badgr_utils = BadgrUtils(BADGR_URL, BADGR_USER, badgr_token, BADGR_ISSUER)

    return (git_utils, gh_utils, jk_utils, badgr_utils)
