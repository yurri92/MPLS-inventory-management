import unittest
import os
from telnet import ShowVersion, ShowIPInterfacesBrief
# print ' no telnet test'

PATH = os.path.join('test', 'sample_telnet')
IP1 = '192.168.0.92'
IP2 = '192.168.1.92'


class TestParseShowVersion(unittest.TestCase):
    show_version = None

    @classmethod
    def setUpClass(cls):
        cls.sv1 = ShowVersion.load(IP1, PATH)
        cls.sv2 = ShowVersion.load(IP2, PATH)
        cls.si1 = ShowIPInterfacesBrief.load(IP1, PATH)
        cls.si2 = ShowIPInterfacesBrief.load(IP2, PATH)

    def test_parse_show_version_model1(self):
        model = '2821'
        self.assertEqual(model, self.sv1.model)

    def test_parse_show_version_hostname1(self):
        hostname = 'router-1-eth'
        self.assertEqual(hostname, self.sv1.hostname)

    def test_parse_show_version_model2(self):
        model = '887VA'
        self.assertEqual(model, self.sv2.model)

    def test_parse_show_version_hostname2(self):
        hostname = 'router-2-atm'
        self.assertEqual(hostname, self.sv2.hostname)

    def test_parse_show_ip_interfaces_brief_r1(self):
        r = {'GigabitEthernet0/0': 'up',
             'GigabitEthernet0/0.100': 'up',
             'GigabitEthernet0/0.200': 'up',
             'GigabitEthernet0/0.300': 'up',
             'GigabitEthernet0/0.400': 'up',
             'GigabitEthernet0/1': 'up',
             'GigabitEthernet0/1.101': 'up',
             'Loopback1': 'up'}
        self.assertItemsEqual(r, self.si1.interface_status)

    def test_parse_show_ip_interfaces_brief_r2(self):
        r = {'ATM0': 'up',
             'ATM0.1': 'up',
             'Ethernet0': 'admin_shut',
             'FastEthernet0': 'up',
             'FastEthernet1': 'admin_shut',
             'FastEthernet2': 'admin_shut',
             'FastEthernet3': 'admin_shut',
             'Loopback1': 'up',
             'Virtual-Access1': 'up',
             'Virtual-Access2': 'up',
             'Virtual-Access3': 'up',
             'Virtual-Template1': 'down',
             'Vlan1': 'admin_shut',
             'Vlan100': 'up',
             'Vlan200': 'up',
             'Vlan300': 'up',
             'Vlan400': 'up'}
        self.assertItemsEqual(r, self.si2.interface_status)
