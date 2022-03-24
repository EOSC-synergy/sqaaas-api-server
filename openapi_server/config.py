import logging
import sys

from configparser import ConfigParser
from configparser import ExtendedInterpolation


logger = logging.getLogger('sqaaas.api.config')

BADGE_SECTION = 'badgr'
CI_SECTION = 'jenkins'


def init(config_file):
    global CONF
    global REPO_BACKEND

    CONF = ConfigParser(interpolation=ExtendedInterpolation())
    config_exists = CONF.read(config_file)
    if not config_exists:
        logger.error('Configuration file <%s> does not exist' % config_file)
        sys.exit(1)
    else:
        replace_sections_with_colon()
    REPO_BACKEND = CONF.defaults()['repository_backend']


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
                    new_value = value.replace(
                        old_section,
                        section_map[old_section]
                    )
                    CONF.set(section, option, new_value)


def replace_sections_with_colon():
    section_map = {}
    for section in CONF.sections():
        if section.count(':') > 1:
            new_section_name = section.replace(':', '__')
            section_map[section] = new_section_name
            replace_section(section, new_section_name)
    replace_values(section_map)


def get(key, fallback=None):
    return CONF.get('DEFAULT', key, fallback=fallback)


def get_repo(key, fallback=None):
    return CONF.get(REPO_BACKEND, key, fallback=fallback)


def get_ci(key, fallback=None):
    return CONF.get(CI_SECTION, key, fallback=fallback)


def get_badge(key, fallback=None):
    return CONF.get(BADGE_SECTION, key, fallback=fallback)


def get_badge_sub(subsection, key, fallback=None):
    return CONF.get(':'.join([BADGE_SECTION, subsection]), key, fallback=fallback)
