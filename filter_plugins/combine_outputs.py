# Copyright: 2019, 2020, Alex Willmer <alex@moreati.org.uk>
# Licensed under the Apache License, Version 2.0

from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.module_utils._text import to_native

def combine_outputs_filter(input1, input2):
    combined = {}
    for item in input1.items():
        try:
            input2_value = input2[item[0]]
        except KeyError as e:
            raise AnsibleFilterError("Missing key in Dictionary: %s" % to_native(e))
        combined_items = [item[1], input2_value]
        combined[item[0]] = combined_items
    return combined

class FilterModule(object):
    def filters(self):
        return {
            'combine_outputs': combine_outputs_filter,
        }
