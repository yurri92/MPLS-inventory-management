from __future__ import print_function
import os
from collections import OrderedDict
from MPLSinventory.tools import search


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
    _json_simplify = []

    def __init__(self, config):
        if isinstance(config, str):
            config = config.splitlines
        config = [line.rstrip() for line in config]
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

    def json(self):
        r = {k: self._make_json(v) for k, v in self.__dict__.items() if k != 'config'}
        for key in self._json_simplify:
            if key in r.keys() and r[key]:
                if 'name' in r[key].keys():
                    r[key] = r[key]['name']
                elif isinstance(r[key], dict):
                    r[key] = [i['name'] for i in r[key].values()]
        return r

    def _make_json(self, obj):
        if isinstance(obj, list):
            return [self._make_json(item) for item in obj]
        if hasattr(obj, "_asdict"):
            # object is a namedtuple convert to ordereddict
            return OrderedDict(zip(obj._fields, (self._make_json(item) for item in obj)))
        if isinstance(obj, tuple):
            return tuple([self._make_json(item) for item in obj])
        elif isinstance(obj, dict):
            return {k: self._make_json(v) for k, v in obj.items()}
        elif isinstance(obj, str): # or isinstance(obj, unicode):
            return obj
        elif isinstance(obj, int) or isinstance(obj, float):
            return obj
        elif hasattr(obj, 'json'):
            return obj.json()
        elif hasattr(obj, '__str__'):
            return str(obj)
        else:
            return obj

    @classmethod
    def load(cls, filename, path=''):
        path = os.path.join(path, filename)
        config = ''
        if os.path.isfile(path):
            with open(path, 'r') as fp:
                config = fp.readlines()
        if len(config) < 2:
            return None
        return cls(config)
