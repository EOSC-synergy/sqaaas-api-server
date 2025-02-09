<!--
SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>

SPDX-License-Identifier: GPL-3.0-only
-->

# SQAaaS OpenAPI server

[![SQAaaS badge shields.io](https://img.shields.io/badge/sqaaas%20software-silver-lightgrey)](https://api.eu.badgr.io/public/assertions/U-GSO-5DS-qHf5I3MernmQ "SQAaaS silver badge achieved")
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![REUSE status](https://api.reuse.software/badge/git.fsfe.org/reuse/api)](https://api.reuse.software/info/git.fsfe.org/reuse/api)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

#### Achievements
[![SQAaaS badge](https://github.com/EOSC-synergy/SQAaaS/raw/master/badges/badges_150x116/badge_software_silver.png)](https://api.eu.badgr.io/public/assertions/U-GSO-5DS-qHf5I3MernmQ "SQAaaS silver badge achieved")

## Founding institutions
<p float="left">
    <img src="images/logo-csic.png" height="50" hspace="10"/>
    <img src="images/logo-UPV.png" height="50" hspace="10"/>
    <img src="images/logo-LIP.png" height="50" hspace="10"/>
</p>

## Overview
API server implementation for the SQA-as-a-Service (SQAaaS) platform.

### API First strategy
The SQAaaS API implementation follows an API First strategy, where changes in the specification
are subsequently coded.

#### The OpenAPI specification
The SQAaaS API specification is maintained in a separate [repository](https://github.com/eosc-synergy/sqaaas-api-spec).

#### OpenAPI Generator
Whenever the specification changes the code is generated by the [OpenAPI Generator](https://openapi-generator.tech) project.
The SQAaaS API uses Python's [Connexion](https://github.com/zalando/connexion) library on top of [aiohttp](https://docs.aiohttp.org/en/stable/).

The generator does not modify the set of files maintained in the [.openapi-generator-ignore](.openapi-generator-ignore).

## Requirements
- Python 3.9.2+
- Dependencies: [requirements.txt](requirements.txt)

## Usage
To run the API server, please execute the following from the root directory:

```
$ pip3 install .
$ sqaaas_api_server --help
usage: sqaaas_api_server [-h] [-c CONFIG_FILE] [-p PORT] [-d]

SQAaaS API server.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config CONFIG_FILE
                        Main configuration file (default: /etc/sqaaas/sqaaas.ini). For a complete example, please check </usr/local/lib/python3.8/dist-packages/etc/sqaaas.ini.sample>
  -p PORT, --port PORT  Port number to be used when exposing the API server (default: 8080)
  -d, --debug           Set DEBUG log level
```

In order to run successfully, the SQAaaS API server requires the presence of a general configuration file, by default in `/etc/sqaaas/sqaaas.ini`. The Python package is distributed with a sample configuration (`sqaaas.ini.sample`).

Assuming the default port 8080 is used, use Swagger UI by opening your browser to here:

```
http://localhost:8080/v1/ui/
```

The SQAaaS OpenAPI definition can be accessed through:

```
http://localhost:8080/v1/openapi.json
```

### Docker
Different SQAaaS API server versions will be made available as Docker images through [Docker Hub site](https://hub.docker.com/orgs/eoscsynergy/repositories).

The following command will execute the given version of the SQAaaS API server container, having the required files in the `my-sqaaas-api-environ` folder:
```
$ docker run -v <my-sqaaas-api-environ>:/etc/sqaaas -t eoscsynergy/sqaaas-api-server:<version>
```

## Development
### Deploy in editable mode
Within the root path, execute:
```
$ pip3 install -e .
```

### Running tests

To launch the integration tests, use pytest:
```
sudo pip install -r test-requirements.txt
pytest
```
### Building the Docker image
In the root path of the current repository, execute:
```
$ docker build -t eoscsynergy/sqaaas-api-server:<version> -f docker/Dockerfile .
```

## Acknowledgements
This software has been developed within the EOSC-Synergy project that has received funding from the European Union's Horizon 2020 research and innovation programme under grant agreement number 857647.

<p align="center">
  <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT1WF4g5KH3PnQE_Ve10QFRS-gZ0NpCQ7Qr-_km1RqnOCEF1fQt" hspace="20">
  <img src="images/logo-SYNERGY.png" height="100">
</p>
