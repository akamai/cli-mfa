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

"""
This module replaces the old test.bash script
Tested with nose2:

```bash

# Optional
AKAMAI_EDGERC_SECTION=mysection
# End Optional

cd test
nose2 -v
open report.html
```

For some specific test
```
nose2 -v test.TestUserGroupManagement.test_import_csv
```
"""

import unittest
import subprocess
import shlex
from pathlib import Path
import collections
import time
import os
import tempfile

# Global variables
encoding = 'utf-8'


class CliMFATest(unittest.TestCase):
    testdir = None
    maindir = None

    def setUp(self):
        self.testdir = Path(__file__).resolve().parent
        self.maindir = Path(__file__).resolve().parent.parent

    def cli_command(self, *args):
        command = shlex.split(f'python3 {self.maindir}/bin/akamai-mfa')
        # command.extend(["--somearg", os.environ['somevariable']])
        command.extend(*args)
        print("\nCOMMAND: ", " ".join(command))
        return command

    def cli_run(self, *args):
        cmd = subprocess.Popen(self.cli_command(str(a) for a in args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return cmd

    def cli_debug_print_output(self, h, line_prefix=""):
        "Handy function to print the CLI output."
        line_count = 1
        for line in h.decode().splitlines():
            print(f"{line_count:4} {line_prefix} {line}")
            line_count += 1

    def cli_debug_output(self, return_code, stdout, stderr=None):
        if return_code != 0 and stderr:
            self.cli_debug_print_output(stderr, "stderr>")
        else:
            self.cli_debug_print_output(stdout, "stdout>")

    def line_count(filename):
        count = 0
        with open(filename) as f:
            while next(f, False):
                count += 1
        return count

    def duplicate_count(filename):
        total_count = 0
        with open(filename) as infile:
            counts = collections.Counter(ln.strip() for ln in infile)
        for line, count in counts.most_common():
            if count > 1:
                print(f"DUPLICATE[{count}] {line}")
                total_count += 1
        return total_count


class TestEvents(CliMFATest):

    after = int(time.time() - 3 * 60 * 60)
    before = int(time.time())

    def test_events(self):
        "Fetch MFA authentication events for last 3 hours."
        cmd = self.cli_run("event", "--start", self.after, "--end", self.before)
        stdout, stderr = cmd.communicate(timeout=60)
        if cmd.returncode != 0:
            print(f"STDERR> {stderr.decode()} <STDERR")
        else:
            print(f"STDOUT> {stdout.decode()} <STDOUT")
        events = stdout.decode(encoding)
        event_count = len(events.splitlines())
        self.assertGreater(event_count, 0, "We expect at least one MFA auth event")
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')

    def test_events_tail(self):
        "Fetch MFA authentication events for last 3 hours."
        stdout = None
        stderr = None
        cmd = self.cli_run("event", "--start", self.after, "--tail")
        # timeout should be > tail_poll_interval
        try:
            cmd.communicate(timeout=10)
        except subprocess.TimeoutExpired as te:
            stdout = te.stdout
            stderr = te.stderr

        if stderr:
            print(f"STDERR> {stderr.decode()} <STDERR")
        if stdout:
            print(f"STDOUT> {stdout.decode()} <STDOUT")
            events = stdout.decode(encoding)
            event_count = len(events.splitlines())
            self.assertGreater(event_count, 0, "We expect at least one MFA auth event")
        else:
            self.fail("No data available")


class TestUserGroupManagement(CliMFATest):

    def test_list(self):
        "List the users configured in the Akamai MFA tenant."
        cmd = self.cli_run('-d', 'users', 'list')
        stdout, stderr = cmd.communicate()
        self.cli_debug_output(cmd.returncode, stdout, stderr)
        self.assertEquals(cmd.returncode, 0, 'CLI return code must be 0')

    def test_invite(self):
        cmd = self.cli_run('users', 'invite', '-g', 'NEW_GROUP')
        stdout, stderr = cmd.communicate()
        self.cli_debug_output(cmd.returncode, stdout, stderr)
        self.assertEquals(cmd.returncode, 0, 'CLI return code must be 0')

    def test_import_csv(self):
        domain = "example.org"
        # Mockup CSV file with 1st row as header
        csv_content = """email,firstName,lastName,username,GROUP\n""" \
            f"""user1@{domain},User1,Lastname1,user1.lastname1,NEW_GROUP\n""" \
            f"""user2@{domain},User2,Lastname2,user2.lastname2,NEW_GROUP\n""" \
            f"""user3@{domain},User3,Lastname3,user3.lastname3,NEW_GROUP\n""" \
            f"""user4@{domain},User4,Lastname4_Kichirō,user4.lastname4,NEW_GROUP\n""" \
            f"""user5@{domain},User5,Lastname5,user5.lastname5,NEW_GROUP2\n""" \
            f"""user6@{domain},User6,Lastname6,user6.lastname6,NEW_GROUP2\n""" \
            f"""user7@{domain},User8,Lastname8,user8.lastname7,NEW_GROUP2\n"""

        csv_fp, csv_filename = tempfile.mkstemp(text=True)
        with os.fdopen(csv_fp, 'w+t') as f:
            f.write(csv_content)

        cmd = self.cli_run('-d', 'importusers', '--ignore-header', '-f', csv_filename)
        stdout, stderr = cmd.communicate()
        self.cli_debug_output(cmd.returncode, stdout, stderr)
        os.unlink(csv_filename)
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')

    def test_csvfiledoesntexist(self):
        cmd = self.cli_run('importusers', '-f', 'csv_file_not_exist')
        stdout, stderr = cmd.communicate()
        self.cli_debug_output(cmd.returncode, stdout, stderr)
        self.assertGreater(cmd.returncode, 0, 'CLI return code must be strictly positive')


class TestCliMFA(CliMFATest):

    def test_no_edgerc(self):
        """
        Call CLI with a bogus edgerc file, help should be displayed.
        """
        cmd = self.cli_run('--edgerc', 'file_not_exist')
        stdout, stderr = cmd.communicate()
        self.cli_debug_output(cmd.returncode, stdout, stderr)
        self.assertIn("ERROR: No section", stderr.decode())
        self.assertEqual(cmd.returncode, 1, 'return code must be 1')

    def test_cli_info(self):
        cmd = self.cli_run('info')
        stdout, stderr = cmd.communicate()
        self.assertIn("cli-mfa_version", stdout.decode(encoding), "string 'cli-mfa_version' must exists")
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')

    def test_cli_version(self):
        """
        Ensure version of the CLI is displayed
        """
        cmd = self.cli_run('version')
        stdout, stderr = cmd.communicate()
        regexp = r'[0-9]+\.[0-9]+\.[0-9]+(-[a-z]*)*\n'
        self.assertRegex(stdout.decode(encoding), regexp,
                         'Version should be formatted as x.y.z or x.y.z-tag')
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')


if __name__ == '__main__':
    unittest.main()
