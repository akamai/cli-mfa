import logging
from http.client import HTTPConnection
import sys
import json

# cli-mfa modules
from . import logger, __VERSION__
from . import cli
from . import config
from . import core


log_file = None


def prepare_logging(cli_config):
    logging.basicConfig(filename=log_file, level=logging.INFO, format=config.LOG_FMT)

    if cli_config.debug:
        HTTPConnection.debuglevel = 1
        logger.setLevel(logging.DEBUG)
        requests_log = logging.getLogger("urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True


def run():
    cli_config = config.MFAConfig()
    prepare_logging(cli_config)

    if cli_config.command is None:
        cli_config.display_help()
        sys.exit(1)
    elif cli_config.command == "version":
        print(__VERSION__)
        sys.exit(0)
    elif cli_config.command == "info":
        cli.print(json.dumps(cli_config.info(), indent=4))
    elif cli_config.command == 'event':
        event_api = core.EventAPI(cli_config)
        event_api.pull_events()
    elif cli_config.command == 'users':
        identity = core.IdentityManagementAPI(cli_config)
        if cli_config.action == "invite":
            identity.enroll_users(cli_config.group)
        elif cli_config.action == "list":
            identity.list_users()
            pass
        else:
            cli.print_error("not supported")
            cli.exit(1)
    elif cli_config.command == 'importusers':
        logger.debug("starting import...")
        identity = core.IdentityManagementAPI(cli_config)
        identity.import_users_from_csv(cli_config.file, cli_config.ignore_header, cli_config.fullname_format)
    else:
        raise ValueError(f"Unsupported command: {cli_config.command}")


"""
Handy handler to be able to run command as module:
  > python3 -m amfa.main info
"""
if __name__ == "__main__":
    run()
