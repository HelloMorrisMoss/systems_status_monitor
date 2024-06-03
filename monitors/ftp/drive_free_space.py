import datetime
import os
import re

import paramiko

from log_setup import lg
from models.systems_settings import SystemModel

# pattern to grab only a continuous series of numerical characters from between non-numerical characters
byte_int_regex_ptn = re.compile('(?:\D*)(\d*)(?:\D*)')

# pattern to check for only a single letter
single_letter_ptn = re.compile('^[a-z|A-Z]$')

local_date_time_ptn = re.compile(  # to extract date-time info from wmic LocalDateTime return text
    rb'(?:\r\r\n)*LocalDateTime=(?P<year>\d{4})'
    rb'(?P<month>\d{2})'
    rb'(?P<day>\d{2})'
    rb'(?P<hour>\d{2})'
    rb'(?P<minute>\d{2})'
    rb'(?P<second>\d{2})'
    rb'\.(?P<microsecond>\d{6})'
    rb'-(?P<tzinfo>\d{3})(?:\r\r\n)*')


class SSHClientBase:
    """Base SSH class for basic SSH operations like connecting and transferring files."""

    def __init__(self, settings_dict: dict, retry=0):
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
                break
            except TimeoutError as to_er:
                timeout_er = to_er
                lg.warning('Could not connect to remote host.')
            finally:
                retry -= 1
        if timeout_er:
            raise timeout_er

    def close(self):
        self.ssh.close()

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

    @property
    def host(self):
        return self._settings_dict['hostname']


class SystemConnection(SSHClientBase):
    """Extended SSH class for additional functionalities like checking system time, changing system time, etc."""

    def __init__(self, system: SystemModel, retry=0):
        hostname = system.hostname if not system.static_ip else system.static_ip
        username = system.username
        password = system.password
        settings_dict = dict(hostname=hostname, username=username, password=password)
        super().__init__(settings_dict, retry)

        self.ldt_ptn: re.Pattern = local_date_time_ptn
        self._shell_type = None
        self.system = system

    def get_free_space(self, drive_to_check: str = 'c'):
        drive_to_check = drive_to_check.strip()
        if not re.match(r'^[a-zA-Z]$', drive_to_check):  # since this is set in the configuration
            raise ValueError(f'Drive letter must be a single letter. {drive_to_check}')

        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(f'fsutil volume diskfree {drive_to_check}:',
                                                                  timeout=5)
        ssh_lines = ssh_stdout.readlines()
        free_bytes, total_bytes, avail_free_bytes = [int(byte_int_regex_ptn.split(line)[1]) for line in ssh_lines]
        return avail_free_bytes

    def get_system_time(self):
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command('wmic os get LocalDateTime /value',
                                                                  timeout=5)
        output_text = ssh_stdout.read()
        system_time = datetime.datetime(
            **{k: int(v) if k != 'tzinfo' else None for k, v in
               self.ldt_ptn.match(output_text).groupdict().items()})
        return system_time

    def nudge_system_time(self, sign):
        s_lower = sign.lower()
        if s_lower in ('negative', '-'):
            sign_str = '-'
        elif s_lower in ('positive', '+'):
            sign_str = ''
        else:
            raise ValueError('The sign parameter can only be a string matching one of:'
                             ' "negative", "-", "positive", or "+".')
        update_string = (f'{"Powershell " if self.shell_type == "CMD" else ""}'
                         f'Set-Date (Get-Date).AddMilliseconds({sign_str}300)')
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(update_string, timeout=5)
        # output_lines = ssh_stdout.read()  # this will not return anything

    @property
    def shell_type(self):
        if self._shell_type is None:
            self._shell_type = self.check_cmd_or_powershell()
        return self._shell_type

    def check_cmd_or_powershell(self):
        check_string = '(dir 2>&1 *`|echo CMD);&<# rem #>echo ($PSVersionTable).PSEdition'
        ssh_stdin, ssh_stdout, ssh_stderr = self.ssh.exec_command(check_string, timeout=5)
        return ssh_stdout.read().strip()


#     ssh = paramiko.SSHClient()
#     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#     ssh.connect(server, username=username, password=password)
#     ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('fsutil volume diskfree c:')
#     ssh_lines = ssh_stdout.readlines()
#     free_bytes, total_bytes, avail_free_bytes = [int(byte_int_regex_ptn.split(line)[1]) for line in ssh_lines]
#     pass
