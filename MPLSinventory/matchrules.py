from __future__ import print_function
""" Match rules for matching dictionary entries.
    can be used by tools.combine
    match_function(json_object, dict2) will return the best matching json_object from dict2 """


def match_telnet_to_router(router_json_object, telnet_dict):
    """match if loopback and hostname of the router correspend to the telnet_dict"""
    router_ip = router_json_object["interfaces['Loopback1'].ip.ip"]
    router_hostname = router_json_object["hostname"]
    for telnet_json_object in telnet_dict.values():
        telnet_ip = telnet_json_object['ip']
        telnet_hostname = telnet_json_object['hostname']
        if router_ip == telnet_ip and router_hostname == telnet_hostname:
            return telnet_json_object
    return None


def match_show_commands(showversion_json_object, showint_dict):
    for showint_json_object in showint_dict.values():
        if showversion_json_object['ip'] == showint_json_object['ip']:
            if showversion_json_object['hostname'] == showint_json_object['hostname']:
                return showint_json_object
    return None
