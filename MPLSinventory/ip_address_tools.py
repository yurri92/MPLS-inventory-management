import sys

""" ip_address.py module that resolves differences between the ipaddr (python2)
    and ipaddress (python3) modules.

    In ipaddr (python2) a IPv4Network can be a single host address within a
    network (i.e. 10.0.1.20/24).
    In ipaddress (python3) a IPv4Network must be the network address
    (i.e. 10.0.1.0/24)

    The ipaddress module has a IPv4Interface object that can be a single host
    with a network (i.e. 10.0.1.20/24).

    The IPv4Interface cannot be used to verify if an IP address is in a network:
    >>> IPv4Address('10.0.1.1') in IPv4Interface('10.0.1.20/24')
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
    TypeError: argument of type 'IPv4Interface' is not iterable


    The IPv4Interface object as a network attribute that returns the IPv4Network:
    >>> IPv4Interface('10.0.1.20/24').network
    IPv4Network('10.0.1.0/24')

    >>> IPv4Address('10.0.1.1') in IPv4Interface('10.0.1.20/20').network
    True
"""

PYTHON2 = sys.version_info[0] < 3

if PYTHON2:
    from ipaddr import IPv4Network, IPv4Address

    class IPv4Interface(IPv4Network):
        # def __init__(self, config):
        #     super(IPv4Interface, self).__init__(config)

        @property
        def network(self):
            return IPv4Network(self)
else:
    from ipaddress import IPv4Network, IPv4Address, IPv4Interface
