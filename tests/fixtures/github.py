# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest


class MockGitHubRepo(object):
    @staticmethod
    def default_branch():
        return "main"


class MockGitHubUtils:
    @staticmethod
    def get_file(*args, **kwargs):
        return "file content"

    @staticmethod
    def get_repository(*args, **kwargs):
        return MockGitHubRepo()

    @staticmethod
    def get_commit_url(*args, **kwargs):
        return "https://example.com/commit_url"


@pytest.fixture
def mock_github_utils():
    return MockGitHubUtils()
