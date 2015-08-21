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
        r = Router(self.config)
        interfaces = r.interfaces
        self.assertItemsEqual(interfaces.keys(), interface_names)

    def test_interface_configlet(self):
        configlet = ['interface GigabitEthernet0/1.101\n',
                     ' description *** WAN interface ***\n',
                     ' encapsulation dot1Q 101\n',
                     ' ip address 192.168.100.2 255.255.255.252\n',
                     ' ip mtu 1500\n',
                     ' no cdp enable\n']
        r = Router(self.config)
        i = r.interfaces['GigabitEthernet0/1.101']
        self.assertSequenceEqual(i.config, configlet)

    def test_interface_ip(self):
        ip = IPv4Network('192.168.100.2/255.255.255.252')
        r = Router(self.config)
        i = r.interfaces['GigabitEthernet0/1.101']
        self.assertEqual(str(ip), str(i.ip))

    def test_qos_policy_names(self):
        qos_policy_names = ['SAMPLE-QOS-IN',
                            'SAMPLE-QOS-OUT',
                            'SAMPLE-SHAPER-OUT']
        r = Router(self.config)
        qos_policies = r.qos_policies
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
        r = Router(self.config)
        q = r.qos_policies['SAMPLE-QOS-OUT']
        self.assertSequenceEqual(q.config, configlet)


if __name__ == '__main__':
    unittest.main()
