import unittest
import os
from router import Router
from ipaddr import IPv4Network, IPv4Address

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
        cls.r = Router(cls.config)

    def test_load(self):
        r = Router(self.config)
        self.assertEqual(r.config, self.config)

    def test_hostname(self):
        self.assertEqual(self.r.hostname, 'router-1')

    def test_interface_names(self):
        interface_names = ['Loopback1', 'Embedded-Service-Engine0/0',
                           'GigabitEthernet0/0', 'GigabitEthernet0/0.100',
                           'GigabitEthernet0/0.200', 'GigabitEthernet0/0.300',
                           'GigabitEthernet0/0.400', 'GigabitEthernet0/1',
                           'GigabitEthernet0/1.101', 'GigabitEthernet0/2']
        interfaces = self.r.interfaces
        self.assertItemsEqual(interfaces.keys(), interface_names)

    def test_interface_configlet(self):
        configlet = ['interface GigabitEthernet0/1.101\n',
                     ' description *** WAN interface ***\n',
                     ' encapsulation dot1Q 101\n',
                     ' ip address 192.168.100.2 255.255.255.252\n',
                     ' ip mtu 1500\n',
                     ' no cdp enable\n']
        i = self.r.interfaces['GigabitEthernet0/1.101']
        self.assertSequenceEqual(i.config, configlet)

    def test_interface_ip(self):
        ip = IPv4Network('192.168.100.2/255.255.255.252')
        i = self.r.interfaces['GigabitEthernet0/1.101']
        self.assertEqual(str(ip), str(i.ip))

    def test_interface_helpers(self):
        helpers = [IPv4Address('10.100.1.2'), IPv4Address('10.100.1.1')]
        i = self.r.interfaces['GigabitEthernet0/0.100']
        self.assertItemsEqual(i.helpers, helpers)

    def test_interface_vlan(self):
        vlan = 100
        i = self.r.interfaces['GigabitEthernet0/0.100']
        self.assertEqual(vlan, i.vlan)

    def test_parent_interface(self):
        parent = 'GigabitEthernet0/0'
        i = self.r.interfaces['GigabitEthernet0/0.100']
        self.assertEqual(parent, i.parent.name)

    def test_qos_policy_names(self):
        qos_policy_names = ['SAMPLE-QOS-IN',
                            'SAMPLE-QOS-OUT',
                            'SAMPLE-SHAPER-OUT']
        qos_policies = self.r.qos_policies
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
        q = self.r.qos_policies['SAMPLE-QOS-OUT']
        self.assertSequenceEqual(q.config, configlet)

    def test_qos_bandwidth(self):
        bandwidth = 18810
        q = self.r.qos_policies['SAMPLE-QOS-OUT']
        self.assertEqual(bandwidth, q.qos_bandwidth)

    def test_shaper_bandwidth(self):
        bandwidth = 19800
        q = self.r.qos_policies['SAMPLE-SHAPER-OUT']
        self.assertEqual(bandwidth, q.shaper)

    def test_sub_policy(self):
        sub_policy = 'SAMPLE-QOS-OUT'
        q = self.r.qos_policies['SAMPLE-SHAPER-OUT']
        self.assertEqual(sub_policy, q.sub_policy)

    def test_priority_class(self):
        priority_class = 'realtime_output'
        q = self.r.qos_policies['SAMPLE-QOS-OUT']
        self.assertEqual(priority_class, q.priority_class.name)


class TestMPLSRouter(object):
    """testclass for the MPLS router"""
    def __init__(self, arg):
        super(TestMPLSRouter, self).__init__()         


if __name__ == '__main__':
    unittest.main()
