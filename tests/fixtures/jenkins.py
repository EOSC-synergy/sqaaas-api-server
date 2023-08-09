# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

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
