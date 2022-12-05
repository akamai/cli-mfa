from ctypes import ArgumentError
import logging
import hashlib
import hmac
import time
import datetime

import sys
import json
import csv

# 3rd party modules
import requests
from akamai.edgegrid import EdgeGridAuth

# local modules
from . import cli
from . import config
from . import __VERSION__
from . import logger


class BaseAPIHelper(object):

    api_version = None  # Specific API can be overriden on derivated class

    def __init__(self, cli_config):
        self.config = cli_config
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': self.user_agent})
        self.baseurl = ""

    @property
    def user_agent(self):
        return f'{self.config.ua_prefix} cli-mfa/{__VERSION__}'

    def prepare_querystring(self, qs_args):
        """Allow inherting class to implement logic to inject querystring arguments."""
        return qs_args

    def get(self, url, params=None):
        url = f"{self.baseurl}{url}"
        api_response = self._session.get(url, params=self.prepare_querystring(params))
        if api_response.status_code != requests.codes.ok:
            error_msg = f"FATAL: API call {api_response.request.method} {api_response.url} " \
                        f"returned HTTP/{api_response.status_code}"
            cli.print_error(error_msg)
            cli.print_error(api_response.text)
            cli.exit(1)
        return api_response.json()

    def post(self, url, params=None, json=None):
        url = f"{self.baseurl}{url}"
        api_response = self._session.post(url, params=self.prepare_querystring(params), json=json)
        if api_response.status_code != 200:
            raise Exception(f"Akamai MFA API response error HTTP/{api_response.status_code}, {api_response.text}")
        return api_response.json()


class MFAServiceAPIHelper(BaseAPIHelper):
    """
    Akamai MFA service API (experimental)
    DO NOT USE, use {OPEN} API through `OpenAPIHelper` whenever possible.
    """

    mfa_api_url = "https://mfa.akamai.com"
    mfa_api_ver = "v1"

    def __init__(self, cli_config, signing_key=None, integration_id=None):
        super().__init__(cli_config)
        self.baseurl = MFAServiceAPIHelper.mfa_api_url
        if not signing_key or not integration_id:  # use the default integration creds
            self._session.auth = AkamaiMFAAuth(self.config.mfa_signing_key, self.config.mfa_integration_id,
                                               self.api_version)
        else:
            self._session.auth = AkamaiMFAAuth(signing_key, integration_id, self.api_version)


class MFALoggingAPIHelper(BaseAPIHelper):
    """
    Akamai MFA Logging Integration API
    """

    mfa_api_url = "https://mfa.akamai.com"
    mfa_api_ver = "v1"

    def __init__(self, cli_config):
        super().__init__(cli_config)
        self.baseurl = MFAServiceAPIHelper.mfa_api_url
        self._session.auth = AkamaiMFAAuth(self.config.mfa_signing_key, self.config.mfa_integration_id)


class OpenAPIHelper(BaseAPIHelper):
    """
    Akamai MFA {OPEN} API
    See https://techdocs.akamai.com/mfa/reference/api for more information
    """
    def __init__(self, cli_config):
        super().__init__(cli_config)
        self.baseurl = f"https://{self.config.host}"
        self._session.auth = EdgeGridAuth(
            client_token=self.config.client_token,
            client_secret=self.config.client_secret,
            access_token=self.config.access_token
        )

    def prepare_querystring(self, qs_args):
        args = super().prepare_querystring(qs_args)
        if isinstance(args, dict):
            final_params = qs_args.copy()
        else:
            final_params = {}
        if self.config.accountkey:
            final_params.update({"accountSwitchKey": self.config.accountkey})
        if hasattr(config, "contract_id") and self.config.contract_id:
            final_params.update({"contractId": self.config.contract_id})
        final_params.update({"ua": self.user_agent})
        return final_params


