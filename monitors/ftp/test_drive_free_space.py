import unittest

import mock

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
    @mock.patch("paramiko.SSHClient")
    def test_free_bytes_on_c_drive(self, mock_ssh_client, mock_getaddrinfo, mock_transport):
        # mock the SSHClient
        instance = mock_ssh_client.return_value
        
        # create a mock stdout
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = (
            b'Total # of free bytes        : 12345678\r\n'
            b'Total # of bytes             : 24691356\r\n'
            b'Total # of avail free bytes  : 12345678\r\n')

        instance.exec_command.return_value = (mock.Mock(), mock_stdout, mock.Mock())

        connec_dict = mock.Mock()
        connec_dict.hostname = self.host
        connec_dict.username = self.username
        connec_dict.password = self.password
        connec_dict.static_ip = None

        # Test the function
        result = SystemConnection(connec_dict).get_free_space()

        # Assert that the function returns the expected result
        self.assertEqual(result, self.expected_result)

    @mock.patch("paramiko.Transport")
    @mock.patch("socket.getaddrinfo")
    @mock.patch("paramiko.SSHClient")
    def test_get_system_time_wmic_success(self, mock_ssh_client, mock_getaddrinfo, mock_transport):
        instance = mock_ssh_client.return_value
        mock_stdout = mock.Mock()
        mock_stdout.read.return_value = b'\r\r\nLocalDateTime=20260918110316.983557-240\r\r\n'
        instance.exec_command.return_value = (None, mock_stdout, None)

        connec_dict = mock.Mock()
        connec_dict.hostname = self.host
        connec_dict.username = self.username
        connec_dict.password = self.password
        connec_dict.static_ip = None

        ssc = SystemConnection(connec_dict)
        result = ssc.get_system_time()
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.hour, 11)
        self.assertEqual(instance.exec_command.call_count, 1)

    @mock.patch("paramiko.Transport")
    @mock.patch("socket.getaddrinfo")
    @mock.patch("paramiko.SSHClient")
    def test_get_system_time_fallback_powershell(self, mock_ssh_client, mock_getaddrinfo, mock_transport):
        instance = mock_ssh_client.return_value

        mock_stdout_wmic = mock.Mock()
        mock_stdout_wmic.read.return_value = b"'wmic' is not recognized\r\n"

        mock_stdout_ps = mock.Mock()
        mock_stdout_ps.read.return_value = b"LocalDateTime=20260918110316.983557-240\r\n"

        instance.exec_command.side_effect = [
            (None, mock_stdout_wmic, None),
            (None, mock_stdout_ps, None)
        ]

        connec_dict = mock.Mock()
        connec_dict.hostname = self.host
        connec_dict.username = self.username
        connec_dict.password = self.password
        connec_dict.static_ip = None

        ssc = SystemConnection(connec_dict)
        result = ssc.get_system_time()
        self.assertEqual(result.year, 2026)
        self.assertEqual(instance.exec_command.call_count, 2)


if __name__ == '__main__':
    unittest.main()

# class MyTestCase(unittest.TestCase):
#     def test_get_free_space(self):
#         SystemConnection
#
#
# if __name__ == '__main__':
#     unittest.main()
