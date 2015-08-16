import re
from ipaddress import IPv4Network, IPv4Address

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


class RegexStructure(object):
    """Create attributes by applying a regex search on a config.

    This class is used for retrieving attributes from Cisco configurations

    Example:
    >>>class Router(RegexStructure):
    ...
    ...  _attributes = {'hostname': (r'^hostname\s+(\S+)$', str)}
    ...
    ...  def __init__(self, config):
    ...    super(self.__class__, self).__init__(config)
    ...
    >>>r = Router('hostname my-test-router')
    >>>r.hostname
    'my-test-router'
    >>>

    The keys in the dictionary _attributes are the attribute names.
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
    _attributes = {}

    def __init__(self, config):
        self.config = config
        for name, (regex, result_type) in self._attributes.items():
            result = search(regex, self.config)
            if result:
                result = result_type(result)
            setattr(self, name, result)
