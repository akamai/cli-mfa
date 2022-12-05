# Python modules
import sys
from math import ceil


def print(s):
    sys.stdout.write("%s\n" % s)
    sys.stdout.flush()


def print_error(s):
    sys.stderr.write("%s\n" % s)
    sys.stderr.flush()


def current_command():
    return "akamai mfa " + " ".join(sys.argv[1:])


def exit(code):
    sys.exit(code)


def mask_string(s, percentage=0.9):
    if s is None:
        return None
    mask_chars = ceil(len(s) * percentage)
    return f'{"*" * mask_chars}{s[mask_chars:]}'
