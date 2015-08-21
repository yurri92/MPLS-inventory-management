import re
import os
from ipaddr import IPv4Network, IPv4Address

COMPILED_REGEXES = {}


def search(regex, thing):
    """ Regex search anything.

     Determine what class the thing is and convert that to a string or list of strings
     returns the results for the first occurance in the list of strings
     the result are the subgroups for the regex match
     - if the regex has a single capture group a single item is returned
     - if the regex has multiple capture groups, a tuple is returned with all subgroups
    """
    result = ()
    if isinstance(thing, list):
        for item in thing:
            result = search(regex, item)
            if result:
                break

    if isinstance(thing, str):
        if regex not in COMPILED_REGEXES.keys():
            COMPILED_REGEXES[regex] = re.compile(regex)
        compiled_regex = COMPILED_REGEXES[regex]
        n = compiled_regex.groups       # number of capture groups requested
        result = tuple(n * [''])        # create tuple of empty strings
        match = re.search(compiled_regex, thing)
        if match:
            result = match.groups('')
        if len(result) == 1:
            result = result[0]
    return result


def search_all(regex, thing):
    """ Regex search all lines in anything.

    determines what class the thing is and converts that to a list of things
    each item or line in the list is searched using the regex and search(regex, thing)
    if the item has a match, the results are added to a list
    """
    result = []
    if isinstance(thing, str):
        thing = thing.splitlines()
    if isinstance(thing, list):
        for item in thing:
            r = search(regex, item)
            if isinstance(r, str):
                if r:
                    result += [r]
            if isinstance(r, tuple):
                if reduce(lambda x, y: bool(x) or bool(y), r):   # test if tuple has results
                    result += [r]
    return result


def search_configlets(key, config, delimiter='!'):
    """Search a config and return a list of configlets that starts with the key.

        - key should be a string, e.g. 'interface'
        - config should be a list of lines or a string that can be split in multiple lines

        The configlet starts with the key, lines are added untill the delimiter or the key is found
        Todo:
        - stop when the indentation stops, see vrf configuration in BGP
    """
    result = []
    if isinstance(config, str):
        config = config.splitlines
    configlet = []
    track = False
    for line in config:
        if search('^\s*('+key+')', line) and track is False:
            configlet.append(line)
            track = True
        elif search('^\s*('+key+')', line) and track is True:
            result.append(configlet)
            configlet = []
            configlet.append(line)
        elif search('^\s*('+delimiter+')', line) and track is True:
            result.append(configlet)
            configlet = []
            track = False
        elif track is True:
            configlet.append(line)
    if configlet:
        result.append(configlet)
    return result


class RegexStructure(object):
    """Create attributes by applying a regex search on a config.

    This class is used for retrieving attributes from Cisco configurations

    Example:
    >>>class Router(RegexStructure):
    ...
    ...  _single_attributes = {'hostname': (r'^hostname\s+(\S+)$', str)}
    ...
    ...  def __init__(self, config):
    ...    super(Router, self).__init__(config)
    ...
    >>>r = Router('hostname my-test-router')
    >>>r.hostname
    'my-test-router'
    >>>

    The keys in the dictionary _single_attributes are the attribute names.
    Each value in this dictionary is a tuple that defines the regex and type.

    The regex should contain one match group '()'. The search function converts the
    configuration to a list of text strings, and searches for the first hit.

    The type conversion usually is str, but can be any function.

    Todo:
     - limit to one match group
     - named tuple?
     - default conversion is str.
     - attributes can not be changed by external operators.
     http://stackoverflow.com/questions/9920677/how-should-i-expose-read-only-fields-from-python-classes
     http://stackoverflow.com/questions/1735434/class-level-read-only-properties-in-python
     - add list attributes of certain class (interfaces, qos_policies etc.)
     - __repr__ should result in config
     - look at memory management....

     - define object-list (interfaces etc.)

    """
    _single_attributes = {}
    _multiple_children = {}
    _single_children = {}

    def __init__(self, config):
        self.config = config
        for name, (regex, result_type) in self._single_attributes.items():
            self._add_single_attribute(name, regex, result_type)
        for name, (key, result_type) in self._multiple_children.items():
            self._add_multiple_children(name, key, result_type)
        for name, (key, result_type) in self._single_children.items():
            self._add_single_children(name, key, result_type)

    def _add_single_attribute(self, name, regex, result_type):
        result = search(regex, self.config)
        if result:
            result = result_type(result)
        setattr(self, name, result)

    def _add_multiple_children(self, name, key, result_type):
        result = []
        if hasattr(result_type, '_single_attributes'):
            if 'name' in result_type._single_attributes.keys():
                result = {}
        configlets = search_configlets(key, self.config)
        for configlet in configlets:
            child = result_type(configlet)
            if isinstance(result, dict):
                result[child.name] = child
            else:
                result.append(child)
        setattr(self, name, result)

    def _add_single_children(self, name, key, result_type):
        result = ''
        configlets = search_configlets(key, self.config)
        if configlets:
            result = result_type(configlets[0])
        setattr(self, name, result)


