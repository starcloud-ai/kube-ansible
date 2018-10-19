from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleFilterError
import json

def convert2jsonstr(value, alias='convert2jsonstr'):
    return json.dumps(value)

# ---- Ansible filters ----
class FilterModule(object):
    ''' URI filter '''

    def filters(self):
        return {
            'convert2jsonstr': convert2jsonstr
        }