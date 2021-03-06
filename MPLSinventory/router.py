from __future__ import print_function
import re
from MPLSinventory.regexstructure import RegexStructure
from MPLSinventory.telnet import ShowVersion, ShowIPInterfacesBrief, ShowIPBGPSum
from MPLSinventory.tools import search, search_all, assign_attr_if_better
from MPLSinventory.ip_address_tools import IPv4Address, IPv4Interface


class RouterBGP(RegexStructure):
    """Class that analyses and stores the settings for BGP configuration"""

    _single_attributes = {
        'local_as': (r'^s*router\sbgp\s+(\d+)\s*$', int)
    }

    def __init__(self, config):
        super(RouterBGP, self).__init__(config)
        self.neighbors = self._get_bgp_neighbors()

    def _get_bgp_neighbors(self):
        active_neighbors = []
        regex = r'^\s*neighbor\s+(\d+\.\d+\.\d+\.\d+)\s+remote-as\s+(\d+)$'
        all_neighbors = search_all(regex, self.config)
        for neighbor, remote_as in all_neighbors:
            regex = r'^\s*neighbor\s+('+neighbor+')\s+shutdown'
            shutdown = bool(search(regex, self.config))
            if not shutdown:
                active_neighbors.append((IPv4Address(neighbor), int(remote_as)))
        active_neighbors = list(set(active_neighbors))
        return active_neighbors


class QoSClass(RegexStructure):
    """Class that analyses and stores the settings for a QoS class.

    Todo:
    - bandwidth remaining ratio
    -

    """
    _single_attributes = {
        'name':              (r'^\s*class\s(\S+)\s*$', str),
        'bandwidth':         (r'^\s*(?:bandwidth|priority)\s+(\d+)\s*', int),
        'bandwidth_percent': (r'^\s*(?:bandwidth|priority)\spercent\s+(\d+)\s*', int),
        'police':            (r'^\s*(?:police|police\srate)\s(\d+)\s*',
                              lambda x: int(x)/1000)
        }

    def __init__(self, config):
        super(QoSClass, self).__init__(config)


class QoSPolicy(RegexStructure):
    """Class that analyses and stores the settings for a QoS policy.

    Todo:
    -  bandwidth remaining ratio
    """
    _single_attributes = {
        'name':          (r'^\s*policy-map\s+(\S+)\s*$', str),
        'description':   (r'^\s*description\s+(.+)$', str),
        'sub_policy':    (r'^\s*service-policy\s+(\S+)\s*$', str),
        'shaper':        (r'^\s*shape\s+average\s+(\d+)\s*',
                          lambda x: int(x)/1000)
        }

    _multiple_children = {
        'qos_classes': ('class', QoSClass)
    }

    def __init__(self, config):
        super(QoSPolicy, self).__init__(config)
        self.qos_bandwidth = self._find_total_qos_bandwidth()
        self.priority_class = self._find_priority_class()
        if not self.qos_bandwidth and hasattr(self.priority_class, 'bandwidth_percent'):
            self.qos_bandwidth = self._find_total_bandwidth_percent()

    def _find_priority_class(self):
        result = ''
        for class_name, qos_class in self.qos_classes.items():
            if 'priority' in ''.join(qos_class.config[1:]):
                result = qos_class
        return result

    def _find_total_qos_bandwidth(self):
        qos_bandwidth = 0
        for class_name, qos_class in self.qos_classes.items():
            if qos_class.bandwidth:
                qos_bandwidth += qos_class.bandwidth
        return qos_bandwidth

    def _find_total_bandwidth_percent(self):
        qos_bandwidth = 0
        if self.priority_class.bandwidth_percent:
            x1 = self.priority_class.bandwidth_percent
            x2 = self.priority_class.police
            if x1 and x2:
                qos_bandwidth = int(x2/(x1/100.00))
        return qos_bandwidth


