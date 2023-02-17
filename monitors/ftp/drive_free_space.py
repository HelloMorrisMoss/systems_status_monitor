import os
import re

import paramiko

from log_setup import lg

# paramiko.util.log_to_file('logs\paramiko.log')

# pattern to grab only a continuous series of numerical characters from between non-numerical characters
byte_int_regex_ptn = re.compile('(?:\D*)(\d*)(?:\D*)')

# pattern to check for only a single letter
single_letter_ptn = re.compile('^[a-z|A-Z]$')


class SSH_Connection:
    """An SFTP over SSH class for retrieving files."""

    def __init__(self, settings_dict: dict, retry=0):
        """:param settings_dict: dict, a dictionary defining the ssh connection parameters: hostname, port, username,
                password

        """

        self._settings_dict = settings_dict
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.connect(retry=retry)

        except TimeoutError:
            lg.info("Could not connect to remote file host.")

    def connect(self, retry=0):
        retry += 1
        timeout_er = None
        while retry:
            try:
                self.ssh.connect(**self._settings_dict)
                timeout_er = None
            except TimeoutError as to_er:
                timeout_er = to_er
                lg.warning('Could not connect to remote host.')
            finally:
                retry -= 1
        if timeout_er:
            raise timeout_er

    def get_files(self, file_paths, destination):
        if isinstance(destination, str):
            destination_paths = [f'{destination}/{os.path.basename(fp)}' for fp in file_paths]
        else:
            destination_paths = destination
        with self.ssh.open_sftp() as sftp:
            for (fp, dp) in zip(file_paths, destination_paths):
                try:
                    sftp.get(fp, dp)
                except FileNotFoundError:
                    lg.exception('File not found on host: %s at filepath: %s', self._settings_dict['hostname'], fp)

    def get_free_space(self, drive_to_check: str = 'c'):
        drive_to_check = drive_to_check.strip()
        if not single_letter_ptn.match(drive_to_check):
            raise ValueError(f'Drive letter must be a single letter. {drive_to_check}')
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(f'fsutil volume diskfree {drive_to_check}:')
        ssh_lines = ssh_stdout.readlines()
        free_bytes, total_bytes, avail_free_bytes = [int(byte_int_regex_ptn.split(line)[1]) for line in ssh_lines]
        return avail_free_bytes

    @property
    def host(self):
        return self._settings_dict['hostname']

#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     ssh.connect(server, username=username, password=password)
#     ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('fsutil volume diskfree c:')
#     ssh_lines = ssh_stdout.readlines()
#     free_bytes, total_bytes, avail_free_bytes = [int(byte_int_regex_ptn.split(line)[1]) for line in ssh_lines]
#     pass
