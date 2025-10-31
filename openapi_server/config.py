# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
import sys
import os
from configparser import ConfigParser, ExtendedInterpolation

from openapi_server.exception import SQAaaSAPIException

logger = logging.getLogger("sqaaas.api.config")


BADGE_SECTION = "badgr"
CI_SECTION = "jenkins"
VCS_SECTION = "git"


def init(config_file):
    global CONF
    global REPO_BACKEND

    CONF = ConfigParser(interpolation=ExtendedInterpolation())
    config_exists = CONF.read(config_file)
    logger.info(config_exists)
    logger.info('texto1'+str(os.getcwd()))
    
    if not config_exists:
        logger.error("Configuration file <%s> does not exist" % config_file)
        sys.exit(1)
    else:
        replace_sections_with_colon()
    REPO_BACKEND = CONF.defaults()["repository_backend"]


def replace_section(old_section_name, new_section_name):
    CONF.add_section(new_section_name)
    for option, value in CONF.items(old_section_name, raw=True):
        CONF.set(new_section_name, option, value)
    CONF.remove_section(old_section_name)


def replace_values(section_map):
    for section in CONF.sections():
        for option, value in CONF.items(section, raw=True):
            for old_section in list(section_map):
                if value.find(old_section) != -1:
                    new_value = value.replace(old_section, section_map[old_section])
                    CONF.set(section, option, new_value)


def replace_sections_with_colon():
    section_map = {}
    for section in CONF.sections():
        if section.count(":") > 1:
            new_section_name = section.replace(":", "__")
            section_map[section] = new_section_name
            replace_section(section, new_section_name)
    replace_values(section_map)


def _get(section, key, fallback=None, fail_if_no_value=False):
    value = CONF.get(section, key, fallback=fallback)
    
    logger.info(value)#(key,value)
    logger.info(key)
    # value enforcement
    if fail_if_no_value and not value:
        raise SQAaaSAPIException(
            422, "Bad API configuration setting: no value defined for %s:%s" % (section, key)
        )
    # handle booleans
    if value in ["true", "True"]:
        value = True
    elif value in ["false", "False"]:
        value = False

    return value


def get(key, fallback=None):
    return _get("DEFAULT", key, fallback=fallback)


def get_repo(key, fallback=None):
    return _get(REPO_BACKEND, key, fallback=fallback, fail_if_no_value=True)


def get_ci(key, fallback='eosc-synergy-org'):
    print('eosc-synergy-org, hardcodeded as fallback')
    return _get(CI_SECTION, key, fallback=fallback)


def get_vcs(key, fallback=None):
    return _get(VCS_SECTION, key, fallback=fallback)


def get_badge(key, subsection_list=None, fallback=None):
    """Get option values from 'badgr' sections.

    :param key: section's key name
    :type key: str
    :param subsection_list: ordered subsection names to concat
    :type subsection_list: list
    :param fallback: fallback value
    :type fallback: str
    """
    if subsection_list:
        subsection_list.insert(0, BADGE_SECTION)
        section_name = "__".join(subsection_list)
    else:
        section_name = BADGE_SECTION
    return _get(section_name, key, fallback=fallback)


def get_service_deployment(iaas):
    """Get all values from service_deployment and given IaaS.

    :param iaas: iaas to get data from
    :type iaas: str
    """
    iaas_section = ":".join(["service_deployment", iaas])
    if not CONF.has_section(iaas_section):
        raise SQAaaSAPIException(
            422, "Could not find settings for IaaS site: %s" % iaas
        )

    data = dict(CONF.items("service_deployment"))
    data.update(dict(CONF.items(iaas_section)))

    return data
