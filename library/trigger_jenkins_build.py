#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: trigger_jenkins_build

short_description: Triggers a Jenkins Build

version_added: "1.0.0"

description: This module allows you to trigger a Jenkins job on a Jenkins instance, via the REST API.

options:
    name:
        description: This is the job to trigger.
        required: true
        type: str
    baseurl:
        description: The base URL of the Jenkins instance.
        required: true
        type: str
    parameters:
        description: The parameters to set when triggering the job.
        required: false
        type: dict
    username:
        description: The username to use for authentication.
        required: true
        type: string
    password:
        description: The password to use for authentication.
        required: true
        type: string

author:
    - James Ruskin (@jpruskin)
'''

EXAMPLES = r'''
# Trigger a job with a parameter
- name: Internalize Packages
  trigger_jenkins_build:
    name: Internalize packages from the Chocolatey Community and Licensed Repositories
    baseurl: http://localhost:8081
    parameters:
      P_PKG_LIST: "{{ InternalizedPackages | Join(',') }}"
    username: admin
    password: "{{ jenkins_password }}"
'''

RETURN = r'''
'''

from ansible.module_utils.basic import AnsibleModule
import requests

def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        name=dict(type='str', required=True),
        baseurl=dict(type='str', required=True),
        parameters=dict(type='dict', required=False, default=None),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True)
    )

    # Define our result object
    result = dict(
        changed=False
    )

    # Retrieve the values passed in by Ansible
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    # Lay out parameters, for easier testing
    name=module.params['name']
    baseurl=module.params['baseurl']
    parameters=module.params['parameters']
    username=module.params['username']
    password=module.params['password']

    # Create a session to handle authentication between the calls
    session = requests.Session()

    # Get a Jenkins-Crumb to authenticate with
    crumb = session.get(
        url=f"{baseurl}/crumbIssuer/api/json",
        auth=requests.auth.HTTPBasicAuth(username, password)
    ).json()['crumb']

    # Get Page Token
    token = session.post(
        url=f"{baseurl}/me/descriptorByName/jenkins.security.ApiTokenProperty/generateNewToken?newTokenName=GHA",
        auth=requests.auth.HTTPBasicAuth(username, password),
        headers={"Jenkins-Crumb":f"{crumb}"}
    ).json()['data']['tokenValue']

    # Invoke the Build with Parameters
    invoke = session.post(
        url=f"{baseurl}/job/{name}/buildWithParameters",
        auth=requests.auth.HTTPBasicAuth(username, token),
        headers={"Jenkins-Crumb":f"{crumb}"},
        data=parameters
    )

    if invoke.ok:
        result['changed'] = True
        module.exit_json(**result)
    else:
        module.fail_json(msg=f"Calling '{name}' failed:", **result)


def main():
    run_module()


if __name__ == '__main__':
    main()