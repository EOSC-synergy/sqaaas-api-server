# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import copy
import json
import logging
import pathlib

import yaml
from openapi_server import config
from openapi_server.controllers import utils as ctls_utils
from openapi_server.controllers.jepl import JePLUtils

DB_FILE = pathlib.Path(config.get("db_file", fallback="/sqaaas/sqaaas.json"))
logger = logging.getLogger("sqaaas.api.controller.db")


def load_content():
    data = {}
    if DB_FILE.exists():
        data = json.loads(DB_FILE.read_text(encoding="utf-8"))
    return data


def store_content(data):
    try:
        DB_FILE.parent.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        logger.debug("DB file path: parent folder already exists")
    else:
        logger.debug("DB file path: parent folder created")

    DB_FILE.write_text(json.dumps(data), encoding="utf-8")


def print_content():
    db = load_content()
    logger.debug("Current DB content: %s" % list(db))


def add_entry(
    pipeline_id,
    pipeline_repo,
    pipeline_repo_url,
    body,
    pipeline_repo_branch=None,
    files_to_commit=[],
    report_to_stdout=False,
):
    """Adds a standard entry in the DB.

    Each entry has both the raw data from the request and the processed data, as treated
    internally by the API. An entry is indexed by the pipeline ID

    |-- <pipeline_id>: ID of the pipeline     |-- 'pipeline_repo': [String] Name of the
    build/assessment repository in the remote platform.     |-- 'pipeline_repo_url':
    [String] Absolute URL of the build/assessment repository in the remote platform. |--
    'pipeline_repo_branch': [String] Name of the branch in the build/assessment
    repository.     |-- 'data': [Dict] Internal representation of the data.         |--
    'config': [List] Each independent JePL-compliant config data.             |--
    'data_json'             |-- 'data_yml'             |-- 'data_when'             |--
    'file_name'         |-- 'composer': [Dict] JePL-compliant composer data. |--
    'data_json'             |-- 'data_yml'             |-- 'file_name'         |--
    'jenkinsfile': [String] Jenkins-compliant pipeline.         |-- 'commands_scripts':
    [List] Scripts generated for the commands builder.         |-- 'files_to_commit':
    [List] Additional files to commit to the pipeline repo.     |-- 'raw_request':
    [Dict] API spec representation (from JSON request).     |-- 'jenkins': [Dict]
    Jenkins-related data about the pipeline execution.         |-- 'job_name'     |--
    'tools': [Dict] Tool-related data (per-criterion mapping)         |--
    'criterion_id': tools     |-- 'badge': [Dict] Badge data for each badge type in
    [software, services, fair]     |-- 'repo_settings': [Dict] Information (metadata)
    about the code repository     |-- 'qaa': [Dict] Assessment results         |--
    'digital_object_type': [String] type of assessment (e.g. 'source code', 'service',
    'fair')         |-- 'criteria_filtered': [Dict] criteria being filtered out

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param pipeline_repo: URL of the remote repository for the Jenkins integration.
    :param body: Raw JSON coming from the HTTP request.
    :param report_to_stdout: Flag to indicate whether the pipeline shall print via via
        stdout the reports produced by the tools (required by QAA module)
    """
    raw_request = copy.deepcopy(body)
    config_json, composer_json, jenkinsfile_data = ctls_utils.get_pipeline_data(body)
    (
        config_data_list,
        composer_data,
        jenkinsfile,
        commands_script_list,
        additional_files_to_commit,
        tool_criteria_map,
    ) = JePLUtils.compose_files(
        config_json, composer_json, report_to_stdout=report_to_stdout
    )

    db = load_content()
    db[pipeline_id] = {
        "pipeline_repo": pipeline_repo,
        "pipeline_repo_url": pipeline_repo_url,
        "pipeline_repo_branch": pipeline_repo_branch,
        "data": {
            "config": config_data_list,
            "composer": composer_data,
            "jenkinsfile": jenkinsfile,
            "commands_scripts": commands_script_list,
            "additional_files_to_commit": additional_files_to_commit,
        },
        "raw_request": raw_request,
        "tools": tool_criteria_map,
    }
    store_content(db)


def get_entry(pipeline_id=None):
    """If pipeline_id is given returns a Dict with the data from the given ID,
    otherwise it returns a Dict with all the existing entries from the DB indexed
    by the ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    """
    db = load_content()
    if pipeline_id:
        logger.debug("Loading pipeline <%s> from DB" % pipeline_id)
        r = db[pipeline_id]
    else:
        logger.debug("Loading ALL existing pipelines from DB (including IDs)")
        r = dict(
            [(pipeline_id, pipeline_data) for pipeline_id, pipeline_data in db.items()]
        )

    return r


