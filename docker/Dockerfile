# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

FROM python:3.10-bullseye
MAINTAINER Pablo Orviz <orviz@ifca.unican.es>

RUN mkdir /sqaaas-api-server
COPY . /sqaaas-api-server
WORKDIR /sqaaas-api-server
RUN pip3 install -r requirements.txt
RUN pip3 install .

COPY ./docker/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