class Interface(RegexStructure):
    """Class that analyses and stores the settings for a Router interface.

        Todo:
      - secondary ip's
      - secondary standby groups
      - vrf
    """
    _single_attributes = {
        'name':               (r'^interface\s(\S+)\s*.*$', str),
        'description':        (r'^\s*description\s+(.+)$', str),
        'ip':                 (r'^\s*ip\saddress\s(\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+)\s*$',
                               lambda ip: IPv4Interface(re.sub(r'\s+', '/', ip))),
        'ip_unnumbered':      (r'^\s*ip\s+unnumbered\s+(\S+)\s*$', str),
        'ip_negotiated':      (r'^\s*ip\saddress\s(negotiated)\s*$', str),
        'admin_bandwidth':    (r'^\s*bandwidth\s+(\d+)', int),
        'hsrp':               (r'^\s*standby\s+\d+\s+ip\s+(\d+\.\d+\.\d+\.\d+)\s*$',
                               IPv4Address),
        'policy_in':          (r'^\s*service-policy\s+input\s+(\S+)\s*$', str),
        'policy_out':         (r'^\s*service-policy\s+output\s+(\S+)\s*$', str),
        'atm_bandwidth':      (r'^\s*(?:cbr|vbr-nrt)\s+(\d+)\s*', int),
        'rate_limit':         (r'^\s*rate-limit\s+output\s+(\d+)\s',
                               lambda x: int(x)/1000),
        'crypto':             (r'^\s*(crypto.+)$', str),
        'dialer_pool':        (r'^\s*dialer\s+pool\s+(\d+)\s*$', int),
        'dialer_pool_member': (r'^\s*dialer\s+pool-member\s+(\d+)\s*$', int),
        'dial_pool_number':   (r'^\s*.+dial-pool-number\s+(\d+)\s*$', int)
        }

    _json_simplify = ['parent']

    def __init__(self, config):
        super(Interface, self).__init__(config)
        self.parent = ''
        self.status = ''
        self._load_interface_details()    # (self)?

    def _load_interface_details(self):
        regex = r'^\s*ip\s+helper-address\s+(\d+\.\d+\.\d+\.\d+)\s*$'
        helpers = search_all(regex, self.config)
        helpers = map(lambda ip: IPv4Address(ip), helpers)
        self.helpers = list(set(helpers))

        regex = r'^\s*Vlan\s*(\d+)\s*$'
        vlan = search(regex, self.name)
        if not vlan:
            regex = r'^\s*encapsulation\s+dot1Q\s+(\d+)\s*$'
            vlan = search(regex, self.config)
        if vlan:
            self.vlan = int(vlan)


class Router(RegexStructure):
    """Class that analyses and stores the settings for a Router.


      Todo:
       - also use interfaces that are not shut down
       - constructor method, to create router from filename
       - change router to config
    """
    _single_attributes = {
        'hostname': (r'^hostname\s+(\S+)$', str)
        }
    _multiple_children = {
        'interfaces': ('interface', Interface),
        'qos_policies': ('policy-map\s+\S+', QoSPolicy)
        }
    _single_children = {
        'bgp': ('router bgp\s+\d+', RouterBGP)
        }

    telnet_dir = 'telnet'

    def __init__(self, config):
        super(Router, self).__init__(config)
        self._set_parent_interfaces()

    def add_telnet_state(self, ip):
        self.state_found = False
        self.show_version = ShowVersion.load(ip, self.telnet_dir)
        self.show_ip_interfaces_brief = ShowIPInterfacesBrief.load(ip, self.telnet_dir)
        self.show_ip_bgp_sum = ShowIPBGPSum.load(ip, self.telnet_dir)

        if self.show_version:
            del self.show_version.config
            del self.show_ip_interfaces_brief.config
            del self.show_ip_bgp_sum.config
            if self.hostname == self.show_version.hostname:
                self.state_found = True
        if self.state_found:
            self._set_interface_status()
            self._set_bgp_status()
            self._set_version()

    def _set_parent_interfaces(self):
        """Sets the parent attribute of an interface to the name of the parent interface.

        interfaces['VirtualTemplate1'].parent = 'ATM0.101'
        interfaces['ATM0.101'].parent = 'ATM0'

        Useful for finding QoS polices on parent interfaces
        to-do:
        - use full virtual interface
        """
        for name, interface in self.interfaces.items():
            parent = search(r'^\s*(\S+)\.\d+', name)
            if parent in self.interfaces.keys():
                self.interfaces[name].parent = self.interfaces[parent]

        # find the parent interface for a ppp Virtual-Template
        for name1 in self.interfaces.keys():
            if 'Virtual-Template' in name1:
                for name2, interface2 in self.interfaces.items():
                    regex = r'^\s*encapsulation.+ppp\s*(Virtual-Template\d+)'
                    if name1 == search(regex, interface2.config):
                        self.interfaces[name1].parent = interface2
                        break

        # find the parent interface for dialer interfaces
        for name1, interface1 in self.interfaces.items():
            if interface1.dialer_pool:
                for interface2 in self.interfaces.values():
                    if interface1.dialer_pool == interface2.dialer_pool_member:
                        self.interfaces[name1].parent = interface2
                        break
                    elif interface1.dialer_pool == interface2.dial_pool_number:
                        self.interfaces[name1].parent = interface2
                        break

    def _set_interface_status(self):
        interface_status = self.show_ip_interfaces_brief.interface_status
        for interface in self.interfaces.keys():
            if interface in interface_status.keys():
                self.interfaces[interface].status = interface_status[interface].status

    def _set_bgp_status(self):
        bgp_neighbor_status = self.show_ip_bgp_sum.neighbors
        if bgp_neighbor_status:
            for neighbor, asnr in self.bgp.neighbors:
                if str(neighbor) in bgp_neighbor_status.keys():
                    pass

    def _set_version(self):
        pass


