import logging
import requests
import time

from urllib.parse import urljoin
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
import jenkins

from openapi_server.exception import SQAaaSAPIException


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
            self.endpoint,
            username = self.access_user,
            password = self.access_token)
        self.logger = logging.getLogger('sqaaas.api.jenkins')

    @staticmethod
    def format_job_name(job_name):
        """Format job name according to what is expected by Jenkins.

        Slash symbol '/' is double-encoded: ''%252F' instead of '%2F'

        :param job_name: Name of the Jenkins job
        """
        return quote_plus(job_name.replace('/', '%2F'))

    def scan_organization(self, org_name='eosc-synergy-org'):
        path = '/job/%s/build?delay=0' % org_name
        r = requests.post(
            urljoin(self.endpoint, path),
            auth=(self.access_user, self.access_token))
        r.raise_for_status()
        self.logger.debug('Triggered GitHub organization scan')

    def get_job_info(self, name, depth=0):
        job_info = {}
        job_name_list = []

        _org, _repo, _branch = name.split('/')
        for folder in self.server.get_jobs(folder_depth=1):
            if folder['name'] in [_org]:
                job_name_list = [job['name'] for job in folder['jobs']]
        # Try case-insensitive (Jenkins org-folder limitation)
        if _repo not in job_name_list:
            self.logger.debug(
                'Trying case-insensitive match with job: <%s>' % name
            )
            for job_name in job_name_list:
                if _repo.lower() in [job_name.lower()]:
                    name = '/'.join([_org, job_name, _branch])
                    self.logger.debug('Using new job name: <%s>' % name)
                    break
        try:
            job_info = self.server.get_job_info(name, depth=depth)
            self.logger.debug('Information for job <%s> obtained from Jenkins: %s' % (
                name, job_info))
        except jenkins.JenkinsException:
            self.logger.error('No info could be fetched for Jenkins job <%s>' % name)
        return job_info

    def exist_job(self, job_name):
        """Check whether given job is defined in Jenkins.

        :param job_name: job name including folder/s, name & branch
        """
        return self.get_job_info(job_name)

    def build_job(self, full_job_name):
        """Build existing job.

        :param full_job_name: job name including folder/s, name & branch
        """
        item_no = None
        try:
            item_no = self.server.build_job(full_job_name)
        except Exception:
            self.logger.warning('Job <%s> has not been queued yet' % full_job_name)
        else:
            self.logger.debug('Triggered job build (queue item number: %s)' % item_no)
        return item_no

    async def get_queue_item(self, item_no):
        """Get the status of the build item in the Jenkins queue.

        :param item_no: item number in the Jenkins queue.
        """
        queue_data = self.server.get_queue_item(item_no)
        executable_data = None
        if 'executable' not in list(queue_data):
            self.logger.debug('Waiting for job to start. Queue item: %s' % queue_data['url'])
        else:
            executable_data = queue_data['executable']
            if executable_data:
                self.logger.debug('Job started the execution (url: %s, number: %s)' % (
                    executable_data['url'], executable_data['number']
                ))
        return executable_data

    def get_build_info(self, full_job_name, build_no, depth=0):
        self.logger.debug('Getting status for job <%s> (build_no: %s)' % (full_job_name, build_no))
        build_info = None
        try:
            build_info = self.server.get_build_info(full_job_name, build_no, depth=depth)
            self.logger.debug('Build info as obtained by Jenkins: %s' % build_info)
        except Exception:
            self.logger.warning(
                'Could not find build info for #%s (job: <%s>)' % (
                    build_no, full_job_name
                )
            )
        return build_info

    def delete_job(self, full_job_name):
        self.logger.debug('Deleting Jenkins job: %s' % full_job_name)
        self.server.delete_job(full_job_name)
        self.logger.debug('Jenkins job <%s> successfully deleted' % full_job_name)

    def get_stage_data(self, job_name, build_no):
        """Get the info from the pipeline stages.

        Via Pipeline Stage View API at https://github.com/jenkinsci/pipeline-stage-view-plugin

        :param job_name: job name including folder/s, name & branch
        :param build_no: build number.
        """
        items = list(map('/job/'.__add__, job_name.split('/')))
        jenkins_job_name = ''.join(items)

        def do_request(path, append=False, json_payload=True):
            if append:
                target_path = '%s/%s/%s' % (jenkins_job_name, build_no, path)
            else:
                target_path = path
            self.logger.debug('Request to <%s>' % target_path)
            requests.packages.urllib3.disable_warnings()
            r = requests.post(
                urljoin(self.endpoint, target_path),
                auth=(self.access_user, self.access_token),
                verify=False
            )
            if json_payload:
                try:
                    out = r.json()
                except ValueError:
                    _reason = 'Could not obtain a JSON response payload from Jenkins path: %s' % target_path
                    self.logger.error(_reason)
                    raise SQAaaSAPIException(502, _reason)
            else:
                out = r

            return out

        def get_text(html_text):
            soup = BeautifulSoup(html_text, 'html.parser')
            console_tags = soup.find_all('pre', class_='console-output')
            if len(console_tags) > 1:
                self.logger.warn((
                    'Detected multiple <pre class="console-output"> tags!'
                    'Falling back to the first one, ignoring the rest'
                ))
            console_output = console_tags[0]
            return console_output.getText()

        def process_stdout(stdout):
            stdout = stdout.strip()
            lines = stdout.split('\n')
            cmd = lines.pop(0)
            if not cmd.startswith('+'):
                self.logger.warn((
                    'Could not identify the command (identified by \'+\' '
                    'prefix) in string <%s>. No change done to stdout' % cmd
                ))
                lines.insert(0, cmd)
                cmd = ''
            output_text = '\n'.join(lines)
            return (cmd, output_text)

        data = do_request('/wfapi/describe', append=True)
        stage_name_prefixes = ('QC.', 'SvcQC.')
        qc_stages = [stage for stage in data['stages'] if stage['name'].startswith(stage_name_prefixes)]
        stage_describe_endpoints = [stage['_links']['self']['href'] for stage in qc_stages]
        self.logger.info('Found %s stage/s that run quality criteria' % len(stage_describe_endpoints))

        criteria_data_list = []
        for qa_stage in stage_describe_endpoints:
            data = do_request(qa_stage)
            name = data['name']
            criterion = name.split()[0]
            status = data['status']
            # Use 'console' endpoint to be subsequently parsed with
            # beautifulsoup4. Unexpected syntaxes have been seen when using
            # instead <text> property from 'log' endpoint
            console_log_endpoint = data['stageFlowNodes'][0]['_links']['console']['href']
            console_log_endpoint += '?consoleFull'
            data = do_request(console_log_endpoint, json_payload=False)
            stdout = get_text(data.text)
            cmd, output_text = process_stdout(stdout)
            if not cmd:
                _reason = (
                    'Could not get the command for the stage: output text '
                    'might be truncated by Jenkins, consider to set/increase '
                    'Pipeline REST API Plugin\'s maxReturnChars property (see '
                    'https://github.com/jenkinsci/pipeline-stage-view-plugin)'
                )
                self.logger.error(_reason)
                raise SQAaaSAPIException(502, _reason)
            criteria_data_list.append({
                'name': name,
                'criterion': criterion,
                'status': status,
                'stdout_command': cmd,
                'stdout_text': output_text,
                'url': urljoin(self.endpoint, console_log_endpoint)
            })

        return criteria_data_list
