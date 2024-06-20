#!/usr/bin/python

import json
import logging
from ansible.module_utils.basic import AnsibleModule
from sonarqube import Core, Group
from sonarqube.exceptions import (
    InsufficientPrivilegesException,
    GroupNotFoundException,
    GroupAlreadyExistsException,
    UnexpectedResponseException
)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    module_args = dict(
        name=dict(type='str', required=True),
        description=dict(type='str', required=False, default=None),
        state=dict(type='str', choices=['present', 'absent'], default='present'),
        url=dict(type='str', required=True),
        token=dict(type='str', required=True, no_log=True)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = module.params['name']
    description = module.params['description']
    state = module.params['state']
    url = module.params['url']
    token = module.params['token']

    core = Core(url=url, token=token)
    group = Group(core=core)

    try:
        if state == 'present':
            result = ensure_group_present(group, name, description)
        elif state == 'absent':
            result = ensure_group_absent(group, name)
        module.exit_json(**result)
    except (InsufficientPrivilegesException, GroupNotFoundException, GroupAlreadyExistsException, UnexpectedResponseException) as e:
        module.fail_json(msg=str(e))
    
    def ensure_group_present(group, name, description):
        try:
            group.create_group(name=name, description=description)
            return dict(changed=True, msg=f"Group '{name}' created")
        except GroupAlreadyExistsException:
            return dict(changed=False, msg=f"Group '{name}' already exists")
    
    def ensure_group_absent(group, name):
        try:
            group.delete_group(name=name)
            return dict(changed=True, msg=f"Group '{name}' deleted")
        except GroupNotFoundException:
            return dict(changed=False, msg=f"Group '{name}' does not exist")

if __name__ == '__main__':
    main()