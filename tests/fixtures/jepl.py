# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import pytest


class MockJePLUtils:
    @staticmethod
    def push_files(*args, **kwargs):
        return "commit_id"


@pytest.fixture
def mock_jepl_utils():
    return MockJePLUtils()
