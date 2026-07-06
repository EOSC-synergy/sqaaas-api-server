# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
from urllib.parse import quote_plus, urljoin

import jenkins
import requests
import timeout_decorator
from bs4 import BeautifulSoup
from jinja2 import Environment, PackageLoader

from openapi_server.exception import SQAaaSAPIException


# original create credential

CREATE_CREDENTIAL_ORG = ("credentials/store/system/domain/_/createCredentials")
'''
CREATE_CREDENTIAL_ORG = (
    "/job/%(folder_name)s/credentials/store/folder/"
    "domain/%(domain_name)s/createCredentials"
)
'''

DELETE_CREDENTIAL_ORG = (
    "credentials/store/system/domain/"
    "%(domain_name)s/credential/%(credential_id)s/config.xml"
)


class JenkinsUtils(object):
    """Class for handling requests to Jenkins API.

    Support only for token-based access.
    """

    def __init__(self, endpoint, access_user, access_token):
        """JenkinsUtils object definition.

        :param endpoint: Jenkins endpoint URL
        :param access_user: Jenkins's access user
        :param access_token: Jenkins's access token
        """
        self.endpoint = endpoint
        self.access_user = access_user
        self.access_token = access_token
        self.server = jenkins.Jenkins(
            self.endpoint, username=self.access_user, password=self.access_token
        )
        self.logger = logging.getLogger("sqaaas.api.jenkins")

    @staticmethod
    def format_job_name(job_name):
        """Format job name according to what is expected by Jenkins.

        Slash symbol '/' is double-encoded: ''%252F' instead of '%2F'

        :param job_name: Name of the Jenkins job
        """
        return quote_plus(job_name.replace("/", "%2F"))

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def scan_organization(self, org_name, job_name=""):
        path = "/job/%s/build?delay=0" % org_name
        label = "SCAN_ORGANIZATION"
        if job_name:
            path = "/job/%s/job/%s/build?delay=0" % (org_name, job_name)
            label = "SCAN_ORGANIZATION_JOB"
            self.logger.debug("Requested to scan a single job. Using path: %s" % path)
        else:
            self.logger.debug(
                "Requested to scan the entire organization. Using path: %s" % path
            )
        r = requests.post(
            urljoin(self.endpoint, path), auth=(self.access_user, self.access_token)
        )
        if not r.ok:
            self.logger.error(
                "Could not trigger %s in Jenkins endpoint: %s" % (label, self.endpoint)
            )
        else:
            self.logger.debug(
                "Successfully triggered %s in Jenkins endpoint: %s"
                % (label, self.endpoint)
            )
        r.raise_for_status()

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def get_job_info(self, name, depth=0, no_branch=False):
        """Return job information.

        :param name: full job name as labelled by Jenkins.
        :param depth: number that indicates depth level for Jenkins.
        :param no_branch: flag to return the presence of the job regardless of the
            branch.
        """
        job_info = {}
        job_name_list = []

        _org, _repo, _branch = name.split("/")
        for folder in self.server.get_jobs(folder_depth=1):
            if folder["name"] in [_org]:
                job_name_list = [job["name"] for job in folder["jobs"]]
        job_without_branch_exists = False
        # Try case-insensitive (Jenkins org-folder limitation)
        if _repo not in job_name_list:
            self.logger.debug("Trying case-insensitive match with job: <%s>" % name)
            for job_name in job_name_list:
                if _repo.lower() in [job_name.lower()]:
                    job_without_branch_exists = True
                    name = "/".join([_org, job_name, _branch])
                    self.logger.debug("Using new job name: <%s>" % name)
                    break
        else:
            job_without_branch_exists = True
        if no_branch:
            return job_without_branch_exists
        try:
            job_info = self.server.get_job_info(name, depth=depth)
            '''self.logger.debug(
                "Information for job <%s> obtained from Jenkins: %s" % (name, job_info)
            )'''
        except jenkins.JenkinsException as e:
            self.logger.error(
                "No info could be fetched for Jenkins job <%s>: %s" % (name, str(e))
            )
        return job_info

    def exist_job(self, job_name, no_branch=False):
        """Check whether given job is defined in Jenkins.

        :param job_name: job name including folder/s, name & branch
        :param no_branch: flag to indicate whether to check for the branch name in the
            job
        """
        return self.get_job_info(job_name, no_branch=no_branch)

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def build_job(self, full_job_name):
        """Build existing job.

        :param full_job_name: job name including folder/s, name & branch
        """
        item_no = None
        try:
            item_no = self.server.build_job(full_job_name)
        except Exception:
            self.logger.warning("Job <%s> has not been queued yet" % full_job_name)
        else:
            self.logger.debug("Triggered job build (queue item number: %s)" % item_no)
        return item_no

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    async def get_queue_item(self, item_no):
        """Get the status of the build item in the Jenkins queue.

        :param item_no: item number in the Jenkins queue.
        """
        queue_data = self.server.get_queue_item(item_no)
        executable_data = None
        if "executable" not in list(queue_data):
            self.logger.debug(
                "Waiting for job to start. Queue item: %s" % queue_data["url"]
            )
        else:
            executable_data = queue_data["executable"]
            if executable_data:
                self.logger.debug(
                    "Job started the execution (url: %s, number: %s)"
                    % (executable_data["url"], executable_data["number"])
                )
        return executable_data

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def get_build_info(self, full_job_name, build_no, depth=0):
        self.logger.debug(
            "Getting status for job <%s> (build_no: %s)" % (full_job_name, build_no)
        )
        build_info = None
        try:
            build_info = self.server.get_build_info(
                full_job_name, build_no, depth=depth
            )
            self.logger.debug("Build info as obtained by Jenkins: %s" % build_info)
        except Exception:
            self.logger.warning(
                "Could not find build info for #%s (job: <%s>)"
                % (build_no, full_job_name)
            )
        return build_info

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def stop_build(self, full_job_name, build_no):
        """Stop a build from a job.

        :param full_job_name: job name including folder/s, name & branch
        :param build_no: build number.
        """
        self.logger.debug(
            "Stopping build for job <%s> (build_no: %s)" % (full_job_name, build_no)
        )
        return self.server.stop_build(full_job_name, build_no)

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def delete_job(self, full_job_name):
        self.logger.debug("Deleting Jenkins job: %s" % full_job_name)
        self.server.delete_job(full_job_name)
        self.logger.debug("Jenkins job <%s> successfully deleted" % full_job_name)

    @timeout_decorator.timeout(
        100,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def get_stage_data(self, job_name, build_no):
        """Get the info from the pipeline stages.

        Via Pipeline Stage View API at
        https://github.com/jenkinsci/pipeline-stage-view-plugin

        :param job_name: job name including folder/s, name & branch
        :param build_no: build number.
        """
        items = list(map("/job/".__add__, job_name.split("/")))
        jenkins_job_name = "".join(items)

        def do_request(path, append=False, json_payload=True):
            if append:
                target_path = "%s/%s/%s" % (jenkins_job_name, build_no, path)
            else:
                target_path = path
            self.logger.debug("Request to <%s>" % target_path)
            requests.packages.urllib3.disable_warnings()
            r = requests.post(
                urljoin(self.endpoint, target_path),
                auth=(self.access_user, self.access_token),
                verify=False,
            )
            if json_payload:
                try:
                    out = r.json()
                except ValueError:
                    _reason = (
                        "Could not obtain a JSON response payload from Jenkins path: %s"
                        % target_path
                    )
                    self.logger.error(_reason)
                    raise SQAaaSAPIException(502, _reason)
            else:
                out = r
            print('jenkins271')
            #print(r.text)
            return out

        def get_text(html_text):
            soup = BeautifulSoup(html_text, "html.parser")
            console_tags = soup.find_all("pre", class_="console-output")
            if len(console_tags) > 1:
                self.logger.warn(
                    (
                        'Detected multiple <pre class="console-output"> tags!'
                        "Falling back to the first one, ignoring the rest"
                    )
                )
            console_output = console_tags[0]
            return console_output.getText()

        def process_stdout(stdout):
            stdout = stdout.strip()
            lines = stdout.split("\n")
            cmd = lines.pop(0)
            if not cmd.startswith("+"):
                self.logger.warn(
                    (
                        "Could not identify the command (identified by '+' "
                        "prefix) in string <%s>. No change done to stdout" % cmd
                    )
                )
                lines.insert(0, cmd)
                cmd = ""
            output_text = "\n".join(lines)
            return (cmd, output_text)

        data = do_request("/wfapi/describe", append=True)
        stage_name_prefixes = ("QC.", "SvcQC.")
        qc_stages = [
            stage
            for stage in data["stages"]
            if stage["name"].startswith(stage_name_prefixes)
        ]
        stage_describe_endpoints = [
            stage["_links"]["self"]["href"] for stage in qc_stages
        ]
        self.logger.info(
            "Found %s stage/s that run quality criteria" % len(stage_describe_endpoints)
        )

        criteria_data_list = []
        for qa_stage in stage_describe_endpoints:
            data = do_request(qa_stage)
            name = data["name"]
            criterion = name.split()[0]
            status = data["status"]
            # Use 'console' endpoint to be subsequently parsed with
            # beautifulsoup4. Unexpected syntaxes have been seen when using
            # instead <text> property from 'log' endpoint
            console_log_endpoint = data["stageFlowNodes"][0]["_links"]["console"][
                "href"
            ]
            console_log_endpoint += "?consoleFull"
            data = do_request(console_log_endpoint, json_payload=False)
            stdout = get_text(data.text)
            cmd, output_text = process_stdout(stdout)
            if not cmd:
                _reason = (
                    "Could not get the command for the stage: output text "
                    "might be truncated by Jenkins, consider to set/increase "
                    "Pipeline REST API Plugin's maxReturnChars property (see "
                    "https://github.com/jenkinsci/pipeline-stage-view-plugin)"
                )
                self.logger.error(_reason)
                raise SQAaaSAPIException(502, _reason)
            criteria_data_list.append(
                {
                    "name": name,
                    "criterion": criterion,
                    "status": status,
                    "stdout_command": cmd,
                    "stdout_text": output_text,
                    "url": urljoin(self.endpoint, console_log_endpoint),
                }
            )

        return criteria_data_list

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def cleanup_stage_failed(self, full_job_name, build_no):
        _cleanup_failed = False
        try:
            stage_list = self.server.get_build_stages(full_job_name, build_no)["stages"]
        except Exception as e:
            self.logger.error(e)
            self.logger.warning(
                "Could not check if cleanup stage failed for build #%s "
                "(job: <%s>)" % (build_no, full_job_name)
            )
        else:
            stage_no = len(stage_list)
            self.logger.debug(
                "Number of stages identified for job <%s> "
                "(build no: %s): %s" % (full_job_name, build_no, stage_no)
            )
            # Assume that cleanup stage is the last one
            if stage_no > 0:
                cleanup_stage = stage_list[-1]
                if cleanup_stage["status"] in ["FAILED"]:
                    _cleanup_failed = True

        return _cleanup_failed

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def remove_credential(self, credential_id, folder_name, domain_name="_"):
        """Removes a temporary credential in Jenkins.

        :param credential_id: Identifier of the credential in Jenkins
        :param folder_name: Credential folder name in Jenkins
        :param domain_name: Credential domain in Jenkins
        """
        print('jenkins399')
        from urllib.parse import quote
        self.logger.debug(
            "Removing a temporary credential <%s> in Jenkins" % credential_id
        )
        try:
            
            r = requests.get(
            urljoin(self.endpoint, "/job/eosc-synergy-org/credentials/api/json?depth=3"),
            auth=(self.access_user, self.access_token),
            )
            data = r.json()
            for store in data.get('stores', {}).values():
               for domain in store.get('domains', {}).values():
             
                 print(domain['credentials'])
                 for item in domain['credentials']:
                   print(item['id'])
                 print(domain.keys())
            print('Iván ', credential_id,folder_name)
            encoded_id = quote_plus(credential_id, safe='')
            #print(self.server.get_jobs())
            print('jenkins418')
            jobs = self.server.get_jobs()
            print('jenkins420')
            i=0
            for job in jobs:
                 i+=1
                 print('jenkins424')
                 print(i)
                 if 'folder' in job.get('_class','').lower() or 'organization' in job.get('_class','').lower():
                    print(job['name'])
                    #print(job)
            print(folder_name)
            print('jenkins419')
            #print('Ivántest',self.server.list_credentials(folder_name))
            #delete old method
            #self.logger.debug("Atempting to delete credential with id: <%r>" % credential_id)
            self.logger.debug("Atempting to delete credential with url: <%r>" % urljoin(
                   self.endpoint,
                   DELETE_CREDENTIAL_ORG % {
                    #"folder_name": folder_name,
                    "domain_name": domain_name,
                    "credential_id": encoded_id,
                    }
                 ))
            r = requests.delete(
                urljoin(
                   self.endpoint,
                   DELETE_CREDENTIAL_ORG % {
                    #"folder_name": folder_name,
                    "domain_name": domain_name,
                    "credential_id": encoded_id,
                    }
                 ),
                auth=(self.access_user, self.access_token),
                #headers={"Jenkins-Crumb":self.server.get_crumb()}
            )
            print('Remove status:', r.status_code)
            print('Remove response:', r.text)
            #self.server.delete_credential(credential_id, folder_name)
            
            print('jenkins434')
            '''
            r = requests.post( urljoin(self.endpoint, f"/job/{folder_name}/credentials/store/folder/domain/{domain_name}/credential/{encoded_id}/doDelete"), auth=(self.access_user, self.access_token),)
            print('Remove status:', r.status_code)
            print('Remove response:', r.text)
            '''
            self.logger.debug("Credential <%s> removed" % credential_id)
            print ('afterremoval')
            r = requests.get(
            urljoin(self.endpoint, "/job/eosc-synergy-org/credentials/api/json?depth=3"),
            auth=(self.access_user, self.access_token),
            )
            data = r.json()
            for store in data.get('stores', {}).values():
               for domain in store.get('domains', {}).values():
             
                 print(domain['credentials'])
                 for item in domain['credentials']:
                   print(item['id'])
                 print(domain.keys())
        except jenkins.NotFoundException as e:
            self.logger.error(e)
            self.logger.debug(
                "Could not remove credential <%s>: not found" % credential_id
            )

    @timeout_decorator.timeout(
        10,
        timeout_exception=jenkins.JenkinsException,
        exception_message="Timeout reached when trying to connect to Jenkins",
    )
    def create_credential(
        self,
        credential_id,
        credential_user,
        credential_token,
        folder_name,
        domain_name="_",
    ):  
        print('creating crederntials')
        #self.logger.info('Ivan- '+credential_id,credential_user,credential_token)
        """Creates a temporary credential in Jenkins.

        :param credential_user: User identifier
        :param credential_token: Secret token
        :param folder_name: Credential folder name in Jenkins
        :param domain_name: Credential domain in Jenkins
        """
        self.logger.debug(
            "Creating a temporary credential <%s> in Jenkins" % credential_id
        )
        print('Iván 437')
        self.logger.debug("Removing existing credential (if any)")
        #print('SQAaaS_creds',self.server.list_credentials('SQAaaS_creds'))#folder_name))
        #print('eosc-synergy-org/credentials',self.server.list_credentials('eosc-synergy-org/credentials'))#folder_name))
        print(folder_name)
        
        
        print('Iván 443')
        print('jenkins452')
        print("jenkins497")
        self.remove_credential(credential_id, folder_name=folder_name)
        print('jenkins454')
        env = Environment(loader=PackageLoader("openapi_server", "templates/jenkins"))
        template = env.get_template("credentials.xml")
        xml_rendered = template.render(
            credential_id=credential_id,
            credential_user=credential_user,
            credential_token=credential_token,
        )
        print('jenkins463')
        
        print('Ivan llga hasta 452',CREATE_CREDENTIAL_ORG % locals(),xml_rendered.encode("utf-8"))
        
        r = requests.post(
            urljoin(self.endpoint, CREATE_CREDENTIAL_ORG % locals()),
            data=xml_rendered.encode("utf-8"),
            auth=(self.access_user, self.access_token),
            headers={"Content-Type": "text/xml; charset=utf-8"},
        )
        #esto esta mal, quitar triple comilla (desde 500 hasta 507 esta quitada)
        #print('Ivan llega hasta 449',r,r.text)
        print('Status create:', r.status_code)
        print('Response create:', r.text)
        print ('jenkins508')
        #r.raise_for_status()
        '''
        #test request code
        r = requests.post(
         urljoin(self.endpoint, CREATE_CREDENTIAL_ORG % locals()),
         data=xml_rendered.encode("utf-8"),
         auth=(self.access_user, self.access_token),
         headers={"Content-Type": "text/xml; charset=utf-8"},
        )
        print('Status create:', r.status_code)
        print('Response create:', r.text)
        #end request code
        '''
        print('jenkins472')
        #print(self.server.list_credentials('eosc-synergy-org'))
        print('URL final:', urljoin(self.endpoint, CREATE_CREDENTIAL_ORG % locals()))
        print('Status:', r.status_code)
        print('Response:', r.text)
        print('llega hasta 451')
        CHECK_CREDENTIALS = "/credentials/store/system/domain/_/api/json?depth=3&pretty=true"
        
        tester = requests.get(urljoin(self.endpoint, CHECK_CREDENTIALS),auth=(self.access_user, self.access_token))
                  
        data = tester.json()
        for cred in data['credentials']:
            print(cred.get('id'), '-', cred.get('typeName'))
            
        print('jenkins535')    
        r = requests.get(
          urljoin(self.endpoint, "/job/eosc-synergy-org/credentials/api/json?depth=3"),
          auth=(self.access_user, self.access_token),
          )
        data = r.json()
        for store in data.get('stores', {}).values():
             for domain in store.get('domains', {}).values():
             
                 print(domain['credentials'])
                 for item in domain['credentials']:
                   print(item['id'])
                   
                   
                   print(domain.keys())
        self.logger.debug("Credential <%s> created" % credential_id)
        
        
        
        
    def update_job_credential(
        self,
        credential_id,
        folder_name,
        job_name,
        domain_name="_",
        ):
        """Updates the SCM credentialsId of an existing Jenkins job.

        :param credential_id: the credential ID to set on the job's Branch Sources
        :param folder_name: Jenkins folder where the job lives (e.g. 'EOSC-Synergy')
        :param repo_name: repository name as it appears in Jenkins (e.g. 'private-sqaaastesting')
        :param domain_name: Credential domain in Jenkins (kept for API consistency)
        """
        #job_name = "%s/%s" % (folder_name, repo_name)
        self.logger.debug(
            "Updating SCM credential for job <%s> to <%s>" % (job_name, credential_id)
        )
        job_name2='eosc-synergy-org/private-sqaaastesting.assess.sqaaas'
        print('jenkins589')
        #print(self.server.get_jobs())
        current_config = self.server.get_job_config(job_name2)
        print('jenkins592')
        print(current_config)
        soup = BeautifulSoup(current_config, "xml")
        print('jenkins594')
        
        cred_tags = soup.find_all("credentialsId")
        if not cred_tags:
            self.logger.warning(
                "No <credentialsId> tag found in job <%s> config" % job_name
            )
            return
        print('jenkins598')
        for tag in cred_tags:
            tag.string = credential_id

        # Get CSRF crumb first
        crumb_url = urljoin(self.endpoint, "/crumbIssuer/api/json")
        crumb_response = requests.get(
            crumb_url,
            auth=(self.access_user, self.access_token)
        )
        crumb_data = crumb_response.json()

        # Post updated config back
        # Drop the branch segment
        job_segments = job_name.split("/")[:-1]  
        # ['eosc-synergy-org', 'private-sqaaasteting.assess.sqaaas']

        items = list(map("/job/".__add__, job_segments))
        path = "".join(items) + "/config.xml"
        # /job/eosc-synergy-org/job/private-sqaaasteting.assess.sqaaas/config.xml
        print('jenkins623')
        r = requests.post(
            urljoin(self.endpoint, path),
            data=str(soup).encode("utf-8"),
            auth=(self.access_user, self.access_token),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                crumb_data["crumbRequestField"]: crumb_data["crumb"]
            }
        )
        self.logger.debug(
            "SCM credential for job <%s> updated to <%s>" % (job_name, credential_id)
            )
        print('jenkins636')
        job_name2='eosc-synergy-org/private-sqaaastesting.assess.sqaaas'
        print(job_name2)
        current_config2 = self.server.get_job_config(job_name2)
        print(current_config2)
        #print(current_config)
        print('jenkins638')
        if current_config==current_config2:
             print('sad')
        else:
             print('happY?')        
