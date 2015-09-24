import os
from regexstructure import RegexStructure, search, search_all
from ipaddr import IPv4Network, IPv4Address


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
        filename = str(ip) + '.txt'
        path = os.path.join(path, cls._showcommand)
        return super(ParseShowCommand, cls).load(filename, path)


class ShowVersion(ParseShowCommand):
    """Class that analyses and stores the settings of 'show version' on a Cisco device"""

    _showcommand = 'version'

    _single_attributes = {
        'model': (r'^\s*.isco\s+(\S+).+memory\.\s*$', str),
        'hostname': (r'^\s*(\S+)\s+uptime', str)
    }

    def __init__(self, config):
        super(ShowVersion, self).__init__(config)

    
def parse_show_interface_status(ip):
    interfaces = []
    hostname = ''
    regex = r'^\s*(\S+)\s+\S+\s+(?:YES|NO)\s+\S+(.+)$'
    text = load_telnet_file('int', ip)
    if text:
        for interface, status in search_all(regex, text):
            if 'admin' in status:
                status = 'admin_shut'
            elif 'down' in status:
                status = 'down'
            elif 'up' in status:
                status = 'up'
            interfaces.append((interface, status))
        hostname = text[-1]
    return {'interfaces': interfaces, 'hostname': hostname}
