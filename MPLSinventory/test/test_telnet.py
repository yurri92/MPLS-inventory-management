import unittest
import os
from telnet import ShowVersion
# print ' no telnet test'

PATH = os.path.join('test', 'sample_telnet')
TELNET_TEST_DIR = 'sample_telnet'
IP1 = '192.168.0.92'
IP2 = '192.168.1.92'

class TestParseShowVersion(unittest.TestCase):
    show_version = None

    @classmethod
    def setUpClass(cls):
        cls.sv1 = ShowVersion.load(IP1, PATH)
        cls.sv2 = ShowVersion.load(IP2, PATH)

    def test_parse_show_version_model1(self):
        model = '2821'
        self.assertEqual(model, self.sv1.model)

    def test_parse_show_version_hostname1(self):
        hostname = 'router-1-eth'
        self.assertEqual(hostname, self.sv1.hostname)