class AkamaiMFAAuth(requests.auth.AuthBase):
    """
    Akamai MFA Integration authentication for Requests.
    """

    def __init__(self, signing_key, integration_id, api_version=None):
        """
        Args:
            config (MFAConfig): cli-mfa config
            api_version (_type_): API version in the backend - optional
        """
        self._signing_key = signing_key
        self._integration_id = integration_id
        self._content_type_json = {'Content-Type': 'application/json'}
        self._api_version = '2021-07-15'
        if api_version:
            self._api_version = api_version

    def get_signature(self, t):
        signature = hmac.new(
            key=self._signing_key.encode("utf-8"),
            msg=str(t).encode("utf-8"),
            digestmod=hashlib.sha256).hexdigest()
        return signature

    def __call__(self, r):
        now = str(int(time.time()))
        signature = self.get_signature(now)
        self._headers = {
            'X-Pushzero-Id': self._integration_id,
            'X-Pushzero-Signature': signature,
            'X-Pushzero-Signature-Time': now,
            'X-Api-Version': self._api_version}
        r.headers.update(self._headers)
        r.headers.update(self._content_type_json)
        return r


class EventAPI(object):

    def __init__(self, cli_config):
        self.config = cli_config

    def pull_events(self):
        api_helper = MFALoggingAPIHelper(self.config)
        api_url = f'/api/{api_helper.mfa_api_ver}/control/reports/auths'
        scan_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=config.MOST_RECENT_PADDING)
        scan_start = scan_end - datetime.timedelta(minutes=5)
        if self.config.end:
            scan_end = datetime.datetime.utcfromtimestamp(self.config.end)
        if self.config.start:
            scan_start = datetime.datetime.utcfromtimestamp(self.config.start)

        while True:  # main loop, used with the --tail/-f mode
            loop_start = time.time()
            continuation_token = None
            params = {
                'after': scan_start.isoformat(),
                'before': scan_end.isoformat()
            }

            while True:  # Iterate until continuation_token attribute is missing
                payload = {}
                if continuation_token:
                    payload = {'continuation_token': continuation_token}
                api_response = api_helper.post(api_url, params=params, json=payload)

                continuation_token = api_response.get('continuation_token')
                scanned_events = api_response.get('result', {}).get('data', [])

                for mfa_event in scanned_events:
                    if self.config.noreceipt:
                        mfa_event.pop('receipt')
                    print(json.dumps(mfa_event))
                    sys.stdout.flush()

                if not continuation_token:
                    break

            if self.config.tail:
                wait = self.config.tail_pull_interval - (time.time() - loop_start)
                logging.debug("Wait %s sec..." % wait)
                time.sleep(wait)
                scan_start = scan_end  # next iteration we stich, start is the previous end
                scan_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=config.MOST_RECENT_PADDING)
            else:
                break