def del_entry(pipeline_id):
    """Deletes the given pipeline ID entry from the DB.

    :param pipeline_id: UUID-format identifier for the pipeline.
    """
    db = load_content()
    db.pop(pipeline_id)
    store_content(db)
    logger.debug("Pipeline <%s> removed from DB" % pipeline_id)


def update_entry(pipeline_id, **kwargs):
    """Updates any of the root properties for the given pipeline ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param kwargs: map with the required properties and values to update.
    """
    db = load_content()
    for k, v in kwargs.items():
        if k in db[pipeline_id].keys():
            db[pipeline_id][k] = v
    store_content(db)
    logger.debug(
        "Updated values in DB for pipeline <%s>. Keys updated: %s"
        % (pipeline_id, list(kwargs))
    )


def update_jenkins(
    pipeline_id,
    jk_job_name,
    commit_id,
    commit_url,
    build_item_no=None,
    build_no=None,
    build_url=None,
    scan_org_wait=False,
    build_status="NOT_EXECUTED",
    creds_tmp=[],
    creds_folder=None,
    issue_badge=False,
):
    """Updates the Jenkins data in the DB for the given pipeline ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param jk_job_name: Name of the pipeline job in Jenkins.
    :param commit_id: Commit ID assigned by git as a result of pushing the JePL files.
    :param commit_url: Commit URL of the git repository platform.
    :param build_item_no: Jenkins' job build item number, i.e. previous to the actual
        build number.
    :param build_no: Jenkins' job build number.
    :param build_url: Jenkins' job build URL.
    :param scan_org_wait: Boolean that represents whether the Jenkins' scan organisation
        has been triggered.
    :param build_status: String representing the build status.
    :param creds_tmp: List of temporary credentials associated with the job.
    :param issue_badge: Flag to indicate whether to issue a badge when the pipeline
        succeeds.
    """
    db = load_content()
    db[pipeline_id]["jenkins"] = {
        "job_name": jk_job_name,
        "issue_badge": issue_badge,
        "build_info": {
            "commit_id": commit_id,
            "commit_url": commit_url,
            "item_number": build_item_no,
            "number": build_no,
            "url": build_url,
            "status": build_status,
        },
        "scan_org_wait": scan_org_wait,
        "creds_tmp": creds_tmp,
        "creds_folder": creds_folder,
    }
    store_content(db)
    logger.debug(
        "Jenkins data updated for pipeline <%s>: %s"
        % (pipeline_id, db[pipeline_id]["jenkins"])
    )


def add_badge_data(pipeline_id, badge_data):
    """Updates the Badgr data in the DB for the given pipeline ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param badge_data: Badge data for the pipeline.
    """
    db = load_content()
    db[pipeline_id]["badge"] = badge_data
    store_content(db)
    logger.debug(
        "Badge data added for pipeline <%s>: %s"
        % (pipeline_id, db[pipeline_id]["badge"])
    )


def add_assessment_data(pipeline_id, assessment_data):
    """Updates the QAA-related data in the DB for the given pipeline ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param assessment_data: Data use for the QAA module.
    """
    db = load_content()
    db[pipeline_id]["qaa"] = assessment_data
    store_content(db)
    logger.debug(
        "QAA data added in DB for pipeline <%s>: %s"
        % (pipeline_id, db[pipeline_id]["qaa"])
    )


def add_tool_data(pipeline_id, criteria_tools):
    """Updates criteria's tools in the DB for the given pipeline ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param criteria_tools: Tool data from each criterion.
    """
    db = load_content()
    db[pipeline_id]["tools"] = criteria_tools
    store_content(db)
    logger.debug(
        "Criteria's tool data added in DB for pipeline <%s>: %s"
        % (pipeline_id, db[pipeline_id]["tools"])
    )


def add_repo_settings(pipeline_id, repo_settings):
    """Stores the information about the code repository.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param repo_settings: Information (metadata) about the code repository.
    """
    db = load_content()
    db[pipeline_id]["repo_settings"] = repo_settings
    store_content(db)
    logger.debug(
        (
            "Repository information (metadata) updated in DB for pipeline "
            "<%s>: %s" % (pipeline_id, db[pipeline_id]["repo_settings"])
        )
    )


def update_environment(pipeline_id, envvar_data):
    """Updates the config.yml's environment data in the DB for the given pipeline
    ID.

    :param pipeline_id: UUID-format identifier for the pipeline.
    :param envvar_data: Dictionary containing new environment variables to set.
    """
    db = load_content()
    for config_file in db[pipeline_id]["data"]["config"]:
        if "environment" not in list(config_file["data_json"]):
            config_file["data_json"]["environment"] = envvar_data
        else:
            config_file["data_json"]["environment"].update(envvar_data)
        config_file["data_yml"] = yaml.dump(config_file["data_json"])
    store_content(db)
    logger.debug(
        "config.yml's environment data updated in DB for pipeline <%s>: %s"
        % (pipeline_id, db[pipeline_id]["data"]["config"])
    )
