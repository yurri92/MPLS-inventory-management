import unittest
import os
import sys
from router import Router, MPLSRouter
from ipaddr import IPv4Network, IPv4Address
from telnet import ShowVersion, ShowIPInterfacesBrief

print sys.version

PATH = os.path.join('test', 'sample_configs')
FILENAME_ETH = 'router_1_eth_conf.cfg'
FILENAME_ATM = 'router_2_atm_conf.cfg'

IP1 = '192.168.0.92'
IP2 = '192.168.1.92'
Router.telnet_dir = os.path.join('test', 'sample_telnet')


class TestRouter(unittest.TestCase):
    config = None

    @classmethod
    def setUpClass(cls):
        cls.r1 = Router.load(FILENAME_ETH, PATH)

    def test_load(self):
        path = os.path.join(PATH, FILENAME_ETH)
        file = open(path, 'rb')
        config = file.readlines()
        config = [l.rstrip() for l in config]
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
        configlet = ['interface GigabitEthernet0/1.101',
                     ' description *** WAN interface ***',
                     ' encapsulation dot1Q 101',
                     ' ip address 192.168.100.2 255.255.255.252',
                     ' ip mtu 1500',
                     ' no cdp enable']
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
                    'policy-map SAMPLE-QOS-OUT',
                    ' description QOS_OUTBOUND_POLICY',
                    ' class mgmt_output',
                    '  police 6000 6000 6000 conform-action set-dscp-transmit 0 exceed-action set-dscp-transmit 0 violate-action set-dscp-transmit 0',
                    '  bandwidth 190',
                    '  random-detect',
                    ' class realtime_output',
                    '  priority 6504 16000',
                    '  police 6504000 16000 16000 conform-action transmit  exceed-action drop  violate-action drop',
                    ' class gold_output',
                    '  bandwidth 3635',
                    '  random-detect dscp-based',
                    ' class silver_output',
                    '  bandwidth 3635',
                    '  random-detect dscp-based',
                    ' class bronze_output',
                    '  bandwidth 3635',
                    '  random-detect dscp-based',
                    ' class class-default',
                    '  bandwidth 1211',
                    '  random-detect']
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
        bgp_config = ['router bgp 64512',
                      ' bgp log-neighbor-changes',
                      ' network 10.0.10.0 mask 255.255.255.0',
                      ' network 10.0.20.0 mask 255.255.255.0',
                      ' network 10.0.30.0 mask 255.255.255.0',
                      ' network 10.0.40.0 mask 255.255.255.0',
                      ' aggregate-address 10.0.0.0 255.255.0.0 summary-only',
                      ' timers bgp 10 30',
                      ' neighbor 10.0.10.2 remote-as 65012',
                      ' neighbor 10.0.10.2 shutdown',
                      ' neighbor 10.0.10.3 remote-as 64512',
                      ' neighbor 10.0.10.3 next-hop-self',
                      ' neighbor 10.0.10.3 send-community both',
                      ' neighbor 10.0.10.3 prefix-list BLOCK_MGMT in',
                      ' neighbor 192.168.100.1 remote-as 10001',
                      ' neighbor 192.168.100.1 description *** EBGP to PE router ***',
                      ' neighbor 192.168.100.1 update-source GigabitEthernet0/1.101',
                      ' neighbor 192.168.100.1 send-community',
                      ' neighbor 192.168.100.1 soft-reconfiguration inbound',
                      ' neighbor 192.168.100.1 route-map SET-LOCAL-PREF in',
                      ' neighbor 192.168.100.1 filter-list 1 out']
        self.assertSequenceEqual(bgp_config, self.r1.bgp.config)

    def test_bgp_neighbors(self):
        bgp_neighbors = [(IPv4Address('10.0.10.3'), 64512),
                         (IPv4Address('192.168.100.1'), 10001)]
        self.assertItemsEqual(bgp_neighbors, self.r1.bgp.neighbors)

    def test_add_telnet_state(self):
        state_found = True
        self.r1.add_telnet_state(IP1)
        self.assertEqual(state_found, self.r1.state_found)


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

    def test_router_qos_interface(self):
        qos_interface = 'GigabitEthernet0/1'
        self.assertEqual(qos_interface, self.r1.qos_interface)

    def test_router_json(self):
        j = self.r1.json()
        qos_interface = 'GigabitEthernet0/1'
        self.assertEqual(j['qos_interface'], qos_interface)

    def test_router_hsrp(self):
        hsrp = '10.0.10.1'
        self.assertEqual(self.r1.hsrp, hsrp)


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
