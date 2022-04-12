import logging
import sys

from configparser import ConfigParser


logger = logging.getLogger('sqaaas.api.config')

BADGE_SECTION = 'badgr'
CI_SECTION = 'jenkins'


def init(config_file):
    global CONF
    global REPO_BACKEND

    CONF = ConfigParser()
    config_exists = CONF.read(config_file)
    if not config_exists:
        logger.error('Configuration file <%s> does not exist' % config_file)
        sys.exit(1)
    REPO_BACKEND = CONF.defaults()['repository_backend']


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
