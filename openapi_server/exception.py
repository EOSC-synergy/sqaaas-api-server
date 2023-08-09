# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

class SQAaaSAPIException(Exception):
    """Generic exception raised for errors in the API operation.

    :param code: HTTP error code
    :param message: explanation of the error
    """

    def __init__(self, http_code, message):
        self.http_code = http_code
        self.message = message
