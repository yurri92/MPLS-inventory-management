import os
from collections import namedtuple
from ipaddr import IPv4Address
from regexstructure import RegexStructure
from tools import search_all

"""Module that provides classes to analyse and store the output of CLI commands
   on network device."""


class ParseShowCommand(RegexStructure):
    """ Base Class that analyses the output of 'show' commands on a Cisco device.

        Show commands are executed from the command prompt on a Cisco device.
        The output is usefull to analyse the status of a Cisco device. Tools and
        scripts exist to retrieve and store the outputs from these commands.

        This Base Class can be used create subclasses that analyze and store the outputs of:
        - show version
        - show ip interfaces brief
        - show diag
        - show ip bgp sum

        The outputs of these show commands should be stored in .txt files in a
        fixed directory structure:

        +- telnet
        |   +-- int
        |   |   +-- 192.168.0.92.txt
        |   |   +-- 192.168.1.92.txt
        |   +-- version
        |       +-- 192.168.0.92.txt
        |       +-- 192.168.1.92.txt

        The subdirectory is stored in the Class variable _showcommand.

        The filename is the management IP address of the device. This has been
        used to login to the device and execute the show command.

        The class is based upon a RegexStructure Base class, with a modified 'load' method.
        Files can be loaded using the IP address and path of the 'telnet' directory.

        The 'load' method adds the ip address as a text attribute to the created object.

        The _showcommand class variable can be set to the correct subdirectory by the
        Sub Classes.
    """
    _showcommand = ''

    def __init__(self, config):
        super(ParseShowCommand, self).__init__(config)

    @classmethod
    def load(cls, ip, path=''):
        """Loads outputs of telnet show commands.

           The directory is the path + the class variable _showcommand.
           The ip can be an IPv4Address object, or a string.
           There is no check if the variable ip is actually an IP address.

           The method sets an attribute 'ip' that is used to store
           ip or filename as string.

           to do:
           - filename can be anything
        """
        filename = str(ip)
        if not filename.endswith('.txt'):
            filename = filename + '.txt'
        if not path.endswith(cls._showcommand):
            path = os.path.join(path, cls._showcommand)
        result = super(ParseShowCommand, cls).load(filename, path)
        if result:
            result.ip = filename[:-4]   # remove '.txt' extension
        return result


class ShowVersion(ParseShowCommand):
    """ Class that analyses and stores the settings of 'show version' on a Cisco device.

        It uses regexes to find the model and the hostname.

        output_show_version = [
            'Cisco IOS Software, 2800 Software (C2800NM-SPSERVICESK9-M), Version 12.4(3)T5, RELEASE SOFTWARE (fc1)',
            'router-1-eth uptime is 1 year, 2 days, 27 minutes',
            'Cisco 2821 (revision 53.xx) with 514048K/10240K bytes of memory.']

        c = ShowVersion(output_show_version)
        c.model    -> '2821'
        c.hostname -> 'router-1-eth'
        c.ios_version -> ('12', '4', '3', 'T' ,'5')

        The 'load' method looks in the 'version' subdirectory of the path=''.
    """

    _showcommand = 'version'

    _single_attributes = {
        'model': (r'^\s*.isco\s+(\S+).+memory\.\s*$', str),
        'hostname': (r'^\s*(\S+)\s+uptime', str),
        'serial': (r'^\s*Processor\s+board\s+ID\s+(\S+)\s*$', str),
        'ios_version': (r'^.*IOS\s+.+,\s+Version\s*(\d+)\.(\d+)\((.+)\)([A-Z]*?)(\d*[a-z]*),.+$', tuple)
    }

    def __init__(self, config):
        super(ShowVersion, self).__init__(config)


IP_interface = namedtuple('IP_interface', ['interface', 'ip', 'status'])


