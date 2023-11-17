# c4b-ansible.win_chocolateyagent

This role ensures that Chocolatey Agent is installed, and that Chocolatey is configured to connect to a provided CCM server.

To use this Windows role, add a task to your playbook as follows:

## Task examples:

```
- name: Connect to CCM
  include_role:
    name: win_chocolateyagent
  vars:
    ccm_hostname: ccm.example.com
    client_salt: !vault
    service_salt: !vault
    repository
      - name: ChocolateyInternal
        url: https://{{ nexus_host }}:{{ nexus_port }}/repository/ChocolateyInternal/
        username: chocouser
        password: ansible123!
```

## Requirements

This role requires a valid Chocolatey for Business license, and a connection to a Nuget repository containing the `chocolatey` and `chocolatey.extension` packages. It should only be used if you have a Chocolatey Central Management instance accessible to the host you're applying it to.

## Role Variables

You can pass in any of the supported variables for the `win_chocolateylicensed` role. See the [linked README](../win_chocolateylicensed/README.md) for further details on those variables.

The following variables are set to a default, but can be overridden:

| Variable     | Default      | Purpose                                                              |
| ------------ | ------------ | -------------------------------------------------------------------- |
| ccm_hostname | {{ccm_fqdn}} | A resolvable hostname for the Chocolatey Central Management service. |

One of the following variables are required by the `win_chocolateylicensed` role:

| Variable        | Example                | Purpose                                                 |
| --------------- | ---------------------- | ------------------------------------------------------- |
| license_path    | chocolatey.license.xml | The path to a valid Chocolatey for Business license.    | 
| license_content | {the license content}  | The content of a valid Chocolatey for Business license. |

Only one of `license_path` and `license_content` are required, though both can be skipped if a `chocolatey-license` package is available on a specified repository.

The following variables are completely optional:

| Variable            | Example  | Purpose                              |
| ------------------- | -------- | ------------------------------------ |
| client_salt         | {a salt} | A value to salt communication with.  |
| service_salt        | {a salt} | A value to salt communication with.  |

# Dependencies

- ansible.windows
- chocolatey.chocolatey
- win_chocolateylicensed
- community.windows