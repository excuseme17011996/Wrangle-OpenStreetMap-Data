#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
"""
Your task is to explore the data a bit more.
Before you process the data and add it into MongoDB, you should check the "k"
value for each "<tag>" and see if they can be valid keys in MongoDB, as well as
see if there are any other potential problems.

We have provided you with 3 regular expressions to check for certain patterns
in the tags. As we saw in the quiz earlier, we would like to change the data
model and expand the "addr:street" type of keys to a dictionary like this:
{"address": {"street": "Some value"}}
So, we have to see if we have such tags, and if we have any tags with
problematic characters.

Please complete the function 'key_type', such that we have a count of each of
four tag categories in a dictionary:
  "lower", for tags that contain only lowercase letters and are valid,
  "lower_colon", for otherwise valid tags with a colon in their names,
  "problemchars", for tags with problematic characters, and
  "other", for other tags that do not fall into the other three categories.
See the 'process_map' and 'test' functions for examples of the expected format.
"""


problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
numbers = re.compile(r'[0-9]')
lower = re.compile(r'^([a-z]|_)*$')
upper = re.compile(r'^([A-Za-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
upper_colon = re.compile(r'^([A-Za-z]|_)*:([A-Za-z]|_)*$')
multiple_colons = re.compile(r'^(([A-Za-z]|_)*:)+([A-Za-z]|_)*$')


def key_type(k, counts, keys):
    if problemchars.search(k):
        key_type = "problemchars"
    elif numbers.search(k):
        key_type = "numbers"
    elif lower.search(k):
        key_type = "lower"
    elif upper.search(k):
        key_type = "upper"
    elif lower_colon.search(k):
        key_type = "lower_colon"
    elif upper_colon.search(k):
        key_type = "upper_colon"
    elif multiple_colons.search(k):
        key_type = "multiple_colons"
    else:
        key_type = "other"

    counts[key_type] += 1
    keys[key_type].append(k)

    return counts, keys


def process_map(filename):
    counts = {"lower": 0, "upper": 0, "lower_colon": 0, "upper_colon": 0, "multiple_colons": 0, "numbers": 0, "problemchars": 0, "other": 0}
    keys = {"lower": [], "upper": [], "lower_colon": [], "upper_colon": [], "multiple_colons": [], "numbers": [], "problemchars": [], "other": []}
    for tag_key in all_tag_keys(filename):
        results, others = key_type(tag_key, counts, keys)

    return {'counts': results, 'keys': keys}

def all_tag_keys(filename):
    results = []
    for _, element in ET.iterparse(filename):
        if element.tag == "tag":
            results.append(element.get("k"))
    return results

def unique_tag_keys(filename):
    return set(all_tag_keys(filename))

def test():
    # You can use another testfile 'map.osm' to look at your solution
    # Note that the assertion below will be incorrect then.
    # Note as well that the test function here is only used in the Test Run;
    # when you submit, your code will be checked against a different dataset.
    results = process_map('example.osm')
    pprint.pprint(results['counts'])
    assert results['counts'] == {"lower": 5, "upper": 1, "lower_colon": 0, "upper_colon": 0, "multiple_colons": 0, "numbers": 0, "problemchars": 1, "other": 0}


if __name__ == "__main__":
    test()
