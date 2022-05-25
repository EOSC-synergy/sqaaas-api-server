import pytest


class MockJePLUtils:
    @staticmethod
    def push_files(*args, **kwargs):
        return 'commit_id'


@pytest.fixture
def mock_jepl_utils():
    return MockJePLUtils()
