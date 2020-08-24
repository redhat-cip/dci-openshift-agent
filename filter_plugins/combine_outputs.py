from __future__ import absolute_import, division, print_function
__metaclass__ = type

from ansible.errors import AnsibleError, AnsibleFilterError
from ansible.module_utils._text import to_native

def combine_outputs_filter(input1, input2):
    combined = {}
    for key, value in input1.items():
        try:
            input2_value = input2[key]
        except KeyError as e:
            raise AnsibleFilterError("Missing key in Dictionary: %s" % to_native(e))
        combined_items = [value, input2_value]
        combined[key] = combined_items
    return combined

class FilterModule(object):
    def filters(self):
        return {
            'combine_outputs': combine_outputs_filter,
        }
