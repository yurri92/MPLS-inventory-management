import re

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


def assign_attr_if_better(attribute_name, obj1, obj2):
    """assign an attribute if from obj1 to obj2 if the attr has a value
    on obj1, and still has no value on obj2"""
    attribute_obj1 = getattr(obj1, attribute_name, None)
    attribute_obj2 = getattr(obj2, attribute_name, None)
    if attribute_obj1 and not attribute_obj2:
        setattr(obj2, attribute_name, attribute_obj1)


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