class ShowIPInterfacesBrief(ParseShowCommand):
    """ Class that analyses and stores the ouput of 'show ip interfaces brief' on a Cisco device

        Finds the status of each interface and the hostname.

        The hostname is the final line of the text. The CLI script can append this,
        since it is the command prompt of a Cisco device.

        output_show_ip_interfaces_brief = [
            'Interface                  IP-Address      OK? Method Status                Protocol',
            'GigabitEthernet0/0         unassigned      YES NVRAM  up                    up',
            'Loopback1                  192.168.0.92    YES NVRAM  up                    up']

        c = ShowIPInterfacesBrief(output_show_ip_interfaces_brief)

        c.interface_status -> {'GigabitEthernet0/0': IP_interface(interface='GigabitEthernet0/0',
                                                                  ip='unassigned', status='up'),
                               'Loopback1': IP_interface(interface='Loopback1',
                                                         ip='192.168.0.92', status='up')}

        The 'load' method looks in the 'int' subdirectory of the path=''.
       """

    _showcommand = 'int'

    def __init__(self, config):
        super(ShowIPInterfacesBrief, self).__init__(config)
        self._set_interface_status()
        self._set_free_eth_ports()

    def _set_interface_status(self):
        self.interface_status = {}
        regex = r'^\s*(\S+)\s+(\S+)\s+(?:YES|NO)\s+\S+(.+)$'
        for interface, ip, status in search_all(regex, self.config):
            if 'admin' in status:
                status = 'admin_shut'
            elif 'down' in status:
                status = 'down'
            elif 'up' in status:
                status = 'up'
            self.interface_status[interface] = IP_interface(interface, ip, status)

    def _set_free_eth_ports(self):
        self.free_eth_ports = 0
        for interface, ip, status in self.interface_status.values():
            if ('Giga' in interface) or ('Fast' in interface):
                if '.' not in interface:
                    if status in ['admin_shut', 'down']:
                        self.free_eth_ports += 1


BGP_neighbor = namedtuple('BGP_neighbor', ['ip', 'remote_as', 'up_down', 'state'])


class ShowIPBGPSum(ParseShowCommand):
    """ Class that analyses and stores the ouput of 'show ip bgp sum' on a Cisco device

        Finds the status of each neighbor.

        output_show_ip_bgp_sum = [
            'BGP router identifier 192.168.0.92, local AS number 64512',
            'BGP activity 121216/119265 prefixes, 270540/268421 paths, scan interval 60 secs',
            'Neighbor        V           AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd',
            '10.0.10.2       4        65012       0       0        1    0    0 never    Idle (Admin)',
            '10.0.10.3       4        64512       0       0        0    0    0 never    Active',
            '192.168.100.1   4        10001 2266971 1872799   576999    0    0 3y12w        1620']

        c = ShowIPBGPSum(output_show_ip_bgp_sum)

        c.neighbors.keys() -> ['10.0.10.2', '10.0.10.3', '192.168.100.1']

        c.neighbor['10.0.10.2'].ip -> IPv4Address('10.0.10.2')
        c.neighbor['10.0.10.2'].remote_as -> 65012
        c.neighbor['10.0.10.2'].up_down -> 'never'
        c.neighbor['10.0.10.2'].state -> 'Idle (Admin)'
        c.neighbor['192.168.100.1'].state -> 1620

        The 'load' method looks in the 'bgp' subdirectory of the path=''.
       """

    _showcommand = 'bgp'

    def __init__(self, config):
        super(ShowIPBGPSum, self).__init__(config)
        self._set_bgp_neighbors()

    def _set_bgp_neighbors(self):
        self.neighbors = {}
        regex = r'^\s*(\d+\.\d+\.\d+\.\d+)\s+\d+\s+(\d+)\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\w+)\s+(.+)\s*$'
        for neighbor, remote_as, up_down, state in search_all(regex, self.config):
            if state.isdigit():
                state = int(state)
            self.neighbors[neighbor] = BGP_neighbor(ip=IPv4Address(neighbor),
                                                    remote_as=int(remote_as),
                                                    up_down=up_down,
                                                    state=state)