class MPLSRouter(Router):
    """Analysis and stores the settings of a MPLS Router
       a mpls router has:
       - a wan interface
       - a interface where the qos policies are applied
       - qos attributes
       - a speed
       - redundancy"""

    service_provider_as_nrs = range(1, 64152)

    # example how to extend attributes
    _single_attributes = {
        'local_as': ('^\s*router\sbgp\s(\d+)\s*$', int)
        }
    _single_attributes.update(Router._single_attributes)

    # attributes that will be inherited from the wan interface to the router
    # improve the utilisation of qos attributes
    _wan_int_attributes = ['atm_bandwidth', 'admin_bandwidth', 'rate_limit']
    _wan_qos_attributes = ['shaper', 'qos_bandwidth']

    _json_simplify = ['wan']

    def __init__(self, config):
        super(MPLSRouter, self).__init__(config)
        self.wan = self._get_wan_interface()
        self._set_wan_attributes()
        self.redundancy = ''
        self.hsrp = self._get_hsrp_address()
        self.pair_with = ''

    def _get_wan_interface(self):
        wan = ''
        bgp_wan_ip = self._bgp_wan_neighbor()
        if bgp_wan_ip:
            for name, interface in self.interfaces.items():
                if interface.ip and bgp_wan_ip in interface.ip.network:
                    wan = interface
        return wan

    def _bgp_wan_neighbor(self):
        bgp_wan_neighbor = ''
        if self.bgp:
            for neighbor, remote_as in self.bgp.neighbors:
                if remote_as in self.service_provider_as_nrs:
                    bgp_wan_neighbor = neighbor
        return bgp_wan_neighbor

    def _set_wan_attributes(self):
        for attribute in self._wan_int_attributes + self._wan_qos_attributes:
            setattr(self, attribute, 0)

        self.qos_interface = ''
        interface = self.wan
        while interface:
            if interface.policy_out:
                qos_policy = self.qos_policies[interface.policy_out]
                self.qos_interface = interface.name
                assign_attr_if_better('shaper', qos_policy, self)
                if qos_policy.sub_policy:
                    qos_policy = self.qos_policies[qos_policy.sub_policy]
                for attribute in self._wan_qos_attributes:
                    assign_attr_if_better(attribute, qos_policy, self)
            for attribute in self._wan_int_attributes:
                assign_attr_if_better(attribute, interface, self)
            interface = interface.parent

        # improve: make configurable items more important than descriptive items
        # or if descriptive item is within range of configurable items
        self.bandwidth = max(self.shaper, self.qos_bandwidth, self.atm_bandwidth,
                             self.admin_bandwidth, self.rate_limit)

    def _get_hsrp_address(self):
        hsrp_list = []
        for interface in self.interfaces.values():
            if interface.hsrp:
                hsrp_list.append(interface.hsrp)
        if hsrp_list:
            return str(sorted(hsrp_list)[0])
        else:
            return ''
