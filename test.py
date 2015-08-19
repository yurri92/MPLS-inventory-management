import unittest
import os
from router import search, search_all, RegexStructure, Router

DIR = 'sampleconfigs'
FILENAME = 'router_1_conf.cfg'


class TestRouter(unittest.TestCase):
    config = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(DIR, FILENAME)
        file = open(path, 'rb')
        cls.config = file.readlines()
        file.close

    def test_load(self):
        self.r = Router(self.config)
        self.assertEqual(self.r.config, self.config)

    def test_hostname(self):
        r = Router(self.config)
        self.assertEqual(r.hostname, 'router-1')

    def test_interface_names(self):
        interface_names = ['Loopback1', 'Embedded-Service-Engine0/0',
                           'GigabitEthernet0/0', 'GigabitEthernet0/0.100',
                           'GigabitEthernet0/0.200', 'GigabitEthernet0/0.300',
                           'GigabitEthernet0/0.400', 'GigabitEthernet0/1',
                           'GigabitEthernet0/1.101', 'GigabitEthernet0/2']
        interface_names = sorted(interface_names)
        r = Router(self.config)
        interfaces = r.interfaces
        self.assertEqual(self, sorted(interfaces.keys()), interface_names)

    def test_interface_configlet(self):
        configlet = ''
        r = Router(self.config)
        i = r.interfaces['GigabitEthernet0/1.101']
        self.assertEqual(self, i.config, configlet)


if __name__ == '__main__':
    unittest.main()
