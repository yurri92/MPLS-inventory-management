from __future__ import print_function
import unittest
import os
import six
from MPLSinventory.telnet import ShowVersion, ShowIPInterfacesBrief, ShowIPBGPSum, IP_interface
from MPLSinventory.ip_address_tools import IPv4Address

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

PATH = os.path.join(BASE_PATH, 'sample_telnet')
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
        r = {'GigabitEthernet0/0': IP_interface(interface='GigabitEthernet0/0', ip='unassigned', status='up'),
             'GigabitEthernet0/0.100': IP_interface(interface='GigabitEthernet0/0.100', ip='10.0.10.2', status='up'),
             'GigabitEthernet0/0.200': IP_interface(interface='GigabitEthernet0/0.200', ip='10.0.20.2', status='up'),
             'GigabitEthernet0/0.300': IP_interface(interface='GigabitEthernet0/0.300', ip='10.0.30.2', status='up'),
             'GigabitEthernet0/0.400': IP_interface(interface='GigabitEthernet0/0.400', ip='10.0.40.2', status='up'),
             'GigabitEthernet0/1': IP_interface(interface='GigabitEthernet0/1', ip='unassigned', status='up'),
             'GigabitEthernet0/1.101': IP_interface(interface='GigabitEthernet0/1.101', ip='192.168.100.2', status='up'),
             'Loopback1': IP_interface(interface='Loopback1', ip='192.168.0.92', status='up')}
        self.assertDictEqual(r, self.si1.interface_status)

    def test_parse_show_ip_interfaces_brief_r2(self):
        r = {'ATM0': IP_interface(interface='ATM0', ip='unassigned', status='up'),
             'ATM0.1': IP_interface(interface='ATM0.1', ip='unassigned', status='up'),
             'Ethernet0': IP_interface(interface='Ethernet0', ip='unassigned', status='admin_shut'),
             'FastEthernet0': IP_interface(interface='FastEthernet0', ip='unassigned', status='up'),
             'FastEthernet1': IP_interface(interface='FastEthernet1', ip='unassigned', status='admin_shut'),
             'FastEthernet2': IP_interface(interface='FastEthernet2', ip='unassigned', status='admin_shut'),
             'FastEthernet3': IP_interface(interface='FastEthernet3', ip='unassigned', status='admin_shut'),
             'Loopback1': IP_interface(interface='Loopback1', ip='192.168.1.92', status='up'),
             'Virtual-Access1': IP_interface(interface='Virtual-Access1', ip='unassigned', status='up'),
             'Virtual-Access2': IP_interface(interface='Virtual-Access2', ip='192.168.1.92', status='up'),
             'Virtual-Access3': IP_interface(interface='Virtual-Access3', ip='unassigned', status='up'),
             'Virtual-Template1': IP_interface(interface='Virtual-Template1', ip='192.168.1.92', status='down'),
             'Vlan1': IP_interface(interface='Vlan1', ip='unassigned', status='admin_shut'),
             'Vlan100': IP_interface(interface='Vlan100', ip='10.1.10.2', status='up'),
             'Vlan200': IP_interface(interface='Vlan200', ip='10.1.20.2', status='up'),
             'Vlan300': IP_interface(interface='Vlan300', ip='10.1.30.2', status='up'),
             'Vlan400': IP_interface(interface='Vlan400', ip='10.1.40.2', status='up')}
        self.assertDictEqual(r, self.si2.interface_status)

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
        # self.assertItemsEqual(neighbor_ips, neighbors.keys())
        six.assertCountEqual(self, neighbor_ips, neighbors.keys())

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

if __name__ == '__main__':
    unittest.main()
