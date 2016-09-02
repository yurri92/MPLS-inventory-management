import unittest
import os
from ipaddr import IPv4Address
from telnet import ShowVersion, ShowIPInterfacesBrief, ShowIPBGPSum

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
        cls.sb1 = ShowIPBGPSum.load(IP1, PATH)
        cls.sb2 = ShowIPBGPSum.load(IP2, PATH)

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

    def test_parse_show_version_ios_version1(self):
        ios_version = ('12', '4', '3', '', '')
        self.assertEqual(ios_version, self. sv1.ios_version)

    def test_parse_show_version_ios_version2(self):
        ios_version = ('15', '1', '2', 'M', '4')
        self.assertEqual(ios_version, self. sv2.ios_version)

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

    def test_free_eth_ports_r1(self):
        r = 0
        self.assertEqual(r, self.si1.free_eth_ports)

    def test_free_eth_ports_r2(self):
        r = 3
        self.assertEqual(r, self.si2.free_eth_ports)

    def test_neighbors_show_ip_bgp_sum_r1(self):
        neighbor_ips = ['10.0.10.2',
                        '10.0.10.3',
                        '192.168.100.1']
        neighbors = self.sb1.neighbors
        self.assertItemsEqual(neighbor_ips, neighbors.keys())

    def test_ip_show_ip_bgp_sum_r1(self):
        ip = IPv4Address('10.0.10.2')
        neighbor = self.sb1.neighbors['10.0.10.2']
        self.assertEqual(ip, neighbor.ip)

    def test_remote_as_show_ip_bgp_sum_r1(self):
        remote_as = 65012
        neighbor = self.sb1.neighbors['10.0.10.2']
        self.assertEqual(remote_as, neighbor.remote_as)

    def test_up_down_show_ip_bgp_sum_r1(self):
        up_down = 'never'
        neighbor = self.sb1.neighbors['10.0.10.2']
        self.assertEqual(up_down, neighbor.up_down)

    def test_state_show_ip_bgp_sum_r1(self):
        state = 'Idle (Admin)'
        neighbor = self.sb1.neighbors['10.0.10.2']
        self.assertEqual(state, neighbor.state)

    def test_up_down_show_ip_bgp_sum_r2(self):
        up_down = '3y12w'
        neighbor = self.sb2.neighbors['192.168.101.1']
        self.assertEqual(up_down, neighbor.up_down)

    def test_state_show_ip_bgp_sum_r2(self):
        state = 1620
        neighbor = self.sb2.neighbors['192.168.101.1']
        self.assertEqual(state, neighbor.state)
