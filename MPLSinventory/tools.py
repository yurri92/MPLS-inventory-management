from __future__ import print_function
import os
import json
import csv
import re
from copy import copy
from tqdm import tqdm

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
                if isinstance(result, tuple):
                    if any(result):  # reduce(lambda x, y: bool(x) or bool(y), result):   # test if tuple has results
                        break
                else:           # if result is not a tuple
                    break

    if isinstance(thing, str):   # or isinstance(thing, unicode):
        if regex not in COMPILED_REGEXES.keys():
            COMPILED_REGEXES[regex] = re.compile(regex)
        compiled_regex = COMPILED_REGEXES[regex]
        n = compiled_regex.groups       # number of capture groups requested
        result = tuple(n * [''])        # create tuple of empty strings
        match = compiled_regex.search(thing)
        # match = re.search(compiled_regex, thing)
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
                if any(r):     # reduce(lambda x, y: bool(x) or bool(y), r):   # test if tuple has results
                    result += [r]
    return result


def list_files(regex, path):
    return search_all(regex, os.listdir(path))


def read_files_to_objects(path, result_type, regex=r'(.+)', id='', verbose=False):
    result = {}
    file_names = list_files(regex, path)
    # if verbose:
    #     file_names = tqdm(file_names)
    total = len(file_names)
    for i, file_name in enumerate(file_names, 1):
        if verbose:
            # pass
            print("opening : {}/{} {}/{}...".format(i, total, path, file_name), end="")
        value = result_type.load(file_name, path=path)
        if value:
            key = getattr(value, id, file_name)
            result[key] = value
            # del value.config
            if verbose:
                # pass
                print("parsed config for :{}".format(key))
        else:
            if verbose:
                # pass
                print("skipping")
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
    """to improve, convert ip objects to str (if type is ip then str(obj))"""
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


def save_dict_as_csv(jdict, filename, attributes=None, sort_by=None, group_by=None):
    keylist = list(jdict.keys())
    if attributes is None:
        attributes = list(jdict[keylist[0]].keys())
    if sort_by:
        emptys = [key for key in keylist if not jdict[key][sort_by]]
        keylist = [key for key in keylist if jdict[key][sort_by]]
        keylist = sorted(keylist, key=lambda i: jdict[i][sort_by])
        keylist.extend(emptys)
    if group_by:
        keylist2 = copy(keylist)
        keylist = []
        while keylist2:
            key = keylist2.pop(0)
            keylist.append(key)
            if jdict[key][group_by]:
                group_id = jdict[key][group_by]
                group = []
                for key in keylist2:
                    if jdict[key][group_by] == group_id:
                        group.append(key)
                keylist.extend(group)
                for key in group:
                    keylist2.remove(key)

    with open(filename, 'w') as fp:
        f = csv.writer(fp)
        f.writerow(attributes)
        for key in keylist:
            item = jdict[key]
            row = []
            for attribute in attributes:
                value = ''
                if attribute in item.keys():
                    value = item[attribute]
                    #  if isinstance(value, list):
                    #   value = '; '.join(value)      # TODO doesnt work if value is a list of lists or tuples
                row.append(value)
            if "lan_ips" in item.keys():
                row.extend(item["lan_ips"])
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
    if isinstance(json_object, str): # or isinstance(json_object, unicode):
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


def combine(dict1, dict2, match_function, key_prepend='', verbose=False):
    """combine the json_objects in dict1 with dict2
    - match_function(json_object, dict2) will return the best matching json_object from dict2
    - dict1 will contain all the combined jsons
    - the keys of the copied items will be prepended with the key_prepend
    - ?? mismatching items will be stored in dict1['mismatch']
    - todo: add not used items from dict2
    """
    # empty_json_object2 = create_empty_template(dict2[dict2.keys()[0]])
    empty_json_object2 = create_empty_template(dict2[list(dict2.keys())[0]])

    if verbose:
        keylist = tqdm(dict1.keys())
    else:
        keylist = dict1.keys()

    for key1 in keylist:
        json_object1 = dict1[key1]
        json_object2 = match_function(json_object1, dict2)
        if not json_object2:
            json_object2 = empty_json_object2
        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)


