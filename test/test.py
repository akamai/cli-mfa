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
EDGERC_SECTION=mysection
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
        if os.environ.get('EDGERC_SECTION'):
            command.extend(["--section", os.environ['EDGERC_SECTION']])
        command.extend(*args)
        print("\nCOMMAND: ", " ".join(command))
        return command

    def cli_run(self, *args):
        cmd = subprocess.Popen(self.cli_command(str(a) for a in args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return cmd

    def line_count(filename):
        count = 0
        with open(filename) as f:
            while next(f, False):
                count += 1
        return count

    def duplicate_count(filename):
        total_count = 0
        with open(filename) as infile:
            counts = collections.Counter(l.strip() for l in infile)
        for line, count in counts.most_common():
            if count > 1:
                print(f"DUPLICATE[{count}] {line}")
                total_count += 1
        return total_count


class TestEvents(CliMFATest):

    after = int(time.time() - 15 * 60)
    before = int(time.time())

    def test_events(self):
        """
        Fetch MFA events
        """
        cmd = self.cli_run("event", "--start", self.after, "--end", self.before)
        stdout, stderr = cmd.communicate(timeout=60)
        events = stdout.decode(encoding)
        # event_count = len(events.splitlines())
        # self.assertGreater(event_count, 0, "We expect at least one threat event")
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')


class TestUserGroupManagement(CliMFATest):

    def test_invite(self):
        cmd = self.cli_run('users', 'invite', '-g', 'NEW_GROUP')
        stdout, stderr = cmd.communicate()
        print(stdout)
        print(stderr)
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
            f"""user6@{domain},User6,Lastname6,user6.lastname6,NEW_GROUP2\n"""

        csv_fp, csv_filename = tempfile.mkstemp(text=True)
        with os.fdopen(csv_fp, 'w+t') as f:
            f.write(csv_content)

        cmd = self.cli_run('importusers', '--ignore-header', '-f', csv_filename)
        stdout, stderr = cmd.communicate()
        print(stdout)
        print(stderr)
        os.unlink(csv_filename)
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')

    def test_csvfiledoesntexist(self):
        cmd = self.cli_run('importusers', '-f', 'csv_file_not_exist')
        stdout, stderr = cmd.communicate()
        self.assertGreater(cmd.returncode, 0, 'CLI return code must be strictly positive')


class TestCliMFA(CliMFATest):

    def test_no_edgerc(self):
        """
        Call CLI with a bogus edgerc file, help should be displayed.
        """
        cmd = self.cli_run('--edgerc', 'file_not_exist')
        stdout, stderr = cmd.communicate()
        output = stdout.decode(encoding)
        error = stderr.decode(encoding)
        self.assertIn("ERROR: No section", error)
        self.assertEqual(cmd.returncode, 1, 'return code must be 1')

    def test_cli_version(self):
        """
        Ensure version of the CLI is displayed
        """
        cmd = self.cli_run('version')
        stdout, stderr = cmd.communicate()
        self.assertRegex(stdout.decode(encoding), r'[0-9]+\.[0-9]+\.[0-9]+\n', 'Version should be x.y.z')
        self.assertEqual(cmd.returncode, 0, 'return code must be 0')


if __name__ == '__main__':
    unittest.main()
