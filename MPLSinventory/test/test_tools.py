import unittest
import os
import json
import tools
from router import MPLSRouter
from telnet import ShowVersion, ShowIPInterfacesBrief
from matchrules import match_telnet_to_router, match_show_commands

# test combine -> create json

# test classify -> based on json


TELNET_DIR = os.path.join('test', 'sample_telnet')
ROUTER_DIR = os.path.join('test', 'sample_configs')


class TestTools(unittest.TestCase):
    router_attributes = ['hostname', "interfaces['Loopback1'].ip.ip", 'hsrp',
                         'wan.name', 'wan.parent.name',
                         'qos_interface',
                         'qos_bandwidth', 'shaper', 'atm_bandwidth',
                         'admin_bandwidth', 'rate_limit',  'description_speed', 'bandwidth',
                         'local_as']

    show_int_attributes = ['hostname', 'ip', 'free_eth_ports']

    @classmethod
    def setUpClass(cls):
        version_dir = os.path.join(TELNET_DIR, 'version')
        interfaces_dir = os.path.join(TELNET_DIR, 'int')
        regex = r'(\d+\.\d+\.\d+\.\d+)'
        cls.routers = tools.read_files_to_objects(ROUTER_DIR, MPLSRouter, id='hostname')
        cls.showversions = tools.read_files_to_objects(version_dir, ShowVersion, regex=regex)
        cls.showinterfaces = tools.read_files_to_objects(interfaces_dir, ShowIPInterfacesBrief)

    def test_router_list_hostnames_as_keys(self):
        hostnames = ['router-1-eth', 'router-2-atm']
        self.assertItemsEqual(hostnames, self.routers.keys())

    def test_showversions_list_ips_as_keys(self):
        ips = ['192.168.0.92', '192.168.1.92']
        self.assertItemsEqual(ips, self.showversions.keys())

    def test_showinterfaces_list_filenames_as_keys(self):
        ips = ['192.168.0.92.txt', '192.168.1.92.txt']
        self.assertItemsEqual(ips, self.showinterfaces.keys())

    def test_router_list_type(self):
        router = self.routers['router-1-eth']
        self.assertIsInstance(router, MPLSRouter)

    def test_create_router_dict_hostnames(self):
        routers_d = tools.create_dict_from_objects(self.routers, attributes=self.router_attributes)
        hostnames = ['router-1-eth', 'router-2-atm']
        self.assertItemsEqual(hostnames, routers_d.keys())

    def test_create_router_dict_attributes(self):
        routers_d = tools.create_dict_from_objects(self.routers, attributes=self.router_attributes)
        router = routers_d['router-1-eth']
        self.assertItemsEqual(self.router_attributes, router.keys())

    def test_router1_dict_wan_interface(self):
        routers_d = tools.create_dict_from_objects(self.routers, attributes=self.router_attributes)
        router = routers_d['router-1-eth']
        wan = 'GigabitEthernet0/1.101'
        self.assertEqual(wan, router['wan.name'])

    def test_router2_dict_wan_interface(self):
        routers_d = tools.create_dict_from_objects(self.routers, attributes=self.router_attributes)
        router = routers_d['router-2-atm']
        wan = ''
        self.assertEqual(wan, router['wan.name'])

    def test_combine_show_commands(self):
        showversions_d = tools.create_dict_from_objects(self.showversions)
        showinterfaces_d = tools.create_dict_from_objects(self.showinterfaces,
                                                          attributes=self.show_int_attributes)
        tools.combine(showversions_d, showinterfaces_d, match_show_commands)
        keys = ['192.168.0.92', '192.168.1.92']
        self.assertItemsEqual(keys, showversions_d.keys())

    def test_combine_show_commands_attributes(self):
        showversions_d = tools.create_dict_from_objects(self.showversions)
        showinterfaces_d = tools.create_dict_from_objects(self.showinterfaces,
                                                          attributes=self.show_int_attributes)
        tools.combine(showversions_d, showinterfaces_d, match_show_commands)
        keys = ['hostname', 'ip', 'free_eth_ports', 'model']
        showversion = showversions_d['192.168.0.92']
        self.assertItemsEqual(keys, showversion.keys())

    def test_save_dict_as_json(self):
        showversions_d = tools.create_dict_from_objects(self.showversions)
        file_name_regex = r'(result_test\.json)'
        file_exists = tools.list_files(file_name_regex, '.')
        if file_exists:
            os.remove('result_test.json')
        tools.save_dict_as_json(showversions_d, 'result_test.json')
        file_exists = tools.list_files(file_name_regex, '.')
        self.assertEqual(file_exists[0], 'result_test.json')

    def test_load_dict_as_json(self):
        showversions_d = tools.create_dict_from_objects(self.showversions)
        file_name_regex = r'(result_test\.json)'
        file_exists = tools.list_files(file_name_regex, '.')
        if file_exists:
            os.remove('result_test.json')
        tools.save_dict_as_json(showversions_d, 'result_test.json')
        with open('result_test.json', 'r') as fp:
            showversions_l = json.load(fp)
        self.assertItemsEqual(showversions_d, showversions_l)

    def test_ordered_csv(self):
        showversions_d = tools.create_dict_from_objects(self.showversions)
        showinterfaces_d = tools.create_dict_from_objects(self.showinterfaces,
                                                          attributes=self.show_int_attributes)
        routers_d = tools.create_dict_from_objects(self.routers, attributes=self.router_attributes)
        tools.combine(showversions_d, showinterfaces_d, match_show_commands)
        tools.combine(routers_d, showversions_d, match_telnet_to_router)
        file_name_regex = r'(result_test\.csv)'
        file_exists = tools.list_files(file_name_regex, '.')
        if file_exists:
            os.remove('result_test.csv')
        tools.save_dict_as_csv(routers_d, 'result_test.csv',
                               attributes=self.router_attributes, sort_by='hostname')
        with open('result_test.csv', 'r') as fp:
            csv = fp.readlines()
            firstline = csv[1].split(',')
        self.assertEqual(firstline[0], 'router-1-eth')

    @classmethod
    def tearDownClass(cls):
        file_name_regex = r'(result_test\.json)'
        file_exists = tools.list_files(file_name_regex, '.')
        if file_exists:
            os.remove('result_test.json')
        file_name_regex = r'(result_test\.csv)'
        file_exists = tools.list_files(file_name_regex, '.')
        if file_exists:
            os.remove('result_test.csv')
