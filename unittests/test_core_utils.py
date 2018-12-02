import unittest
from unittest.mock import call, patch, MagicMock
from core.utils import *

class TestCoreUtils(unittest.TestCase):

    @patch('core.utils.xml2json')
    @patch('core.utils.Host')
    @patch('core.utils.host_scan')
    def test_get_hosts(self, mock_scan, mock_host, mock_xml):
        mock_xml.return_value = {
            'nmaprun': {
                'host': [{
                    'address': {
                        '@addr': '127.0.0.1'
                    }
                }]
            }
        }
        mock_host.return_value = 'MockHost'

        ret = get_hosts('MockSubnet')
        self.assertEquals(ret, ['MockHost'])

    @patch('core.utils.xml2json')
    @patch('core.utils.port_scan')
    def test_get_services(self, mock_port, mock_xml):
        mock_xml.return_value = {
            'nmaprun': {
                'host': {
                    'ports': {
                        'port': [{
                            '@portid': '22',
                            'service': {'@name': 'ssh'},
                            'state': {'@state': 'open'},
                        }]
                    }
                }
            }
        }

        ret = get_services('MockHost')
        self.assertEquals(
            ret, {'ports': [{'state': 'open', 'id': '22', 'name': 'ssh'}]})

    def test_verify_subnet(self):
        # Test with no subnet notation
        ret = verify_subnet('1.1.1.1')
        self.assertEquals(ret, '')

        # Test with no IP notation
        ret = verify_subnet('/24')
        self.assertEquals(ret, '')

        # Test with good ip/subnet notation
        ret = verify_subnet('1.1.1.1/24')
        self.assertEquals(ret, '1.1.1.1/24')

    @patch('core.utils.parse')
    @patch('core.utils.error')
    @patch('core.utils.loads')
    @patch('core.utils.dumps')
    @patch('builtins.open')
    def test_xml2json(self, mock_open, mock_dumps, mock_loads, mock_error, mock_parse):
        mock_dumps.return_value = 'moreMocks'
        mock_loads.return_value = 'moreMocks'
        mock_parse = 'moreMocks'

        # Test bad file raises and returns None
        mock_open.side_effect = IOError()
        res = xml2json('mockFile')
        self.assertRaises(IOError)
        self.assertEquals(res, None)
        self.assertEquals(mock_open.call_count, 1)

        # Test good file read
        mock_open.return_value = 'mockMocks'
        res = xml2json('mockFile')
        self.assertEquals(res, None)
        self.assertEquals(mock_open.call_count, 2)

    @patch('builtins.open')
    @patch('core.utils.loads')
    @patch('core.utils.zap_spider_auth')
    @patch('core.utils.zap_spider')
    @patch('core.utils.start_zap')
    @patch('core.utils.nikto_scan_auth')
    @patch('core.utils.nikto_scan')
    @patch('core.utils.xml2json')
    def test_web_scan(self,
                      mock_xml,
                      mock_nikto,
                      mock_nikto_auth,
                      mock_start,
                      mock_spider,
                      mock_spider_auth,
                      mock_loads,
                      mock_open):
        host = MagicMock()
        host.get_services.return_value = [
            {
                'state': 'open',
                'id': '80',
                'name': 'MockPort'
            },
            {
                'state': 'open',
                'id': '22',
                'name': 'MockPort2'
            }
        ]
        host.get_credentials.return_value = {'user': 'user', 'passwd': 'password'}

        drive_web_scan(host, False)
        expected_calls = [
            call(mock_nikto())
        ]
        for c in expected_calls:
            self.assertIn(c, mock_xml.mock_calls)

        drive_web_scan(host, True)
        expected_calls = [
            call(mock_nikto_auth('user', 'passwd')),
        ]
        for c in expected_calls:
            self.assertIn(c, mock_xml.mock_calls)

    @patch('core.utils.loads')
    @patch('core.utils.error')
    @patch('builtins.open')
    @patch('core.utils.hydra_scan')
    @patch('core.utils.debug')
    def test_auth_scan(self, mock_debug, mock_hydra, mock_open, mock_error, mock_loads):
        host = MagicMock()
        host.get_services.return_value = [{'id': '8080'}]

        # Test with no auth ports to test
        ret = drive_auth_scan(host)
        self.assertEquals(ret, True)
        mock_hydra.assert_not_called()

        # Test with port to test
        host.get_services.return_value = [{'id': '22'}]
        loads.return_value = {'results': [{'login': 'mockuser', 'password': 'mockpw'}]}

        ret = drive_auth_scan(host)
        mock_hydra.assert_called_with(host, '22', 'ssh')
        self.assertNotEquals(host.get_services, {})

        # Test with exception ocurring
        mock_loads.side_effect = IOError

        ret = drive_auth_scan(host)
        self.assertEquals(ret, False)