class IdentityManagementAPI(object):
    """
    Manage users/groups on Akamai MFA
    """

    api_version = "2022-02-22"

    def __init__(self, cli_config):
        """
        This class use two different API set with different auth logic.
        We prepare them here based on what's available in the .edgerc file.
        """
        self.service_api_helper = None
        self.open_api_helper = None
        if cli_config.mfa_api_signing_key and cli_config.mfa_api_integration_id:
            self.service_api_helper = MFAServiceAPIHelper(
                cli_config,
                cli_config.mfa_api_signing_key,
                cli_config.mfa_api_integration_id
            )
        if cli_config.host:
            self.open_api_helper = OpenAPIHelper(cli_config)

    def list_groups(self):
        """
        Fetch the list of groups visible in Akamai MFA.
        """
        return self.service_api_helper.get("/api/v1/control/groups")

    def group_id(self, group_name):
        """
        Return Group ID for a given group name
        If the group name is not found return None
        If multiple matches, raise an exception

        Args:
            group_name (string): Group name

        Returns:
            string: ID of the group found
        """
        group_info = self.service_api_helper.get("/api/v1/control/groups", params={'name': group_name})
        matches = group_info.get('result', {}).get('page', [])
        group_id = None
        for m in matches:
            if m.get('name') == group_name:
                if group_id is None:
                    group_id = m.get('id')
                else:
                    raise Exception(f"Ambiguity, more than one group matching name {group_name}")
        return group_id

    def create_group(self, group_name, group_summary=None):
        """Create a new group in MFA backend."""
        payload = {
            "name": group_name,
            "summary": group_summary
        }
        return self.service_api_helper.post("/api/v1/control/groups", json=payload)

    def create_users(self, users):
        payload = {"ignore_conflicts": True, "users": users}
        logger.debug("create_users payload %s" % payload)
        return self.service_api_helper.post("/api/v1/control/users/bulk/create", json=payload)

    def associate_users_to_group(self, usernames, group_id):
        logger.debug(f"Adding users {usernames} to group {group_id}")
        return self.service_api_helper.post(f"/api/v1/control/groups/{group_id}/users/bulk/associate", json=usernames)

    def import_users_from_csv(self, csv_filename, ignore_header, fullname_format):
        """
        Read a CSV file containing user identity, and one group
        Create the users, groups and association in the Akamai MFA backend.

        Args:
            csv_filename (_type_): path to the csv file
            ignore_header (_type_): ignore the first line of the file
            fullname_format (_type_): How the user Fullname should be formatted
        """
        new_users = []
        scanned_groups = set()
        user_groupname_map = {}

        # Parse the CSV file to prepare the API calls
        with open(csv_filename) as csvfile:
            reader = csv.reader(csvfile)
            if ignore_header:
                next(reader)
            for row in reader:
                newuser = {
                    'full_name': fullname_format.format(firstname=row[1], lastname=row[2]),
                    'last_name': row[2],
                    'email': row[0],
                    'username': row[3]
                }
                user_groupname_map[row[3]] = row[4]
                scanned_groups.add(row[4])
                new_users.append(newuser)

        # First, let's figure out groups, existing vs. ones in the input file
        count_group_added = 0
        count_group_existing = 0
        existing_groups = self.list_groups()
        groups_map = {g.get('id'): g.get('name') for g in existing_groups.get('result').get('page')}
        reverse_groups_map = {g.get('name'): g.get('id') for g in existing_groups.get('result').get('page')}
        for g in scanned_groups:
            if g not in groups_map.values():
                r = self.create_group(g, f"Created with command: {cli.current_command()}")
                groups_map[r.get('result').get('id')] = r.get('result').get('name')
                reverse_groups_map[r.get('result').get('name')] = r.get('result').get('id')
                count_group_added += 1
            else:
                count_group_existing += 1
                logger.debug(f"Group {g} was already present, not added.")
        logger.debug("Final groups: %s" % groups_map)
        cli.print(f"{count_group_added} group(s) added, {count_group_existing} group(s) were already existing")

        # Second, bulk user insertion
        new_users_response = self.create_users(new_users)
        logger.debug("new_users: %s" % new_users_response)
        cli.print(f"{len(new_users_response.get('result'))} user(s) added or changed")

        # Third, associate user to group
        for new_user in new_users_response.get('result', []):
            group_id = reverse_groups_map[user_groupname_map[new_user.get('username')]]
            self.associate_users_to_group([new_user.get('id')], group_id)

    def enroll_users(self, group_name):
        """
        Sends off emails to users in a list of groups.
        """
        if not isinstance(group_name, str):
            raise ArgumentError("groups must be an string")

        group_id = self.group_id(group_name)
        if group_id is None:
            cli.print_error("Group %s not found." % group_name)
            cli.exit(2)
        payload = {'exclude_enrolled_users': True}
        payload["groups"] = [group_id]
        cli.print("Sending enrollment email to ununrolled users in group %s..." % group_name)
        response = self.service_api_helper.post("/api/v1/control/email/enroll_users", json=payload)
        logger.debug(response)

    def list_users(self, json_fmt=False):
        """
        List the users synchronized with the MFA tenant.
        """
        page = 1
        page_size = 500
        total_page = None
        total_users = 0

        while total_page is None or page <= total_page:
            logger.info(f"Page {page} of {total_page if total_page else 'unknown'}")
            params = {'page': page, 'pageSize': page_size}
            scan_users = self.open_api_helper.get('/amfa/v1/users', params)
            total_page = scan_users.get('totalPages', 1)
            page += 1
            for u in scan_users.get('users', []):
                if json_fmt:
                    cli.print(json.dumps(u, indent=4))
                else:
                    cli.print(f"{u.get('userId')},{u.get('username')},{u.get('userStatus')}")
                total_users += 1

        cli.print(f"# Total users exported: {total_users}")
