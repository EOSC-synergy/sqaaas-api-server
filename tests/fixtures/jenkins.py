import pytest


class MockJenkinsUtils:
    @staticmethod
    def format_job_name(*args, **kwargs):
        return 'job_name'

    @staticmethod
    def exist_job(*args, **kwargs):
        return False

    @staticmethod
    def scan_organization(*args, **kwargs):
        return True


@pytest.fixture
def mock_jenkins_utils():
    return MockJenkinsUtils()
