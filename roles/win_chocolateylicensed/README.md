# c4b-ansible.win_chocolateylicensed

This role ensures Chocolatey and Chocolatey.Extension are installed, and a valid license is in place.

To use this Windows role, add a task to your playbook as follows:

## Task examples:

You can install it, providing a license path and internal infrastructure to provide nupkgs:

```
- name: Bootstrap Chocolatey for Business
  include_role:
    name: win_chocolateylicensed
  vars:
    license_path: "{{ chocolatey_license_path }}"
    repository:
      - name: ChocolateyInternal
        url: https://nexus.example.com:8443/repository/ChocolateyInternal/
        user: chocouser
        password: !vault...
```

You can instead provide the license content, by passing `license_content` instead of `license_path`.

If you don't provide values to direct you to a specific repository, it will use existing Chocolatey infrastructure to source installation files.

```
- name: Bootstrap Chocolatey for Business from Chocolatey Licensed Feed
  include_role:
    name: win_chocolateylicensed
  vars:
    license_content: "{{ chocolatey_license }}"
```

We provide default configuration and features, but if you want to configure your own you can pass additional variables:

```
- name: Bootstrap Chocolatey for Business with Additional Configuration
  include_role:
    name: win_chocolateylicensed
  vars:
    license_content: "{{ chocolatey_license }}"
    chocolatey_features:
      - allowGlobalConfirmation: enabled
      - allowEmptyChecksumsSecure: disabled
    chocolatey_config:
      - cacheLocation: C:\choco\cache
```

> **Note:** Passing features and config will override our defaults. If you want to supplement the defaults, we recommend adding a [`win_chocolatey_config`](https://docs.ansible.com/ansible/latest/collections/chocolatey/chocolatey/win_chocolatey_config_module.html) or []`win_chocolatey_feature`](https://docs.ansible.com/ansible/latest/collections/chocolatey/chocolatey/win_chocolatey_feature_module.html) step after adding this role.

## Requirements

This role requires a valid Chocolatey for Business license, and a connection to a Nuget repository containing the `chocolatey` and `chocolatey.extension` packages.

## Role Variables

The following variables are set to a default, but can be overridden:

| Variable            | Default   | Purpose                                                                    |
| ------------------- | --------- | -------------------------------------------------------------------------- |
| chocolatey_version  | latest    | If you want to install a specific version of Chocolatey, this can be used. |
| chocolatey_features | See below | Specify features and their state.                                          |
| chocolatey_config   | See below | Specify configuration values                                               |
| install_gui         | false     | Installs ChocolateyGUI and ChocolateyGUI Extension if set                  |

`chocolatey_features` accepts a hashtable of feature names and if they are `enabled` or `disabled.`

By default, this sets the following features:

| Feature                                              | State    |
| ---------------------------------------------------- | -------- |
| showNonElevatedWarnings                              | Disabled |
| useBackgroundService                                 | Enabled  |
| useBackgroundServiceWithNonAdministratorsOnly        | Enabled  |
| allowBackgroundServiceUninstallsFromUserInstallsOnly | Enabled  |
| excludeChocolateyPackagesDuringUpgradeAll            | Enabled  |

`chocolatey_config` accepts a hashtable of configuration names and the value you want.

By default, it configures the following settings:

| Configuration Name               | Value                                 |
| -------------------------------- | ------------------------------------- |
| cacheLocation                    | C:\ProgramData\chocolatey\choco-cache |
| commandExecutionTimeoutSeconds   | 14400                                 |
| backgroundServiceAllowedCommands | install,upgrade,uninstall             |

The following variables are required:

| Variable        | Example                | Purpose                                                |
| --------------- | ---------------------- | ------------------------------------------------------ |
| license_path    | chocolatey.license.xml | The path to a valid Chocolatey for Business license    | 
| license_content | {the license content}  | The content of a valid Chocolatey for Business license |

Only one of `license_path` and `license_content` are required, though both can be skipped if a `chocolatey-license` package is available on a specified repository.

The following variables are completely optional:

| Variable            | Example                                           | Purpose                              |
| ------------------- | ------------------------------------------------- | ------------------------------------ |
| repository          |                                                   | A list of dicts containing values    |
|     name            | ChocolateyInternal                                | The name of the source to add        |
|     url             | https://repo.local/repository/ChocolateyInternal/ | The URI of the source to add         |
|     user            | chocouser                                         | A user with access to the resources  |
|     password        | {a password}                                      | The password for the user            |

If repository values are specified, the repository will be used to source the packages for the rest of the role. It will also be added as a source on the machine, with the credentials as given.

You can specify multiple repositories.

# Dependencies

- ansible.windows
- chocolatey.chocolatey
- community.windows