# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
#
# SPDX-License-Identifier: GPL-3.0-only

import functools
import json
import logging
import requests
import time

from urllib.parse import urljoin


class BadgrUtils(object):
    """Class for handling requests to Badgr API."""

    def __init__(self, endpoint, access_user, access_pass, issuer_name):
        """BadgrUtils object definition.

        :param endpoint: Badgr endpoint URL
        :param access_user: Badgr's access user id
        :param access_pass: Badgr's user password
        :param issuer_name: String that corresponds to the Issuer name (as it
                            appears in Badgr web)
        """
        self.logger = logging.getLogger("sqaaas.api.badgr")
        self.endpoint = endpoint
        self.issuer_name = issuer_name
        self.access_user = access_user
        self.access_pass = access_pass

        try:
            access_token, refresh_token, expiry = self.get_token()
            if not access_token:
                raise Exception("Could not get access token from Badgr API!")
        except Exception as e:
            self.logger.debug(e)
        else:
            self.access_token = access_token
            self.refresh_token = refresh_token
            # Give a small buffer of 100 seconds
            self.access_token_expiration = time.time() + expiry - 100

    def get_token(self, refresh=False):
        """Obtains a Bearer-type token according to the provided credentials.

        Return a (access_token, refresh_token, expires_in) tuple.
        """
        path = "o/token"
        if refresh:
            if self.refresh_token:
                self.logger.debug(
                    "Refreshing user token using Badgr API: 'POST %s'" % path
                )
                data = {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token,
                }
            else:
                self.logger.warn("No refresh token found, cannot renew token")
        else:
            self.logger.debug("Getting user token from Badgr API: 'POST %s'" % path)
            data = {"username": self.access_user, "password": self.access_pass}
        try:
            r = requests.post(urljoin(self.endpoint, path), data=data)
            self.logger.debug("'POST %s' response content: %s" % (path, r.__dict__))
            r.raise_for_status()
            r_json = r.json()
            return (
                r_json["access_token"],
                r_json["refresh_token"],
                r_json["expires_in"],
            )
        except Exception as e:
            self.logger.debug(e)
            return None

    def refresh_token(f):
        """Decorator to handle the expiration of the Badgr API token"""

        @functools.wraps(f)
        def decorated_function(cls, *args, **kwargs):
            if time.time() > cls.access_token_expiration:
                cls.logger.debug("Reached token expiration date")
                access_token, refresh_token, expiry = cls.get_token()
                cls.access_token = access_token
                cls.refresh_token = refresh_token
                # Give a small buffer of 100 seconds
                cls.access_token_expiration = time.time() + expiry - 100
            return f(cls, *args, **kwargs)

        return decorated_function

    @refresh_token
    def get_issuers(self):
        """Gets all the Issuers associated with the current user."""
        path = "v2/issuers"
        headers = {"Authorization": "Bearer %s" % self.access_token}
        self.logger.debug("Getting issuers from Badgr API: 'GET %s'" % path)
        r = requests.get(urljoin(self.endpoint, path), headers=headers)
        self.logger.debug("'GET %s' response content: %s" % (path, r.__dict__))
        if r.ok:
            r_json = r.json()
            return r_json["result"]

    @refresh_token
    def get_badgeclasses(self, issuer_id):
        """Gets all the BadgeClasses associated with the given Issuer.

        :param issuer_id: issuer entityID to where this BadgeClass belongs.
        """
        path = "v2/issuers/%s/badgeclasses" % issuer_id
        headers = {"Authorization": "Bearer %s" % self.access_token}
        self.logger.debug(
            (
                "Getting BadgeClasses for Issuer <%s> from Badgr API: "
                "'GET %s'" % (issuer_id, path)
            )
        )
        r = requests.get(urljoin(self.endpoint, path), headers=headers)
        self.logger.debug("'GET %s' response content: %s" % (path, r.__dict__))
        if r.ok:
            r_json = r.json()
            return r_json["result"]

    def _get_matching_entity_id(self, entity_name, entity_type, **kwargs):
        """Get the ID of the specified entity type that matches the given name.

        :param entity_name: String that designates the entity (as it appears
            in Badgr web)
        :param entity_type: valid types are ('issuer', 'badgeclass')
        """
        if entity_type == "issuer":
            all_entities = self.get_issuers()
        elif entity_type == "badgeclass":
            all_entities = self.get_badgeclasses(**kwargs)

        entity_name_dict = dict(
            [
                [entity["name"], entity["entityId"]]
                for entity in all_entities
                if entity["name"] == entity_name
            ]
        )
        entity_name_list = entity_name_dict.keys()
        if len(entity_name_list) > 1:
            self.logger.warn(
                "Number of matching entities (type: %s) bigger than one: %s"
                % (entity_type, entity_name_list)
            )
            raise Exception(
                (
                    "Found more than one entity (type: %s) matching the given "
                    "name" % entity_type
                )
            )
        if len(entity_name_list) == 0:
            self.logger.warn(
                "Found 0 matches for entity name <%s> (type: %s)"
                % (entity_name, entity_type)
            )
            raise Exception("No matching entity name found (type: %s)" % entity_type)

        return entity_name_dict[entity_name]

    def get_badgeclass_entity(self, badgeclass_name):
        """Returns the BadgeClass entityID corresponding to the given Issuer
        and Badgeclass name combination.

        :param badgeclass_name: String that corresponds to the BadgeClass name
            (as it appears in Badgr web).
        """
        issuer_id = self._get_matching_entity_id(self.issuer_name, entity_type="issuer")
        badgeclass_id = self._get_matching_entity_id(
            badgeclass_name, entity_type="badgeclass", issuer_id=issuer_id
        )
        return badgeclass_id

    @refresh_token
    def issue_badge(
        self,
        badge_type,
        badgeclass_name,
        url,
        tag=[],
        commit_id=[],
        build_commit_id=None,
        build_commit_url=None,
        ci_build_url=None,
        sw_criteria=[],
        srv_criteria=[],
    ):
        """Issues a badge (Badgr's assertion).

        :param badge_type: String that identifies the type of badge
        :param badgeclass_name: String that corresponds to the BadgeClass
            name (as it appears in Badgr web)
        :param url: Upstream repository URL
        :param tag: Active tag of the upstream repository
        :param commit_id: SHA that corresponds to the upstream version being
            assessed
        :param build_commit_id: Commit ID assigned by git as a result of pushing
            the JePL files.
        :param build_commit_url: Absolute URL pointing to the commit that triggered
            the pipeline
        :param ci_build_url: Absolute URL pointing to the build results of the
            pipeline
        :param sw_criteria: List of fulfilled criteria codes from the Software
            baseline
        :param srv_criteria: List of fulfilled criteria codes from the Service
            baseline
        """
        badgeclass_id = self.get_badgeclass_entity(badgeclass_name)
        self.logger.info(
            (
                "BadgeClass entityId found for Issuer <%s> and BadgeClass "
                "<%s>: %s" % (self.issuer_name, badgeclass_name, badgeclass_id)
            )
        )
        path = "v2/badgeclasses/%s/assertions" % badgeclass_id
        headers = {
            "Authorization": "Bearer %s" % self.access_token,
            "Content-Type": "application/json",
        }
        # First item is the main repository
        main_repo = url.pop(0)
        main_repo_tag = tag.pop(0)
        main_repo_commit_id = commit_id.pop(0)
        # Assertion data: narrative
        narrative = None
        if badge_type in ["fair"]:
            narrative = "SQAaaS assessment results for dataset %s" % url
        else:
            narrative = (
                "SQAaaS assessment results for repository %s "
                "(commit: %s, branch/tag: %s)"
                % (main_repo, main_repo_commit_id, main_repo_tag)
            )
            if len(url) > 0:
                narrative += "\n Additional repositories being analysed:"
                for index in range(len(url)):
                    narrative += "\n\t- %s (commit: %s, branch/tag: %s)" % (
                        url[index],
                        commit_id[index],
                        tag[index],
                    )

        assertion_data = json.dumps(
            {
                "recipient": {"identity": main_repo, "hashed": True, "type": "url"},
                "narrative": narrative,
                "evidence": [
                    {"url": build_commit_url, "narrative": "SQAaaS build repository"},
                    {"url": ci_build_url, "narrative": "Build page from Jenkins CI"},
                ],
            }
        )
        self.logger.debug("Assertion data: %s" % assertion_data)

        self.logger.debug(
            (
                "Posting to get an Assertion of BadgeClass <%s> from Badgr API: "
                "'POST %s'" % (badgeclass_name, path)
            )
        )
        r = requests.post(
            urljoin(self.endpoint, path), headers=headers, data=assertion_data
        )
        r_json = r.json()
        self.logger.debug("Result from 'POST %s': %s" % (path, r_json))

        if r.ok:
            if len(r_json["result"]) > 1:
                self.logger.warn("More than one badge being issued")

            # Return the first result
            return r_json["result"][0]
        else:
            if "fieldErrors" in r_json.keys() and r_json["fieldErrors"]:
                self.logger.warn(
                    "Unsuccessful POST (Field errors): %s" % r_json["fieldErrors"]
                )
            if "validationErrors" in r_json.keys() and r_json["validationErrors"]:
                self.logger.warn(
                    (
                        "Unsuccessful POST (Validation errors): "
                        "%s" % r_json["validationErrors"]
                    )
                )
            r.raise_for_status()
