import pytest


class MockGitHubRepo(object):
    @staticmethod
    def default_branch():
        return 'main'


class MockGitHubUtils:
    @staticmethod
    def get_file(*args, **kwargs):
        return "file content"

    @staticmethod
    def get_repository(*args, **kwargs):
        return MockGitHubRepo()

    @staticmethod
    def get_commit_url(*args, **kwargs):
        return 'https://example.com/commit_url'


@pytest.fixture
def mock_github_utils():
    return MockGitHubUtils()
