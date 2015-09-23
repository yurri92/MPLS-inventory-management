import os
from regexstructure import RegexStructure, search, search_all


def load_telnet_file(path, ip):
    result = []
    filename = str(ip)+'.txt'
    path = os.path.join('telnet', path, filename)
    if os.path.isfile(path):
        with open(path, 'r') as fp:
            result = fp.readlines()
    return result


def parse_show_version(ip):
    model = ''
    hostname = ''
    text = load_telnet_file('version', ip)
    if text:
        regex = r'^\s*.isco\s+(\S+).+memory\.\s*$'
        model = search(regex, text)
        hostname = text[-1]
    return {'model': model, 'hostname': hostname}


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
