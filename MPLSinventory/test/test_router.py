import unittest
import os
import sys
from router import Router, MPLSRouter
from ipaddr import IPv4Network, IPv4Address

print sys.version

PATH = os.path.join('test', 'sample_configs')
FILENAME_ETH = 'router_1_eth_conf.cfg'
FILENAME_ATM = 'router_2_atm_conf.cfg'


class TestRouter(unittest.TestCase):
    config = None

    @classmethod
    def setUpClass(cls):
        cls.r1 = Router.load(FILENAME_ETH, PATH)

    def test_load(self):
        path = os.path.join(PATH, FILENAME_ETH)
        file = open(path, 'rb')
        config = file.readlines()
        file.close
        self.assertEqual(self.r1.config, config)

    def test_hostname(self):
        self.assertEqual(self.r1.hostname, 'router-1-eth')

    def test_interface_names_r1(self):
        interface_names = ['Loopback1', 'Embedded-Service-Engine0/0',
                           'GigabitEthernet0/0', 'GigabitEthernet0/0.100',
                           'GigabitEthernet0/0.200', 'GigabitEthernet0/0.300',
                           'GigabitEthernet0/0.400', 'GigabitEthernet0/1',
                           'GigabitEthernet0/1.101', 'GigabitEthernet0/2']
        interfaces = self.r1.interfaces
        self.assertItemsEqual(interfaces.keys(), interface_names)

    def test_interface_configlet(self):
        configlet = ['interface GigabitEthernet0/1.101\n',
                     ' description *** WAN interface ***\n',
                     ' encapsulation dot1Q 101\n',
                     ' ip address 192.168.100.2 255.255.255.252\n',
                     ' ip mtu 1500\n',
                     ' no cdp enable\n']
        i = self.r1.interfaces['GigabitEthernet0/1.101']
        self.assertSequenceEqual(i.config, configlet)

    def test_interface_ip(self):
        ip = IPv4Network('192.168.100.2/255.255.255.252')
        i = self.r1.interfaces['GigabitEthernet0/1.101']
        self.assertEqual(str(ip), str(i.ip))

    def test_interface_helpers(self):
        helpers = [IPv4Address('10.100.1.2'), IPv4Address('10.100.1.1')]
        i = self.r1.interfaces['GigabitEthernet0/0.100']
        self.assertItemsEqual(i.helpers, helpers)

    def test_interface_vlan(self):
        vlan = 100
        i = self.r1.interfaces['GigabitEthernet0/0.100']
        self.assertEqual(vlan, i.vlan)

    def test_parent_interface(self):
        parent = 'GigabitEthernet0/0'
        i = self.r1.interfaces['GigabitEthernet0/0.100']
        self.assertEqual(parent, i.parent.name)

    def test_qos_policy_names(self):
        qos_policy_names = ['SAMPLE-QOS-IN',
                            'SAMPLE-QOS-OUT',
                            'SAMPLE-SHAPER-OUT']
        qos_policies = self.r1.qos_policies
        self.assertItemsEqual(qos_policies.keys(), qos_policy_names)

    def test_qos_policy_configlet(self):
        configlet = [
                    'policy-map SAMPLE-QOS-OUT\n',
                    ' description QOS_OUTBOUND_POLICY\n',
                    ' class mgmt_output\n',
                    '  police 6000 6000 6000 conform-action set-dscp-transmit 0 exceed-action set-dscp-transmit 0 violate-action set-dscp-transmit 0\n',
                    '  bandwidth 190\n',
                    '  random-detect\n',
                    ' class realtime_output\n',
                    '  priority 6504 16000\n',
                    '  police 6504000 16000 16000 conform-action transmit  exceed-action drop  violate-action drop \n',
                    ' class gold_output\n',
                    '  bandwidth 3635\n',
                    '  random-detect dscp-based\n',
                    ' class silver_output\n',
                    '  bandwidth 3635\n',
                    '  random-detect dscp-based\n',
                    ' class bronze_output\n',
                    '  bandwidth 3635\n',
                    '  random-detect dscp-based\n',
                    ' class class-default\n',
                    '  bandwidth 1211\n',
                    '  random-detect\n']
        q = self.r1.qos_policies['SAMPLE-QOS-OUT']
        self.assertSequenceEqual(q.config, configlet)

    def test_qos_bandwidth(self):
        bandwidth = 18810
        q = self.r1.qos_policies['SAMPLE-QOS-OUT']
        self.assertEqual(bandwidth, q.qos_bandwidth)

    def test_shaper_bandwidth(self):
        bandwidth = 19800
        q = self.r1.qos_policies['SAMPLE-SHAPER-OUT']
        self.assertEqual(bandwidth, q.shaper)

    def test_sub_policy(self):
        sub_policy = 'SAMPLE-QOS-OUT'
        q = self.r1.qos_policies['SAMPLE-SHAPER-OUT']
        self.assertEqual(sub_policy, q.sub_policy)

    def test_priority_class(self):
        priority_class = 'realtime_output'
        q = self.r1.qos_policies['SAMPLE-QOS-OUT']
        self.assertEqual(priority_class, q.priority_class.name)

    def test_bgp_config(self):
        bgp_config = ['router bgp 64512\n',
                      ' bgp log-neighbor-changes\n',
                      ' network 10.0.10.0 mask 255.255.255.0\n',
                      ' network 10.0.20.0 mask 255.255.255.0\n',
                      ' network 10.0.30.0 mask 255.255.255.0\n',
                      ' network 10.0.40.0 mask 255.255.255.0\n',
                      ' aggregate-address 10.0.0.0 255.255.0.0 summary-only\n',
                      ' timers bgp 10 30\n',
                      ' neighbor 10.0.10.3 remote-as 64512\n',
                      ' neighbor 10.0.10.3 next-hop-self\n',
                      ' neighbor 10.0.10.3 send-community both\n',
                      ' neighbor 10.0.10.3 prefix-list BLOCK_MGMT in\n',
                      ' neighbor 192.168.100.1 remote-as 10001\n',
                      ' neighbor 192.168.100.1 description *** EBGP to PE router ***\n',
                      ' neighbor 192.168.100.1 update-source GigabitEthernet0/1.101\n',
                      ' neighbor 192.168.100.1 send-community\n',
                      ' neighbor 192.168.100.1 soft-reconfiguration inbound\n',
                      ' neighbor 192.168.100.1 route-map SET-LOCAL-PREF in\n',
                      ' neighbor 192.168.100.1 filter-list 1 out\n']
        self.assertSequenceEqual(bgp_config, self.r1.bgp.config)

    def test_bgp_neighbors(self):
        bgp_neighbors = [(IPv4Address('10.0.10.3'), 64512),
                         (IPv4Address('192.168.100.1'), 10001)]
        self.assertItemsEqual(bgp_neighbors, self.r1.bgp.neighbors)


