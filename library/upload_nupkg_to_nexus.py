#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: upload_nupkg_to_nexus

short_description: Uploads a NUPKG file to a Nexus repository using the REST API, rather than nuget.

version_added: "1.0.0"

description: This module should allow you to upload an artifact to a Sonatype Nexus Repository repository.

options:
    file:
        description: The file (nupkg) to upload.
        required: true
        type: string
    baseuri:
        description: The base url of the Nexus instance to upload to.
        required: true
        type: string
    repository:
        description: The name of the nupkg repository to upload to.
        required: true
        type: string
    username:
        description: The username to authenticate with.
        required: true
        type: string
    password:
        description: The password to authenticate with.
        required: true
        type: string

author:
    - James Ruskin (@jpruskin)
'''

EXAMPLES = r'''
# Upload a package to a given repository
- name: Upload Packages to Setup Repository
  upload_nupkg_to_nexus:
    file: files/chocolatey.2.2.2.nupkg
    baseuri: "https://{{ nexus_fqdn }}:{{ nexus_port }}/nexus"
    repository: ChocolateySetup
    username: chocouser
    password: "{{ chocouser_password }}"
'''

RETURN = r'''
original_file:
    description: The original file param that was passed in.
    type: str
    returned: always
    sample: 'chocolatey.2.2.2.nupkg'
artifact_uri:
    description: The output path that the nupkg is stored at.
    type: str
    returned: always
    sample: 'https://nexus.example.com/repository/ChocolateySetup/chocolatey/2.2.2'
'''

from ansible.module_utils.basic import AnsibleModule
import requests
import jmespath
import re
import zipfile
import xml.etree.ElementTree as ET

def run_module():
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        baseuri=dict(type='str', required=True),
        repository=dict(type='str', required=True),
        file=dict(type='str', required=True),
        username=dict(type='str', required=True),
        password=dict(type='str', required=True)
    )

    # Define the output object
    result = dict(
        changed=False,
        original_file='',
        artifact_uri=''
    )

    # Retrieve parameters passed by Ansible
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # Redefining parameters as variables, for REASONS
    baseuri = module.params['baseuri']
    repository = module.params['repository']
    filename = module.params['file']
    user = module.params['username']
    password = module.params['password']

    result['original_file'] = filename
    api_url = f'{baseuri}/service/rest/v1/components'
    params = {'repository': repository}
    
    # Try and naively figure out the package id and version
    packageid, packageversion = get_packageid_and_version_from_path(filename)
    # Check to see if the package exists already in the repository
    existingPackage = get_existing_package(packageid, packageversion, api_url, repository, user, password)

    if module.check_mode:
        result['changed'] = True if existingPackage else False
        module.exit_json(**result)

    if existingPackage:
        result['artifact_uri'] = existingPackage
    else:
        # Upload the file if it's missing
        payload = {
            'nuget.asset': (open(filename, 'rb'))
        }
        response = requests.post(
            url=api_url,
            params=params,
            files=payload,
            auth=requests.auth.HTTPBasicAuth(user, password),
            verify=False,
            timeout=None
        )
        if response.ok:
            result['artifact_uri'] = f'{baseuri}/repository/{repository}/{packageid}/{packageversion}'
            result['changed'] = True
        else:
            module.fail_json(msg='The upload failed.', **result)

    module.exit_json(**result)

def get_packageid_and_version_from_path(path):
    archive = zipfile.ZipFile(path, 'r')
    nuspec_name = [ fi for fi in archive.namelist() if fi.endswith(".nuspec") ][0]
    nuspec = ET.fromstring(archive.read(nuspec_name))
    archive.close()
    return nuspec.find(".//{*}id").text, nuspec.find(".//{*}version").text

def get_existing_package(package_id, package_version, api_url, repository_name, user, password):    
    query_response = requests.get(
        url=api_url,
        params={"repository": repository_name},
        auth=requests.auth.HTTPBasicAuth(user, password)
    )
    found_package = jmespath.search(f"items[?name == `{package_id}` && version == `{package_version}`].assets[0].downloadUrl | [0]", query_response.json())
    # We should cache these, but I'm unsure it will work between queries, even on localhost
    while found_package == None and query_response.json()['continuationToken']:
        query_response = requests.get(
            url=api_url,
            params={"repository": repository_name, "continuationToken": query_response.json()['continuationToken']},
            auth=requests.auth.HTTPBasicAuth(user, password)
        )
        found_package = jmespath.search(f"items[?name == `{package_id}` && version == `{package_version}`].assets[0].downloadUrl | [0]", query_response.json())
    return found_package

def main():
    run_module()

if __name__ == '__main__':
    main()