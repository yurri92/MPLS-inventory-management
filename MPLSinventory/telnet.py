import os
from regexstructure import RegexStructure
from tools import search_all


class ParseShowCommand(RegexStructure):
    """Class that analyses and stores the out put of 'show'commands on a Cisco device"""
    _showcommand = ''

    def __init__(self, config):
        super(ParseShowCommand, self).__init__(config)

    # get hostname from last line
    # load config based on ip only
    # version -> telnet/version/ip.txt

    @classmethod
    def load(cls, ip, path=''):
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
        self.interfaces = {}
        regex = r'^\s*(\S+)\s+\S+\s+(?:YES|NO)\s+\S+(.+)$'
        for interface, status in search_all(regex, self.config):
            if 'admin' in status:
                status = 'admin_shut'
            elif 'down' in status:
                status = 'down'
            elif 'up' in status:
                status = 'up'
            self.interfaces[interface] = status
 