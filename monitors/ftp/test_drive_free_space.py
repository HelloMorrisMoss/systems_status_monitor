import socket
import unittest

import mock
import paramiko

from monitors.ftp.drive_free_space import SystemConnection


class TestFreeBytesOnCDrive(unittest.TestCase):
    def setUp(self):
        self.host = "mock_host"
        self.username = "mock_user"
        self.password = "mock_password"
        self.expected_result = 12345678

    # @mock.patch("paramiko.client.socket.socket")
    # @mock.patch("paramiko.client.socket.getaddrinfo")
    # @mock.patch("paramiko.client.SSHClient.exec_command")
    @mock.patch("paramiko.Transport")
    @mock.patch("socket.getaddrinfo")
    # @mock.patch("paramiko.client.SSHClient.exec_command")
    @mock.patch(paramiko.SSHClient)
    def test_free_bytes_on_c_drive(self, mock_transport, mock_getaddrinfo, mock_ssh_client):
        # mock the SFTPClient
        mock_ssh_client = mock.Mock()
        mock_ssh_client.stat.return_value.st_size = self.expected_result
        mock_ssh_client.connect = mock.Mock()

        mock_transport.return_value.open_ssh.return_value = mock_ssh_client

        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('127.0.0.1', 22))]

        # create a mock channel
        mock_channel = mock.Mock()
        mock_channel.recv_exit_status.return_value = 0

        # create a mock stdout
        mock_stdout = mock.Mock()
        mock_stdout.readlines.return_value = [
            'Total # of free bytes        : 12345678\r\n',
            'Total # of bytes             : 24691356\r\n',
            'Total # of avail free bytes  : 12345678\r\n']

        # configure the channel to return the mock stdout
        mock_channel.makefile.return_value = mock_stdout

        # configure the transport to return the mock channel
        mock_transport.return_value.open_channel.return_value = mock_channel

        # mock_std_out = '''< paramiko.ChannelFile
        # from < paramiko.Channel
        # 0(closed) -> < paramiko.Transport
        # at
        # 0x51544ac0(cipher
        # aes128 - ctr, 128
        # bits) (active; 0 open channel(s)) >> >'''
        # mock_exec_command.return_value = ['Total # of free bytes        : 12345678\r\n', 'Total # of bytes
        # : 24691356\r\n',
        #  'Total # of avail free bytes  : 12345678\r\n']

        # mock_getaddrinfo = mock.Mock()
        # getaddrinfo.return_value = (
        #     ("irrelevant", None, None, None, "whatever"),
        # )

        connec_dict = dict(hostname=self.host, username=self.username, password=self.password)

        # Test the function
        result = SystemConnection(connec_dict).get_free_space()

        # Assert that the function returns the expected result
        self.assertEqual(result, self.expected_result)


if __name__ == '__main__':
    unittest.main()

# class MyTestCase(unittest.TestCase):
#     def test_get_free_space(self):
#         SystemConnection
#
#
# if __name__ == '__main__':
#     unittest.main()