class routerBGP(RegexStructure):
    """Class that analyses and stores the settings for BGP configuration"""

    _single_attributes = {
        'local_as': (r'^s*router\sbgp\s+(\d+)\s*$', int)
    }

    def __init__(self, config):
        super(routerBGP, self).__init__(config)
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
    -  bandwidth remaining ratio (ne-ceva-ams71-amh-eu, ne-ceva-ams71-amh-eu)
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
            if self.priority_class.bandwidth_percent:
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
        if self.ef.bandwidth_percent:
            x1 = self.ef.bandwidth_percent
            x2 = self.ef.police
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
        'name':              (r'^interface\s(\S+)\s*.*$', str),
        'description':       (r'^\s*description\s+(.+)$', str),
        'ip':                (r'^\s*ip\saddress\s(\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+)\s*$',
                              lambda ip: IPv4Network(re.sub(r'\s+', '/', ip))),
        'ip_unnumbered':     (r'^\s*ip\s+unnumbered\s+(\S+)\s*$', str),
        'ip_negotiated':     (r'^\s*ip\saddress\s(negotiated)\s*$', str),
        'admin_bandwidth':   (r'^\s*bandwidth\s+(\d+)', int),
        'hsrp':              (r'^\s*standby\s+\d+\s+ip\s+(\d+\.\d+\.\d+\.\d+)\s*$',
                              IPv4Address),
        'policy_in':         (r'^\s*service-policy\s+input\s+(\S+)\s*$', str),
        'policy_out':        (r'^\s*service-policy\s+output\s+(\S+)\s*$', str),
        'atm_bandwidth':     (r'^\s*(?:cbr|vbr-nrt)\s+(\d+)\s*', int),
        'rate_limit':        (r'^\s*rate-limit\s+output\s+(\d+)\s',
                              lambda x: int(x)/1000),
        'description_speed': (r'^\s*description\s+.+[S|s]peed:(\d+).+$', int),
        'description_oid':   (r'^\s*description\s+.+SR:(\d+).+$', str),
        'crypto':            (r'^\s*(crypto.+)$', str)
        }

    def __init__(self, config):
        super(Interface, self).__init__(config)
        self.parent = ''
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
        'bgp': ('router bgp\s+\d+', routerBGP)
        }

    def __init__(self, config):
        super(Router, self).__init__(config)
        self._set_parent_interfaces()

    def _set_parent_interfaces(self):
        """Sets the parent attribute of an interface to the name of the parent interface.

        interfaces['VirtualTemplate1'].parent = 'ATM0.101'
        interfaces['ATM0.101'].parent = 'ATM0'

        Useful for finding QoS polices on parent interfaces
        """
        for name, interface in self.interfaces.items():
            parent = search(r'^\s*(\S+)\.\d+', name)
            if parent in self.interfaces.keys():
                self.interfaces[name].parent = self.interfaces[parent]

    @classmethod
    def load(cls, filename, path=''):
        path = os.path.join(path, filename)
        file = open(path, 'rb')
        config = file.readlines()
        file.close
        return cls(config)


class MPLSRouter(Router):
    """Analysis and stores the settings of a MPLS Router
       a mpls router has:
       - a wan interface
       - a speed
       - redundancy"""

    service_provider_as_nrs = xrange(1, 64152)

    # example how to extend attributes
    _single_attributes = {
        'local_as': ('^\s*router\sbgp\s(\d+)\s*$', int)
        }
    _single_attributes.update(Router._single_attributes)

    def __init__(self, config):
        super(MPLSRouter, self).__init__(config)
        self.wan = self._get_wan_interface()

    def _get_wan_interface(self):
        wan = ''
        bgp_wan_ip = self._bgp_wan_neighbor()
        if bgp_wan_ip:
            for name, interface in self.interfaces.items():
                network = interface.ip
                if network and (bgp_wan_ip in network):
                    wan = interface
        return wan

    def _bgp_wan_neighbor(self):
        bgp_wan_neighbor = ''
        for neighbor, remote_as in self.bgp.neighbors:
            if remote_as in self.service_provider_as_nrs:
                bgp_wan_neighbor = neighbor
        return bgp_wan_neighbor