class TestMPLSRouter(unittest.TestCase):
    config = None

    @classmethod
    def setUpClass(cls):
        path = os.path.join(PATH, FILENAME_ETH)
        file = open(path, 'rb')
        cls.config = file.readlines()
        file.close
        cls.r1 = MPLSRouter(cls.config)

    def test_local_as(self):
        local_as = 64512
        self.assertEqual(local_as, self.r1.bgp.local_as)

    def test_wan_interface(self):
        wan_interface = 'GigabitEthernet0/1.101'
        self.assertEqual(wan_interface, self.r1.wan.name)

    def test_router_shaper(self):
        router_shaper = 19800
        self.assertEqual(router_shaper, self.r1.shaper)

    def test_router_qos_bandwidth(self):
        router_qos_bandwidth = 18810
        self.assertEqual(router_qos_bandwidth, self.r1.qos_bandwidth)

    def test_router_bandwidth(self):
        router_bandwidth = 19800
        self.assertEqual(router_bandwidth, self.r1.bandwidth)


class TestMPLSRouter_ATM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r2 = MPLSRouter.load(FILENAME_ATM, PATH)

    def test_interface_names_r2(self):
        interface_names = ['Virtual-Template1', 'Vlan400',
                           'Vlan1', 'Vlan300', 'Ethernet0',
                           'ATM0', 'Vlan200', 'FastEthernet0',
                           'FastEthernet1', 'FastEthernet2',
                           'FastEthernet3', 'ATM0.1', 'Vlan100',
                           'Loopback1']
        interfaces = self.r2.interfaces
        self.assertItemsEqual(interfaces.keys(), interface_names)

    def test_parent_interface(self):
        interface = self.r2.interfaces['Virtual-Template1']
        parent = 'ATM0.1'
        self.assertEqual(parent, interface.parent.name)


if __name__ == '__main__':
    unittest.main()