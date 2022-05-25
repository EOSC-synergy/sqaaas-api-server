import pytest


class MockDB:
    db = {
        'dd7d8481-81a3-407f-95f0-a2f1cb382a4b': {
            'pipeline_repo': 'org/repo_name',
            'pipeline_repo_url': 'https://example.com/org/repo_name',
            'data': {
                'config': [
                    {
                        'data_json': {
                            'config': {
                                'project_repos': {},
                            },
                            'credentials': [],
                            'environment': {},
                            'sqa_criteria': {}
                        },
                        'data_yml': '',
                        'data_when': {},
                        'file_name': '',
                    },
                ],
                'composer': {
                    'data_json': {},
                    'data_yml': '',
                    'file_name': '',
                },
                'jenkinsfile': '',
                'commands_scripts': []
            }
        }
    }

    @staticmethod
    def load_content():
        return MockDB.db

    @staticmethod
    def get_entry(*args, **kwargs):
        return MockDB.db['dd7d8481-81a3-407f-95f0-a2f1cb382a4b']

    @staticmethod
    def update_jenkins(*args, **kwargs):
        return True


@pytest.fixture
def mock_db():
    return MockDB()
