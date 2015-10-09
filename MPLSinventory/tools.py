import os
import json
import csv
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


def list_files(regex, path):
    return search_all(regex, os.listdir(path))


def read_files_to_objects(path, result_type, regex=r'(.+)', id='', verbose=False):
    result = {}
    file_names = list_files(regex, path)
    total = len(file_names)
    for i, file_name in enumerate(file_names, 1):
        if verbose:
            print "opening :", str(i) + '/' + str(total), path + '/' + file_name, "...",
        value = result_type.load(file_name, path=path)
        if value:
            key = getattr(value, id, file_name)
            result[key] = value
            if verbose:
                print "parsed config for :", key
        else:
            if verbose:
                print "skipping"
    return result


def assign_attr_if_better(attribute_name, obj1, obj2):
    """assign an attribute if from obj1 to obj2 if the attr has a value
    on obj1, and still has no valueon obj2"""
    attribute_obj1 = getattr(obj1, attribute_name, None)
    attribute_obj2 = getattr(obj2, attribute_name, None)
    if attribute_obj1 and not attribute_obj2:
        setattr(obj2, attribute_name, attribute_obj1)


def getattr_recursive(obj, name):
    """Gets attributes from objects recursively.

    'name' can contain multiple attributes
    'todo': lists and dicts

    """

    # split the name into a queue of keywords
    name_queue = []
    while name:
        if name[0] == '.':
            name = name[1:]
        attribute, remainder = search(r'^([\w_]+)(.*)', name)           # normal attribute name
        if attribute:
            name = remainder
            name_queue.append(attribute)
        key, remainder = search(r'^\[[\'\"](.+?)[\'\"]\](.*)', name)    # dictionary key
        if key:
            name = remainder
            name_queue.append(key)
        index, remainder = search(r'^\[(\d+)\](.*)', name)              # list index
        if index:
            name = remainder
            name_queue.append(int(index))

    # retrieve the keywords from the object.
    result = obj
    while name_queue and result:
        if isinstance(result, list):
            index = name_queue.pop(0)
            if index < len(result):
                result = result[index]
            else:
                result = ''
        elif isinstance(result, dict):
            key = name_queue.pop(0)
            if key in result.keys():
                result = result[key]
            else:
                result = ''
        else:
            attribute = name_queue.pop(0)
            result = getattr(result, attribute, '')
    return result


def create_dict_from_objects(objects, attributes=[]):
    """to improve, convert ip objects to str"""
    result = {}
    for key, my_obj in objects.items():
        if not attributes:
            result[key] = my_obj.json()
        else:
            r = {}
            for attribute in attributes:
                item = getattr_recursive(my_obj, attribute)
                if attribute.endswith('ip') and item:
                    item = str(item)
                if attribute == 'hsrp' and item:
                    item = str(item)
                r[attribute] = item
            result[key] = r
    return result


def save_dict_as_json(dict, filename):
    with open(filename, 'w') as fp:
        json.dump(dict, fp, indent=4)


def save_dict_as_csv(dict, filename, attributes=None):
    if attributes is None:
        attributes = dict[dict.keys()[0]].keys()
    with open(filename, 'wb') as fp:
        f = csv.writer(fp)
        f.writerow(attributes)
        for item in dict.values():
            row = []
            for attribute in attributes:
                value = ''
                if attribute in item.keys():
                    value = item[attribute]
                row.append(value)
            f.writerow(row)


def create_empty_template(json_object):
    if isinstance(json_object, dict):
        r = {}
        for key, value in json_object.items():
            r[key] = create_empty_template(value)
        return r
    if isinstance(json_object, list):
        r = []
        for value in json_object:
            i = create_empty_template(value)
            if i:
                r.append(i)
        return r
    if isinstance(json_object, str) or isinstance(json_object, unicode):
        return ''
    if isinstance(json_object, int) or isinstance(json_object, float):
        return 0


def copy_json_object(json_object1, json_object2, attributes=None, key_prepend=''):
    """copy attributes from json_object2 to json_object1
    - prepend the keys with key_prepend
    """
    if attributes is None:
        attributes = json_object2.keys()
    for attribute in attributes:
        key1 = key_prepend + attribute
        if key1 in json_object1.keys():
            if json_object1[key1] and not json_object2[attribute]:
                continue
        json_object1[key1] = json_object2[attribute]


def combine(dict1, dict2, match_function, key_prepend=''):
    """combine the json_objects in dict1 with dict2
    - match_function(json_object, dict2) will return the best matching json_object from dict2
    - dict1 will contain all the combined jsons
    - the keys of the copied items will be prepended with the key_prepend
    - ?? mismatching items will be stored in dict1['mismatch']
    """
    empty_json_object2 = create_empty_template(dict2[dict2.keys()[0]])
    for key1, json_object1 in dict1.items():
        json_object2 = match_function(json_object1, dict2)
        if not json_object2:
            json_object2 = empty_json_object2
        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)


# move to match_rules.py
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

