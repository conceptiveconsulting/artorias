import unittest
from unittest.mock import call, patch, MagicMock
from core.host import Host

class TestCoreHost(unittest.TestCase):

    @patch('core.host.__init__')
    def setUp(self, mock_host):
        self.host = Host()

    def test_has_web_interface(self):
        self.host._services = [{'id': '80'}]

        ret = self.host.has_web_interface()
        self.assertEquals(ret, True)

        self.host._services = [{'id': '22'}]

        ret = self.host.has_web_interface()
        self.assertEquals(ret, False)

    def test_has_auth_surface(self):
        self.host._services = [{'id': '22'}]

        ret = self.host.has_auth_surface()
        self.assertEquals(ret, True)

        self.host._services = [{'id': '8080'}]

        ret = self.host.has_auth_surface()
        self.assertEquals(ret, False)