def combine2(dict1, dict2, match_function, key_prepend=''):
    """combine the json_objects in dict1 with dict2 and create a new dict
    - match_function(json_object, dict2) will return the best matching json_object from dict2
    - dict1 will contain all the combined jsons
    - the keys of the copied items will be prepended with the key_prepend
    - ?? mismatching items will be stored in dict1['mismatch']
    - todo: add not used items from dict2
    """
    keys2 = list(dict2.keys())
    # empty_json_object1 = create_empty_template(dict1.values()[0])
    # empty_json_object2 = create_empty_template(dict2.values()[0])
    empty_json_object2 = create_empty_template(dict2[list(dict2.keys())[0]])
    empty_json_object1 = create_empty_template(dict1[list(dict1.keys())[0]])
    for key1, json_object1 in dict1.items():
        json_object2 = empty_json_object2
        key2 = match_function(json_object1, dict2)
        if key2:
            json_object2 = dict2[key2]
            if key2 in keys2:
                keys2.remove(key2)
        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)
    for i, key2 in enumerate(keys2):
        json_object1 = copy(empty_json_object1)
        json_object2 = dict2[key2]
        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)
        dict1['mismatch'+str(i)] = json_object1


def combine3(dict1, dict2, score_function, key_prepend='', add_unused=True, verbose=False, unknown='unknown'):
    """combine best match from dict2 to dict1 based on a score.
    For each item in dict1 the best possible candidate from dict2 is combined.

    - Calculates for each combination of items in dict1 and dict2 the score
    - For each item from dict1 all the possible candidates are selected from dict2
      based on max(score).
    - For each candidate from dict2 the max(score) to all items in dict1 is calculated.
    If these max(score)'s are identical there is a fit.
    If not, the canidate in dict2 has a better fit to another dict1 item.

    """
    empty_json_object1 = create_empty_template(dict1[list(dict1.keys())[0]])
    empty_json_object2 = create_empty_template(dict2[list(dict2.keys())[0]])
    # empty_json_object1 = create_empty_template(dict1.values()[0])
    # empty_json_object2 = create_empty_template(dict2.values()[0])
    keys1 = list(dict1.keys())
    keys2 = list(dict2.keys())
    used_keys2 = []
    scores_matrix = []
    candidates = {}

    if verbose:
        keylist = tqdm(keys1)
    else:
        keylist = keys1

    for k1 in keylist:
        # create matrix row
        row = []
        for k2 in keys2:
            score = score_function(dict1[k1], dict2[k2])
            row.append(score)
        scores_matrix.append(row)

        # find max scoring elements from dict2 as candidates for dict1[k1]
        candidates[k1] = []
        max_score = max(row)
        # find k2's for that score
        if max_score > 0:
            for i, (k2, score) in enumerate(zip(keys2, row)):
                if score == max_score:
                    candidates[k1].append((i, k2, score))

    for k1 in keys1:
        json_object1 = dict1[k1]
        json_object2 = empty_json_object2

        for i, k2, score in candidates[k1]:
            keys2_column = column(scores_matrix, i)
            max_score = max(keys2_column)
            if max_score == score:
                json_object2 = dict2[k2]
                used_keys2.append(k2)

        copy_json_object(json_object1, json_object2, key_prepend=key_prepend)

    if add_unused:
        # unused values from dict2 will be added in dict1 with a key 'unknown##'
        # where ## is a sequence nr
        # first find any 'unknown##' keys in dict1
        # and determine the starting value
        unknowns_in_keys1 = [k for k in keys1 if k.startswith(unknown)]
        l = len(unknown)
        unknown_numbers_in_keys1 = [int(k[l:]) for k in unknowns_in_keys1]
        if unknown_numbers_in_keys1:
            start_unknown_value = max(unknown_numbers_in_keys1)+1
        else:
            start_unknown_value = 1

        unused_keys2 = list(set(keys2)-set(used_keys2))
        for i, key2 in enumerate(unused_keys2, start=start_unknown_value):
            json_object1 = copy(empty_json_object1)
            json_object2 = dict2[key2]
            copy_json_object(json_object1, json_object2, key_prepend=key_prepend)
            dict1[unknown+str(i)] = json_object1


def column(matrix, i):
    return [row[i] for row in matrix]
