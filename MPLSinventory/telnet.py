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
        """
        filename = str(ip)
        if not filename.endswith('.txt'):
            filename = filename + '.txt'
        if not path.endswith(cls._showcommand):
            path = os.path.join(path, cls._showcommand)
        result = super(ParseShowCommand, cls).load(filename, path)
        result.ip = filename[:-4]
        return result


class ShowVersion(ParseShowCommand):
    """Class that analyses and stores the settings of 'show version' on a Cisco device"""

    _showcommand = 'version'

    _single_attributes = {
        'model': (r'^\s*.isco\s+(\S+).+memory\.\s*$', str),
        'hostname': (r'^\s*(\S+)\s+uptime', str)
    }

    def __init__(self, config):
        super(ShowVersion, self).__init__(config)


class ShowIPInterfacesBrief(ParseShowCommand):
    """Class that analyses and stores the ouput of 'show ip interfaces brief' on a Cisco device"""

    _showcommand = 'int'

    def __init__(self, config):
        super(ShowIPInterfacesBrief, self).__init__(config)
        self._set_interface_status()
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
 