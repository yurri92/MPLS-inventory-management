import os
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
            'router-1-eth uptime is 1 year, 2 days, 27 minutes',
            'Cisco 2821 (revision 53.xx) with 514048K/10240K bytes of memory.']

        c = ShowVersion(output_show_version)
        c.model    -> '2821'
        c.hostname -> 'router-1-eth'

        The 'load' method looks in the 'version' subdirectory of the path=''.
    """

    _showcommand = 'version'

    _single_attributes = {
        'model': (r'^\s*.isco\s+(\S+).+memory\.\s*$', str),
        'hostname': (r'^\s*(\S+)\s+uptime', str),
        'serial': (r'^\s*Processor\s+board\s+ID\s+(\S+)\s*$', str)
    }

    def __init__(self, config):
        super(ShowVersion, self).__init__(config)


class ShowIPInterfacesBrief(ParseShowCommand):
    """ Class that analyses and stores the ouput of 'show ip interfaces brief' on a Cisco device

        Finds the status of each interface and the hostname.

        The hostname is the final line of the text. The CLI script can append this,
        since it is the command prompt of a Cisco device.

        output_show_ip_interfaces_brief = [
            'Interface                  IP-Address      OK? Method Status                Protocol',
            'GigabitEthernet0/0         unassigned      YES NVRAM  up                    up',
            'Loopback1                  192.168.0.92    YES NVRAM  up                    up',
            'router-1-eth']

        c = ShowIPInterfacesBrief(output_show_ip_interfaces_brief)

        c.hostname -> 'router-1-eth'

        c.interfaces_status -> { 'GigabitEthernet0/0': 'up',
                                'Loopback1': 'up'}

        The 'load' method looks in the 'int' subdirectory of the path=''.
       """

    _showcommand = 'int'

    def __init__(self, config):
        super(ShowIPInterfacesBrief, self).__init__(config)
        self._set_interface_status()
        self._set_free_eth_ports()
        self.hostname = self.config[-1]

    def _set_interface_status(self):
        self.interface_status = {}
        regex = r'^\s*(\S+)\s+\S+\s+(?:YES|NO)\s+\S+(.+)$'
        for interface, status in search_all(regex, self.config):
            if 'admin' in status:
                status = 'admin_shut'
            elif 'down' in status:
                status = 'down'
            elif 'up' in status:
                status = 'up'
            self.interface_status[interface] = status

    def _set_free_eth_ports(self):
        self.free_eth_ports = 0
        for interface, status in self.interface_status.items():
            if ('Giga' in interface) or ('Fast' in interface):
                if '.' not in interface:
                    if status in ['admin_shut', 'down']:
                        self.free_eth_ports += 1
