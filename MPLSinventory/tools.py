import os
import json
import csv
from regexstructure import search_all
from telnet import ShowVersion, ShowIPInterfacesBrief


def list_files(regex, path):
    return search_all(regex, os.listdir(path))


def read_files_to_objects(path, result_type, regex=r'(.+)', id=''):
    result = {}
    for file_name in list_files(regex, path):
        value = result_type.load(file_name, path=path)
        key = getattr(value, id, file_name)
        result[key] = value
    return result


def getattr_recursive(obj, name):
    """Gets attributes from objects recursively.

    'name' can contain multiple attributes

    todo:
    - make function recursive
    - error handling in case attribute does not exist (raise same error)
    - getattr can be provided with default value (eliminate hasattr)"""
    while '.' in name:
        sub, name = name.split('.', 1)
        obj = getattr(obj, sub, '')
    return getattr(obj, name, '')


def create_dict_from_objects(objects, attributes):
    result = {}
    for key, my_obj in objects.items():
        dict = {}
        for attribute in attributes:
            item = getattr_recursive(my_obj, attribute)
            if attribute == 'mgmt_ip' and item:
                item = str(item.ip)
            if attribute == 'hsrp' and item:
                item = str(item)
            dict[attribute] = item
        result[key] = dict
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
                row.append(item[attribute])
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
    if attributes is None:
        attributes = json_object1.keys()
    for attribute in attributes:
        json_object2[key_prepend + attribute] = json_object1[attribute]


def combine(dict1, dict2, match_function, key_prepend=''):
    """combine the json_objects in dict1 with dict2
    - match_function(json_object, dict2) will return the best matching json_object from dict27
    - dictx will contain all the combined jsons
    - the keys of the copied items will be prepended with the key_prepend
    - ?? mismatching items will be stored in dict2['mismatch']
    """
    empty_json_object2 = create_empty_template(dict2[dict2.keys()[0]])
    for key1, json_object1 in dict1.items():
        json_object2 = match_function(json_object1, dict2)
        if not json_object2:
            json_object2 = empty_json_object2
        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)
        # HOLD continue here






