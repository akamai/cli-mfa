#!/usr/bin/env python3

# Copyright 2022 Akamai Technologies, Inc. All Rights Reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import configparser
import os
import logging
import sys

from . import __VERSION__
from . import cli


#: Log formatting aligned with other CLIs
LOG_FMT = '%(asctime)s [%(levelname)s] %(threadName)s %(message)s'
#: Near real-time, 30s ago is the most recent by default
MOST_RECENT_PADDING = 30

epilog = '''Copyright (C) Akamai Technologies, Inc\n''' \
         '''Visit http://github.com/akamai/cli-mfa for detailed documentation'''

#: How often we pull data in --tail mode (default is 60 seconds)
tail_pull_interval = 60


class MFAConfig():
    """
    Manage CLI MFA input parameters
    """

    CONFIG_KEYS = [
        'mfa_integration_id',      # SIEM Log Integration
        'mfa_signing_key',         # SIEM Log Integration
        'mfa_api_integration_id',  # Service API prior to {OPEN} launch - experimental
        'mfa_api_signing_key',     # Service API prior to {OPEN} launch - experimental
        'client_secret',           # {OPEN}
        'host',                    # {OPEN}
        'access_token',            # {OPEN}
        'client_token',            # {OPEN}
        'contract_id',             # {OPEN}
        'accountkey'               # {OPEN}
    ]

    def __init__(self):

        self.mfa_integration_id = None
        self.mfa_signing_key = None
        self.mfa_api_integration_id = None
        self.mfa_api_signing_key = None

        # 1. Scan parameters from the CLI arguments

        self.parser = argparse.ArgumentParser(prog="akamai mfa", epilog=epilog,
                                              description='Process command line options.',
                                              formatter_class=argparse.RawTextHelpFormatter)

        subparsers = self.parser.add_subparsers(dest='command', help='Main command')
        subparsers.add_parser('version', help="Display CLI-MFA version")
        subparsers.add_parser('info', help="Show CLI-MFA configuration informations")
        eventparser = subparsers.add_parser('event', help="Dump MFA events")
        eventparser.add_argument("--start", "-s", default=None, type=int, help="Scan for events after this epoch")
        eventparser.add_argument("--end", "-e", default=None, type=int, help="Scan for events before this epoch")
        eventparser.add_argument("--tail", "-f", default=False, action="store_true",
                                 help="""Do not stop when most recent log is reached, rather
                                         wait for additional data to be appended to the input.""")
        eventparser.add_argument("--noreceipt", default=False, action="store_true",
                                 help="Discard the receipt attribute to save log space")

        # User sub parser, will replace the loaduserparser down the road
        user_parser = subparsers.add_parser('users', help="User operations (search, import, etc...)")
        # userparser.add_argument("action", choices=['search', 'import', 'invite'])
        user_action_parser = user_parser.add_subparsers(dest="action", help='User operations (search, import, etc...)')

        # usersearch_parser = user_action_parser.add_parser("search", help="Search users")
        # usersearch_parser.add_argument('-g', '--group', dest="group", help='Limit search to users in this group')
        # usersearch_parser.add_argument(dest='filter', default="*", help="Pattern to search user, default is *")
        invite_parser = user_action_parser.add_parser("invite", help="Send enrollement invite over email")
        invite_parser.add_argument('-g', '--group', dest="group", help='Send invite to member of this group')
        listuser_parser = user_action_parser.add_parser("list", help="List users")
        listuser_parser.add_argument('--json', action="store_true", help='Format list of users as JSON')
        listuser_parser.add_argument('--include-devices', dest="include_devices", default=False, action="store_true",
                                     help='Include device details for listed users')

        # ad-hoc implementation to support MFA customers
        loaduserparser = subparsers.add_parser('importusers', help="Import users from a CSV file")
        loaduserparser.add_argument("--file", "-f", required=True, help="CSV file used as input")
        loaduserparser.add_argument("--ignore-header", "-i", dest="ignore_header", default=False, action="store_true",
                                    help="Ignore the first line (if header is present)")
        loaduserparser.add_argument("--fullname-format", "-n", dest="fullname_format", default="{firstname} {lastname}",
                                    help="Full name formatting (default is '{firstname} {lastname}')")

        self.parser.add_argument("--edgerc", type=str, default="~/.edgerc",
                                 help='Location of the credentials file (default is "~/.edgerc")')

        self.parser.add_argument("--section", '-c',
                                 help="Section inside .edgerc, default is [default] ($AKAMAI_EDGERC_SECTION)",
                                 default=os.environ.get("AKAMAI_EDGERC_SECTION", "default"))
        self.parser.add_argument("--accountkey", "--account-key", help="Account Switch Key",
                                 default=os.environ.get('AKAMAI_EDGERC_ACCOUNT_KEY'))
        self.parser.add_argument("--debug", '-d', action="store_true", default=False, help="Debug mode")
        self.parser.add_argument("--user-agent-prefix", dest='ua_prefix', default='Akamai-CLI', help=argparse.SUPPRESS)

        try:
            scanned_cli_args = self.parser.parse_args()
            cli_args = vars(scanned_cli_args)
            for option in cli_args:
                setattr(self, option, cli_args[option])
        except Exception as e:
            logging.exception(e)
            sys.exit(1)

        # 2. Load MFA params from .edgerc
        edgerc_config = configparser.ConfigParser()
        edgerc_config.read(os.path.expanduser(self.edgerc))
        if not edgerc_config.has_section(self.section):
            err_msg = "ERROR: No section named %s was found in your .edgerc file\n" % self.section
            err_msg += "ERROR: Please generate credentials for the script functionality\n"
            err_msg += "ERROR: and run 'python gen_edgerc.py %s' to generate the credential file\n" % self.edgerc
            sys.exit(err_msg)
        for key, value in edgerc_config.items(self.section):
            if key in MFAConfig.CONFIG_KEYS:
                setattr(self, key, value)

        # And the environment variables
        if os.getenv('MFA_INTEGRATION_ID'):
            self.integration_id = os.getenv('MFA_INTEGRATION_ID')
        if os.getenv('MFA_SIGNING_KEY'):
            self.signing_key = os.getenv('MFA_SIGNING_KEY')
        if os.getenv('MFA_API_INTEGRATION_ID'):
            self.mfa_api_integration_id = os.getenv('MFA_API_INTEGRATION_ID')
        if os.getenv('MFA_API_SIGNING_KEY'):
            self.mfa_api_signing_key = os.getenv('MFA_API_SIGNING_KEY')

    def display_help(self):
        self.parser.print_help()

    def info(self):
        """
        Display information about the current CLI.
        Helpful for troubleshooting
        """
        config_info = {
            "general": {
                "cli-mfa_version": __VERSION__,
                "python": sys.version.replace("\n", " "),
                "akamai_cli": os.environ.get("AKAMAI_CLI_VERSION"),
                "edgerc_file": self.edgerc,
                "edgerc_section": self.section
            }
        }

        # Logging Integration API
        if self.mfa_integration_id or self.mfa_signing_key:
            config_info["amfa-logging-api"] = {}
            if self.mfa_integration_id:
                config_info["amfa-logging-api"]["mfa_integration_id"] = self.mfa_integration_id
            if self.mfa_signing_key:
                config_info["amfa-logging-api"]["mfa_signing_key"] = cli.mask_string(self.mfa_signing_key)

        # Akamai MFA Service API (unsupported, do not use)
        if self.mfa_api_integration_id or self.mfa_api_signing_key:
            config_info["amfa-service-api"] = {}
            if self.mfa_api_integration_id:
                config_info["amfa-service-api"]["mfa_api_integration_id"] = self.mfa_api_integration_id
            if self.mfa_api_signing_key:
                config_info["amfa-service-api"]["mfa_api_signing_key"] = cli.mask_string(self.mfa_api_signing_key)

        # {OPEN} API
        config_info["akamai-open-api"] = {}
        if hasattr(self, "host"):
            config_info["akamai-open-api"]["host"] = self.host
        if hasattr(self, "access_token"):
            config_info["akamai-open-api"]["access_token"] = cli.mask_string(self.access_token)
        if hasattr(self, "client_token"):
            config_info["akamai-open-api"]["client_token"] = cli.mask_string(self.client_token)
        if hasattr(self, "client_secret"):
            config_info["akamai-open-api"]["client_secret"] = cli.mask_string(self.client_secret)
        if hasattr(self, "accountkey") and self.accountkey:
            config_info["akamai-open-api"]["accountkey"] = self.accountkey
        if hasattr(self, "contract_id") and self.contract_id:
            config_info["akamai-open-api"]["contract_id"] = self.contract_id

        return config_info
